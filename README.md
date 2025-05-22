*A Blender addon for assisting with FFXIV modding workflows.*

> [!NOTE]
> FFXIVPyon v2.X Upcoming Changes:
> - Additional body import options (more preset bodies, glTF/MDL file import)
> - Addition of export operation (FBX/glTF/MDL)
> - Addition of upscaling operation for simplifying mesh deforms
>
> Future Changes:
> - Full character import (from MCDF)
> - Import/Export textures (TEX) & animations (PAP)
> - Full mod import (PMP) with mod merging support
> - Full mod export (PMP)
> - Animation & facial expression editing operations

## Installation

- Download FFXIVPyon [here](https://github.com/priprii/FFXIVPyon/releases/latest/download/FFXIVPyon.zip)
- In Blender:
  - Edit > Preferences > Addons
  - Click the arrow in top-right > Install from Disk... > Locate the downloaded `FFXIVPyon.zip`
  - Search 'FFXIVPyon' & check the box to enable it.
  - You should now find FFXIVPyon in the Tools panel (hotkey 'N')

## Updating

- Follow steps as above, but uninstall the current version from Preferences > Addons, prior to installing new version

> [!NOTE]
> This addon is in active development, the below documentation is currently outdated.
> I will soon create demonstration videos for the various features of this addon instead of the below walls of text :3

## YAS Automation

*A tool for simplifying the process of adding YAS support to mods via weight transfer. Despite the name, this can also be used for non-YAS weight transfering.*

- Firstly, import the mod you're adding YAS to into a new Blender project.

### 1. Create Vertex Weight Body Source

- If the body used by the mod already has YAS weighting (with 'ya_' bones):
  - Select a body object part in the scene, check `From Selection` & click `Create Body Source` to create a joined copy of the body to use as a vertex weighting reference.
- Otherwise:
  - Uncheck `From Selection` & select a body to use from the list, then click `Create Body Source` to import the body for use as a vertex weighting reference.
- In either case, you'll end up with a BodySource object. You can optionally toggle the 'Lock' button to prevent accidental changes to this source object.

### 2. Reparent Armature

- If you imported an additional Rue body, your Scene may have multiple Armatures.
- In the `Target` list, select the Armature that has a number of 'yas' bones.
- Click `Reparent to Armature` to parent all objects in scene to this selected target Armature.

### 3. Assign Weights

- Select an object in the Scene which you would like to apply weights to.
- Enable which type of vertex groups you want to copy from BodySource to the selected object.
  - You should probably start with only 'YAS' selected & test clipping in-game before including other groups if necessary.
- Adjust the Weight Multiplier
  - Again, this is something you should leave at '1.0' to start with, and adjust if necessary.
- Click `Apply Weights`, this will copy the specified groups from BodySource to the selected object which resulted in any influence.
  - Note: Enable Weight Paint mode & select the Vertex Group in the Data tab to visualize the changes.
- Repeat this process for other objects, you can also repeat it for the same object to adjust the weighting result if necessary.

### 4. Cleanup

- When you are finished, click `Cleanup Scene` to remove the BodySource object and any unused Armatures in the Scene.
- You can then export as FBX & import to TexTools to replace the existing mod.

## Upscaling

*A tool to assist with the process of upscaling mods for different body types.*

Currently this just has option for importing Rue M/L body type, after import you should use the above `Reparent Armature` operation.
