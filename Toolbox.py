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
# Most of the important stuff happens here
#

import FreeCAD
import os
from PySide import QtGui, QtUiTools, QtCore
import shutil
import defusedxml.ElementTree as tree
from zipfile import ZipFile

# make the directories that relevant files are stored in
# available to the rest of the workbench
__dir__ = os.path.dirname(__file__)
iconPath = os.path.join(__dir__, "Icons")
objpath = os.path.join(__dir__, "ObjModels")
UIPath = os.path.join(__dir__, "UI")
ThumbPath = os.path.join(__dir__, "Thumbnails")
MacroPath = os.path.join(__dir__, "Macro")
# set up some icons
PartIcon = QtGui.QIcon(os.path.join(iconPath, "PartsToolbox_Part.svg"))
FolderIcon = FreeCAD.Gui.getIcon("Group")
# import user preferences
UserParams = FreeCAD.ParamGet(
    "User parameter:BaseApp/Preferences/Mod/PartsToolbox")
# class that defines the dock widget
# adapted from here: https://wiki.freecadweb.org/Macro_SplitToolboxDock


class ToolboxDock(QtGui.QDockWidget):
    def __init__(self) -> None:
        mw = FreeCAD.Gui.getMainWindow()
        super(ToolboxDock, self).__init__()  # run inherited class constructor
        self.setParent(mw)
        self.setObjectName("ToolboxBrowser")
        self.setWindowTitle("Toolbox Browser")
        UIFilePath = os.path.join(UIPath, "ToolboxBrowserWidget.ui")
        UI = QtUiTools.QUiLoader().load(UIFilePath)
        self.setWidget(UI)
        # configure the UI with our data and functions
        # import object hierarchy
        ObjHierarchy = readObjTypes(objpath)
        userpath = UserParams.GetString("UserObjPath")
        if userpath:
            # prefix user objects with the 'User' category so that they are
            # placed in their own top level folder:
            ObjHierarchy += [(x[0], ["User"]+x[1])
                             for x in readObjTypes(userpath)]
        # store locations of files for reference
        objectpaths = {os.path.basename(x[0]).removesuffix(
            ".FCStd"): x[0] for x in ObjHierarchy}
        populate_tree(UI.treeWidget, ObjHierarchy)
        # set the import mode to the users preferred default
        UI.comboBox.setCurrentIndex(UserParams.GetInt("DefaultImportType"))
        # disable ok button initially
        # (it can't do anything until the user selects a part to add)
        UI.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
        # connect signals
        UI.treeWidget.clicked.connect(lambda: selectionChanged(
            UI.buttonBox.button(
                QtGui.QDialogButtonBox.Ok), UI.label, UI.treeWidget.currentItem()
        ))
        UI.buttonBox.accepted.connect(
            lambda: InsertParamObj(objectpaths[UI.treeWidget.currentItem().text(0)],
                                   UI.comboBox.currentIndex()))
        UI.show()


def OpenToolboxDock():
    '''
    start an instance of our custom dock
    this is what the GUI command actually does
    '''
    # check if the dock already exists (and is just hidden)
    pe = FreeCAD.Gui.getMainWindow().findChild(QtGui.QWidget, 'ToolboxBrowser')
    # initialize if needed, otherwise just toggle visibility
    if not pe:
        FreeCAD.Gui.getMainWindow().addDockWidget(
            QtCore.Qt.RightDockWidgetArea, ToolboxDock())
    else:
        pe.setVisible(pe.isHidden())


def readObjTypes(path):
    """
    given a path to a parts library part 'path', return the contents
    of the property Part.Type, split into individual strings where
    '|' is used as the delimiter 
    """
    data = []
    for item in getFCFiles(path):
        fullpath = os.path.join(path, item)
        catStr = getDataFromFCFile(fullpath)["Type"]
        data.append((fullpath, [x for x in catStr.split("|") if x != ""]))
    return data


def populate_tree(top_level_obj, items):
    '''
    Fill the tree view widget with an organized hierarchy
    of available parts
    '''
    for i, cats in items:
        # repeatedly add categories
        currentParent = top_level_obj
        for cat in cats:
            subobj = treeHasChild(cat, currentParent)
            if not subobj:
                subobj = QtGui.QTreeWidgetItem(currentParent)
            subobj.setIcon(0, FolderIcon)
            subobj.setText(0, cat)
            currentParent = subobj
        # add the object to the bottom level category
        subobj = QtGui.QTreeWidgetItem(currentParent)
        subobj.setIcon(0, PartIcon)
        subobj.setText(0, os.path.basename(i).removesuffix(".FCStd"))


def treeHasChild(text, QTreeObj):
    '''
    If a QTreeWidget _OR_ a QTreeWidgetItem has a child
    with specific text in column 0, return that child item.
    Otherwise, return None.
    '''
    if type(QTreeObj) == QtGui.QTreeWidget:
        x = QTreeObj.findItems(text, QtCore.Qt.MatchFixedString)
        if x:
            return x[0]
    else:
        for i in range(QTreeObj.childCount()):
            child = QTreeObj.child(i)
            if child.text(0) == text:
                return child
    return None


