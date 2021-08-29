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
# this file contains classes to construct the main GUI tools for this addon
#

import FreeCAD
import os
from PySide import QtGui, QtUiTools, QtCore
from PTb_Base import UIPath, objpath, UserParams
from PTb_FCFileTools import InsertParamObj, getFCFiles, getDataFromFCFile


def ToggleToolboxDock():
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


class ToolboxDock(QtGui.QDockWidget):
    def __init__(self) -> None:
        mw = FreeCAD.Gui.getMainWindow()
        super(ToolboxDock, self).__init__()  # run inherited class constructor
        self.setParent(mw)
        self.setObjectName("ToolboxBrowser")
        self.setWindowTitle("Toolbox Browser")
        UIFilePath = os.path.join(UIPath, "ToolboxBrowserWidget.ui")
        self.UI = QtUiTools.QUiLoader().load(UIFilePath)
        self.setWidget(self.UI)
        # configure the UI with our data and functions
        # import object hierarchy
        self.ObjHierarchy = self.readObjTypes(objpath)
        userpath = UserParams.GetString("UserObjPath")
        if userpath:
            # prefix user objects with the 'User' category so that they are
            # placed in their own top level folder:
            self.ObjHierarchy += [(x[0], ["User"]+x[1])
                                  for x in self.readObjTypes(userpath)]
        # store locations of files for reference
        self.objectpaths = {os.path.basename(x[0]).removesuffix(
            ".FCStd"): x[0] for x in self.ObjHierarchy}
        self.populate_tree()
        # set the import mode to the users preferred default
        self.UI.comboBox.setCurrentIndex(
            UserParams.GetInt("DefaultImportType"))
        # disable ok button initially
        # (it can't do anything until the user selects a part to add)
        self.UI.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(False)
        # connect signals
        self.UI.treeWidget.clicked.connect(self.selectionChanged)
        self.UI.buttonBox.accepted.connect(
            lambda: InsertParamObj(self.objectpaths[self.UI.treeWidget.currentItem().text(0)],
                                   self.UI.comboBox.currentIndex()))
        self.UI.show()

    def readObjTypes(self, path):
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

    def populate_tree(self):
        '''
        Fill the tree view widget with an organized hierarchy
        of available parts
        '''
        PartIcon = FreeCAD.Gui.getIcon("PartsToolbox_Part")
        FolderIcon = FreeCAD.Gui.getIcon("Group")
        for i, cats in self.ObjHierarchy:
            # repeatedly add categories
            currentParent = self.UI.treeWidget
            for cat in cats:
                subobj = self.treeHasChild(cat, currentParent)
                if not subobj:
                    subobj = QtGui.QTreeWidgetItem(currentParent)
                subobj.setIcon(0, FolderIcon)
                subobj.setText(0, cat)
                currentParent = subobj
            # add the object to the bottom level category
            subobj = QtGui.QTreeWidgetItem(currentParent)
            subobj.setIcon(0, PartIcon)
            subobj.setText(0, os.path.basename(i).removesuffix(".FCStd"))

    def treeHasChild(self, text, QTreeObj):
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

    def selectionChanged(self):
        '''
        this runs every time the user selects a different part in the tree view
        '''
        OKButton = self.UI.buttonBox.button(QtGui.QDialogButtonBox.Ok)
        selectedTreeItem = self.UI.treeWidget.currentItem()
        if selectedTreeItem:
            # if a category is selected, disable the add button:
            if selectedTreeItem.childCount() > 0:
                OKButton.setEnabled(False)
                self.UI.label.setPixmap(None)
            else:
                OKButton.setEnabled(True)
                # update thumbnail
                imagePath = os.path.join(
                    objpath, selectedTreeItem.text(0), "thumbnails/Thumbnail.png")
                # this fails silently if no thumbnail is found
                pixmap = QtGui.QPixmap(imagePath)
                self.UI.label.setPixmap(pixmap)
        else:
            OKButton.setEnabled(True)
