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

# make the directories that relevant files are stored in
# available to the rest of the workbench
__dir__ = os.path.dirname(__file__)
iconPath = os.path.join(__dir__, "Icons")
objpath = os.path.join(__dir__, "ObjModels")
UIPath = os.path.join(__dir__, "UI")
ThumbPath = os.path.join(__dir__, "Thumbnails")

# class that defines the dock widget
# adapted from here: https://wiki.freecadweb.org/Macro_SplitPropEditor


class PropEditor(QtGui.QDockWidget):
    def __init__(self) -> None:
        mw = FreeCAD.Gui.getMainWindow()
        super(PropEditor, self).__init__()  # run inherited class constructor
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
            lambda: InsertParamObj(getSelectedFile(UI.treeView)))
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
            QtCore.Qt.RightDockWidgetArea, PropEditor())
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

# when the user confirms their choice, parse out the selected file


def getSelectedFile(tree):
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

# open the selected part and copy it into the active freecad document


def InsertParamObj(objname):
    doc = FreeCAD.ActiveDocument
    if not doc:
        FreeCAD.Console.PrintMessage("Can't add part - No active document found!")
        return
    st = time.time()
    # copy the Part from the source to destination document
    fpath = os.path.join(objpath, objname)
    # hidden should be set to True, but that caused errors...
    importdoc = FreeCAD.openDocument(fpath, hidden=False)
    # we allow for a few different importable objects:
    if hasattr(importdoc,"Part"):
        top_obj = importdoc.Part
    elif hasattr(importdoc,"Body"):
        top_obj = importdoc.Body
    else: 
        top_obj = None
    if top_obj:
        objlist = [top_obj] + top_obj.OutListRecursive
        FreeCAD.Gui.Selection.clearSelection()
        for x in objlist:
            FreeCAD.Gui.Selection.addSelection(x)
        FreeCAD.Gui.runCommand("Std_Copy")
        FreeCAD.Gui.Selection.clearSelection()
        FreeCAD.setActiveDocument(doc.Name)
        FreeCAD.Gui.runCommand("Std_Paste", 0)
        FreeCAD.closeDocument(importdoc.Name)
        FreeCAD.ActiveDocument.recompute()
        FreeCAD.Console.PrintMessage(
            f"imported {objname} in {time.time()-st:.3f} s\n")
    else:
        print(f"no suitable object to import in file {objname}")
