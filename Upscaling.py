import os
import sys

LibPath = os.path.join(os.path.dirname(__file__), 'lib')
if LibPath not in sys.path:
    sys.path.append(LibPath)

import bpy
import bmesh
import time
import json
import importlib
import mathutils
from mathutils import Vector
from mathutils import Matrix
from bpy.types import Operator
import numpy as np

from . import Util

MissingLibs = []
try: importlib.import_module("scipy")
except ImportError: MissingLibs.append("scipy")
if not MissingLibs:
    import scipy as sp

class FFXIVPyon_PT_upscaling(bpy.types.Panel):
    bl_label = "Upscaling"
    bl_idname = "FFXIVPyon_PT_upscaling"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FFXIVPyon'
    bl_parent_id = "FFXIVPyon_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.FFXIVPyonProps
        
        self.DrawSculptingSection(context)
        
        self.DrawWrappingSection(context)
            
    def DrawSculptingSection(self, context):
        props = context.scene.FFXIVPyonProps
        
        box = self.layout.box()
        box.label(text="Sculpting", icon='SCULPTMODE_HLT')
        
        mesh_objs = [o for o in context.selected_objects if o.type == 'MESH']
        
        if not props.Upscale_IsSculpting:
            if mesh_objs:
                box.label(text=f"{len(mesh_objs)} object(s) selected", icon='MESH_DATA')
            else:
                box.label(text="Select 1 or more objects to sculpt", icon='ERROR')
                
            col = box.column(align=True)
            col.prop(props, "Upscale_SculptBrushType")
            row = col.row(align=True)
            row.prop(props, "Upscale_SculptBrushRadius")
            row.prop(props, "Upscale_SculptBrushStrength")
            col.prop(props, "Upscale_SculptMirrorX")
            
            col = box.column(align=True)
            col.enabled = len(mesh_objs) > 0
            col.operator("ffxivpyon.start_sculpting", text="Start Sculpting", icon='SCULPTMODE_HLT')
        else:
            box.label(text="Sculpting is Active", icon='INFO')
            
            col = box.column(align=True)
            col.prop(props, "Upscale_SculptBrushType")
            row = col.row(align=True)
            row.prop(props, "Upscale_SculptBrushRadius")
            row.prop(props, "Upscale_SculptBrushStrength")
            col.prop(props, "Upscale_SculptMirrorX")

            box.operator("ffxivpyon.end_sculpting", text="End Sculpting", icon='CHECKMARK')
        
    def DrawWrappingSection(self, context):
        props = context.scene.FFXIVPyonProps
        
        box = self.layout.box()
        box.label(text="Wrapping", icon='MOD_SHRINKWRAP')

        col = box.column(align=True)
        col.prop(props, "Upscale_TargetObject")

        if not props.Upscale_IsWrapping:
            col = box.column(align=True)
            col.operator("ffxivpyon.start_wrapping", text="Start Wrapping")
            col.enabled = props.Upscale_TargetObject is not None and context.selected_objects is not None
        else:
            col = box.column(align=True)
            row = col.row(align=True)
            row.prop(props, "Upscale_WrapOffset")
            row.prop(props, "Upscale_WrapDisplaceStrength")

            col = box.column(align=True)
            row = col.row(align=True)
            if props.Upscale_IsWrapInfluenceEditing:
                row.prop(props, "Upscale_WrapInfluenceInvert", toggle=True, icon='ARROW_LEFTRIGHT')
                row.operator("ffxivpyon.apply_wrapinfluence",  text="Apply Wrap Influence", icon='BRUSH_DATA')
                row.operator("ffxivpyon.cancel_wrapinfluence", text="", icon='CANCEL_LARGE')

                row = col.row(align=True)
                row.operator("ffxivpyon.test_smooth", text="Smooth")
            else:
                row.prop(props, "Upscale_WrapInfluenceInvert", toggle=True, icon='ARROW_LEFTRIGHT')
                row.operator("ffxivpyon.start_wrapinfluence", text="Edit Wrap Influence", icon='BRUSH_DATA')
                hasWrapInfluence = False
                for entry in props.Upscale_Objects:
                    obj = entry.obj
                    if not obj:
                        continue
                    if Util.ObjectHasVertexGroup(obj, "Pyon_Wrap"):
                        hasWrapInfluence = True
                        break
                if hasWrapInfluence:
                    row.operator("ffxivpyon.cancel_wrapinfluence", text="", icon='CANCEL_LARGE')

            col = box.column(align=True)
            row = col.row(align=True)
            c1 = row.column(align=True)
            c2 = row.row(align=True)
            c1.operator("ffxivpyon.apply_wrapping", text="Apply Wrapping")
            c1.enabled = props.Upscale_TargetObject is not None
            c2.operator("ffxivpyon.cancel_wrapping", text="", icon='CANCEL_LARGE')

