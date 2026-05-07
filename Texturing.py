import os
import bpy
import subprocess

from . import Util

ProjectionCachedNodeSocket = None

class TEXTURE_UL_filtered_textures(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if item.image:
                layout.label(text=item.image.name, icon_value=item.image.preview.icon_id)

    def draw_filter(self, context, layout): pass

class FFXIVPyon_PT_texturing(bpy.types.Panel):
    bl_label = "Texturing"
    bl_idname = "FFXIVPyon_PT_texturing"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'FFXIVPyon'
    bl_parent_id = "FFXIVPyon_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.FFXIVPyonProps
        prefs = context.preferences.filepaths

        box = layout.box()
        col = box.column(align=True)
        row = col.row(align=True)
        row.label(text="Texture Projection", icon='MOD_UVPROJECT')

        if not prefs.image_editor:
            col = box.column(align=True)
            col.label(text="Image Editor must be set!", icon='ERROR')
            col.label(text="Edit > Preferences > File Paths > Image Editor")
            return
        else:
            row.operator("ffxivpyon.reload_texture", text="", icon='FILE_REFRESH')

        col = box.column(align=True)
        col.prop(props, "Texture_ProjectionMaterial")
        col.template_list("TEXTURE_UL_filtered_textures", "", props, "Texture_ProjectionFilteredTextures", props, "Texture_ProjectionFilteredTexturesIndex", rows=3)
        col.enabled = not props.Texture_IsProjecting

        row = col.row()
        row.prop(props, "Texture_ProjectionSize")
        row.enabled = not props.Texture_IsProjecting

        col = box.column(align=True)
        row = col.row(align=True)
        if not props.Texture_IsProjecting:
            c1 = row.column(align=True)
            c2 = row.column(align=True)
            c1.prop(props, "Texture_UseOverlay", text="", icon='IMAGE_ALPHA', toggle=True)
            c1.enabled = True
            c2.operator("ffxivpyon.start_projection", text="Start Projection")
            c2.enabled = Util.HasTextures(props.Texture_ProjectionMaterial) and props.Texture_ProjectionTexture is not None
        else:
            c1 = row.column(align=True)
            c2 = row.row(align=True)
            c1.prop(props, "Texture_UseOverlay", text="", icon='IMAGE_ALPHA', toggle=True)
            c1.enabled = False
            c2.prop(props, "Texture_SaveTexture", text="", icon='FILE_TICK', toggle=True)
            c2.operator("ffxivpyon.stop_projection", text="Stop Projection")
            c2.prop(props, "Texture_DeleteTempImage", text="", icon='TRASH', toggle=True)
            c2.operator("ffxivpyon.open_explorer", text="", icon='FILE_FOLDER')

class FFXIVPyon_OT_start_projection(bpy.types.Operator):
    """Start projecting the current scene view to your image editing application.\nSaved changes to the projected image will automatically be previewed in Blender."""
    bl_idname = "ffxivpyon.start_projection"
    bl_label = "Start Texture Projection"
    
    _timer = None
    _lastModifiedTime = 0
    _projectedImagePath = ""

    def execute(self, context):
        props = context.scene.FFXIVPyonProps
        projMat = props.Texture_ProjectionMaterial
        projTex = props.Texture_ProjectionTexture

        bpy.ops.object.mode_set(mode='TEXTURE_PAINT')

        if not projMat or not projMat.use_nodes:
            self.report({'ERROR'}, "Projection Failed: Invalid material")
            return {'CANCELLED'}

        if not projTex:
            self.report({'ERROR'}, "Projection Failed: Invalid texture")
            return {'CANCELLED'}

        obj = bpy.context.object
        if not obj:
            self.report({'ERROR'}, "No object exists for projection")
            return {'CANCELLED'}

        if props.Texture_UseOverlay:
            RemoveProjectionTextureOverlay(context)

            width, height = projTex.size

            overlayName = f"{projTex.name}_Overlay"
            overlayTex = bpy.data.images.new(name=overlayName, width=width, height=height, alpha=True, float_buffer=False)
            overlayTex.generated_color = (0, 0, 0, 0)
            overlayTex.file_format = 'PNG'
            SaveProjectionOverlayTexture(overlayTex, overlayName)

            props.Texture_ProjectionTextureOverlay = overlayTex
            
            AddProjectionOverlayTextureToMaterial(props, projMat, overlayTex)
            SetActiveTextureNode(obj, projMat, overlayTex)
            overlayTex.reload()
        else:
            SetActiveTextureNode(obj, projMat, projTex)
            projTex.reload()
        
        context.scene.tool_settings.image_paint.screen_grab_size = props.Texture_ProjectionSize[:]

        cachedImages = set(bpy.data.images)
        bpy.ops.image.project_edit()
        props.Texture_IsProjecting = True

        props.Texture_ProjectedImage = GetProjectedImage(cachedImages)
        if not props.Texture_ProjectedImage:
            self.report({'ERROR'}, "Projection Failed: Projected image not found")
            return {'CANCELLED'}

        self._projectedImagePath = bpy.path.abspath(props.Texture_ProjectedImage.filepath)
        self._lastModifiedTime = os.path.getmtime(self._projectedImagePath)

        wm = context.window_manager
        self._timer = wm.event_timer_add(1.0, window=context.window)
        wm.modal_handler_add(self)

        self.report({'INFO'}, f"Projecting: {props.Texture_ProjectedImage.name}")
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        props = context.scene.FFXIVPyonProps

        if not props.Texture_IsProjecting:
            return self.cancel(context)

        if event.type == 'TIMER':
            try:
                newModifiedTime = os.path.getmtime(self._projectedImagePath)
                if newModifiedTime != self._lastModifiedTime:
                    self._lastModifiedTime = newModifiedTime

                    if props.Texture_ProjectionTexture:
                        props.Texture_ProjectionTexture.reload()
                    if props.Texture_UseOverlay and props.Texture_ProjectionTextureOverlay:
                        props.Texture_ProjectionTextureOverlay.reload()
                    bpy.ops.image.project_apply()
            except:
                pass

        return {'PASS_THROUGH'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        return {'CANCELLED'}

class FFXIVPyon_OT_stop_projection(bpy.types.Operator):
    """Stop projecting image.\nResulting actions will depend on whether 'Generate Overlay'/'Save Texture' are enabled.\nIf 'Save Texture' is disabled, any projected changes will be lost."""
    bl_idname = "ffxivpyon.stop_projection"
    bl_label = "Stop Texture Projection"

    def execute(self, context):
        props = context.scene.FFXIVPyonProps
        props.Texture_IsProjecting = False

        if props.Texture_UseOverlay and props.Texture_ProjectionTextureOverlay:
            props.Texture_ProjectionTexture.reload()

            if props.Texture_SaveTexture:
                props.Texture_ProjectionTextureOverlay.save()
                imageEditorPath = bpy.context.preferences.filepaths.image_editor
                overlayPath = bpy.path.abspath(props.Texture_ProjectionTextureOverlay.filepath_raw)

                if imageEditorPath and overlayPath:
                    subprocess.Popen([imageEditorPath, overlayPath])

                self.report({'INFO'}, f"Overlay texture saved to: {overlayPath}")

            RemoveProjectionTextureOverlay(context)

        if not props.Texture_UseOverlay and props.Texture_ProjectionTexture:
            if props.Texture_SaveTexture:
                if props.Texture_ProjectionTexture.filepath_raw:
                    props.Texture_ProjectionTexture.save()
                    self.report({'INFO'}, f"Saved changes to {props.Texture_ProjectionTexture.name}")
                else:
                    self.report({'WARNING'}, "Texture has no file path, cannot auto-save.")
            else:
                props.Texture_ProjectionTexture.reload()
                self.report({'INFO'}, f"Reverted changes to {props.Texture_ProjectionTexture.name}")

        if props.Texture_DeleteTempImage and props.Texture_ProjectedImage:
            try:
                path = bpy.path.abspath(props.Texture_ProjectedImage.filepath)
                if os.path.exists(path):
                    os.remove(path)
                bpy.data.images.remove(props.Texture_ProjectedImage)
                props.Texture_ProjectedImage = None
            except Exception as e:
                self.report({'WARNING'}, f"Failed to delete projected image: {e}")

        return {'FINISHED'}

class FFXIVPyon_OT_reload_texture(bpy.types.Operator):
    """Reload selected texture"""
    bl_idname = "ffxivpyon.reload_texture"
    bl_label = "Reload Texture"

    def execute(self, context):
        props = context.scene.FFXIVPyonProps

        if props.Texture_ProjectionTexture and props.Texture_ProjectionTexture.filepath:
            self.report({'INFO'}, f"Reloaded: {props.Texture_ProjectionTexture.name}")
        return {'FINISHED'}

class FFXIVPyon_OT_open_explorer(bpy.types.Operator):
    """Open destination folder of projected image in file explorer"""
    bl_idname = "ffxivpyon.open_explorer"
    bl_label = "Open Explorer"

    def execute(self, context):
        props = context.scene.FFXIVPyonProps

        if props.Texture_ProjectedImage and props.Texture_ProjectedImage.filepath:
            projectedImagePath = os.path.dirname(bpy.path.abspath(props.Texture_ProjectedImage.filepath))
            subprocess.Popen(['explorer', projectedImagePath])
        else:
            self.report({'WARNING'}, "Projected image not found")
        return {'FINISHED'}

def SaveProjectionOverlayTexture(overlayTex, overlayName: str) -> str:
    try:
        blendPath = bpy.path.abspath("//")
        savePath = os.path.join(blendPath, f"{overlayName}.png")
        overlayTex.filepath_raw = savePath
        overlayTex.save()
    except Exception as e:
        desktopPath = os.path.join(os.path.expanduser("~"), "Desktop")
        savePath = os.path.join(desktopPath, f"{overlayName}.png")
        overlayTex.filepath_raw = savePath
        overlayTex.save()

def SetActiveTextureNode(obj, material, image):
    if not material.use_nodes:
        return

    for node in material.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.image and node.image.name == image.name:
            obj.active_material = material
            material.node_tree.nodes.active = node
            return

def GetProjectedImage(cachedImages):
    newImages = set(bpy.data.images) - cachedImages
    for img in newImages:
        if img.source == 'FILE':
            return img
    return None

def AddProjectionOverlayTextureToMaterial(props, material, overlayTex):
    nodes = material.node_tree.nodes
    links = material.node_tree.links

    bsdfNode = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    if not bsdfNode:
        return

    if not bsdfNode.inputs['Base Color'].is_linked:
        return

    nodeLink = bsdfNode.inputs['Base Color'].links[0]
    global ProjectionCachedNodeSocket
    ProjectionCachedNodeSocket = nodeLink.from_socket

    overlayNode = nodes.new('ShaderNodeTexImage')
    overlayNode.image = overlayTex
    overlayNode.label = overlayTex.name
    overlayNode.interpolation = 'Linear'
    overlayNode.extension = 'CLIP'

    mixNode = nodes.new('ShaderNodeMixRGB')
    mixNode.blend_type = 'MIX'
    mixNode.label = f"Overlay_{overlayTex.name}"
    mixNode.inputs['Fac'].default_value = 1.0

    links.new(ProjectionCachedNodeSocket, mixNode.inputs['Color1'])

    links.new(overlayNode.outputs['Color'], mixNode.inputs['Color2'])

    if overlayNode.outputs.get('Alpha'):
        links.new(overlayNode.outputs['Alpha'], mixNode.inputs['Fac'])

    links.remove(nodeLink)

    links.new(mixNode.outputs['Color'], bsdfNode.inputs['Base Color'])

    return overlayNode

def RemoveProjectionTextureOverlay(context):
    props = context.scene.FFXIVPyonProps
    mat = props.Texture_ProjectionMaterial

    if not mat or not mat.use_nodes:
        return

    global ProjectionCachedNodeSocket
    if ProjectionCachedNodeSocket:
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        bsdfNode = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bsdfNode:
            while bsdfNode.inputs['Base Color'].is_linked:
                link = bsdfNode.inputs['Base Color'].links[0]
                links.remove(link)

            links.new(ProjectionCachedNodeSocket, bsdfNode.inputs['Base Color'])

            toRemove = []
            for node in nodes:
                try:
                    if node.type in {'TEX_IMAGE', 'MIX_RGB', 'SEPARATE_RGB'} and node.label.startswith(props.Texture_ProjectionTextureOverlay.name):
                        toRemove.append(node)
                    elif node.name.startswith(f"Overlay_{props.Texture_ProjectionTextureOverlay.name}"):
                        toRemove.append(node)
                except Exception as e:
                    pass

            for node in toRemove:
                nodes.remove(node)

    if props.Texture_ProjectionTextureOverlay:
        if props.Texture_ProjectionMaterial and props.Texture_ProjectionTexture:
            SetActiveTextureNode(bpy.context.object, props.Texture_ProjectionMaterial, props.Texture_ProjectionTexture)

        if props.Texture_ProjectionTextureOverlay.name in bpy.data.images:
            bpy.data.images.remove(props.Texture_ProjectionTextureOverlay)

    props.Texture_ProjectionTextureOverlay = None
    ProjectionCachedNodeSocket = None

classes = [
    TEXTURE_UL_filtered_textures,
    FFXIVPyon_PT_texturing,
    FFXIVPyon_OT_start_projection,
    FFXIVPyon_OT_stop_projection,
    FFXIVPyon_OT_reload_texture,
    FFXIVPyon_OT_open_explorer
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
