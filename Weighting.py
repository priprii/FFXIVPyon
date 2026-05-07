# Weight Transfer Mode C based on:
# https://github.com/rin-23/RobustSkinWeightsTransferCode
# https://github.com/sentfromspacevr/robust-weight-transfer

import os
import sys

LibPath = os.path.join(os.path.dirname(__file__), 'lib')
if LibPath not in sys.path:
    sys.path.append(LibPath)

import bpy
import bmesh
import math
import importlib
import subprocess
import threading
import numpy as np

from . import Util

InstalledDependencies = False
MissingLibs = []
try: importlib.import_module("robust_laplacian")
except ImportError: MissingLibs.append("robust_laplacian")
try: importlib.import_module("igl")
except ImportError: MissingLibs.append("libigl==2.6.1")
try: importlib.import_module("scipy")
except ImportError: MissingLibs.append("scipy")
if not MissingLibs:
    import igl
    import scipy as sp
    from scipy.spatial import cKDTree
    import robust_laplacian

class FFXIVPyon_PT_weighting(bpy.types.Panel):
    bl_label = "Weighting"
    bl_idname = "FFXIVPyon_PT_weighting"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FFXIVPyon'
    bl_parent_id = "FFXIVPyon_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.FFXIVPyonProps

        box = layout.box()
        row = box.row(align=True)
        row.label(text="Weighting Source", icon='MESH_CUBE')

        if not props.Weight_SourceObject:
            row = box.row()
            row.label(text="Source Object: None")
        
            box.operator("ffxivpyon.create_source", text="Create Weighting Source from Selected")
        else:
            lock_icon = 'LOCKED' if props.Weight_SourceObject.hide_select else 'UNLOCKED'
            row.operator("ffxivpyon.toggle_lock_source", text="", icon=lock_icon)

            row = box.row()
            row.label(text=f"Source Object: {props.Weight_SourceObject.name}")
            
            box.operator("ffxivpyon.remove_source", text="Remove Weighting Source")

        if props.Weight_SourceObject:
            box = layout.box()
            box.label(text="Transfer Weights", icon='MOD_DATA_TRANSFER')

            selectedObjects = [obj for obj in context.selected_objects if obj.type == 'MESH' and obj != props.Weight_SourceObject]
            if not selectedObjects:
                box.label(text="Select object(s) to receive weight.", icon='ERROR')
            else:
                col = box.column(align=True)
                col.label(text="Included Groups")
                row = col.row(align=True)
                row.prop(props, "Weight_IncludeYAS")
                row.prop(props, "Weight_IncludeIVCS")
                row.prop(props, "Weight_IncludeOther")

                col = box.column(align=True)
                col.label(text="Transfer Mode")
                row = col.row(align=True)
                row.prop(props, "Weight_TransferMode", expand=True)
                
                mode = props.Weight_TransferMode
                if mode == 'A':
                    self.DisplayWeightsA(context, box)
                elif mode == 'B':
                    self.DisplayWeightsB(context, box)
                elif mode == 'C':
                    self.DisplayWeightsC(context, box)
                
    def DisplayWeightsA(self, context, box):
        props = context.scene.FFXIVPyonProps

        col = box.column(align=True)
        col.label(text="Transfer via data transfer.", icon='INFO')

        row = col.row()
        split = row.split(factor=0.05)
        split.prop(props, "Weight_ExpandingProperties", text=" ", icon='DOWNARROW_HLT' if props.Weight_ExpandingProperties else 'RIGHTARROW', emboss=False)
        split = split.split(factor=0.35)
        split.prop(props, "Weight_ExpandingProperties", text="Properties", emboss=False)
        split.prop(props, "Weight_ExpandingProperties", text="", emboss=False)
        if props.Weight_ExpandingProperties:
            col.label(text='Vertex Matching')
            row = col.row(align=True)
            row.prop(props, "WeightA_MaxDistance")

            col.label(text='Influence')
            row = col.row(align=True)
            row.prop(props, "WeightA_InfluenceMultiplier")
        
        col = box.column(align=True)
        col.operator("ffxivpyon.transfer_weights_a", text="Transfer Weights")

    def DisplayWeightsB(self, context, box):
        props = context.scene.FFXIVPyonProps

        col = box.column(align=True)

        row = col.row()
        split = row.split(factor=0.05)
        col.label(text="Mode B is currently unavailable.", icon='ERROR')
        return
        
        split.prop(props, "Weight_ExpandingProperties", text=" ", icon='DOWNARROW_HLT' if props.Weight_ExpandingProperties else 'RIGHTARROW', emboss=False)
        split = split.split(factor=0.35)
        split.prop(props, "Weight_ExpandingProperties", text="Properties", emboss=False)
        split.prop(props, "Weight_ExpandingProperties", text="", emboss=False)
        if props.Weight_ExpandingProperties:
            col.label(text='Vertex Matching')
            row = col.row(align=True)
            row.prop(props, "WeightB_MinDistance")
            row.prop(props, "WeightB_MaxDistance")

            col.label(text='Influence')
            row = col.row(align=True)
            row.prop(props, "WeightB_InfluenceMultiplier")
        
        col = box.column(align=True)
        col.operator("ffxivpyon.transfer_weights_b", text="Transfer Weights")

    def DisplayWeightsC(self, context, box):
        layout = self.layout
        props = context.scene.FFXIVPyonProps

        if LibsNotAvailable(layout):
            return
        
        col = box.column(align=True)
        col.label(text="Transfer via weight filling.", icon='INFO')

        row = col.row()
        split = row.split(factor=0.05)
        split.prop(props, "Weight_ExpandingProperties", text=" ", icon='DOWNARROW_HLT' if props.Weight_ExpandingProperties else 'RIGHTARROW', emboss=False)
        split = split.split(factor=0.35)
        split.prop(props, "Weight_ExpandingProperties", text="Properties", emboss=False)
        split.prop(props, "Weight_ExpandingProperties", text="", emboss=False)
        if props.Weight_ExpandingProperties:
            col.label(text='Vertex Matching')
            row = col.row(align=True)
            row.prop(props, "WeightC_MinDistance")
            row.prop(props, "WeightC_MaxDistance")
            row = col.row(align=True)
            row.prop(props, "WeightC_MaxNormalAngle")

            col.label(text='Weight Filling')
            row = col.row(align=True)
            row.prop(props, 'WeightC_WeightFillSmoothing')
            row.prop(props, 'WeightC_WeightFillMode')
            
            row = col.row(align=True)
            row.prop(props, "WeightC_EqualizeCoincidentVertices")

        objs = lambda x: [obj for obj in x if obj != props.Weight_SourceObject and isinstance(obj.data, bpy.types.Mesh)]
        target_objs = objs(context.selected_objects)
        if (len(target_objs) > 0 and any(Util.HasTopologyModifiers(obj) for obj in target_objs)):
            col = layout.column(align=True)
            col.label(text='Topology modifiers must be applied!', icon='ERROR')

        source_obj = props.Weight_SourceObject
        if source_obj:
            armature_mods = [mod for mod in source_obj.modifiers if mod.type == "ARMATURE"]
            if len(armature_mods) == 0:
                col = layout.column(align=True)
                col.label(text=f'Subset is set to Deform Pose Bones,', icon='ERROR')
                col.label(text=f'but {source_obj.name} has no Armature Modifier')
            elif len(armature_mods) == 1:
                if not armature_mods[0].object:
                    col = layout.column(align=True)
                    col.label(text=f'Subset is set to Deform Pose Bones,', icon='ERROR')
                    col.label(text=f'but {source_obj.name} has an empty Armature Modifier object')
            else:
                col = layout.column(align=True)
                col.label(text=f'Subset is set to Deform Pose Bones,', icon='ERROR')
                col.label(text=f'but {source_obj.name} has multiple Armature Modifiers')

        col = box.column(align=True)
        col.operator("ffxivpyon.transfer_weights_c", text="Transfer Weights")
        col.operator('ffxivpyon.inpaint', text="Inpaint")

