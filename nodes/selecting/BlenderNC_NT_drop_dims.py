#!/usr/bin/env python3
# Imports
from collections import defaultdict

import bpy

from blendernc.decorators import NodesDecorators
from blendernc.python_functions import get_possible_dims, update_value_and_node_tree


class BlenderNC_NT_drop_dims(bpy.types.Node):
    # === Basics ===
    # Description string
    """Select axis"""
    # Optional identifier string. If not explicitly defined,
    # the python class name is used.
    bl_idname = "netCDFdims"
    # Label for nice name display
    bl_label = "Drop Dimension"
    # Icon identifier
    bl_icon = "MESH_GRID"
    blb_type = "NETCDF"

    blendernc_dims: bpy.props.EnumProperty(
        items=get_possible_dims,
        name="Select Dimension",
        update=update_value_and_node_tree,
    )

    # Dataset requirements
    blendernc_dataset_identifier: bpy.props.StringProperty()
    blendernc_dict = defaultdict(None)

    # === Optional Functions ===
    # Initialization function, called when a new node is created.
    # This is the most common place to create the sockets for a node,
    # as shown below.
    def init(self, context):
        self.inputs.new("bNCnetcdfSocket", "Dataset")
        self.outputs.new("bNCnetcdfSocket", "Dataset")

    # Copy
    def copy(self, node):
        print("Copying from node ", node)

    # Free function to clean up on removal.
    def free(self):
        if self.blendernc_dataset_identifier != "":
            self.blendernc_dict.pop(self.blendernc_dataset_identifier)
        print("Removing node ", self, ", Goodbye!")

    # Additional buttons displayed on the node.
    def draw_buttons(self, context, layout):
        layout.prop(self, "blendernc_dims", text="")

    # Detail buttons in the sidebar.
    # If this function is not defined,
    # the draw_buttons function is used instead
    def draw_buttons_ext(self, context, layout):
        pass

    # Optional: custom label
    # Explicit user label overrides this,
    # but here we can define a label dynamically
    def draw_label(self):
        return "Drop Dimension"

    @NodesDecorators.node_connections
    def update(self):
        blendernc_dict = self.blendernc_dict[self.blendernc_dataset_identifier]
        dataset = blendernc_dict["Dataset"]
        # Drop dimensions
        if self.blendernc_dims != "":
            if self.blendernc_dims in dataset.dims:
                dataset = (
                    dataset.isel({self.blendernc_dims: 0})
                    .drop(self.blendernc_dims)
                    .squeeze()
                )
            else:
                dataset = dataset.drop_dims(self.blendernc_dims).squeeze()

        blendernc_dict["Dataset"] = dataset