class FFXIVPyon_OT_start_sculpting(bpy.types.Operator):
    """
    Start sculpt session.

    Duplicates selected mesh objects, applies transforms, joins into a single
    temporary sculpt object, hides originals and switches to Sculpt mode.
    """
    bl_idname = "ffxivpyon.start_sculpting"
    bl_label  = "Start Sculpting"
    bl_options = {"UNDO"}

    def execute(self, context):
        props = context.scene.FFXIVPyonProps

        if props.Upscale_IsSculpting:
            self.report({'ERROR'}, "A sculpting session is already active.")
            return {'CANCELLED'}

        mesh_objs = [o for o in context.selected_objects if o.type == 'MESH']
        if not mesh_objs:
            self.report({'ERROR'}, "Select at least 1 mesh object to sculpt.")
            return {'CANCELLED'}

        scene = context.scene
        view_layer = context.view_layer

        if context.object and context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        duplicates = []
        source_names = [o.name for o in mesh_objs]

        obj_id_map = {obj.name: i for i, obj in enumerate(mesh_objs)}

        for obj in mesh_objs:
            dup = obj.copy()
            dup.data = obj.data.copy()
            dup.name = f"{obj.name}_SculptingSource"
            scene.collection.objects.link(dup)
            dup.matrix_world = obj.matrix_world.copy()

            view_layer.objects.active = dup
            dup.select_set(True)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            dup.select_set(False)

            me = dup.data

            id_attr = me.attributes.get("SculptingSourceId")
            if not id_attr:
                id_attr = me.attributes.new("SculptingSourceId", 'INT', 'POINT')

            index_attr = me.attributes.get("SculptingSourceIndex")
            if not index_attr:
                index_attr = me.attributes.new("SculptingSourceIndex", 'INT', 'POINT')

            src_id = obj_id_map[obj.name]
            for i, v in enumerate(me.vertices):
                id_attr.data[i].value = src_id
                index_attr.data[i].value = i

            duplicates.append(dup)

        if not duplicates:
            self.report({'ERROR'}, "Failed to create duplicates for sculpting.")
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')
        for dup in duplicates:
            dup.select_set(True)
        view_layer.objects.active = duplicates[0]

        bpy.ops.object.join()

        temp_obj = view_layer.objects.active
        temp_obj.name = "SculptingSource"

        temp_obj["SculptingSources"] = json.dumps(source_names)
        temp_obj["SculptingSourceIdMap"] = json.dumps(obj_id_map)
        temp_obj["SculptingSourceVertexCount"] = len(temp_obj.data.vertices)

        orig_positions = []
        for v in temp_obj.data.vertices:
            wp = temp_obj.matrix_world @ v.co
            orig_positions.append([wp.x, wp.y, wp.z])
        temp_obj["SculptingSourceOrigPos"] = json.dumps(orig_positions)

        for obj in mesh_objs:
            obj.hide_set(True)
            obj.select_set(False)

        bpy.ops.object.mode_set(mode='SCULPT')
        Util.UpdateSculptBrushProperties(self, context)

        props.Upscale_IsSculpting = True
        self.report({'INFO'}, f"Sculpting {len(mesh_objs)} object(s).")
        return {'FINISHED'}