class FFXIVPyon_OT_create_source(bpy.types.Operator):
    """Create an object as weighting source from the selected object(s)."""
    bl_idname = "ffxivpyon.create_source"
    bl_label = "Create Weighting Source from Selected"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        props = context.scene.FFXIVPyonProps
        
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        target_objects = [o for o in context.selected_objects if o.type == 'MESH']

        if len(target_objects) == 0:
            self.report({'ERROR'}, "Invalid object selection")
            return {'CANCELLED'}
    
        hidden_states = {o.name: o.hide_get() for o in target_objects}
    
        bpy.ops.object.select_all(action='DESELECT')
        for o in target_objects:
            o.hide_set(False)
            o.select_set(True)
        bpy.ops.object.duplicate()
        duplicated_objects = [o for o in context.selected_objects if o.type == 'MESH']
    
        bpy.ops.object.select_all(action='DESELECT')
        for o in duplicated_objects:
            o.hide_set(False)
            o.select_set(True)
        context.view_layer.objects.active = duplicated_objects[0]
    
        if len(duplicated_objects) > 1:
            bpy.ops.object.join()
        
        result_obj = context.active_object
        Util.RenameObject(result_obj, "WeightingSource")

        props.Weight_SourceObject = result_obj
    
        return {'FINISHED'}

class FFXIVPyon_OT_toggle_lock_source(bpy.types.Operator):
    """Toggle the lock state of the weighting source object to prevent accidental changes."""
    bl_idname = "ffxivpyon.toggle_lock_source"
    bl_label = "Lock Weighting Source"
    bl_options = {'UNDO'}

    def execute(self, context):
        source = context.scene.FFXIVPyonProps.Weight_SourceObject
        if source:
            source.hide_select = not source.hide_select
        return {'FINISHED'}

class FFXIVPyon_OT_remove_source(bpy.types.Operator):
    """Remove Weighting Source Object."""
    bl_idname = "ffxivpyon.remove_source"
    bl_label = "Remove Weighting Source"
    bl_options = {'UNDO'}

    def execute(self, context):
        props = context.scene.FFXIVPyonProps

        if props.Weight_SourceObject and props.Weight_SourceObject.name in context.scene.objects:
            Util.RemoveObject(props.Weight_SourceObject)
            props.Weight_SourceObject = None

        return {'FINISHED'}

def CacheVertexGroups(obj):
    cache = {}
    for vg in obj.vertex_groups:
        weights = {v.index: g.weight for v in obj.data.vertices for g in v.groups if g.group == vg.index}
        cache[vg.name] = weights
    return cache

