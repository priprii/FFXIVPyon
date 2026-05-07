*A Blender addon for assisting with FFXIV modding workflows, developed by Pyon.*

> [!NOTE]
> Future Changes:
> - I'm setting my expectations for what I want to achieve with this addon back a bit because I am very busy with other projects. But I would like to get around to adding some tools for simplifying workflow of creating/editing animations eventually.

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
> I will soon create demonstration videos for the various features of this addon.

## Features

> [!NOTE]
> Currently, many features of this addon expect object names to be formatted like `Item Part {GroupID}.{PartID}` whereby `GroupID` is the identifier which objects sharing same material are assigned, and `PartID` is the unique identifier of each object within that group.
> 
> This is the resulting formatting when exporting mods via TexTools to FBX format
> 
> I would not recommend using Penumbra glTF export, TexTools workflow is more stable

The below previews are a bit outdated, I am lazy

![image](https://github.com/user-attachments/assets/57a83f9c-a034-4e4a-bb7c-4a0be9959f39) Import body for upscaling and/or weighting reference

![image](https://github.com/user-attachments/assets/65d99b54-ea12-40b0-b969-64cd07bac0db) Retarget armature/objects for yas/ivcs support, upscaling & mod merging

![image](https://github.com/user-attachments/assets/0d6e7833-fc24-4ec7-8a38-f8d2ac270fed) Assign weights to selected objects using upscaled body as weighting reference

![image](https://github.com/user-attachments/assets/79ae7907-3f60-481f-abc1-e29c8d89764c) Real-time projection of textures for easy doodling on your body/clothes

## Credits

> Weight Transfer Mode C is based on the projects below with some FFXIV specific changes:
> 
> https://github.com/rin-23/RobustSkinWeightsTransferCode
>
> https://github.com/sentfromspacevr/robust-weight-transfer

