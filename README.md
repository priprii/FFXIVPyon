*A Blender addon for assisting with FFXIV modding workflows, developed by Primu Pyon.*

> [!NOTE]
> FFXIVPyon v2.X Upcoming Changes:
> - Additional body import options (more preset bodies & selective import)
> - Model import/export operation (glTF/MDL)
> - Mod import/export operation (PMP+options with Penumbra auto-install)
> - Upscaling operation for simplifying mesh deforms
> 
> Import/export changes are because I dislike having to use TexTools, and glTF Import/Export in Penumbra often fails.
>
> Future Changes:
> - Full character import (from MCDF & in-game Renderer)
> - Import/Export textures (TEX) & animations (PAP)
> - Animation & facial expression editing operations
> - Automatic IK/constraints on rig for easier animation
> - Automatic physics on ears/tails for animations that were not made with wiggles in mind

## Installation

- Download FFXIVPyon [here](https://github.com/priprii/FFXIVPyon/releases/latest/download/FFXIVPyon.zip)
- In Blender:
  - Edit > Preferences > Addons
  - Click the arrow in top-right > Install from Disk... > Locate the downloaded `FFXIVPyon.zip`
  - (Blender may hang for a bit during installation, because this addon is quite big)
  - Search 'FFXIVPyon' & check the box to enable it.
  - You should now find FFXIVPyon in the Tools panel (hotkey 'N')

## Updating

- Follow steps as above, but uninstall the current version from Preferences > Addons, prior to installing new version

> [!NOTE]
> This addon is in active development, there is currently minimal documentation but feel free to contact me on Discord (id: Primu) if you need help with anything.
> I will soon create demonstration videos for the various features of this addon when I'm done implementing 2.X changes.

## Features

> [!NOTE]
> Currently, many features of this addon expect object names to be formatted like `Item Part {GroupID}.{PartID}` whereby `GroupID` is the identifier which objects sharing same material are assigned, and `PartID` is the unique identifier of each object within that group.
> 
> This is the resulting formatting when exporting mods via TexTools to FBX format
> 
> Penumbra glTF export may result in different naming format which is not yet supported, but will be supported in the next update

![image](https://github.com/user-attachments/assets/57a83f9c-a034-4e4a-bb7c-4a0be9959f39) Import body for upscaling and/or weighting reference

![image](https://github.com/user-attachments/assets/65d99b54-ea12-40b0-b969-64cd07bac0db) Retarget armature/objects for yas/ivcs support, upscaling & mod merging

![image](https://github.com/user-attachments/assets/0d6e7833-fc24-4ec7-8a38-f8d2ac270fed) Assign weights to selected objects using upscaled body as weighting reference

![image](https://github.com/user-attachments/assets/79ae7907-3f60-481f-abc1-e29c8d89764c) Real-time projection of textures for easy doodling on your body/clothes