class FFXIVPyon_OT_end_sculpting(bpy.types.Operator):
    """
    End sculpt session.

    Pushes sculpted vertex deltas from the temporary sculpt object back
    into the original objects (Basis + all shapekeys in a consistent way),
    then deletes the temporary object.
    Topology changes (dyntopo/remesh/etc.) are not supported.
    """
    bl_idname = "ffxivpyon.end_sculpting"
    bl_label  = "End Sculpting"
    bl_options = {"UNDO"}

    def execute(self, context):
        props = context.scene.FFXIVPyonProps
        scene = context.scene

        if not props.Upscale_IsSculpting:
            self.report({'ERROR'}, "No active sculpting session.")
            return {'CANCELLED'}

        temp_obj = scene.objects.get("SculptingSource")
        if not temp_obj or temp_obj.type != 'MESH':
            self.report({'ERROR'}, "Temporary sculpt object is missing.")
            props.Upscale_IsSculpting = False
            return {'CANCELLED'}

        prev_mode = context.object.mode if context.object else 'OBJECT'
        temp_active = context.view_layer.objects.active

        try:
            if prev_mode != 'SCULPT':
                temp = scene.objects.get("SculptingSource")
                if temp:
                    context.view_layer.objects.active = temp
                    bpy.ops.object.mode_set(mode='SCULPT')
            Util.SaveSculptBrushProperties(self, context)
        except Exception:
            pass
        finally:
            try:
                if context.object and context.object.mode != prev_mode:
                    bpy.ops.object.mode_set(mode=prev_mode)
            except Exception:
                pass
            if temp_active and temp_active.name in scene.objects:
                context.view_layer.objects.active = temp_active

        if context.object and context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        me = temp_obj.data
        verts = me.vertices

        orig_vert_count = temp_obj.get("SculptingSourceVertexCount", -1)
        if orig_vert_count != -1 and orig_vert_count != len(verts):
            self._restore_original_visibility(scene, temp_obj)
            props.Upscale_IsSculpting = False
            self.report(
                {'ERROR'},
                "Topology changed during sculpt (vertex count mismatch). "
                "Cannot auto-apply. Original objects restored; temporary sculpt kept."
            )
            return {'CANCELLED'}

        try:
            orig_positions = json.loads(temp_obj["SculptingSourceOrigPos"])
        except Exception:
            self._restore_original_visibility(scene, temp_obj)
            props.Upscale_IsSculpting = False
            self.report({'ERROR'}, "Original sculpt positions missing or corrupt. Cannot apply sculpt.")
            return {'CANCELLED'}

        if len(orig_positions) != len(verts):
            self._restore_original_visibility(scene, temp_obj)
            props.Upscale_IsSculpting = False
            self.report({'ERROR'}, "Original position count mismatch. Cannot apply sculpt.")
            return {'CANCELLED'}

        id_attr = me.attributes.get("SculptingSourceId")
        index_attr = me.attributes.get("SculptingSourceIndex")
        if not id_attr or not index_attr:
            self._restore_original_visibility(scene, temp_obj)
            props.Upscale_IsSculpting = False
            self.report({'ERROR'}, "Mapping attributes missing on sculpt object. Cannot apply sculpt.")
            return {'CANCELLED'}

        try:
            obj_id_map = json.loads(temp_obj.get("SculptingSourceIdMap", "{}"))
        except Exception:
            obj_id_map = {}
        inverse_id_map = {int(v): k for k, v in obj_id_map.items()}

        per_object_deltas: dict[str, list[tuple[int, mathutils.Vector]]] = {}
        for i, v in enumerate(verts):
            orig_id = id_attr.data[i].value
            orig_name = inverse_id_map.get(orig_id)
            idx = index_attr.data[i].value

            if orig_name is None or idx < 0:
                self._restore_original_visibility(scene, temp_obj)
                props.Upscale_IsSculpting = False
                self.report(
                    {'ERROR'},
                    "Mapping data invalid for some vertices. Cannot auto-apply sculpt."
                )
                return {'CANCELLED'}

            ox, oy, oz = orig_positions[i]
            orig_world = mathutils.Vector((ox, oy, oz))
            new_world = temp_obj.matrix_world @ v.co
            delta_world = new_world - orig_world

            if delta_world.length_squared == 0.0:
                continue

            per_object_deltas.setdefault(orig_name, []).append((idx, delta_world))

        changed_objs = []
        view_layer = context.view_layer
        prev_active = view_layer.objects.active

        for orig_name, data in per_object_deltas.items():
            obj = scene.objects.get(orig_name)
            if not obj or obj.type != 'MESH':
                continue

            obj.hide_set(False)

            vcount = len(obj.data.vertices)
            max_idx = max(idx for idx, _ in data)
            if max_idx >= vcount:
                self.report(
                    {'WARNING'},
                    f"{orig_name}: vertex count changed, skipping sculpt application."
                )
                continue

            inv = obj.matrix_world.inverted()

            shape_keys = obj.data.shape_keys
            if not shape_keys or not shape_keys.key_blocks:
                for idx, delta_world in data:
                    delta_local = inv @ delta_world
                    obj.data.vertices[idx].co += delta_local
                obj.data.update()
                changed_objs.append(obj)
                continue

            key_blocks = shape_keys.key_blocks
            basis_block = key_blocks.get("Basis") or key_blocks[0]

            if len(basis_block.data) != vcount:
                self.report(
                    {'WARNING'},
                    f"{orig_name}: Basis shapekey vertex count mismatch, skipping sculpt application."
                )
                continue

            bad = False
            for kb in key_blocks:
                if len(kb.data) != vcount:
                    self.report(
                        {'WARNING'},
                        f"{orig_name}: Shapekey '{kb.name}' vertex count mismatch, skipping sculpt application."
                    )
                    bad = True
                    break
            if bad:
                continue

            basis_old = [v.co.copy() for v in basis_block.data]
            shapekey_old = {
                kb.name: [v.co.copy() for v in kb.data]
                for kb in key_blocks
                if kb is not basis_block
            }

            basis_new = basis_old[:]
            for idx, delta_world in data:
                delta_local = inv @ delta_world
                basis_new[idx] = basis_old[idx] + delta_local

            for i, co in enumerate(basis_new):
                basis_block.data[i].co = co

            for kb in key_blocks:
                if kb is basis_block:
                    continue
                old_coords = shapekey_old.get(kb.name)
                if not old_coords or len(old_coords) != vcount:
                    continue

                for i in range(vcount):
                    offset = old_coords[i] - basis_old[i]
                    kb.data[i].co = basis_new[i] + offset

            for i, v in enumerate(obj.data.vertices):
                v.co = basis_new[i].copy()

            obj.data.update()
            changed_objs.append(obj)

        self._restore_original_visibility(scene, temp_obj)

        bpy.ops.object.select_all(action='DESELECT')
        first_obj = None
        for obj in changed_objs:
            obj.select_set(True)
            if not first_obj:
                first_obj = obj
        if first_obj:
            view_layer.objects.active = first_obj
        else:
            view_layer.objects.active = prev_active

        self._safe_delete_temp(temp_obj, me)

        props.Upscale_IsSculpting = False
        self.report({'INFO'}, "Sculpt applied to original object(s).")
        return {'FINISHED'}

    def _restore_original_visibility(self, scene, temp_obj):
        """Unhide all source objects if sculpt cannot be applied."""
        try:
            source_names = json.loads(temp_obj.get("SculptingSources", "[]"))
        except Exception:
            source_names = []
        for name in source_names:
            obj = scene.objects.get(name)
            if obj and obj.type == 'MESH':
                obj.hide_set(False)

    def _safe_delete_temp(self, temp_obj, me):
        try:
            if temp_obj.name in bpy.data.objects:
                bpy.data.objects.remove(temp_obj, do_unlink=True)
        except ReferenceError:
            pass

        try:
            if me and (me.name in bpy.data.meshes) and me.users == 0:
                bpy.data.meshes.remove(me)
        except ReferenceError:
            pass

