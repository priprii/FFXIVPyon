import bpy
import sys
import webbrowser

def GetVersion():
    version = sys.modules.get("FFXIVPyon").bl_info.get("version", None)
    return ".".join(map(str, version))

class FFXIVPyonPanel(bpy.types.Panel):
    bl_label = f"FFXIVPyon v{GetVersion()}"
    bl_idname = "FFXIVPyon_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FFXIVPyon'
    bl_description = "Tools to assist with FFXIV modding workflows."
    
    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.operator("ffxivpyon.open_github", text="Github", icon='INFO')
        row.operator("ffxivpyon.open_kofi", text="Ko-fi", icon='SOLO_ON')

class FFXIVPyon_OT_open_github(bpy.types.Operator):
        """Open FFXIVPyon Github Documentation in browser"""
        bl_idname = "ffxivpyon.open_github"
        bl_label = "Github"

        def execute(self, context):
            webbrowser.open("https://github.com/priprii/FFXIVPyon")
            return {'FINISHED'}

class FFXIVPyon_OT_open_kofi(bpy.types.Operator):
        """Open Pyon's Ko-fi page in browser.\nBuy me a coffee if you like what I do! ^^"""
        bl_idname = "ffxivpyon.open_kofi"
        bl_label = "Ko-fi"

        def execute(self, context):
            webbrowser.open("https://ko-fi.com/primu")
            return {'FINISHED'}

classes = [
    FFXIVPyonPanel,
    FFXIVPyon_OT_open_github,
    FFXIVPyon_OT_open_kofi
]

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            pass
            
def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
