import bpy
import re

def GetPropBodyTypeItems(self, context):
    items = []
    items.append(("Rue-M-WC", "Rue-M-WC", ""))
    items.append(("Rue-L-WC", "Rue-L-WC", ""))
    items.append(("YAB-M-WC", "YAB-M-WC", ""))
    
    return items

def GetPropObjectGroupItems(self, context):
    items = []
    matchedGroups = set()
    matches = []

    for obj in context.scene.objects:
        if obj.type != 'MESH':
            continue

        match = re.search(r"(.*?)Part\s+(\d+)\.(\d+)", obj.name)
        if match:
            prefix = match.group(1).strip()
            groupID = int(match.group(2))
            partID = int(match.group(3))
            matches.append((prefix, groupID, partID, obj.name))

    matches.sort(key=lambda m: (m[0].lower(), m[1], m[2]))

    for prefix, groupID, partID, objName in matches:
        groupKey = f"{prefix}_{groupID}"
        if groupKey not in matchedGroups:
            matchedGroups.add(groupKey)
            label = f"{prefix} | Part {groupID}.X"
            items.append((objName, label, ""))

    return items

def GetPropObjectItems(self, context):
    items = []

    for obj in context.scene.objects:
        if obj.type != 'MESH':
            continue

        items.append((obj.name, obj.name, ""))

    items.sort()

    return items

def format_armature_name(obj):
    ya_bones = sum(1 for b in obj.data.bones if b.name.lower().startswith("ya_"))
    iv_bones = sum(1 for b in obj.data.bones if b.name.lower().startswith("iv_"))
    return f"{obj.name} (yas: {ya_bones}, iv: {iv_bones})"

def GetPropArmatureItems(self, context):
    items = []
    for obj in context.scene.objects:
        if obj.type == 'ARMATURE' and obj.data:
            label = format_armature_name(obj)
            items.append((obj.name, label, ""))
    return items

def UpdatePropTextureList(props, context):
    props.Texture_ProjectionFilteredTextures.clear()
    mat = props.Texture_ProjectionMaterial
    if not mat or not mat.use_nodes:
        return

    added = set()
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.image and node.image.name not in added:
            item = props.Texture_ProjectionFilteredTextures.add()
            item.image = node.image
            added.add(node.image.name)

            if item.image and not item.image.preview:
                item.image.preview_ensure()
    
    if props.Texture_ProjectionTexture not in [i.image for i in props.Texture_ProjectionFilteredTextures]:
        props.Texture_ProjectionTexture = None
        props.Texture_ProjectionFilteredTexturesIndex = 0

def UpdatePropProjectionTexture(props, context):
    if 0 <= props.Texture_ProjectionFilteredTexturesIndex < len(props.Texture_ProjectionFilteredTextures):
        props.Texture_ProjectionTexture = props.Texture_ProjectionFilteredTextures[props.Texture_ProjectionFilteredTexturesIndex].image
    else:
        props.Texture_ProjectionTexture = None

def GetPropMaterialTextures(self, context):
    props = context.scene.FFXIVPyonProps
    items = []

    if not props.Texture_ProjectionMaterial:
        return items

    mat = bpy.data.materials.get(props.Texture_ProjectionMaterial)
    if not mat or not mat.use_nodes:
        return items

    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.image:
            items.append((node.image.name, node.image.name, ""))

    return items

def HasTextures(mat):
    if not mat or not mat.use_nodes:
        return False

    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.image:
            return True

    return False

BRUSH_ASSET_PATHS = {
    'DRAW': r"brushes\essentials_brushes-mesh_sculpt.blend\Brush\Draw",
    'DRAW_SHARP': r"brushes\essentials_brushes-mesh_sculpt.blend\Brush\Draw Sharp",
    'GRAB': r"brushes\essentials_brushes-mesh_sculpt.blend\Brush\Grab",
    'GRAB_2D': r"brushes\essentials_brushes-mesh_sculpt.blend\Brush\Grab 2D",
    'GRAB_CLOTH': r"brushes\essentials_brushes-mesh_sculpt.blend\Brush\Grab Cloth",
    'GRAB_SILHOUETTE': r"brushes\essentials_brushes-mesh_sculpt.blend\Brush\Grab Silhouette",
    'POSE': r"brushes\essentials_brushes-mesh_sculpt.blend\Brush\Pose",
    'PULL': r"brushes\essentials_brushes-mesh_sculpt.blend\Brush\Pull",
    'THUMB': r"brushes\essentials_brushes-mesh_sculpt.blend\Brush\Thumb",
    'TWIST': r"brushes\essentials_brushes-mesh_sculpt.blend\Brush\Twist",
    'SNAKE_HOOK': r"brushes\essentials_brushes-mesh_sculpt.blend\Brush\Snake Hook",
    'SMOOTH': r"brushes\essentials_brushes-mesh_sculpt.blend\Brush\Smooth",
}