class FFXIVPyon_OT_start_wrapping(bpy.types.Operator):
    """
    Start wrapping.
    """
    bl_idname = "ffxivpyon.start_wrapping"
    bl_label = "Start Wrapping"
    bl_options = {"UNDO"}

    def execute(self, context):
        props = context.scene.FFXIVPyonProps
        props.Upscale_Objects.clear()

        target = props.Upscale_TargetObject
        if not target or target.type != 'MESH':
            self.report({'ERROR'}, "No valid target object selected.")
            return {'CANCELLED'}

        added = 0
        for obj in context.selected_objects:
            if obj.type != 'MESH' or obj == target:
                continue

            if obj.modifiers.get("Pyon_Wrap") and obj.modifiers.get("Pyon_Displace") and obj.modifiers.get("Pyon_Smooth"):
                entry = props.Upscale_Objects.add()
                entry.obj = obj
                added += 1
                continue

            if not obj.modifiers.get("Pyon_Wrap"):
                wrap = obj.modifiers.new("Pyon_Wrap", 'SHRINKWRAP')
                wrap.target = target
                wrap.wrap_method = 'NEAREST_SURFACEPOINT'
                wrap.offset = props.Upscale_WrapOffset

            if not obj.modifiers.get("Pyon_Displace"):
                disp = obj.modifiers.new("Pyon_Displace", 'DISPLACE')
                disp.strength  = props.Upscale_WrapDisplaceStrength
                disp.direction = 'NORMAL'

            if not obj.modifiers.get("Pyon_Smooth"):
                smooth = obj.modifiers.new("Pyon_Smooth", 'CORRECTIVE_SMOOTH')
                smooth.iterations = 3

            entry = props.Upscale_Objects.add()
            entry.obj = obj
            added += 1

        if added == 0:
            self.report({'ERROR'}, "No valid objects selected for wrapping to target.")
            return {'CANCELLED'}
        else:
            self.report({'INFO'}, f"Starting wrapping process for {added} object(s).")

        props.Upscale_IsWrapping = True
        return {'FINISHED'}

