import bpy
import re

from . import Util

class FFXIVPyon_PT_exporting(bpy.types.Panel):
    bl_label = "Exporting"
    bl_idname = "FFXIVPyon_PT_exporting"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FFXIVPyon'
    bl_parent_id = "FFXIVPyon_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.FFXIVPyonProps

        doCleanup = False

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Cleanup", icon='TRASH')
        
        if props.Weight_SourceObject and props.Weight_SourceObject.name in context.scene.objects:
            col = box.column(align=True)
            col.operator("ffxivpyon.remove_weightsource", text="Remove Weighting Source")
            doCleanup = True
        if UnusedArmaturesExist(context):
            col = box.column(align=True)
            col.operator("ffxivpyon.remove_armatures", text="Remove Unused Armatures")
            doCleanup = True

        if not doCleanup:
            col = box.column(align=True)
            col.label(text="Ready for export!", icon='CHECKMARK')
        else:
            col = box.column(align=True)
            col.label(text="Cleanup required!", icon='ERROR')
            col.label(text="The above cleanup is necessary before export.", icon='INFO')

        if EmptyGroupsExist(context):
            col = box.column(align=True)
            col.operator("ffxivpyon.remove_empties", text="Remove Empty Groups")

        if not doCleanup:
            box = layout.box()
            col = box.column(align=True)
            col.label(text="Export", icon='EXPORT')

            col = box.column(align=True)
            col.label(text="Export options coming soon!", icon='INFO')

class FFXIVPyon_OT_remove_empties(bpy.types.Operator):
    """Remove empty groups.\nThis cleanup step is optional, it just keeps the scene collection tidy!"""
    bl_idname = "ffxivpyon.remove_empties"
    bl_label = "Remove Empty Groups"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        for obj in list(context.scene.objects):
            if obj.type == 'EMPTY' and not obj.children:
                Util.RemoveObject(obj)
            elif obj.type == 'EMPTY':
                if all(child.type == 'EMPTY' and re.match(r".*Group \d+$", child.name) for child in obj.children):
                    for child in obj.children:
                        Util.RemoveObject(child)
                    Util.RemoveObject(obj)

        return {'FINISHED'}

def EmptyGroupsExist(context):
    for obj in list(context.scene.objects):
        if obj.type == 'EMPTY' and not obj.children:
            return True
        elif obj.type == 'EMPTY':
            if all(child.type == 'EMPTY' and re.match(r".*Group \d+$", child.name) for child in obj.children):
                return True
    return False

def UnusedArmaturesExist(context):
    for obj in list(context.scene.objects):
        if obj.type == 'ARMATURE' and all(child.parent != obj for child in context.scene.objects):
            return True
    return False

class FFXIVPyon_OT_remove_weightsource(bpy.types.Operator):
    """Remove Weighting Source Object."""
    bl_idname = "ffxivpyon.remove_weightsource"
    bl_label = "Remove Weighting Source"
    bl_options = {'UNDO'}

    def execute(self, context):
        props = context.scene.FFXIVPyonProps

        if props.Weight_SourceObject and props.Weight_SourceObject.name in context.scene.objects:
            Util.RemoveObject(props.Weight_SourceObject)
            props.Weight_SourceObject = None

        return {'FINISHED'}

class FFXIVPyon_OT_remove_armatures(bpy.types.Operator):
    """Remove unused armatures."""
    bl_idname = "ffxivpyon.remove_armatures"
    bl_label = "Remove Unused Armatures"
    bl_options = {'UNDO'}

    def execute(self, context):
        for obj in list(context.scene.objects):
            if obj.type == 'ARMATURE' and all(child.parent != obj for child in context.scene.objects):
                Util.RemoveObject(obj)

        return {'FINISHED'}

classes = [
    FFXIVPyon_PT_exporting,
    FFXIVPyon_OT_remove_empties,
    FFXIVPyon_OT_remove_weightsource,
    FFXIVPyon_OT_remove_armatures
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