def RestoreCachedVertexGroups(obj, cache, props):
    include_prefixes = []
    if props.Weight_IncludeYAS:
        include_prefixes.append("ya_")
    if props.Weight_IncludeIVCS:
        include_prefixes.append("iv_")

    def should_include(name):
        if any(name.startswith(prefix) for prefix in include_prefixes):
            return True
        if props.Weight_IncludeOther and not name.startswith("ya_") and not name.startswith("iv_"):
            return True
        return False

    for vg in list(obj.vertex_groups):
        if should_include(vg.name):
            continue

        if vg.name in cache:
            vg_index = vg.index
            for v in obj.data.vertices:
                weight = cache[vg.name].get(v.index)
                if weight is not None:
                    vg.add([v.index], weight, 'REPLACE')
                else:
                    vg.remove([v.index])
        else:
            obj.vertex_groups.remove(vg)

def VertexGroupIsEmpty(obj, vg):
    vg_index = vg.index
    for v in obj.data.vertices:
        for g in v.groups:
            if g.group == vg_index:
                return False
    return True

def ApplyDataTransfer(context, sourceObj, targetObj, groupName, maxDistance):
    mod = targetObj.modifiers.new(name=groupName, type='DATA_TRANSFER')
    mod.object = sourceObj
    mod.use_vert_data = True
    mod.data_types_verts = {'VGROUP_WEIGHTS'}
    mod.vert_mapping = 'POLYINTERP_NEAREST'
    mod.use_max_distance = maxDistance != 0
    mod.max_distance = maxDistance
    mod.mix_mode = 'REPLACE'
    mod.mix_factor = 1
    mod.layers_vgroup_select_src = groupName
    mod.layers_vgroup_select_dst = 'NAME'

    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = targetObj
    targetObj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=mod.name)

def GetVertexCoords(obj):
    return np.array([obj.matrix_world @ v.co for v in obj.data.vertices])

def GetWeightArray(obj, vg_name):
    vg = obj.vertex_groups.get(vg_name)
    if not vg:
        return np.zeros(len(obj.data.vertices))
    weights = np.zeros(len(obj.data.vertices))
    for v in obj.data.vertices:
        for g in v.groups:
            if g.group == vg.index:
                weights[v.index] = g.weight
    return weights

def ApplyWeightArray(obj, vg_name, weights):
    if vg_name not in obj.vertex_groups:
        obj.vertex_groups.new(name=vg_name)
    vg = obj.vertex_groups[vg_name]

    weight_groups = defaultdict(list)
    for i, w in enumerate(weights):
        if w > 0:
            w = round(w, 4)
            weight_groups[w].append(i)

    for weight, indices in weight_groups.items():
        vg.add(indices, weight, 'REPLACE')

def TransferWeightsKDTree(source, target, source_vgs, influence=1.0):
    source_coords = GetVertexCoords(source)
    target_coords = GetVertexCoords(target)
    tree = cKDTree(source_coords)
    _, nearest = tree.query(target_coords)

    for name in source_vgs:
        source_weights = GetWeightArray(source, name)
        target_weights = source_weights[nearest] * influence
        ApplyWeightArray(target, name, target_weights)

def SmoothVertexGroup(obj, group):
    mesh = obj.data
    vg_index = group.index

    adjacency = {v.index: set() for v in mesh.vertices}
    for poly in mesh.polygons:
        for i in poly.vertices:
            for j in poly.vertices:
                if i != j:
                    adjacency[i].add(j)

    iterations = 4
    for _ in range(iterations):
        weights = {v.index: 0.0 for v in mesh.vertices}
        counts = {v.index: 0 for v in mesh.vertices}

        for v in mesh.vertices:
            try:
                self_weight = next(g.weight for g in v.groups if g.group == vg_index)
            except StopIteration:
                continue

            neighbors = adjacency[v.index]
            total_weight = self_weight
            count = 1

            for n in neighbors:
                nv = mesh.vertices[n]
                try:
                    neighbor_weight = next(g.weight for g in nv.groups if g.group == vg_index)
                    total_weight += neighbor_weight
                    count += 1
                except StopIteration:
                    continue

            weights[v.index] = total_weight / count
            counts[v.index] = count

        for idx, weight in weights.items():
            if counts[idx] > 0:
                group.add([idx], weight, 'REPLACE')

def GetClosestVertexWeights(srcVerts, srcTris, srcNorms, tarVerts, tarNorms, srcWeights, minSqrdDistThreshold, maxSqrdDistThreshold, degAngleThreshold):
    """
    Find closest matching vertices on source mesh relative to target mesh.

    Returns:
        matchedVerts: List of booleans indicating if each target vertex has a match
        srcWeightsInterp: List of interpolated weights on source mesh
    """
    
    closestSqrdDist, closestFaceIndex, closestPoint = igl.point_mesh_squared_distance(tarVerts, srcVerts, srcTris)
    t = srcTris[closestFaceIndex,:]

    v1 = srcVerts[t[:,0],:]
    v2 = srcVerts[t[:,1],:]
    v3 = srcVerts[t[:,2],:]
    closestBary = igl.barycentric_coordinates(closestPoint, v1, v2, v3)
    
    w1 = srcWeights[t[:,0],:]
    w2 = srcWeights[t[:,1],:]
    w3 = srcWeights[t[:,2],:]

    n1 = srcNorms[t[:,0],:]
    n2 = srcNorms[t[:,1],:]
    n3 = srcNorms[t[:,2],:]

    b1 = closestBary[:,0]
    b2 = closestBary[:,1]
    b3 = closestBary[:,2]
    b1 = b1.reshape(-1,1)
    b2 = b2.reshape(-1,1)
    b3 = b3.reshape(-1,1)
    
    srcWeightsInterp = w1*b1 + w2*b2 + w3*b3
    srcNormsInterp = n1*b1 + n2*b2 + n3*b3

    norm1 = np.linalg.norm(srcNormsInterp, axis=1, keepdims=True)
    norm2 = np.linalg.norm(tarNorms, axis=1, keepdims=True)
    srcNormsNormalized = srcNormsInterp / norm1
    tarNormsNormalized = tarNorms / norm2

    dotProduct = np.einsum('ij,ij->i', srcNormsNormalized, tarNormsNormalized)
    dotProduct = np.clip(dotProduct, -1.0, 1.0)
    radAngle = np.arccos(dotProduct)
    degAngle = np.degrees(radAngle)
    angleThreshold = np.full(degAngle.shape, degAngleThreshold)
    inAngleThreshold = degAngle <= angleThreshold

    degAngleFlipped = 180 - degAngle
    inAngleThreshold = np.logical_or(inAngleThreshold, degAngleFlipped <= angleThreshold)

    inDistThreshold = np.logical_and(
        closestSqrdDist >= minSqrdDistThreshold,
        closestSqrdDist <= maxSqrdDistThreshold
    )
    matchedVerts = np.logical_and(inDistThreshold, inAngleThreshold)   
    
    return matchedVerts, srcWeightsInterp