class FFXIVPyon_OT_apply_wrapping(bpy.types.Operator):
    """
    Apply wrapping.
    """
    bl_idname = "ffxivpyon.apply_wrapping"
    bl_label = "Apply Wrapping"
    bl_options = {"UNDO"}

    def execute(self, context):
        props = context.scene.FFXIVPyonProps
        Util.UpdateUpscalingObjectMods(self, context)

        count = 0
        depsgraph = context.evaluated_depsgraph_get()
        for entry in props.Upscale_Objects:
            obj = entry.obj
            if obj is None:
                continue
            
            objEval = obj.evaluated_get(depsgraph)
            newMesh = bpy.data.meshes.new_from_object(objEval)
            obj.data = newMesh
            
            Util.RemoveUpscalingMods(self, context)
            
            count += 1

        props.Upscale_Objects.clear()
        props.Upscale_IsWrapping = False
        self.report({'INFO'}, f"Wrapping applied to {count} object(s).")
        return {'FINISHED'}

class FFXIVPyon_OT_cancel_wrapping(bpy.types.Operator):
    """
    Cancel wrapping
    """
    bl_idname = "ffxivpyon.cancel_wrapping"
    bl_label = "Cancel Wrapping"
    bl_options = {"UNDO"}

    def execute(self, context):
        props = context.scene.FFXIVPyonProps
        
        Util.RemoveUpscalingMods(self, context)
        
        props.Upscale_Objects.clear()
        props.Upscale_IsWrapping = False
        return {'FINISHED'}

class FFXIVPyon_OT_start_wrapinfluence(Operator):
    """Add/Edit wrap influence mask
    This will add a temporary vertex group for painting areas of the mesh that the wrapping operation will influence"""
    bl_idname = "ffxivpyon.start_wrapinfluence"
    bl_label  = "Edit Wrap Influence"
    bl_options = {'UNDO'}

    def execute(self, context):
        props = context.scene.FFXIVPyonProps

        objs = [entry.obj for entry in props.Upscale_Objects if entry.obj]
        if not objs:
            self.report({'ERROR'}, "No valid objects selected.")
            return {'CANCELLED'}

        for obj in objs:
            vg = Util.AddVertexGroup(obj, "Pyon_Wrap")
            wrap = obj.modifiers.get("Pyon_Wrap")
            if wrap:
                wrap.vertex_group = vg.name
                wrap.invert_vertex_group = props.Upscale_WrapInfluenceInvert

        context.view_layer.objects.active = objs[0]
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')

        brush = bpy.context.tool_settings.weight_paint.brush
        if brush:
            brush.size = int(props.Upscale_WrapPaintRadius)
            brush.strength = props.Upscale_WrapPaintStrength

        props.Upscale_IsWrapInfluenceEditing = True
        return {'FINISHED'}

