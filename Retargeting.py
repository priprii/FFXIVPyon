import bpy
import re

from . import Util

class FFXIVPyon_PT_retargeting(bpy.types.Panel):
    bl_label = "Retargeting"
    bl_idname = "FFXIVPyon_PT_retargeting"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FFXIVPyon'
    bl_parent_id = "FFXIVPyon_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.FFXIVPyonProps
        
        box = layout.box()
        col = box.column(align=True)
        col.label(text="Retarget Armature", icon='MOD_ARMATURE')
        col = box.column(align=True)
        col.prop(props, "Retarget_TargetArmature")
        col = box.column(align=True)
        row = col.row(align=True)
        row.prop(props, "Retarget_RemoveUnweightedBones", text="", icon='GROUP_BONE')
        row.operator("ffxivpyon.retarget_to_armature", text="Retarget Armature")

        box = layout.box()
        col = box.column(align=True)
        mode = props.Retarget_ObjectRetargetMode
        if mode == 'GROUP':
            col.label(text="Retarget Object Group", icon='OBJECT_DATA')
        elif mode == 'PART':
            col.label(text="Retarget Object Part", icon='OBJECT_HIDDEN')
        row = col.row(align=True)
        row.prop(props, "Retarget_ObjectRetargetMode", expand=True)
        if mode == 'GROUP':
            col = box.column(align=True)
            col.label(text="Target Group:")
            col.prop(props, "Retarget_TargetObjectGroup")
            col.prop(props, "Retarget_TargetUnmatchedAction")
            col = box.column(align=True)
            col.label(text="Replace with:")
            col.prop(props, "Retarget_SourceObjectGroup")
            col.prop(props, "Retarget_SourceUnmatchedAction")
            col = box.column(align=True)
            col.operator("ffxivpyon.replace_objectgroup", text="Retarget Object Group")
        elif mode == 'PART':
            col = box.column(align=True)
            col.label(text="Target Object:")
            col.prop(props, "Retarget_TargetObjectItem")
            col = box.column(align=True)
            col.label(text="Replace with:")
            col.prop(props, "Retarget_SourceObjectItem")
            col = box.column(align=True)
            col.operator("ffxivpyon.replace_object", text="Retarget Object")

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Remove Object Group", icon='CON_OBJECTSOLVER')
        col = box.column(align=True)
        col.prop(props, "Retarget_RemovalObjectGroup")
        col = box.column(align=True)
        col.operator("ffxivpyon.remove_objectgroup", text="Remove Object Group")

class FFXIVPyon_OT_retarget_to_armature(bpy.types.Operator):
    """Retarget all objects to the selected armature."""
    bl_idname = "ffxivpyon.retarget_to_armature"
    bl_label = "Retarget to Selected Armature"
    bl_options = {'UNDO'}

    def execute(self, context):
        props = context.scene.FFXIVPyonProps

        if not props.Retarget_TargetArmature:
            self.report({'ERROR'}, "No valid armature selected")
            return {'CANCELLED'}

        targetArmature = context.scene.objects.get(props.Retarget_TargetArmature)
        if not targetArmature or targetArmature.type != 'ARMATURE':
            self.report({'ERROR'}, "No valid armature selected")
            return {'CANCELLED'}

        for obj in context.scene.objects:
            if obj.type == 'MESH':
                for mod in obj.modifiers:
                    if mod.type == 'ARMATURE':
                        mod.object = targetArmature
                        obj.parent = targetArmature

        if props.Retarget_RemoveUnweightedBones:
            self.RemoveUnweightedBones(context, targetArmature)

        self.RemoveUnusedArmatures(context, exclude=targetArmature)

        targetArmature.name = "n_root"
        targetArmature.data.name = "n_root"

        return {'FINISHED'}

    def RemoveUnweightedBones(self, context, armature):
        meshUsers = [
            obj for obj in context.scene.objects
            if obj.type == 'MESH' and any(mod.type == 'ARMATURE' and mod.object == armature for mod in obj.modifiers)
        ]

        usedBones = set()
        for obj in meshUsers:
            for vg in obj.vertex_groups:
                usedBones.add(vg.name)

        bpy.ops.object.mode_set(mode='OBJECT')
        context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='EDIT')

        editBones = armature.data.edit_bones
        toRemove = [b.name for b in editBones if b.name not in usedBones]

        for name in toRemove:
            bone = editBones.get(name)
            if bone:
                editBones.remove(bone)

        bpy.ops.object.mode_set(mode='OBJECT')

    def RemoveUnusedArmatures(self, context, exclude):
        usedArmatures = set()
        for obj in context.scene.objects:
            if obj.type == 'MESH':
                for mod in obj.modifiers:
                    if mod.type == 'ARMATURE' and mod.object:
                        usedArmatures.add(mod.object)

        toRemove = [
            obj for obj in bpy.data.objects
            if obj.type == 'ARMATURE' and obj not in usedArmatures and obj != exclude
        ]

        for obj in toRemove:
            if obj.name in context.scene.objects:
                context.scene.collection.objects.unlink(obj)

            if obj.data.users == 0 and obj.data.name in bpy.data.armatures:
                bpy.data.armatures.remove(obj.data)

            bpy.data.objects.remove(obj)