def selectionChanged(OKButton, thumbnailBox, selectedTreeItem):
    '''
    this runs every time the user selects a different part in the tree view
    '''
    if selectedTreeItem:
        # if a category is selected, disable the add button:
        if selectedTreeItem.childCount() > 0:
            OKButton.setEnabled(False)
            thumbnailBox.setPixmap(None)
        else:
            OKButton.setEnabled(True)
            # update thumbnail
            imagePath = os.path.join(
                objpath, selectedTreeItem.text(0), "thumbnails/Thumbnail.png")
            # this fails silently if no thumbnail is found
            pixmap = QtGui.QPixmap(imagePath)
            thumbnailBox.setPixmap(pixmap)
    else:
        OKButton.setEnabled(True)


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


def getDependenciesRecursive(docObj):
    """
    recursively get dependencies of a given document object
    """
    dependencies = docObj.OutList[:]
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
    docObjs = list(root.iter(tag="ObjectData"))[0]
    partObj = None
    for x in docObjs:
        if x.attrib["name"] == "Part":
            partObj = x
    proplist = []
    if partObj:
        proplist = list(partObj.iter(tag="Properties"))[0]
    else:
        raise ValueError(f"Document {docPath} has no object named Part")
    mdata = {
        "Id": "",
        "Type": "",
        "License": "",
        "LicenseURL": "",
    }
    for prop in proplist:
        if prop.attrib["name"] in mdata.keys():
            mdata[prop.attrib["name"]] = prop[0].attrib["value"]
    return(mdata)


def partMetaBrowser():
    """
    Open a Qt widget to browse and edit metadata fields of parts library parts
    """
    UIFilePath = os.path.join(UIPath, "PartMetaBrowser.ui")
    UI = QtUiTools.QUiLoader().load(UIFilePath)
    files = os.listdir(objpath)
    UI.tableWidget.setRowCount(0)
    UI.tableWidget.setColumnCount(5)
    header = UI.tableWidget.horizontalHeader()
    header.setResizeMode(QtGui.QHeaderView.ResizeToContents)
    header.setResizeMode(0, QtGui.QHeaderView.Stretch)
    tablecolumns = ["File Name", "Type", "Id", "License", "LicenseURL"]
    # keep a reference copy of all metadata as a nested list
    datalist = {}
    UI.tableWidget.setHorizontalHeaderLabels(tablecolumns)
    for f in files:
        itemData = getDataFromFCFile(os.path.join(objpath, f))
        if itemData:
            currentRow = UI.tableWidget.rowCount()
            UI.tableWidget.setRowCount(UI.tableWidget.rowCount()+1)
            fileNameItem = QtGui.QTableWidgetItem(PartIcon, f)
            # set filename items to be non-editable
            fileNameItem.setFlags(QtCore.Qt.ItemIsEnabled)
            UI.tableWidget.setItem(currentRow, 0, fileNameItem)
            datalist.update({f: {"Type": itemData["Type"], "Id": itemData["Id"],
                            "License": itemData["License"], "LicenseURL": itemData["LicenseURL"]}})
            for j, col in enumerate(tablecolumns[1:]):
                item = QtGui.QTableWidgetItem(itemData[col])
                UI.tableWidget.setItem(currentRow, j+1, item)
    UI.buttonBox.accepted.connect(
        lambda: (updateMetadata(datalist, UI.tableWidget), UI.close()))
    UI.show()


def updateMetadata(oldData, tableWidget):
    #tablecolumns = ["File Name", "Type", "ID", "License", "LicenseURL"]
    newData = {}
    for row in range(tableWidget.rowCount()):
        fname = tableWidget.item(row, 0).text()
        newData.update({fname: {
            "Type": tableWidget.item(row, 1).text(),
            "Id": tableWidget.item(row, 2).text(),
            "License": tableWidget.item(row, 3).text(),
            "LicenseURL": tableWidget.item(row, 4).text()
        }})
    for file in oldData.keys():
        if oldData[file] != newData[file]:
            FreeCAD.Console.PrintMessage(f"PartsToolbox: Update {file}\n")
            doc = FreeCAD.openDocument(
                os.path.join(objpath, file), hidden=True)
            for key, val in newData[file].items():
                setattr(doc.Part, key, val)
            doc.recompute()
            doc.save()
            FreeCAD.closeDocument(doc.Name)


def getFCFiles(folder):
    """
    get all FreeCAD documents stored in 'folder'. finds files saved 
    as both .FCStd and directory format. Ignores FreeCAD backup files
    """
    freecadfiles = []
    for x in os.listdir(folder):
        if os.path.isfile(os.path.join(folder,x)):
            if x.endswith(".FCStd"):
                freecadfiles.append(x)
        else:
            if "Document.xml" in os.listdir(os.path.join(folder, x)):
                freecadfiles.append(x)
    return freecadfiles
