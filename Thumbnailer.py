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
# WIP - code to generate thumbnails from FreeCAD files
# not sure how I want to use this functionality yet

import FreeCAD
#import Toolbox
import os

__dir__ = os.path.dirname(__file__)
iconPath = os.path.join(__dir__, "Icons")
objpath = os.path.join(__dir__, "ObjModels")
UIPath = os.path.join(__dir__, "UI")


def generate_thumbnails(Dry_run=False):
    # get full path to each .FCStd file in the toolbox
    filepaths = [os.path.join(dp, f) for dp, dn, fn in os.walk(
        os.path.expanduser(objpath)) for f in fn]
    # open each on and generate a thumbnail
    # 300x300 png
    for file in filepaths:
        # make directories until there's a place for the image
        filedir = os.path.dirname(file)
        imgfilename = os.path.basename(file)[:-6]+".png"
        while os.path.basename(filedir) != "ObjModels":
            imgfilename = os.path.join(os.path.basename(filedir), imgfilename)
            filedir = os.path.dirname(filedir)
        imgfilename = os.path.join(__dir__, "Thumbnails", imgfilename)
        os.makedirs(os.path.dirname(imgfilename), exist_ok=True)
        if Dry_run:
            print(f"write {imgfilename}")
        else:
            FreeCAD.openDocument(file)
            # FreeCAD.setActiveDocument(doc)
            FreeCAD.Gui.SendMsgToActiveView("ViewFit")
            FreeCAD.Gui.ActiveDocument.activeView().viewIsometric()
            FreeCAD.Gui.activeDocument().activeView().saveImage(
                imgfilename, 300, 300, "Transparent")


if __name__ == "__main__":
    generate_thumbnails()