def SaveSculptBrushProperties(self, context):
    """
    Read current sculpt brush settings from Blender and store into addon props.
    Call this when ENDING sculpt (or when you want to snapshot from native UI).
    """
    props = context.scene.FFXIVPyonProps

    ts = getattr(context, "tool_settings", None)
    if not ts:
        return

    sculpt = getattr(ts, "sculpt", None)
    if not sculpt:
        return

    ups = getattr(sculpt, "unified_paint_settings", None)
    brush = sculpt.brush

    radius = None
    try:
        if ups and getattr(ups, "use_unified_size", False):
            radius = ups.size
        elif brush:
            radius = brush.size
    except Exception:
        pass

    if radius is not None:
        props.Upscale_SculptBrushRadius = int(radius)

    strength = None
    try:
        if ups and getattr(ups, "use_unified_strength", False):
            strength = ups.strength
        elif brush:
            strength = brush.strength
    except Exception:
        pass

    if strength is not None:
        props.Upscale_SculptBrushStrength = float(strength)

    if brush and hasattr(brush, "sculpt_tool"):
        try:
            props.Upscale_SculptBrushType = brush.sculpt_tool
        except Exception:
            pass

    obj = context.object
    if obj and hasattr(obj, "use_mesh_mirror_x"):
        try:
            props.Upscale_SculptMirrorX = bool(obj.use_mesh_mirror_x)
        except Exception:
            pass
    
def UpdateSculptBrushProperties(self, context):
    props = context.scene.FFXIVPyonProps

    ts = getattr(context, "tool_settings", None)
    if not ts:
        return

    sculpt = getattr(ts, "sculpt", None)
    if not sculpt:
        return

    ups = getattr(sculpt, "unified_paint_settings", None)

    brush = sculpt.brush

    brush_key = props.Upscale_SculptBrushType
    if brush_key:
        rel_id = BRUSH_ASSET_PATHS.get(brush_key)
        if rel_id:
            try:
                bpy.ops.brush.asset_activate(
                    asset_library_type='ESSENTIALS',
                    asset_library_identifier="",
                    relative_asset_identifier=rel_id
                )
                sculpt = getattr(context.tool_settings, "sculpt", None)
                brush = sculpt.brush if sculpt else None
            except RuntimeError:
                pass

    try:
        r = int(props.Upscale_SculptBrushRadius)
        if ups:
            ups.size = r
            if hasattr(ups, "use_unified_size"):
                ups.use_unified_size = True
        if brush:
            brush.size = r
    except Exception:
        pass

    try:
        s = float(props.Upscale_SculptBrushStrength)
        if ups and hasattr(ups, "strength"):
            ups.strength = s
            if hasattr(ups, "use_unified_strength"):
                ups.use_unified_strength = True
        if brush:
            brush.strength = s
    except Exception:
        pass

    obj = context.object
    if obj and hasattr(obj, "use_mesh_mirror_x"):
        try:
            obj.use_mesh_mirror_x = bool(props.Upscale_SculptMirrorX)
        except Exception:
            pass

def UpdateUpscalingObjectMods(self, context):
    props = context.scene.FFXIVPyonProps
    
    toRemove = []
    for entry in props.Upscale_Objects:
        if not entry.obj:
            toRemove.append(entry)
            continue
        mods = entry.obj.modifiers
        if not all(m in mods for m in ("Pyon_Wrap", "Pyon_Displace", "Pyon_Smooth")):
            toRemove.append(entry)
            continue

    for item in toRemove:
        props.Upscale_Objects.remove(item)

    for entry in props.Upscale_Objects:
        if entry.obj is not None:
            entry.obj.modifiers["Pyon_Wrap"].offset = props.Upscale_WrapOffset
            entry.obj.modifiers["Pyon_Displace"].strength = props.Upscale_WrapDisplaceStrength

