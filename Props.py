# type: ignore

import bpy
import math

from . import Util

class TextureProjectionTextureItem(bpy.types.PropertyGroup):
    image: bpy.props.PointerProperty(type=bpy.types.Image)

class UpscaleObjectItem(bpy.types.PropertyGroup):
    obj: bpy.props.PointerProperty(type=bpy.types.Object)

class FFXIVPyonProps(bpy.types.PropertyGroup):
    Import_IsImporting: bpy.props.BoolProperty(
        name = "Importing", 
        default = False
    )
    Import_BodyType: bpy.props.EnumProperty(
        name = "", description = "Select which body to import",
        items = Util.GetPropBodyTypeItems
    )

    PMP_ImportPath: bpy.props.StringProperty(
        name="PMP Directory",
        subtype='DIR_PATH',
        default="//",
    )
    PMP_ImportFile: bpy.props.StringProperty(
        name="PMP File",
        default="",
    )

    Retarget_TargetArmature: bpy.props.EnumProperty(
        name = "Target", description = "Select which armature to parent objects to",
        items = Util.GetPropArmatureItems
    )
    Retarget_RemoveUnweightedBones: bpy.props.BoolProperty(
        name="Remove Unweighted Bones",
        description="Remove bones from target armature that are not used by any vertex groups",
        default=True,
    )

    Retarget_ObjectRetargetMode: bpy.props.EnumProperty(
        name = "Object Retarget Mode", description = "Select object retarget mode",
        items = [
            ('GROUP', "Group", "Retarget Object Group"),
            ('PART', "Part", "Retarget Object Part")
        ],
        default = 'GROUP'
    )
    Retarget_SourceObjectGroup: bpy.props.EnumProperty(
        name = "", description = "Select object group being retained",
        items = Util.GetPropObjectGroupItems
    )
    Retarget_TargetObjectGroup: bpy.props.EnumProperty(
        name = "", description = "Select object group being replaced",
        items = Util.GetPropObjectGroupItems
    )
    Retarget_SourceUnmatchedAction: bpy.props.EnumProperty(
        name = "Unmatched", description = "Select how to handle unmatched source parts",
        items = [
            ('IGNORE', "Ignore", "Keep unmatched source parts in the source group"),
            ('ADD', "Add", "Add unmatched source parts to the target group"),
            ('DISCARD', "Discard", "Discard unmatched source parts")
        ],
        default = 'ADD'
    )
    Retarget_TargetUnmatchedAction: bpy.props.EnumProperty(
        name = "Unmatched", description = "Select how to handle unmatched target parts",
        items = [
            ('IGNORE', "Ignore", "Keep unmatched target parts in the target group"),
            ('DISCARD', "Discard", "Discard unmatched target parts from the target group")
        ],
        default = 'DISCARD'
    )
    Retarget_SourceObjectItem: bpy.props.EnumProperty(
        name = "", description = "Select object being retained",
        items = Util.GetPropObjectItems
    )
    Retarget_TargetObjectItem: bpy.props.EnumProperty(
        name = "", description = "Select object being replaced",
        items = Util.GetPropObjectItems
    )
    Retarget_RemovalObjectGroup: bpy.props.EnumProperty(
        name = "Group", description = "Select object group to remove",
        items = Util.GetPropObjectGroupItems
    )

    Upscale_IsSculpting: bpy.props.BoolProperty(name="Sculpting", default=False)
    Upscale_SculptBrushType: bpy.props.EnumProperty(
        name="Brush",
        description="Default sculpt brush",
        items=[
            ('DRAW', "Draw", ""),
            ('DRAW_SHARP', "Draw Sharp", ""),
            ('GRAB', "Grab", ""),
            ('GRAB_2D', "Grab 2D", ""),
            ('GRAB_CLOTH', "Grab Cloth", ""),
            ('GRAB_SILHOUETTE', "Grab Silhouette", ""),
            ('POSE', "Pose", ""),
            ('PULL', "Pull", ""),
            ('THUMB', "Thumb", ""),
            ('TWIST', "Twist", ""),
            ('SNAKE_HOOK', "Snake Hook", ""),
            ('SMOOTH', "Smooth", ""),
        ],
        default='GRAB'
    , update=Util.UpdateSculptBrushProperties)
    Upscale_SculptBrushRadius: bpy.props.IntProperty(name="Radius", description="Default sculpt brush radius", default=400, min=1, max=1000, update=Util.UpdateSculptBrushProperties)
    Upscale_SculptBrushStrength: bpy.props.FloatProperty(name="Strength", description="Default sculpt brush strength", default=0.15, min=0.0, max=1.0, update=Util.UpdateSculptBrushProperties)
    Upscale_SculptMirrorX: bpy.props.BoolProperty(name="X Mirror", description="Use X-axis symmetry while sculpting", default=True, update=Util.UpdateSculptBrushProperties)

    Upscale_IsWrapping: bpy.props.BoolProperty(name = "Wrapping", default = False)
    Upscale_TargetObject: bpy.props.PointerProperty(name="Target", type=bpy.types.Object, description="Target object for scaling to")
    Upscale_Objects: bpy.props.CollectionProperty(type=UpscaleObjectItem, name="Objects With Auto-Upscale Modifiers")
    Upscale_WrapOffset: bpy.props.FloatProperty(name="Offset", description="Distance offset from target mesh to scale to", default=0.002, min=-1.0, max=1.0, step=0.01, precision=3, update=Util.UpdateUpscalingObjectMods)
    Upscale_WrapDisplaceStrength: bpy.props.FloatProperty(name="Strength", description="Amount to displace selected meshes by", default=0, min=-1.0, max=1.0, step=0.01, precision=3, update=Util.UpdateUpscalingObjectMods)

    Upscale_IsWrapInfluenceEditing: bpy.props.BoolProperty(name = "Wrap Influence Editing", default = False)
    Upscale_WrapInfluenceInvert: bpy.props.BoolProperty(name="", description="Invert wrap influence mask", default=False, update=Util.UpdateWrapInfluence)
    Upscale_WrapPaintRadius: bpy.props.FloatProperty(name="Radius", default=100, min=1, max=500, update=Util.UpdateWrapInfluence)
    Upscale_WrapPaintStrength: bpy.props.FloatProperty(name="Strength", default=0.5, min=0, max=1, update=Util.UpdateWrapInfluence)

    Weight_SourceObject: bpy.props.PointerProperty(type=bpy.types.Object)
    Weight_TransferMode: bpy.props.EnumProperty(
        name = "Transfer Mode", description = "Select weight transfer mode",
        items = [
            ('A', "A", "Face interpolation data transfer."),
            ('B', "B", "cKDTree algorithm."),
            ('C', "C", "Laplacian algorithm."),
        ],
        default = 'A'
    )
    Weight_ExpandingProperties: bpy.props.BoolProperty(
        name = "Properties", description = "Toggle display of properties",
        default = False
    )
    Weight_IncludeYAS: bpy.props.BoolProperty(
        name = "YAS", description = "Transfer YAS weights from 'ya_' vertex groups.", 
        default = True
    )
    Weight_IncludeIVCS: bpy.props.BoolProperty(
        name = "IVCS", description = "Transfer IVCS weights from 'iv_' vertex groups.", 
        default = True
    )
    Weight_IncludeOther: bpy.props.BoolProperty(
        name = "Other", description = "Transfer weights from all other vertex groups.", 
        default = True
    )

    WeightA_MaxDistance: bpy.props.FloatProperty(
        name="Max Distance", description="Max distance between source and target vertex.\nValue of 0 will ignore distance.", 
        default=0, min=0, unit='LENGTH', subtype='DISTANCE'
    )
    WeightA_InfluenceMultiplier: bpy.props.FloatProperty(
        name = "Weight Multiplier", description = "Multiplier applied to copied vertex weights",
        default = 1.0, min = 0.0, max = 4.0, precision = 2, subtype = 'FACTOR'
    )

    WeightB_MinDistance: bpy.props.FloatProperty(
        name="Min Distance", description="Min distance between source and target vertex", 
        default=0, min=0, unit='LENGTH', subtype='DISTANCE'
    )
    WeightB_MaxDistance: bpy.props.FloatProperty(
        name="Max Distance", description="Max distance between source and target vertex", 
        default=0.05, min=0, unit='LENGTH', subtype='DISTANCE'
    )
    WeightB_InfluenceMultiplier: bpy.props.FloatProperty(
        name = "Weight Multiplier", description = "Multiplier applied to copied vertex weights",
        default = 1.0, min = 0.0, max = 4.0, precision = 2, subtype = 'FACTOR'
    )

    WeightC_MinDistance: bpy.props.FloatProperty(
        name="Min Distance", description="Min distance between source and target vertex", 
        default=0, min=0, unit='LENGTH', subtype='DISTANCE'
    )
    WeightC_MaxDistance: bpy.props.FloatProperty(
        name="Max Distance", description="Max distance between source and target vertex", 
        default=0.05, min=0, unit='LENGTH', subtype='DISTANCE'
    )
    WeightC_MaxNormalAngle: bpy.props.FloatProperty(
        name="Normal Angle", description="Max normal angle between source and target vertex",
        default=math.radians(30), min=0, max=math.pi, precision=3, step=100, unit='ROTATION', subtype='ANGLE'
    )
    WeightC_WeightFillMode: bpy.props.EnumProperty(
        name = "",
        description = "Weight Fill Mode",
        items = [
            ('MESH', 'Mesh', 'Mesh is used as is. Weights "flow" only inside a mesh/loose part. More likely to fail compared to "Point"'),
            ('POINTCLOUD', 'Point Cloud', 'Object is remeshed internally. Weights can "flow" outside a mesh/loose part and more robust' )
        ],
        default = 'POINTCLOUD')
    WeightC_WeightFillSmoothing: bpy.props.IntProperty(
        name = "Smoothing", description="Smoothing iterations for filled weights, may cause issues with seperated meshes",
        default = 0, min = 0, max = 10
    )
    WeightC_EqualizeCoincidentVertices: bpy.props.BoolProperty(
        name = "Equalize Coincident Vertices", description = "Apply the same averaged weight to vertices occupying the same position.\nThis prevents mesh splitting along disconnected edges.", 
        default = True
    )

    Texture_IsProjecting: bpy.props.BoolProperty(name="Projecting", default=False)
    Texture_ProjectedImage: bpy.props.PointerProperty(type=bpy.types.Image)
    Texture_ProjectionMaterial: bpy.props.PointerProperty(
        name="",
        description="Select a material to project a texture from",
        type=bpy.types.Material,
        update=lambda self, ctx: Util.UpdatePropTextureList(self, ctx)
    )
    Texture_ProjectionTexture: bpy.props.PointerProperty(name="Texture", type=bpy.types.Image)
    Texture_ProjectionTextureOverlay: bpy.props.PointerProperty(name="Texture", type=bpy.types.Image)
    Texture_ProjectionFilteredTextures: bpy.props.CollectionProperty(type=TextureProjectionTextureItem)
    Texture_ProjectionFilteredTexturesIndex: bpy.props.IntProperty(
        name="Select texture to project",
        default=0,
        update=Util.UpdatePropProjectionTexture
    )
    Texture_ProjectionSize: bpy.props.IntVectorProperty(
        name="Resolution",
        size=2,
        default=(2048, 2048),
        min=256,
        description="Resolution of the projection"
    )
    Texture_UseOverlay: bpy.props.BoolProperty(
        name="Generate Overlay",
        default=True,
        description="Project changes onto a generated overlay texture instead of directly onto the original texture"
    )
    Texture_SaveTexture: bpy.props.BoolProperty(
        name="Save Texture",
        default=True,
        description="Save projected changes when stopping projection.\nIf 'Generate Overlay' is enabled, projected changes will save to an overlay image and open in your image editing application, so you can copy it as a seperate layer over the original texture.\nOtherwise, projected changes will apply directly to the original texture."
    )
    Texture_DeleteTempImage: bpy.props.BoolProperty(
        name="Delete Projected Image",
        default=True,
        description="Whether to automatically delete the temporary projected image when stopping projection"
    )

classes = [
    TextureProjectionTextureItem,
    UpscaleObjectItem,
    FFXIVPyonProps
]

def register():
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            pass
            
    bpy.types.Scene.FFXIVPyonProps = bpy.props.PointerProperty(type=FFXIVPyonProps)

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
            
    del bpy.types.Scene.FFXIVPyonProps
