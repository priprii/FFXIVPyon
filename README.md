*A Blender addon for assisting with FFXIV modding workflows.*

## Installation

- Download FFXIVPyon from [here](https://github.com/priprii/FFXIVPyon/releases/download/1.0/FFXIVPyon.zip)
- In Blender:
  - Edit > Preferences > Addons
  - Click the arrow in top-right > Install from Disk... > Locate the downloaded `FFXIVPyon.zip`
  - Search 'FFXIVPyon' & check the box to enable it.
  - You should now find FFXIVPyon in the Tools panel (hotkey 'N')

## YAS Automation

*A tool for simplifying the process of adding YAS support to mods via weight transfer. Despite the name, this can also be used for non-YAS weight transfering.*

- Firstly, import the mod you're adding YAS to into a new Blender project.
- If the mod's armature/base body does not include 'ya_' bones, additionally import a Rue/Yab body which includes YAS.

### 1. Create Vertex Weight Body Source

- Select one of the body object parts & under YAS Automation:
  - If you are using the mod's base body, enable 'As Duplicate', otherwise disable this option if using an imported Rue/Yab body (and you don't intend to export this body).
  - Click `Create Body Source`, this will merge the body parts to use as a vertex weighting reference.
  - You can optionally toggle the 'Lock' button to prevent accidental changes to this source object.

### 2. Reparent Armature

- If you imported a Rue/Yab body, your Scene may have multiple Armatures.
- In the `Target` list, select the Armature that has a number of 'yas' bones.
- Click `Reparent to Armature` to parent all objects in scene to this selected target Armature.

### 3. Assign Weights

- Select an object in the Scene which you would like to apply weights to.
- Enable which type of vertex groups you want to copy from the source body to the selected object.
  - You should probably start with only 'YAS' selected & test clipping in-game before including other groups if necessary.
- Adjust the Weight Multiplier
  - Again, this is something you should leave at '1.0' to start with, and adjust if necessary.
- Click `Apply Weights`, this will copy the specified groups from the source body to the selected object which resulted in any influence.
  - Note: Enable Weight Paint mode & select the Vertex Group in the Data tab to visualize the changes.
- Repeat this process for other objects, you can also repeat it for the same object to adjust the weighting result if necessary.

### 4. Cleanup

- When you are finished, click `Cleanup Scene` to remove the BodySource object and any unused Armatures in the Scene.
- You can then export as FBX & import to TexTools to replace the existing mod.
