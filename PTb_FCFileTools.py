# -*- coding: utf-8 -*-
# ***************************************************************************
# *                                                                         *
# *   Copyright (c) 2021 Alex Neufeld <alex.d.neufeld@gmail.com>            *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************
#
# functions to work with freecad files
#

import FreeCAD
import os
import shutil
from zipfile import ZipFile
import defusedxml.ElementTree as tree
from PTb_Base import UserParams


def getDependenciesRecursive(docObj):
    """
    recursively get dependencies of a given document object
    """
    dependencies = docObj.OutList[:]
    print(f"document {docObj.Name} depends on {dependencies}")
    full_list = []
    for item in dependencies:
        full_list.append(item.FileName)
        full_list.extend(getDependenciesRecursive(item))
    return list(set(full_list))


def verifySavedDoc():
    """
    Get the active FreeCAD document, and check that it is 
    saved to disk. Otherwise, raise an exception
    """
    doc = FreeCAD.ActiveDocument
    if not doc:
        raise NoOpenDocument
    path_to_doc = os.path.dirname(doc.FileName)
    if path_to_doc == "":
        raise NoOpenDocument
    return (doc, path_to_doc)


class NoOpenDocument(Exception):
    '''
    Custom exception class,
    for use when adding a part to the current document
    '''
    pass


def copyFreeCADDocument(docFilePath, destinationDir):
    """
    given a FreeCAD document saved to docFilePath, copy its file and
    any files it depends on to the directory destinationDir.
    """
    # open the document, get its dependencies, then close it
    docObj = FreeCAD.openDocument(docFilePath, hidden=True)
    files = [docObj.FileName] + getDependenciesRecursive(docObj)
    print("dependant files are ",files)
    FreeCAD.closeDocument(docObj.Name)
    # DocumentObject.FileName gets us the full path to the files
    # which is convenient
    for f in files:
        # copy each file. handle both .FCStd and save-as-directory
        # file formats
        if not os.path.exists(os.path.join(destinationDir, os.path.basename(f))):
            # don't copy files that already exist
            if f.endswith(".FCStd"):
                # .FCStd format
                shutil.copy(f, destinationDir)
            else:
                # directory format
                shutil.copytree(f, os.path.join(
                    destinationDir, os.path.basename(f)))
    return


def getDataFromFCFile(docPath):
    """
    given a FreeCAD document file, return metadata
    of a parts library object stored there.
    Handles directory and .FCStd formats
    """
    if os.path.isdir(docPath):  # save-as-folder mode
        doc = tree.parse(open(os.path.join(docPath, "Document.xml")))
    else:  # .FCStd file mode
        with ZipFile(docPath, 'r') as zippedFCStd:
            doc = tree.parse(zippedFCStd.open('Document.xml', 'r'))
    root = doc.getroot()
    # we have the xml data, let's get something useful out of it
    docObjects = list(root.iter(tag="ObjectData"))[0]
    partObj = None
    for x in docObjects:
        if x.attrib["name"] == "Part":
            partObj = x
    proplist = []
    if partObj:
        proplist = list(partObj.iter(tag="Properties"))[0]
    else:
        raise ValueError(f"Document {docPath} has no object named Part")
    metadata = {
        "Id": "",
        "Type": "",
        "License": "",
        "LicenseURL": "",
    }
    for prop in proplist:
        if prop.attrib["name"] in metadata.keys():
            metadata[prop.attrib["name"]] = prop[0].attrib["value"]
    return(metadata)


def getFCFiles(folder):
    """
    get all FreeCAD documents stored in 'folder'. finds files saved 
    as both .FCStd and directory format. Ignores FreeCAD backup files
    """
    freecadfiles = []
    for x in os.listdir(folder):
        if os.path.isfile(os.path.join(folder, x)):
            if x.endswith(".FCStd"):
                freecadfiles.append(x)
        else:
            if "Document.xml" in os.listdir(os.path.join(folder, x)):
                freecadfiles.append(x)
    return freecadfiles


def InsertParamObj(sourcePartPath, importMode):
    """
    Given a part filename, add a copy of that part to the 
    active FreeCAD document
    """
    try:
        doc, pathToDoc = verifySavedDoc()
    except NoOpenDocument:
        FreeCAD.Console.PrintError(
            "PartsToolbox Error: Active document not found or not saved to a file!\n")
        return
    partFileName = os.path.basename(sourcePartPath)
    partFilePath = os.path.join(
        pathToDoc, "ToolboxParts", partFileName)
    # place a "ToolboxParts" directory next to the open document:
    os.makedirs(os.path.dirname(partFilePath), exist_ok=True)
    # copy the parts document to the users project folder if it
    # isn't already there:
    copyFreeCADDocument(sourcePartPath, os.path.join(
        pathToDoc, "ToolboxParts"))
    # open the local copy of the part file so we can get an obj from it
    part_doc = FreeCAD.openDocument(partFilePath, hidden=True)
    # grab either a part or a body to link to:
    if hasattr(part_doc, "Part"):
        top_obj = part_doc.Part
    elif hasattr(part_doc, "Body"):
        top_obj = part_doc.Body
    else:
        FreeCAD.Console.PrintError(
            f"PartsToolbox Error: file {partFileName} has no suitable objects to copy!\n")
        return
    if importMode == 0:  # shapeBinder mode
        # add a shapebinder and assign an object to link
        binder = doc.addObject('PartDesign::SubShapeBinder', 'ToolboxPart')
        binder.Support = top_obj
        # modify the shapebinders properties so it behaves correctly
        binder.BindCopyOnChange = 'Enabled'
        # binder renders transparent w. yellow lines if this is True.
        binder.ViewObject.UseBinderStyle = UserParams.GetBool("UseBinderStyle")
        # set label to mirror source objects label
        # getExpression returns a tuple (propname, extressionStr)
        objLabel = top_obj.getExpression("Label")
        if objLabel:
            binder.setExpression("Label", objLabel[1])
    elif importMode == 1:  # regular App::Link mode
        link = doc.addObject('App::Link')
        link.LinkedObject = top_obj
        link.LinkCopyOnChange = 'Enabled'
        objLabel = top_obj.getExpression("Label")
        if objLabel:
            link.setExpression("Label", objLabel[1])
    elif importMode == 2:  # simple copy mode
        objlist = [top_obj] + top_obj.OutListRecursive
        FreeCAD.Gui.Selection.clearSelection()
        for x in objlist:
            FreeCAD.Gui.Selection.addSelection(x)
        FreeCAD.Gui.runCommand("Std_Copy")
        FreeCAD.Gui.Selection.clearSelection()
        FreeCAD.setActiveDocument(doc.Name)
        FreeCAD.Gui.runCommand("Std_Paste", 0)
    # set the active document back to the users project:
    # NOTE: FreeCAD.setActiveDocument(x) != FreeCAD.Gui.setActiveDocument(x)
    FreeCAD.setActiveDocument(doc.Name)
    FreeCAD.ActiveDocument.recompute()
    return