class FFXIVPyon_OT_replace_objectgroup(bpy.types.Operator):
    """Replace object parts from Target object group with another object group."""
    bl_idname = "ffxivpyon.replace_objectgroup"
    bl_label = "Replace Object Group"
    bl_options = {'UNDO'}

    def execute(self, context):
        props = context.scene.FFXIVPyonProps

        source_name = props.Retarget_SourceObjectGroup
        target_name = props.Retarget_TargetObjectGroup
        source = context.scene.objects.get(source_name)
        target = context.scene.objects.get(target_name)

        if not source or not target or source == target:
            self.report({'ERROR'}, "No valid source/target selected")
            return {'CANCELLED'}

        source_base_name = source_name.rsplit(" Part ", 1)[0]
        target_base_name = target_name.rsplit(" Part ", 1)[0]

        source_match = re.search(r"Part (\d+)\.(\d+)$", source_name)
        target_match = re.search(r"Part (\d+)\.(\d+)$", target_name)
        if not source_match or not target_match:
            self.report({'ERROR'}, "Invalid object name format")
            return {'CANCELLED'}
        
        source_group = source_match.group(1)
        target_group = target_match.group(1)
        source_pattern = f"{source_base_name} Part {source_group}."
        target_pattern = f"{target_base_name} Part {target_group}."

        source_parts = {
            match.group(1): obj
            for obj in context.scene.objects
            if obj.name.startswith(source_pattern) and (match := re.search(rf"{source_pattern}(\d+)$", obj.name))
        }
        target_parts = {
            match.group(1): obj
            for obj in context.scene.objects
            if obj.name.startswith(target_pattern) and (match := re.search(rf"{target_pattern}(\d+)$", obj.name))
        }

        matched_part_numbers = []
        for part_number, target_obj in target_parts.items():
            source_obj = source_parts.get(part_number)

            if not source_obj:
                if props.Retarget_TargetUnmatchedAction == 'DISCARD':
                    Util.RemoveObject(target_obj)
                continue

            matched_part_numbers.append(part_number)

            target_name = target_obj.name
            target_data_name = target_obj.data.name
            parent = target_obj.parent
            armature_obj = next((m.object for m in target_obj.modifiers if m.type == 'ARMATURE'), None)

            Util.RemoveObject(target_obj)

            source_obj.name = target_name
            source_obj.parent = parent

            if source_obj.data.users == 1:
                source_obj.data.name = target_data_name
            else:
                new_data = source_obj.data.copy()
                new_data.name = target_data_name
                source_obj.data = new_data

            if armature_obj:
                for mod in source_obj.modifiers:
                    if mod.type == 'ARMATURE':
                        mod.object = armature_obj
                        break

        if props.Retarget_SourceUnmatchedAction == 'DISCARD':
            for part_number, obj in source_parts.items():
                if part_number not in matched_part_numbers:
                    Util.RemoveObject(obj)
        elif props.Retarget_SourceUnmatchedAction == 'ADD':
            for part_number, source_obj in source_parts.items():
                if part_number in matched_part_numbers:
                    continue

                new_obj_name = f"{target_base_name} Part {target_group}.{part_number}"
                new_data_name = f"{new_obj_name} Mesh Attribute"

                source_obj.name = new_obj_name
                if source_obj.data.users == 1:
                    source_obj.data.name = new_data_name
                else:
                    new_data = source_obj.data.copy()
                    new_data.name = new_data_name
                    source_obj.data = new_data

                source_obj.parent = parent

                if armature_obj:
                    for mod in source_obj.modifiers:
                        if mod.type == 'ARMATURE':
                            mod.object = armature_obj
                            break

        return {'FINISHED'}

