# FreeCAD Mechanical Components Workbench ![](Icons/WBIcon.svg)

A FreeCAD workbench for building and deploying libraries of parametric parts.

## Goals:

- Impliment a library of standard componenents that can be included in .FCStd files, such that those files can be shared/opened _without_ needing this workbench to be installed on the users computer

- Write tools that make it easy to add new parts to the library - eg: Parts are designed using regular FreeCAD documents

## Parametric Parts

### Adding Data

![](Icons/AddParamData.svg)

We store data in a format compatible with [the BOLTS specification.](https://www.bolts-library.org/en/docs/0.3/specification.html) This is a relatively simple, human-readable yaml file.

The **AddParamData** command imports a BLT class from one of the available yaml files. The data can then be used to drive parametric FreeCAD models. Most of the time, these models are the parts in our parts library.

### Adding a Part 

![](Icons/AddObject.svg)

The **addObject** command insert a parametric part into the active FreeCAD document.

### Creating new Parts

![](Icons/PObjTemplate.svg)

The **PObjTemplate** command opens a tempalte FreeCAD file that the user can use to create a new parametric part in. The edited tempate can be saved in the `ObjModels` folder to add it to the parts library

## Useful Resources

- [The ISO standards catalogue](https://www.iso.org/standards-catalogue/browse-by-ics.html) is a nice place to draw inspiration as to what sorts of components we should impliment in the library.
- [The FreeCAD FastenersWB](https://github.com/shaise/FreeCAD_FastenersWB) and [BOLTS Project](https://github.com/boltsparts/BOLTS) - 2 good examples of Parts Library functionality in FreeCAD
- [Full list of ASME standards](https://www.asme.org/codes-standards/find-codes-standards)
- [onlineocr.net](https://www.onlineocr.net/) and [gImageReader](https://github.com/manisandro/gImageReader) - OCR tools for pulling text out of PDF files

## Contributing

Feel free to open an Issue or pull request - They are always welcomed!