def GetFilledWeights(vertices, faceIndices, weights, matched, pointCloud):
    """
    Fill in (inpaint) unknown weights (matched[i] = False) using neighbor-weighted averaging (Laplacian smoothing).

    Args:
        vertices: List of target vertices
        faceIndices: List of target faces (index triples)
        weights: List of weights as a list of bone weights per vertex from source
        matched: List of bools indicating whether weights for particular vertex on source are known matches
    Returns:
        filledWeights: List of filled weights
    """

    if not pointCloud and faceIndices is not None and len(faceIndices) > 0:
        L, M = robust_laplacian.mesh_laplacian(vertices, faceIndices)
    else:
        L, M = robust_laplacian.point_cloud_laplacian(vertices)
    L = -L
    
    Minv = sp.sparse.diags(1 / M.diagonal())

    Q2 = -L + L*Minv*L
    Q2 = Q2.astype(np.float64)

    Aeq = sp.sparse.csc_matrix((0, L.shape[0]), dtype=np.float64)
    Beq = np.zeros((0, weights.shape[1]), dtype=np.float64)
    B = np.zeros(shape = (L.shape[0], weights.shape[1]), dtype=np.float64)

    b = np.array(range(0, int(vertices.shape[0])), dtype=np.int64)
    b = b[matched]
    bc = weights[matched,:].astype(np.float64)
    
    if not np.any(matched): raise RuntimeError("No matches")
    
    filledWeights = igl.min_quad_with_fixed(Q2, B, b, bc, Aeq, Beq, True)
    filledWeights = filledWeights.astype(np.float32)
    filledWeights = filledWeights.reshape(weights.shape)
    return filledWeights

def GetBoneFilteredWeights(weights, adjacencyMatrix):
    """
    Get weights filtered with bone limit

    Args:
        weights: List of weights
        adjacencyMatrix: List of adjacency matrix
    Returns:
        weights: Weights after discarding excess
    """

    weights[weights <= 0.0001] = 0
    boneLimit = 4
    if weights.shape[1] <= boneLimit:
        filtered = np.zeros_like(weights)
    else:
        count = np.count_nonzero(weights, axis=1)
        exceedsLimit = count > boneLimit
        k = weights.shape[1] - boneLimit
        weightIndices = np.argpartition(weights, kth=k, axis=1)[:, :k]
        rowIndices = np.arange(weights.shape[0])[:, None]
        erosionFilter = np.zeros_like(weights, dtype=bool)
        erosionFilter[rowIndices, weightIndices] = True
        erosionFilter = np.logical_and(erosionFilter, exceedsLimit[:, np.newaxis])
        erosionFilter = sp.sparse.csr_array(erosionFilter).astype(np.float32)
        degrees = adjacencyMatrix.sum(axis=1)
        smoothMatrix = (1/degrees[:, np.newaxis]) * adjacencyMatrix

        smoothingIterations = 5
        for _ in range(smoothingIterations):
            avgWeights = smoothMatrix @ erosionFilter
            erosionFilter = erosionFilter.maximum(avgWeights)
    
        filtered = erosionFilter.toarray()

    weights = (1 - filtered) * weights
    weights[weights <= 0.0001] = 0

    return weights

def EqualizeCoincidentVertexWeights(verts: np.ndarray, weights: np.ndarray, epsilon: float = 1e-4) -> np.ndarray:
    """
    Equalize weight for vertices occupying same position.
    This is performed after bone filtering & will apply a 2nd filtering pass.

    Args:
        verts: vertex positions
        weights: bone weights
        epsilon: distance tolerance for same position
    """

    if verts.shape[0] == 0 or weights.shape[0] == 0:
        return weights

    boneLimit = 4
    scale = 1.0 / epsilon # Eps should later be configurable
    quant = np.round(verts * scale).astype(np.int64)

    dtype = np.dtype([('x', np.int64), ('y', np.int64), ('z', np.int64)])
    structured = np.ascontiguousarray(quant).view(dtype)

    keys, inverse, counts = np.unique(structured, return_inverse=True, return_counts=True)

    group_indices = np.where(counts > 1)[0]
    if group_indices.size == 0:
        return weights

    B = weights.shape[1]
    for g in group_indices:
        idxs = np.where(inverse == g)[0] # vertices in coincident group
        group_weights = weights[idxs, :]
        avg = group_weights.mean(axis=0)

        if boneLimit > 0 and B > boneLimit:
            sorted_idx = np.argsort(avg)[::-1]
            keep = sorted_idx[:boneLimit]
            
            mask = np.zeros_like(avg, dtype=bool)
            mask[keep] = True
            avg[~mask] = 0.0
            
        avg[avg <= 0.0001] = 0.0
        weights[idxs, :] = avg

    weights[weights <= 0.0001] = 0.0
    return weights