def UpdateWrapInfluence(self, context):
    props = context.scene.FFXIVPyonProps

    for entry in props.Upscale_Objects:
        obj = entry.obj
        if not obj:
            continue
        wrap = obj.modifiers.get("Pyon_Wrap")
        if wrap:
            wrap.vertex_group = "Pyon_Wrap"
            wrap.invert_vertex_group = props.Upscale_WrapInfluenceInvert

    brush = bpy.context.tool_settings.weight_paint.brush
    if brush:
        brush.size = props.Upscale_WrapPaintRadius
        brush.strength = props.Upscale_WrapPaintStrength
        
def RemoveUpscalingMods(self, context):
    props = context.scene.FFXIVPyonProps
    
    for entry in props.Upscale_Objects:
        obj = entry.obj
        if not obj:
            continue
            
        mods = entry.obj.modifiers
        wrap = mods.get("Pyon_Wrap")
        displace = mods.get("Pyon_Displace")
        smooth = mods.get("Pyon_Smooth")
        if wrap:
            mods.remove(wrap)
        if displace:
            mods.remove(displace)
        if smooth:
            mods.remove(smooth)
 
def CacheModStack(obj):
    cached = []
    for mod in obj.modifiers:
        if not mod.name.startswith("Pyon_"):
            props = {}
            for attr in dir(mod):
                if attr.startswith("_"): # Ignore Blender internal
                    continue
                prop = getattr(mod, attr)
                if isinstance(prop, (int, float, str, bool, bpy.types.ID, tuple)):
                    try:
                        props[attr] = prop
                    except:
                        pass
            cached.append((mod.name, mod.type, props))
    return cached
    
def RestoreModStack(obj, cached_mods):
    for mod_name, mod_type, props in cached_mods:
        new_mod = obj.modifiers.new(mod_name, mod_type)
        for attr, value in props.items():
            try:
                setattr(new_mod, attr, value)
            except Exception:
                pass

def RemoveObject(obj):
    meshName = obj.data.name if obj.data else None
    bpy.data.objects.remove(obj, do_unlink=True)
    if meshName and meshName in bpy.data.meshes:
        bpy.data.meshes.remove(bpy.data.meshes[meshName], do_unlink=True)

def RenameObject(obj, name):
    obj.name = name
    if obj.data and obj.data.name != name:
        obj.data.name = name

def HasVertexGroup(vertexGroups, vertexGroupName):
    return len(vertexGroupName) > 0 and vertexGroupName in vertexGroups

def ObjectHasVertexGroup(obj, vertexGroupName):
    return obj.vertex_groups.get(vertexGroupName)

def AddVertexGroup(obj, vertexGroupName):
    vg = obj.vertex_groups.get(vertexGroupName)
    if not vg:
        vg = obj.vertex_groups.new(name=vertexGroupName)
    return vg

def RemoveVertexGroup(obj, vertexGroupName):
    vg = obj.vertex_groups.get(vertexGroupName)
    if vg:
        obj.vertex_groups.remove(vg)

def VertexGroupIsDeformBone(obj, vertexGroupName):
    for mod in obj.modifiers:
        if mod.type == 'ARMATURE':
            if not mod.object or mod.object.type != 'ARMATURE':
                return False

            bone = mod.object.data.bones.get(vertexGroupName)
            if bone and bone.use_deform:
                return True

    return False

def HasModifier(obj: bpy.types.Object, *modTypes):
    if obj and obj.type == 'MESH' and obj.modifiers:
        return any(mod.type in modTypes for mod in obj.modifiers)
    return False

TOPOLOGY_MODS = { 'ARRAY', 'BEVEL', 'BOOLEAN', 'BUILD', 'DECIMATE', 'EDGE_SPLIT', 'MASK', 'MIRROR', 'MULTIRES', 'REMESH', 'SCREW', 'SKIN', 'SOLIDIFY', 'SUBSURF', 'TRIANGULATE', 'WELD', 'WIREFRAME' }
def HasTopologyModifiers(obj: bpy.types.Object):
    return HasModifier(obj, *TOPOLOGY_MODS)

classes = []

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