class FFXIVPyon_OT_apply_wrapinfluence(Operator):
    """Apply wrap influence mask"""
    bl_idname = "ffxivpyon.apply_wrapinfluence"
    bl_label  = "Apply Wrap Influence"
    bl_options = {'UNDO'}

    def execute(self, context):
        props = context.scene.FFXIVPyonProps

        bpy.ops.object.mode_set(mode='OBJECT')

        for entry in props.Upscale_Objects:
            obj = entry.obj
            if not obj:
                continue
            vg = obj.vertex_groups.get("Pyon_Wrap")
            if vg:
                obj.vertex_groups.active = vg
                bpy.context.view_layer.objects.active = obj
                try:
                    bpy.ops.object.vertex_group_smooth(group_select_mode='BONE_DEFORM', factor=0.5, repeat=3)
                except RuntimeError:
                    pass

        props.Upscale_IsWrapInfluenceEditing = False
        return {'FINISHED'}

class FFXIVPyon_OT_cancel_wrapinfluence(bpy.types.Operator):
    """Discard wrap influence mask"""
    bl_idname = "ffxivpyon.cancel_wrapinfluence"
    bl_label  = "Discard Wrap Influence"
    bl_options = {'UNDO'}

    def execute(self, context):
        props = context.scene.FFXIVPyonProps

        for entry in props.Upscale_Objects:
            obj = entry.obj
            if not obj:
                continue
            Util.RemoveVertexGroup(obj, "Pyon_Wrap")
            wrap = obj.modifiers.get("Pyon_Wrap")
            if wrap and wrap.vertex_group == "Pyon_Wrap":
                wrap.vertex_group = ""

        bpy.ops.object.mode_set(mode='OBJECT')
        props.Upscale_IsWrapInfluenceEditing = False
        return {'FINISHED'}

def SmoothVertexWeights(obj, group_name, distance_threshold=0.1, smoothing_iterations=10, smoothing_factor=1):
    if MissingLibs:
        return
    
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()

    verts = np.array([v.co[:] for v in bm.verts], dtype=np.float32)
    group_index = obj.vertex_groups[group_name].index

    deform_layer = bm.verts.layers.deform.verify()

    weights = np.zeros(len(bm.verts), dtype=np.float32)
    matched = np.zeros(len(bm.verts), dtype=bool)

    for i, v in enumerate(bm.verts):
        d = v[deform_layer]
        if group_index in d:
            weights[i] = d[group_index]
            matched[i] = True

    adjacency_list = [[] for _ in bm.verts]
    for edge in bm.edges:
        a, b = edge.verts[0].index, edge.verts[1].index
        adjacency_list[a].append(b)
        adjacency_list[b].append(a)

    row, col = [], []
    for i, neighbors in enumerate(adjacency_list):
        for j in neighbors:
            row.append(i)
            col.append(j)

    adjacency_matrix = sp.sparse.coo_array((np.ones(len(row)), (row, col)), shape=(len(bm.verts), len(bm.verts))).tocsr()

    unmatched = ~matched
    smooth_verts = np.zeros(len(bm.verts), dtype=bool)

    def GetPointsInRange(index):
        queue = [index]
        while queue:
            v = queue.pop()
            for n in adjacency_list[v]:
                if not smooth_verts[n] and np.linalg.norm(verts[index] - verts[n]) < distance_threshold:
                    smooth_verts[n] = True
                    queue.append(n)

    for i in range(len(bm.verts)):
        if unmatched[i]:
            GetPointsInRange(i)

    degrees = np.array(adjacency_matrix.sum(axis=1)).ravel()
    smooth_matrix = sp.sparse.diags(1 / degrees) @ adjacency_matrix
    smoothed_weights = weights.copy()

    for _ in range(smoothing_iterations):
        smoothed_weights = (1 - smoothing_factor) * smoothed_weights + smoothing_factor * (smooth_matrix @ smoothed_weights)
        smoothed_weights[~smooth_verts] = weights[~smooth_verts]

    for i, w in enumerate(smoothed_weights):
        obj.vertex_groups[group_name].add([i], float(w), 'REPLACE')

    bm.free()

def BlurVertexGroup(obj, group_name, iterations=1, factor=0.5):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')

    group_index = obj.vertex_groups[group_name].index
    obj.vertex_groups.active_index = group_index

    bpy.ops.mesh.select_all(action='SELECT')

    for _ in range(iterations):
        bpy.ops.object.vertex_group_smooth(factor=factor, repeat=1, expand=True)

    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')