def SmoothVertexWeigths(verts, weights, matched, adjacencyMatrix, adjacencyList, distanceThreshold, smoothingIterations):
    """
    Smooth filled weights in relation to neighbours.

    Args:
        verts: List of vertex positions (Vector3)
        weights: List of weights
        matched: List of bools
        adjacencyMatrix: List of adjacency matrix
        adjacencyList: List of Lists of neighbour indices
        distanceThreshold: Distance threshold for smoothing
        smoothingIterations: Number of smoothing iterations
    Returns:
        smoothedWeights: List of smoothed weights
    """
    
    unmatched = ~matched
    smoothVerts = np.zeros(verts.shape[0], dtype=bool)

    def GetPointsInRange(verts, vertIndex, distanceThreshold):
        """
        Get all neighbours of vertex within distanceThreshold
        """
        queue = []
        queue.append(vertIndex)
        while len(queue) != 0:
            v = queue.pop()
            if v < len(adjacencyList):
                neighbours = adjacencyList[v]
                for n in neighbours:
                    if ~smoothVerts[n] and np.linalg.norm(verts[vertIndex,:]-verts[n]) < distanceThreshold:
                        smoothVerts[n] = True
                        if n not in queue:
                            queue.append(n)

    for i in range(verts.shape[0]):
        if unmatched[i]:
            GetPointsInRange(verts, i, distanceThreshold)
            
    adjMatrix = adjacencyMatrix.astype(np.float32)
    degrees = adjMatrix.sum(axis=1)
    
    smoothMatrix = sp.sparse.diags(1/degrees) @ adjMatrix
    smoothedWeights = sp.sparse.csr_array(weights)

    smoothingFactor = 0.2
    for _ in range(smoothingIterations):
        smoothedWeights = (1 - smoothingFactor) * smoothedWeights + smoothingFactor * (smoothMatrix @ smoothedWeights)
        smoothedWeights[~smoothVerts] = weights[~smoothVerts]
    return smoothedWeights.todense()

def GetObjectWorldGeometry(obj: bpy.types.Object):
    """
    Get the world-space geometry of an object.

    Returns:
        worldVertices: List of world-space positions for vertices.
        indices: List of triangles (indices of vertices forming each triangle).
        worldNormals: List of normals in world space.
    """

    mesh: bpy.types.Mesh = obj.data
    mesh.calc_loop_triangles()

    vertices = np.empty((len(mesh.vertices), 3), dtype=np.float32)
    indices = np.empty((len(mesh.loop_triangles), 3), dtype=np.int64)
    normals = np.empty((len(mesh.vertices), 3), dtype=np.float32)

    mesh.vertices.foreach_get("co", vertices.reshape(-1))
    mesh.loop_triangles.foreach_get("vertices", indices.reshape(-1))
    mesh.vertices.foreach_get('normal', normals.reshape(-1))
    
    worldMatrix = np.array(obj.matrix_world)
    ones = np.ones((vertices.shape[0], 1))
    vertices4d = np.hstack((vertices, ones))
    worldVertices4d = (worldMatrix @ vertices4d.T).T
    worldVertices4d = np.ascontiguousarray(worldVertices4d, dtype=np.float32)
    worldVertices = worldVertices4d[:,:3] / worldVertices4d[:, 3][:, np.newaxis]
    worldNormals = (np.linalg.inv(worldMatrix[:3, :3]).T @ normals.T).T
    worldNormals = np.ascontiguousarray(worldNormals, dtype=np.float32)
    
    return worldVertices, indices, worldNormals

def GetVertexWeightsForGroup(obj: bpy.types.Object, vertexGroupName):
    """
    Get per-vertex weights of an object for specific vertex group.

    Args:
        obj: The object to get vertex weights for.
        vertexGroupName: Name of vertex group to get weights for.
    Returns:
        weights: List of per-vertex weights matching vertex group.
    """

    mesh: bpy.types.Mesh = obj.data
    if not isinstance(mesh, bpy.types.Mesh): return

    vgIndex = obj.vertex_groups[vertexGroupName].index

    weights = np.zeros(len(mesh.vertices), dtype=np.float32)
    for i, v in enumerate(mesh.vertices):
        for vg in v.groups:
            if vg.group == vgIndex:
                weights[i] = vg.weight

    return weights

def GetVertexWeights(obj: bpy.types.Object, filteredGroups: list[bool]=None):
    """
    Get the per-vertex weights of an object, with optional filtering for specific vertex groups.

    Args:
        obj: The object to get vertex weights for.
        filteredGroups: Optional list of booleans indicating which vertex groups to include (by index), if unset then all groups are included.
    Returns:
        weights: 2D list representing the per-vertex weights for all vertex groups, or only the filteredGroups.
    """

    mesh: bpy.types.Mesh = obj.data
    if not isinstance(mesh, bpy.types.Mesh): return

    weights = np.zeros((len(mesh.vertices), len(obj.vertex_groups)), dtype=np.float32)
    for i, v in enumerate(mesh.vertices):
        vertex = weights[i]

        for vg in v.groups:
            if vg.group >= weights.shape[1]:
                continue
            if filteredGroups and filteredGroups[vg.group]:
                vertex[vg.group] = vg.weight
            elif not filteredGroups:
                vertex[vg.group] = vg.weight

    return weights

