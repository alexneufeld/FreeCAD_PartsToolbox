## Various notes and things

Pile of experiments and notes related to FreeCAD, python, etc.

### Effects of .FCStd file compression on load times

I saved two versions of the same file and tried importing them with the **AddObject** command. before importing, I changed the [file compression level](https://wiki.freecadweb.org/File%20Format%20FCStd) in each file: one file was set to max compression, the other to min. This change seems to make no difference in the time it takes to execute the following code:

``` python
st = time.time()
    the_obj = self.objlist.currentText()
    fpath = os.path.join(MCBase.objpath,the_obj+".FCStd")
    importdoc = FreeCAD.openDocument(fpath,hidden=True)
    top_obj = importdoc.Part
    objlist = [top_obj,importdoc.ParamObjData] + top_obj.OutListRecursive
    Gui.Selection.clearSelection()
    for x in objlist:
      Gui.Selection.addSelection(x)
    Gui.runCommand('Std_Copy')
    Gui.Selection.clearSelection()
    FreeCAD.setActiveDocument(self.thedoc.Name)
    Gui.runCommand('Std_Paste',0)
    FreeCAD.closeDocument(importdoc.Name)
    print(f"obj import took {time.time()-st} s")
```
Both imports took ~0.12s over a few repetitions.
This result is nice, because maximizing the compression level decreased file size by over 90%! (132.1 KiB to 11.2 KiB in this case)

### Casting parameters to strings for use in expressions

FreeCAD allows us to set the *label* parameter of objects using an expression. so we can do something like this: `<<This is a string>>` (FreeCAD required strings to be enclosed in double angle brackets).
We can concatenate strings in the usual pythonic way: `<<Hello >> + <<World!>>`

Some functionality is not directly available, though. Let's say we want to include a dimension in a label. (Assume the current FreeCAD document has an object called `Part` with an `App::PropertyLength` property called `dim1`). The following expression will generate an error:

`<<A part with length>> + Part.dim1`

This behaviour is due to the fact that the expression engine doesn't cast the quantity to a string. the fix is as follows:

`<<A part with length>> + Part.dim1.UserString`

### Pile of useful FreeCAD forum threads, wiki pages, etc.

very important.

- [Loading UI forms using PySide](https://forum.freecadweb.org/viewtopic.php?f=10&t=5374)
- [Scripted objects with attachment](https://wiki.freecadweb.org/Scripted_objects_with_attachment)
- [Documenting Python Extensions](https://forum.freecadweb.org/viewtopic.php?t=47132)
- [FreeCAD external editor with Code – OSS](https://pythoncvc.net/?p=869)
- [[Wiki Discussion] Scripted Objects Complete Method Reference](https://forum.freecadweb.org/viewtopic.php?f=22&t=49194)
- [FeaturePython methods](https://wiki.freecadweb.org/FeaturePython_methods)
- [Feature Request: Part::FeaturePython claimChildren](https://forum.freecadweb.org/viewtopic.php?t=13112)
- [Prevent dragging items in the document tree.](https://forum.freecadweb.org/viewtopic.php?t=51917)

### Other useful link:

- [list of interchangeable standards for fasteners](https://fullerfasteners.com/tech/din-iso-en-crossover-chart/)

### Ref image of FreeCAD's object heirarchy
![](https://wiki.freecadweb.org/images/0/01/FreeCAD_core_objects.svg)

### Pulling thumbnail images from .FCStd files

The "Save Picture" GUI command just runs the following python code:

``` python
Gui.activeDocument().activeView().saveImage(path_to_image,width,height,'Current')
```

Digging around in the FreeCAD source  and Python console reveals some more potentially useful things:

``` python
# with a freecad doc open:
x = Gui.activeDocument()
x.ActiveView.fitAll()
# these 2 are the same?
x.ActiveView.viewAxonometric()
x.ActiveView.viewAxometric()
# produces a very close dupe of the current 3D view
x.ActiveView.saveImage(path,400,400,"Current")
# transparent background --> potentially useful
x.ActiveView.saveImage(path,400,400,"Transparent")
# this also works, but each triangle in the rendered 
# mesh becomes an svg object --> resource intensive
x.ActiveView.saveVectorGraphic(path)
```

There is also [This Tool](https://github.com/FreeCAD/FreeCAD/blob/5d49bf78de785a536f941f1a6d06d432582a95d3/src/Tools/freecad-thumbnailer) in the FreeCAD source that pulls embedded thumbnails from .FCStd files. 

Actually, the entire [FreeCAD/src/Tools](https://github.com/FreeCAD/FreeCAD/tree/5d49bf78de785a536f941f1a6d06d432582a95d3/src/Tools) directory is worth digging through at some point in the future.

Sliptonic has some possibly relevant notes [here.](https://github.com/FreeCAD/FreeCAD/blob/5d49bf78de785a536f941f1a6d06d432582a95d3/src/Mod/Path/Tools/README.md#tools)  

### List of objects to implement

- [ ] ISO 14579 thru ISO 14587
- [ ] standards for rubber grommets?
- [ ] coupling nuts
- [ ] DIN 976
- [ ] ISO 888 might provide a clean solution to fastener lengths


### Purge FreeCAD backup files recursively

```
find . -name "*.FCStd1" -type f -delete
```