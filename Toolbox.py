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
# we're importing pyside whether our python environment
# likes it or not >:)
try:
    from PySide import QtGui, QtUiTools, QtCore
except:
    from PySide2 import QtGui, QtUiTools, QtCore
import shutil
import yaml
import defusedxml.ElementTree as tree

# make the directories that relevant files are stored in
# available to the rest of the workbench
__dir__ = os.path.dirname(__file__)
iconPath = os.path.join(__dir__, "Icons")
objpath = os.path.join(__dir__, "ObjModels")
UIPath = os.path.join(__dir__, "UI")
ThumbPath = os.path.join(__dir__, "Thumbnails")
# set up some icons
PartIcon = QtGui.QIcon(os.path.join(iconPath, "PartsToolbox_Part.svg"))
FolderIcon = QtGui.QIcon(os.path.join(iconPath, "Group.svg"))
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
        # import object hierarchy from yaml
        ObjHierarchy = readObjTypes()
        # recursive function to parse the nested list
        populate_tree(UI.treeWidget, ObjHierarchy)
        # disable ok button initially
        # (it can't do anything until the user selects a part to add)
        UI.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
        # connect signals
        UI.treeWidget.clicked.connect(lambda: selectionChanged(
            UI.buttonBox.button(
                QtGui.QDialogButtonBox.Ok), UI.label, UI.treeWidget.currentItem()
        ))
        UI.buttonBox.accepted.connect(
            lambda: InsertParamObjBind(UI.treeWidget.currentItem().text(0)))
        # TODO filtered files will still appear, they just won't be selectable
        # hide their rows to completely remove them
        #UI.treeView.setRowHidden(row, parent, True)
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


def readObjTypes():
    data = []
    for item in os.listdir(objpath):
        catStr = getDataFromFCFolder(os.path.join(objpath, item))["Type"]
        data.append((item, catStr.split("|")))
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
                subobj = QtGui.QTreeWidgetItem(top_level_obj)
            subobj.setIcon(0, FolderIcon)
            subobj.setText(0, cat)
            currentParent = subobj
        # add the object to the bottom level category
        subobj = QtGui.QTreeWidgetItem(currentParent)
        subobj.setIcon(0, PartIcon)
        subobj.setText(0, i)
        print(i)


def treeHasChild(text, QTreeObj):
    '''
    If a QTreeWidget _OR_ a QTreeWidgetItem has a child
    with specific text in column 0, return that child item.
    Otherwise, return None.
    '''
    if type(QTreeObj) == QtGui.QTreeWidget:
        x = QTreeObj.findItems(text, QtCore.Qt.MatchContains)
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
            try:
                pixmap = QtGui.QPixmap(imagePath)
                thumbnailBox.setPixmap(pixmap)
            except Exception as E:
                print(f"failed to set thumbnail - {E}")

    else:
        OKButton.setEnabled(True)


def InsertParamObjBind(partFileName):
    """
    Given a part filename, add a copy of that part to the 
    active FreeCAD document
    """
    doc, pathToDoc = verifySavedDoc()
    sourcePartPath = os.path.join(objpath, partFileName)
    partFilePath = os.path.join(
        pathToDoc, "ToolboxParts", partFileName)
    # place a "ToolboxParts" directory next to the open document:
    os.makedirs(os.path.dirname(partFilePath), exist_ok=True)
    # copy the parts document to the users project folder if it
    # isn't already there:
    copyFreecadDocument(sourcePartPath, os.path.join(
        pathToDoc, "ToolboxParts"))
    # open the local copy of the part file so we can get an obj from it
    part_doc = FreeCAD.openDocument(partFilePath, hidden=True)
    # grab either a part or a body to link to:
    if hasattr(part_doc, "Part"):
        top_obj = part_doc.Part
    elif hasattr(part_doc, "Body"):
        top_obj = part_doc.Body
    else:
        raise Exception(
            f"file {partFileName} has no suitable objects to copy!")
    # add a shapebinder and assign an object to link
    binder = doc.addObject('PartDesign::SubShapeBinder', 'ToolboxPart')
    binder.Support = top_obj
    # modify the shapebinders properties so it behaves correctly
    binder.BindCopyOnChange = 'Enabled'
    # binder renders transparent w. yellow lines if this is True.
    binder.ViewObject.UseBinderStyle = False
    # set label to mirror source objects label
    # getExpression returns a tuple (propname, extressionStr)
    binder.setExpression("Label", top_obj.getExpression("Label")[1])
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
    path_to_doc = os.path.dirname(doc.FileName)
    if not doc:
        raise Exception("Can't add Part - No active document found!")
    if path_to_doc == "":
        raise Exception(
            "Can't add Part - Active Document must be saved to a file!")
    return (doc, path_to_doc)


def copyFreecadDocument(docFilePath, destinationDir):
    """
    given a FreeCAD document saved to docFilePath, copy its file and
    any files it depends on to the directory destinationDir.
    """
    # open th document, get its dependencies, then close it
    docObj = FreeCAD.openDocument(docFilePath, hidden=True)
    files = [docObj.FileName] + getDependenciesRecursive(docObj)
    FreeCAD.closeDocument(docObj.Name)
    # DocumentObject.FileName gets us the full path to the files
    # which is convenient
    for f in files:
        print(f"copying {f} to {destinationDir}")
        # copy each file. handle both .FCStd and save-as-directory
        # file formats
        if not os.path.exists(os.path.join(destinationDir, os.path.basename(f))):
            # don't copy files that already exist
            if f.endswith(".FCStd"):
                # .FCStd format
                shutil.copyfile(f, destinationDir)
            else:
                # directory format
                shutil.copytree(f, os.path.join(
                    destinationDir, os.path.basename(f)))
    return


def getDataFromFCFolder(folderPath):
    """
    given a FreeCAD document folder, return metadata
    of a parts library object stored there
    """
    doc = tree.parse(open(os.path.join(folderPath, "Document.xml")))
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
        raise ValueError(f"Document {folderPath} has no object named Part")
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
        itemData = getDataFromFCFolder(os.path.join(objpath, f))
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
            print(f"Update {file}")
            doc = FreeCAD.openDocument(
                os.path.join(objpath, file), hidden=True)
            for key, val in newData[file].items():
                setattr(doc.Part, key, val)
            doc.recompute()
            doc.save()
            FreeCAD.closeDocument(doc.Name)