class FFXIVPyon_OT_replace_object(bpy.types.Operator):
    """Replace Target object with another object."""
    bl_idname = "ffxivpyon.replace_object"
    bl_label = "Replace Object"
    bl_options = {'UNDO'}

    def execute(self, context):
        props = context.scene.FFXIVPyonProps

        source_name = props.Retarget_SourceObjectItem
        target_name = props.Retarget_TargetObjectItem
        source = context.scene.objects.get(source_name)
        target = context.scene.objects.get(target_name)

        if not source or not target or source == target:
            self.report({'ERROR'}, "No valid source/target selected")
            return {'CANCELLED'}

        target_data_name = target.data.name
        parent = target.parent
        armature_obj = next((m.object for m in target.modifiers if m.type == 'ARMATURE'), None)

        Util.RemoveObject(target)

        source.name = target_name
        source.parent = parent

        if source.data.users == 1:
            source.data.name = target_data_name
        else:
            new_data = source.data.copy()
            new_data.name = target_data_name
            source.data = new_data

        if armature_obj:
            for mod in source.modifiers:
                if mod.type == 'ARMATURE':
                    mod.object = armature_obj
                    break

        return {'FINISHED'}

class FFXIVPyon_OT_remove_objectgroup(bpy.types.Operator):
    """Remove the selected object group."""
    bl_idname = "ffxivpyon.remove_objectgroup"
    bl_label = "Remove Object Group"
    bl_options = {'UNDO'}

    def execute(self, context):
        props = context.scene.FFXIVPyonProps
        objgroup_name = props.Retarget_RemovalObjectGroup
        objgroup = context.scene.objects.get(objgroup_name)

        if not objgroup:
            self.report({'ERROR'}, "No valid group selected")
            return {'CANCELLED'}

        objgroup_base_name = objgroup_name.rsplit(" Part ", 1)[0]

        objgroup_match = re.search(r"Part (\d+)\.(\d+)$", objgroup_name)
        if not objgroup_match:
            self.report({'ERROR'}, "Invalid object name format")
            return {'CANCELLED'}
        
        obj_group = objgroup_match.group(1)
        obj_pattern = f"{objgroup_base_name} Part {obj_group}."

        objgroup_parts = {}
        for obj in context.scene.objects:
            if obj.name.startswith(obj_pattern):
                match = re.search(rf"{obj_pattern}(\d+)$", obj.name)
                if match:
                    objgroup_parts[match.group(1)] = obj

        for part_number, part_obj in objgroup_parts.items():
            Util.RemoveObject(part_obj)

        return {'FINISHED'}

classes = [
    FFXIVPyon_PT_retargeting,
    FFXIVPyon_OT_retarget_to_armature,
    FFXIVPyon_OT_replace_objectgroup,
    FFXIVPyon_OT_replace_object,
    FFXIVPyon_OT_remove_objectgroup
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
