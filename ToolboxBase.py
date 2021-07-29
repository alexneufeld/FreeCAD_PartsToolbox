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
# helper functions etc
#

import FreeCAD
import os
import time
from PySide import QtUiTools

# make the directories that relevant files are stored in
# available to the rest of the workbench
__dir__ = os.path.dirname(__file__)
iconPath = os.path.join(__dir__, "Icons")
objpath = os.path.join(__dir__, "ObjModels")
UIPath = os.path.join(__dir__, "UI")


def InsertParamObj(doc, objname):
    st = time.time()
    # copy the Part from the source to destination document
    fpath = os.path.join(objpath, objname)
    # hidden should be set to True, but that caused errors...
    importdoc = FreeCAD.openDocument(fpath, hidden=False)
    # doc must have an object called Part
    top_obj = importdoc.Part
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
        f"imported {objname} in {time.time()-st:.3f} s")


def runAddObjCmd():
    thedoc = FreeCAD.ActiveDocument
    # import the UI structure from disc
    UIFilePath = os.path.join(UIPath, "AddObject.ui")
    UI = QtUiTools.QUiLoader().load(UIFilePath)
    # configure the UI with our data and functions
    for f in os.listdir(objpath):
        if f[-6:] == ".FCStd":
            UI.comboBox.addItem(f)
    UI.accepted.connect(
        lambda: InsertParamObj(
            thedoc, UI.comboBox.currentText())
    )
    UI.show()
