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
from PTb_Base import UIPath, objpath
from PTb_FCFileTools import getDataFromFCFile

def partMetaBrowser():
    """
    Open a Qt widget to browse and edit metadata fields of parts library parts
    """
    PartIcon = FreeCAD.Gui.getIcon("PartsToolbox_Part")
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
        filename = tableWidget.item(row, 0).text()
        newData.update({filename: {
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
