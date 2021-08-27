'''
Macro to set up a default new document for a parts toolbox object
- creates a part, body, and spreadsheet
- initializes some metadata properties
'''

import FreeCAD

# open a new document and add objects
Doc = FreeCAD.newDocument()
part = Doc.addObject("App::Part","Part")
body = Doc.addObject("PartDesign::Body","Body")
sheet = Doc.addObject('Spreadsheet::Sheet','Spreadsheet')
part.Group = [body, sheet]

# set some sensible default part properties
PartProperties = {
	"Type": "",
	"Id": "???", # set this to prompt the user to fill in their own part#
	"License": "LGPL-3.0-or-later",
	"LicenseURL": "https://www.gnu.org/licenses/lgpl-3.0-standalone.html",
}
# do the same for the document object
DocProperties = {
	"Comment": "",
	"Company": "",
	"CreatedBy": "FreeCAD PartToolBox authors",
	"License": "LGPL-3.0-or-later",
	"LicenseURL": "https://www.gnu.org/licenses/lgpl-3.0-standalone.html",
}
for key,val in DocProperties.items():
	setattr(Doc,key,val)
for key,val in PartProperties.items():
	setattr(part,key,val)

# done - recompute
Doc.recompute()
