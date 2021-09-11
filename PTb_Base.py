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

"""
Useful objects to be imported by other parts of the PartsToolbox package

Exports:
 - objPath is the path to the folder of FreeCAD parts
 - UIpath is the path to Qt UI xml files
 - iconPath is the path to icons included in this addon
 - UserParams holds FreeCAD user parameters related to the Parts Toolbox  
"""

import os
import FreeCAD

# relevant directories
__dir__ = os.path.dirname(__file__)
objpath = os.path.join(__dir__, "ObjModels")
UIPath = os.path.join(__dir__, "UI")
MacroPath = os.path.join(__dir__, "Macro")
iconPath = os.path.join(__dir__, "Icons")
# import user preferences
UserParams = FreeCAD.ParamGet(
    "User parameter:BaseApp/Preferences/Mod/PartsToolbox")
