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
import time
from PySide import QtGui, QtUiTools, QtCore
import shutil

# make the directories that relevant files are stored in
# available to the rest of the workbench
__dir__ = os.path.dirname(__file__)
iconPath = os.path.join(__dir__, "Icons")
objpath = os.path.join(__dir__, "ObjModels")
UIPath = os.path.join(__dir__, "UI")
ThumbPath = os.path.join(__dir__, "Thumbnails")

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
        # setup tree view
        # https://srinikom.github.io/pyside-docs/PySide/QtGui/QTreeView.html
        model = QtGui.QFileSystemModel()
        model.setRootPath("/")
        UI.treeView.setModel(model)
        UI.treeView.setRootIndex(model.index(objpath))
        # hide extra columns (size, dataModified, etc.) that aren't useful here
        UI.treeView.hideColumn(1)
        UI.treeView.hideColumn(2)
        UI.treeView.hideColumn(3)
        UI.treeView.setHeaderHidden(True)
        UI.treeView.setExpandsOnDoubleClick(True)
        # disable ok button initially
        # (it can't do anything until the user selects a part to add)
        UI.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
        # connect signals
        UI.treeView.clicked.connect(lambda: selectionChanged(
            UI.buttonBox.button(QtGui.QDialogButtonBox.Ok), UI.label, getSelectedFile(UI.treeView)))
        UI.buttonBox.accepted.connect(
            lambda: InsertParamObjBind(getSelectedFile(UI.treeView)))
        # filter out unwanted files
        model.setNameFilters(["*.FCStd"])
        # TODO filtered files will still appear, they just won't be selectable
        # hide their rows to completely remove them
        #UI.treeView.setRowHidden(row, parent, True)
        UI.show()

# start an instance of our custom dock
# this is what the GUI command actually does


def OpenToolboxDock():
    # check if the dock already exists (and is just hidden)
    pe = FreeCAD.Gui.getMainWindow().findChild(QtGui.QWidget, 'ToolboxBrowser')
    # initialize if needed, otherwise just toggle visibility
    if not pe:
        FreeCAD.Gui.getMainWindow().addDockWidget(
            QtCore.Qt.RightDockWidgetArea, ToolboxDock())
    else:
        pe.setVisible(pe.isHidden())

# some helper functions to react to UI signals
#
# this one runs every time the user selects a different part in the tree view


def selectionChanged(OKbutton, thumbnailBox, selectedobj):
    # we need to do a couple of things here:
    # - update the preview thumbnail if a file was selected
    # - enable/disable the OK button
    # print(selectedobj)
    if selectedobj[-6:] == ".FCStd":
        OKbutton.setEnabled(True)
        # update thumbnail
        imgpath = os.path.join(ThumbPath, selectedobj[:-6]+".png")
        try:
            pixmap = QtGui.QPixmap(imgpath)
            thumbnailBox.setPixmap(pixmap)
        except Exception as E:
            print(f"failed to set thumbnail - {E}")
    else:
        OKbutton.setEnabled(False)


def getSelectedFile(tree):
    # when the user confirms their choice, parse out the selected file
    # the tree has a list of selected items, but the GUI only allows
    # one item to be selected -> just grab index 0
    SelectedItem = tree.selectedIndexes()[0]
    path = SelectedItem.data()
    # to handle items in folder: work up the tree to get the full path
    # from below the ObjModels folder
    while SelectedItem.parent().data() != "ObjModels":
        path = os.path.join(SelectedItem.parent().data(), path)
        SelectedItem = SelectedItem.parent()
    return path


def InsertParamObjBind(objname):
    # This version of object insert uses a shape binder to refer to part
    # subobject shapebinders do a lot of work for us, such as abstracting
    # the parts model hierarchy out of view of the user
    # we need an active document to put a part in
    doc = FreeCAD.ActiveDocument
    path_to_doc = os.path.dirname(doc.FileName)
    if not doc:
        FreeCAD.Console.PrintError(
            "Can't add Part - No active document found!\n")
        return
    if path_to_doc == "":
        FreeCAD.Console.PrintError(
            "Can't add Part - Active Document must be saved to a file!\n")
        return
    #  TODO: fix terrible variable names here
    objfilepath = os.path.join(
        path_to_doc, "ToolboxParts", os.path.basename(objname))
    # place a "ToolboxParts" directory next to the open document:
    os.makedirs(os.path.dirname(objfilepath), exist_ok=True)
    sourcefilepath = os.path.join(objpath, objname)
    # copy the parts document to the users project folder if it
    # isn't already there:
    if not os.path.exists(objfilepath):
        shutil.copyfile(sourcefilepath, objfilepath)
    # open the local copy of the part file se we can get an obj from it
    part_doc = FreeCAD.openDocument(objfilepath, hidden=True)
    # grab either a part or a body to link to with a shapebinder:
    if hasattr(part_doc, "Part"):
        top_obj = part_doc.Part
    elif hasattr(part_doc, "Body"):
        top_obj = part_doc.Body
    else:
        top_obj = None
    if top_obj:
        # keep track of how long this all takes
        st = time.time()
        # add a shapebinder and assign an object to link
        binder = doc.addObject('PartDesign::SubShapeBinder', 'ToolboxPart')
        binder.Support = top_obj
        FreeCAD.Console.PrintMessage(
            f"imported {objname} in {time.time()-st:.3f} s\n")
        # modify the shapebinders properties so it behaves correctly
        binder.BindCopyOnChange = 'Enabled'
        # binder renders transparent w. yellow lines if this is True.
        # perhaps a desirable effect? TODO make this a config option
        binder.ViewObject.UseBinderStyle = False
        # this probably won't work very well...
        # getExpression returns a tuple (propname, extressionStr)
        binder.setExpression("Label", top_obj.getExpression("Label")[1])
    # can't close the import document, it must stay opened in the background
    # or the part will error on recompute
    # FreeCAD.closeDocument(part_doc.Name)
    # set the active document back to the users project:
    # note: FreeCAD.setActiveDocument(x) != FreeCAD.Gui.setActiveDocument(x)
    FreeCAD.setActiveDocument(doc.Name)
    FreeCAD.ActiveDocument.recompute()
    return
