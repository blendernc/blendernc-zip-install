#!/usr/bin/env python3
# Imports
from collections import defaultdict

import bpy

from blendernc.decorators import NodesDecorators
from blendernc.image import dataset_2_image_preview
from blendernc.python_functions import (
    update_colormap_interface,
    update_image,
    update_value,
)


class BlenderNC_NT_output(bpy.types.Node):
    # === Basics ===
    # Description string
    """NetCDF loading resolution"""
    # Optional identifier string. If not explicitly defined,
    # the python class name is used.
    bl_idname = "netCDFOutput"
    # Label for nice name display
    bl_label = "Output"
    # Icon identifier
    bl_icon = "RENDER_RESULT"
    blb_type = "NETCDF"

    update_on_frame_change: bpy.props.BoolProperty(
        name="Update on frame change",
        default=False,
    )

    image: bpy.props.PointerProperty(
        type=bpy.types.Image,
        name="",
        update=update_value,
    )

    frame_loaded: bpy.props.IntProperty(
        default=-1,
    )

    frame: bpy.props.IntProperty(
        default=1,
    )

    keep_nan: bpy.props.BoolProperty(
        name="Replace nan with zeros",
        default=True,
    )

    grid_node_name: bpy.props.StringProperty()

    # Dataset requirements
    blendernc_dataset_identifier: bpy.props.StringProperty()
    blendernc_dict = defaultdict(None)

    # === Optional Functions ===
    # Initialization function, called when a new node is created.
    # This is the most common place to create the sockets for a node,
    # as shown below.
    def init(self, context):
        self.frame_loaded = -1
        self.inputs.new("bNCnetcdfSocket", "Dataset")
        self.color = (0.8, 0.4, 0.4)
        self.use_custom_color = True

    # Copy function to initialize a copied node from an existing one.
    def copy(self, node):
        print("Copying from node ", node)

    # Free function to clean up on removal.
    def free(self):
        if self.blendernc_dataset_identifier != "":
            self.blendernc_dict.pop(self.blendernc_dataset_identifier)
        print("Removing node ", self, ", Goodbye!")

    # Additional buttons displayed on the node.
    def draw_buttons(self, context, layout):
        identifier = self.blendernc_dataset_identifier
        # Generated image supported by bpy to display,
        # but perhaps show a preview of field?
        layout.template_ID_preview(
            self,
            "image",
            new="image.new",
            open="image.open",
            rows=2,
            cols=3,
        )
        if self.image:
            is_custom_image = self.image.preview.is_image_custom
            blender_dict_keys = self.blendernc_dict.keys()
            if self.image.is_float and (
                not is_custom_image and identifier in blender_dict_keys
            ):
                image_preview = dataset_2_image_preview(self)
                self.image.preview.image_pixels_float[0:] = image_preview

        if self.image and identifier in blender_dict_keys:
            layout.prop(self, "update_on_frame_change")

            layout.prop(self, "keep_nan")

            operator = layout.operator(
                "blendernc.colorbar",
                icon="GROUP_VCOL",
            )
            operator.node = self.name
            operator.node_group = self.rna_type.id_data.name
            operator.image = self.image.name

        node_names = self.rna_type.id_data.nodes.keys()
        if "Input Grid" in node_names and len(self.inputs) == 1:
            self.inputs.new("bNCnetcdfSocket", "Grid")
        elif "Input Grid" not in node_names and len(self.inputs) == 2:
            self.inputs.remove(self.inputs.get("Grid"))

    # Detail buttons in the sidebar.
    # If this function is not defined,
    # the draw_buttons function is used instead
    def draw_buttons_ext(self, context, layout):
        pass
        # TODO: Implement manual purge.
        # layout.label(text="INFO: Purge all frames", icon='INFO')
        # operator = layout.operator("blendernc.purge_all",
        #                             icon='GROUP_VCOL')

    # Optional: custom label
    # Explicit user label overrides this,
    # but here we can define a label dynamically
    def draw_label(self):
        return "Image Output"

    @NodesDecorators.node_connections
    def update(self):
        node_tree = self.rna_type.id_data.name
        # TODO Move this section to the decorator.
        if len(self.inputs) == 2:
            if self.inputs[1].is_linked and self.inputs[1].links:
                self.grid_node_name = self.inputs[1].links[0].from_node.name

        if self.image:
            update_image(
                bpy.context,
                self.name,
                node_tree,
                bpy.context.scene.frame_current,
                self.image.name,
                self.grid_node_name,
            )
            if self.image.users >= 3:
                update_colormap_interface(bpy.context, self.name, node_tree)