def GetVertexNeighbourMatrix(mesh: bpy.types.Mesh, includeSelf=False):
    edges = np.empty((len(mesh.edges), 2), dtype=int)
    mesh.edges.foreach_get("vertices", edges.reshape(-1))

    vertexCount = len(mesh.vertices)
    eRows = np.hstack([edges[:, 0], edges[:, 1]])
    eCols = np.hstack([edges[:, 1], edges[:, 0]])
    data = np.ones(len(eRows), dtype=int)

    neighbourMatrix = sp.sparse.csr_array((data, (eRows, eCols)), shape=(vertexCount, vertexCount))
    if includeSelf:
        neighbourMatrix.setdiag(1)

    return neighbourMatrix
    
def GetVertexNeighbours(mesh: bpy.types.Mesh):
    edges = np.empty((len(mesh.edges), 2), dtype=int)
    mesh.edges.foreach_get("vertices", edges.reshape(-1))

    vertexCount = len(mesh.vertices)
    neighbours = [[] for _ in range(vertexCount)]
    for edge in edges:
        neighbours[edge[0]].append(edge[1])
        neighbours[edge[1]].append(edge[0])

    return neighbours

def BeginWeightTransfer(context, targetObjects):
    mapActiveGroup = {}
    for targetObject in targetObjects:
        if targetObject.vertex_groups.active:
            try:
                mapActiveGroup[targetObject.name] = targetObject.vertex_groups.active.name
            except UnicodeDecodeError:
                mapActiveGroup[targetObject.name] = None

    cacheActiveObject = context.view_layer.objects.active
    cacheSelectedObjects = [obj for obj in context.selected_objects]
    cacheMode = bpy.context.object.mode
    if cacheMode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    return (mapActiveGroup, cacheActiveObject, cacheSelectedObjects, cacheMode)

def EndWeightTransfer(context, targetObjects, mapActiveGroup, cacheActiveObject, cacheSelectedObjects, cacheMode):
    if bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    for obj in targetObjects:
        name = mapActiveGroup.get(obj.name)
        if name and name in obj.vertex_groups:
            obj.vertex_groups.active = obj.vertex_groups.get(name)

    bpy.ops.object.select_all(action='DESELECT')
    for obj in cacheSelectedObjects:
        obj.select_set(True)
    context.view_layer.objects.active = cacheActiveObject

    if cacheMode != 'OBJECT':
        bpy.ops.object.mode_set(mode=cacheMode)

def RemoveEmptyGroups(obj, sourceGroups):
    for sourceGroup in sourceGroups:
        vg = obj.vertex_groups.get(sourceGroup.name)
        if vg and VertexGroupIsEmpty(obj, vg):
            obj.vertex_groups.remove(vg)

class FFXIVPyon_OT_transfer_weights_a(bpy.types.Operator):
    """Transfer weights from WeightingSource to the selected object(s)."""
    bl_idname = "ffxivpyon.transfer_weights_a"
    bl_label = "Transfer Weights"
    bl_options = {'UNDO'}

    def execute(self, context):
        props = context.scene.FFXIVPyonProps
        sourceObject = props.Weight_SourceObject

        if not sourceObject or sourceObject.name not in context.scene.objects or sourceObject.type != 'MESH':
            self.report({'ERROR'}, "WeightingSource object has not been created")
            return {'CANCELLED'}

        targetObjects = [obj for obj in context.selected_objects if obj.type == 'MESH' and obj != sourceObject]
        if not targetObjects:
            self.report({'ERROR'}, "Select at least 1 valid target object")
            return {'CANCELLED'}

        depsgraph = context.evaluated_depsgraph_get()
        sourceObject = sourceObject.evaluated_get(depsgraph) # obj as evaluated obj after applied mods

        (mapActiveGroup, cacheActiveObject, cacheSelectedObjects, cacheMode) = BeginWeightTransfer(context, targetObjects)

        sourceGroups = list(sourceObject.vertex_groups)
        for targetObject in targetObjects:
            cacheTargetGroups = CacheVertexGroups(targetObject) # Cache current vertex groups
            targetGroupNames = {vg.name for vg in targetObject.vertex_groups}

            for sourceGroup in sourceGroups:
                if sourceGroup.name not in targetGroupNames:
                    targetObject.vertex_groups.new(name=sourceGroup.name)

                ApplyDataTransfer(context, sourceObject, targetObject, sourceGroup.name, props.WeightA_MaxDistance)

                if props.WeightA_InfluenceMultiplier != 1.0:
                    vg = targetObject.vertex_groups.get(sourceGroup.name)
                    if vg:
                        index = vg.index
                        for v in targetObject.data.vertices:
                            for g in v.groups:
                                if g.group == index:
                                    new_weight = min(g.weight * props.WeightA_InfluenceMultiplier, 1.0)
                                    vg.add([v.index], new_weight, 'REPLACE')

            RemoveEmptyGroups(targetObject, sourceGroups)
            RestoreCachedVertexGroups(targetObject, cacheTargetGroups, props)

        EndWeightTransfer(context, targetObjects, mapActiveGroup, cacheActiveObject, cacheSelectedObjects, cacheMode)

        self.report({'INFO'}, f'Weights transfered complete')
        return {'FINISHED'}

