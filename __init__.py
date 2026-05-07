bl_info = {
    "name": "FFXIVPyon",
    "description": "Tools to assist with FFXIV modding workflows.",
    "author": "Pyon",
    "version": (3, 0, 0),
    "blender": (4, 0, 0),
    "wiki_url": "https://github.com/priprii/FFXIVPyon",
    "tracker_url": "",
    "location": "View3D > Sidebar > FFXIVPyon",
    "category": "3D View"
}

if "bpy" not in locals():
    import bpy
    Reloading = False
else:
    Reloading = True
    
if not Reloading:
    from . import FFXIVPyon
    from . import Util
    from . import Props
    from . import Retargeting
    from . import Upscaling
    from . import Weighting
    from . import Texturing
    from . import Exporting
else:
    import importlib
    importlib.reload(FFXIVPyon)
    importlib.reload(Util)
    importlib.reload(Props)
    importlib.reload(Retargeting)
    importlib.reload(Upscaling)
    importlib.reload(Weighting)
    importlib.reload(Texturing)
    importlib.reload(Exporting)
    
def register():
    FFXIVPyon.register()
    Util.register()
    Props.register()
    Retargeting.register()
    Upscaling.register()
    Weighting.register()
    Texturing.register()
    Exporting.register()
    
def unregister():
    Exporting.unregister()
    Texturing.unregister()
    Weighting.unregister()
    Upscaling.unregister()
    Retargeting.unregister()
    Props.unregister()
    Util.unregister()
    FFXIVPyon.unregister()
    
if __name__ == "__main__":
    register()
