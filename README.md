### FreeCAD Parts Toolbox ![](Icons/toolbox.png)

Copies standardized parts into your FreeCAD projects. 
Conceptually similar to utilities with the same name 
available for other closed-source CAD software

### Installing

```
cd ~/.FreeCAD/Mod
git clone $THISREPO$
```

You'll then have to use the [customization tool](https://wiki.freecadweb.org/Customize_Toolbars) to add the partsToolBox commands to a custom toolbar.

### How it Works

Parts are provided as `.FCStd` files. We use FreeCAD's existing 
ability to create parametric objects to our advantage.
The user facing command provided by this toolbox just copy
The correct document objects from files in the `ObjModels` directory
the active document. This approach has the advantage that no python 
code is required to add a new part to the library, which allows for 
faster growth of the toolbox.

For a better understanding of how parametric parts are implemented here, take a look at `ObjModels/DIN557.FCStd`. Also check out [This FreeCAD forum post.](https://forum.freecadweb.org/viewtopic.php?f=17&t=42183)

### Acknowledgements

Much of the dimensional data on objects provided by the toolbox
is based on the FreeCAD FastenersWB and BOLTS projects. 

Toolbox icon: [Adib Sulthon](https://www.flaticon.com/authors/adib-sulthon) - [www.flaticon.com](https://www.flaticon.com/)