class FFXIVPyon_OT_transfer_weights_b(bpy.types.Operator):
    """Transfer weights from WeightingSource to the selected object(s)."""
    bl_idname = "ffxivpyon.transfer_weights_b"
    bl_label = "Transfer Weights"
    bl_options = {'UNDO'}

    def execute(self, context):
        props = context.scene.FFXIVPyonProps
        sourceObject = props.Weight_SourceObject

        if not sourceObject or sourceObject.name not in context.scene.objects or sourceObject.type != 'MESH':
            self.report({'ERROR'}, "WeightingSource object has not been created")
            return {'CANCELLED'}

        targetObjects = [obj for obj in context.selected_objects if obj.type == 'MESH' and obj != sourceObject]
        if not targetObjects:
            self.report({'ERROR'}, "Select at least 1 valid target object")
            return {'CANCELLED'}

        depsgraph = context.evaluated_depsgraph_get()
        sourceObject = sourceObject.evaluated_get(depsgraph) # obj as evaluated obj after applied mods

        (mapActiveGroup, cacheActiveObject, cacheSelectedObjects, cacheMode) = BeginWeightTransfer(context, targetObjects)

        sourceGroups = list(sourceObject.vertex_groups)
        colGroupIndices = {vg.index: i for i, vg in enumerate(sourceGroups)}

        sourceVerts = np.array([v.co[:] for v in sourceObject.data.vertices])
        sourceWeights = np.zeros((len(sourceVerts), len(sourceGroups)), dtype=np.float32)
        tree = cKDTree(sourceVerts)

        for v in sourceObject.data.vertices:
            for g in v.groups:
                col = colGroupIndices.get(g.group)
                if col is not None:
                    sourceWeights[v.index, col] = g.weight
        
        for targetObject in targetObjects:
            cacheTargetGroups = CacheVertexGroups(targetObject)
            targetVerts = np.array([v.co[:] for v in targetObject.data.vertices])
            dists, indices = tree.query(targetVerts)

            weights = sourceWeights[indices]
            weightCounts = np.count_nonzero(weights, axis=0)

            for i, count in enumerate(weightCounts):
                if count == 0:
                    continue

                sourceGroup = sourceGroups[i]
                if sourceGroup.name not in targetObject.vertex_groups:
                    targetObject.vertex_groups.new(name=sourceGroup.name)

                targetGroup = targetObject.vertex_groups[sourceGroup.name]
                if targetGroup.lock_weight:
                    continue

                groupWeights = weights[:, i] * props.WeightB_InfluenceMultiplier
                mask = (dists >= props.WeightB_MinDistance) & (dists <= props.WeightB_MaxDistance) & (groupWeights >= 0.00001)
                if not np.any(mask):
                    continue

                validIndices = np.nonzero(mask)[0]
                validWeights = groupWeights[mask]

                for idx, w in zip(validIndices, validWeights):
                    targetGroup.add([int(idx)], float(w), 'REPLACE')

                zeroIndices = np.setdiff1d(np.arange(len(groupWeights)), validIndices)
                if len(zeroIndices) > 0:
                    targetGroup.remove(zeroIndices.tolist())

            for vg in targetObject.vertex_groups:
                if not VertexGroupIsEmpty(targetObject, vg):
                    SmoothVertexGroup(targetObject, vg)

            RemoveEmptyGroups(targetObject, sourceGroups)
            RestoreCachedVertexGroups(targetObject, cacheTargetGroups, props)

        EndWeightTransfer(context, targetObjects, mapActiveGroup, cacheActiveObject, cacheSelectedObjects, cacheMode)

        self.report({'INFO'}, f'Weights transfered complete')
        return {'FINISHED'}

