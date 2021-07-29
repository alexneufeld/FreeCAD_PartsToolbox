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

import FreeCAD
import os
import WB_locator

# these have to be global variables or 
# the FCToolboxAddCmd class members can't access them
global ToolboxIconPath
ToolboxIconPath = os.path.join(os.path.dirname(WB_locator.__file__), "Icons")
global ToolboxDataPath
ToolboxDataPath = os.path.join(os.path.dirname(WB_locator.__file__), "Icons")


# command to add a standard part
class FCToolboxAddCmd:
    def __init__(self):
        # parse the ObjModels directory for available parts
        # TODO
        pass

    def GetResources(self):
        return {
            "Pixmap": os.path.join(ToolboxIconPath, "toolbox.png"),
            "MenuText": "add a parts library object",
            "ToolTip": "add a configurable object from the parts database",
        }

    def IsActive(self):
        if FreeCAD.ActiveDocument:
            return True
        return False

    def Activated(self):
        # show the Ui and allow the user to select an object
        print("the command works!")


FreeCAD.Gui.addCommand("ToolBox_AddObject", FCToolboxAddCmd())