def BlurVertexGroupB(obj, group_name, iterations=5, factor=0.5):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='OBJECT')

    group = obj.vertex_groups.get(group_name)
    if not group:
        return

    zero_weight_verts = []
    for i, v in enumerate(obj.data.vertices):
        try:
            weight = group.weight(i)
            if weight == 0:
                zero_weight_verts.append(i)
        except RuntimeError:
            zero_weight_verts.append(i)

    bpy.ops.object.mode_set(mode='EDIT')

    group_index = group.index
    obj.vertex_groups.active_index = group_index

    bpy.ops.mesh.select_all(action='SELECT')

    for _ in range(iterations):
        bpy.ops.object.vertex_group_smooth(factor=factor, repeat=1, expand=True)

    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')

    for i in zero_weight_verts:
        group.add([i], 0.0, 'REPLACE')

class FFXIVPyon_OT_test_smooth(Operator):
    """Smooth"""
    bl_idname = "ffxivpyon.test_smooth"
    bl_label  = "Smooth"
    bl_options = {'UNDO'}

    def execute(self, context):
        props = context.scene.FFXIVPyonProps

        for entry in props.Upscale_Objects:
            obj = entry.obj
            if not obj:
                continue
            vg = obj.vertex_groups.get("Pyon_Wrap")
            if vg:
                BlurVertexGroup(obj, "Pyon_Wrap")

        return {'FINISHED'}

class FFXIVPyon_OT_upscale_to_body(bpy.types.Operator):
    """
    Deforms a mesh to conform to a body mesh using proximity-based projection,
    preserving curvature and relative offsets. Supports X-axis mirroring.
    """
    bl_idname = "ffxivpyon.upscale_to_body"
    bl_label = "Upscale Object to Body"
    bl_options = {"UNDO"}

    def execute(self, context):
        props = context.scene.FFXIVPyonProps

        outfit_obj = context.object
        body_obj = props.Weight_SourceObject

        if not outfit_obj or outfit_obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh.")
            return {'CANCELLED'}

        if not body_obj or body_obj.type != 'MESH':
            self.report({'ERROR'}, "Target body must be a valid mesh object.")
            return {'CANCELLED'}

        outfit_mesh = outfit_obj.data
        bm = bmesh.new()
        bm.from_mesh(outfit_mesh)

        depsgraph = bpy.context.evaluated_depsgraph_get()
        body_eval = body_obj.evaluated_get(depsgraph)
        body_bvhtree = mathutils.bvhtree.BVHTree.FromObject(body_eval, depsgraph)

        world_to_local = outfit_obj.matrix_world.inverted()
        body_matrix = body_obj.matrix_world

        for v in bm.verts:
            world_pos = outfit_obj.matrix_world @ v.co
            hit = body_bvhtree.find_nearest(body_matrix.inverted() @ world_pos)

            if hit is None:
                continue

            hit_pos, normal, _, dist = hit
            hit_pos_world = body_matrix @ hit_pos

            if dist < props.Upscale_ProjectionDistance:
                direction = (world_pos - hit_pos_world).normalized()
                target_pos = hit_pos_world + normal * props.Upscale_SurfaceOffset

                influence = 1.0 - (dist / props.Upscale_ProjectionDistance)
                new_world_pos = world_pos.lerp(target_pos, influence)

                v.co = world_to_local @ new_world_pos

        bm.to_mesh(outfit_mesh)
        bm.free()
        body_eval.to_mesh_clear()

        if props.Upscale_ApplyMirror:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.symmetrize(direction='NEGATIVE_X')
            bpy.ops.object.mode_set(mode='OBJECT')

        return {'FINISHED'}

classes = [
    FFXIVPyon_PT_upscaling,
    FFXIVPyon_OT_start_sculpting,
    FFXIVPyon_OT_end_sculpting,
    FFXIVPyon_OT_start_wrapping,
    FFXIVPyon_OT_apply_wrapping,
    FFXIVPyon_OT_cancel_wrapping,
    FFXIVPyon_OT_start_wrapinfluence,
    FFXIVPyon_OT_apply_wrapinfluence,
    FFXIVPyon_OT_cancel_wrapinfluence,
    FFXIVPyon_OT_test_smooth
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