class FFXIVPyon_OT_transfer_weights_c(bpy.types.Operator):
    """Transfer weights from WeightingSource to the selected object(s)."""
    bl_idname = "ffxivpyon.transfer_weights_c"
    bl_label = "Transfer Weights"
    bl_options = {'UNDO'}

    def execute(self, context: bpy.types.Context):
        props = context.scene.FFXIVPyonProps
        sourceObject = props.Weight_SourceObject

        if not sourceObject or sourceObject.name not in context.scene.objects or sourceObject.type != 'MESH':
            self.report({'ERROR'}, "WeightingSource object has not been created")
            return {'CANCELLED'}

        targetObjects = [obj for obj in context.selected_objects if obj.type == 'MESH' and obj != sourceObject]
        if not targetObjects:
            self.report({'ERROR'}, "Select at least 1 valid target object")
            return {'CANCELLED'}

        depsgraph = context.evaluated_depsgraph_get()
        sourceObject = sourceObject.evaluated_get(depsgraph) # obj as evaluated obj after applied mods

        (mapActiveGroup, cacheActiveObject, cacheSelectedObjects, cacheMode) = BeginWeightTransfer(context, targetObjects)

        resultWeights = []
        sourceVerts, sourceTris, sourceNorms = GetObjectWorldGeometry(sourceObject)

        isDeformBone = [Util.VertexGroupIsDeformBone(sourceObject, g.name) for g in sourceObject.vertex_groups]
        sourceWeights = GetVertexWeights(sourceObject, isDeformBone)

        for targetObject in targetObjects:
            targetVerts, targetTris, targetNorms = GetObjectWorldGeometry(targetObject.evaluated_get(depsgraph)) # obj as evaluated obj after applied mods

            matchedVerts, weights = GetClosestVertexWeights(sourceVerts, sourceTris, sourceNorms, targetVerts, targetNorms, sourceWeights, props.WeightC_MinDistance ** 2, props.WeightC_MaxDistance ** 2, math.degrees(props.WeightC_MaxNormalAngle))

            try:
                weights = GetFilledWeights(targetVerts, targetTris, weights, matchedVerts, props.WeightC_WeightFillMode == 'POINTCLOUD')
            except Exception as e:
                self.report({'ERROR'}, f'Weight filling failed for {targetObject.name}')
                return {'CANCELLED'}

            adjMatrix = GetVertexNeighbourMatrix(targetObject.data, True)
            if props.WeightC_WeightFillSmoothing != 0:
                adjList = GetVertexNeighbours(targetObject.data)
                weights = SmoothVertexWeigths(targetVerts, weights, matchedVerts, adjMatrix, adjList, props.WeightC_MaxDistance, props.WeightC_WeightFillSmoothing)

            weights = GetBoneFilteredWeights(weights, adjMatrix)
            
            if props.WeightC_EqualizeCoincidentVertices:
                weights = EqualizeCoincidentVertexWeights(targetVerts, weights)
            
            resultWeights.append(weights)

        for targetObject, weights in zip(targetObjects, resultWeights):
            cacheTargetGroups = CacheVertexGroups(targetObject)
            sourceGroups = sourceObject.vertex_groups
            weightCounts = np.count_nonzero(weights, axis=0)

            for sourceGroup, weightCount in zip(sourceGroups, weightCounts):
                if weightCount > 0:
                    if sourceGroup.name not in targetObject.vertex_groups:
                        targetObject.vertex_groups.new(name=sourceGroup.name)

            isDeformBone = [Util.VertexGroupIsDeformBone(sourceObject, g.name) for g in sourceGroups]
            for i, w in enumerate(weights.T):
                weightCount = weightCounts[i]
                if weightCount == 0: continue
                
                sourceGroup = sourceGroups[i]
                targetGroup = targetObject.vertex_groups[sourceGroup.name]
                
                if targetGroup.lock_weight:
                    continue
                if not isDeformBone[i]:
                    continue
                    
                for j, wv in enumerate(w):
                    if wv >= 0.00001:
                        targetGroup.add([j], wv, 'REPLACE')
                ind = np.where(w < 0.00001)[0].tolist()
                targetGroup.remove(ind)

            RemoveEmptyGroups(targetObject, sourceGroups)
            RestoreCachedVertexGroups(targetObject, cacheTargetGroups, props)

        EndWeightTransfer(context, targetObjects, mapActiveGroup, cacheActiveObject, cacheSelectedObjects, cacheMode)

        self.report({'INFO'}, f'Weights transfered complete')
        return {'FINISHED'}

def LibsNotAvailable(layout):
    if MissingLibs:
        box = layout.box()
        col = box.column()
        global InstalledDependencies
        if InstalledDependencies:
            col.label(text="Dependencies installed!", icon='INFO')
            col.label(text="Restart Blender!", icon='ERROR')
            InstalledDependencies = True
            return True

        col.label(text=f"Dependencies are required: {MissingLibs}")
        col.operator("ffxivpyon.install_libs", icon='IMPORT')
        return True

    return False

class FFXIVPyon_OT_install_libs(bpy.types.Operator):
    """Install required dependencies for complex weighting."""
    bl_idname = "ffxivpyon.install_libs"
    bl_label = "Install Dependencies"
    
    def execute(self, context):
        self.install_libs(context)

        return {'FINISHED'}

    def install_libs(self, context):
        def install():
            try:
                PythonExe = sys.executable
                print(PythonExe)

                global LibPath
                if not os.path.exists(LibPath):
                    os.makedirs(LibPath)

                subprocess.check_call([PythonExe, "-m", "ensurepip"])
                subprocess.check_call([PythonExe, "-m", "pip", "install", "--no-deps", *MissingLibs, "--target", LibPath])
                bpy.app.timers.register(lambda: self.install_success(context), first_interval=0.1)
            except subprocess.CalledProcessError as e:
                self.error_msg = str(e)
                bpy.app.timers.register(lambda: self.install_failed(context), first_interval=0.1)

        threading.Thread(target=install).start()

    def install_success(self, context):
        props = context.scene.FFXIVPyonProps

        global InstalledDependencies
        InstalledDependencies = True
        
        self.report({'INFO'}, "Dependencies installed! Restart Blender.")
        return None

    def install_failed(self, context):
        props = context.scene.FFXIVPyonProps

        self.report({'ERROR'}, f"Installation failed: {self.error_msg}")
        return None

classes = [
    FFXIVPyon_PT_weighting,
    FFXIVPyon_OT_create_source,
    FFXIVPyon_OT_toggle_lock_source,
    FFXIVPyon_OT_remove_source,
    FFXIVPyon_OT_transfer_weights_a,
    FFXIVPyon_OT_transfer_weights_b,
    FFXIVPyon_OT_transfer_weights_c,
    FFXIVPyon_OT_install_libs
]

def check_obj_in_scene(scene):
    props = scene.FFXIVPyonProps
    
    if props.Weight_SourceObject is not None:
        if props.Weight_SourceObject.name not in scene.objects:
            Util.RemoveObject(props.Weight_SourceObject)
            props.Weight_SourceObject = None

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            pass

    if not check_obj_in_scene in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(check_obj_in_scene)
    
def unregister():
    if check_obj_in_scene in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(check_obj_in_scene)

    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
