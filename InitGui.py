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
# normally we would define an entire workbench here
# since we just want one GUI command, this file has
# less than usual

import FreeCAD
import os
import Toolbox
import shutil


class FCToolboxAddCmd:
    """
    command to add a standard part
    """

    def __init__(self):
        # parse the ObjModels directory for available parts
        import Toolbox
        self.iconPath = Toolbox.iconPath

    def GetResources(self):
        return {
            "Pixmap": os.path.join(self.iconPath, "toolbox.png"),
            "MenuText": "add a parts library object",
            "ToolTip": "add a configurable object from the parts database",
        }

    def IsActive(self):
        return True

    def Activated(self):
        import Toolbox
        # show the UI and allow the user to select an object
        Toolbox.OpenToolboxDock()


def InsertParamObj(thedoc, astr):
    print(astr)
    return


FreeCAD.Gui.addCommand("ToolBox_AddObject", FCToolboxAddCmd())
# setup preferences page
FreeCAD.Gui.addPreferencePage(os.path.join(
    Toolbox.UIPath, 'ToolboxPreferences.ui'), 'Parts Toolbox')
FreeCAD.Gui.addIconPath(Toolbox.iconPath)
# add the macros bundled with this module to the users macro directory
UserMacroDir = FreeCAD.ParamGet(
    "User parameter:BaseApp/Preferences/Macro").GetString("MacroPath")
toolboxmacros = os.listdir(Toolbox.MacroPath)
for f in toolboxmacros:
    shutil.copy(os.path.join(Toolbox.MacroPath, f), UserMacroDir)
print("Loaded Parts Toolbox")
