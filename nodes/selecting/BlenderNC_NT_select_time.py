#!/usr/bin/env python3
# Imports
from collections import defaultdict

import bpy

from blendernc.core.dates import (
    get_item_days,
    get_item_month,
    get_item_time,
    get_item_year,
    update_date,
)
from blendernc.decorators import NodesDecorators
from blendernc.python_functions import (
    refresh_cache,
    update_datetime_text,
    update_node_tree,
)


class BlenderNC_NT_select_time(bpy.types.Node):
    # === Basics ===
    # Description string
    """Select axis"""
    # Optional identifier string. If not explicitly defined,
    # the python class name is used.
    bl_idname = "netCDFtime"
    # Label for nice name display
    bl_label = "Select Time"
    # Icon identifier
    bl_icon = "TIME"
    blb_type = "NETCDF"
    bl_width_default = 160

    step: bpy.props.EnumProperty(
        items=get_item_time,
        name="Time",
        update=update_date,
    )

    selected_time: bpy.props.StringProperty(name="")

    year: bpy.props.EnumProperty(
        items=get_item_year,
        name="Year",
        update=update_date,
    )
    month: bpy.props.EnumProperty(
        items=get_item_month,
        name="Month",
        update=update_date,
    )
    day: bpy.props.EnumProperty(
        items=get_item_days,
        name="Day",
        update=update_date,
    )
    hour: bpy.props.EnumProperty(
        items=[],
        name="Hour",
        update=update_date,
    )

    pre_selected: bpy.props.StringProperty()

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
        if (
            self.inputs[0].is_linked
            and self.inputs[0].links
            and self.blendernc_dataset_identifier
        ):
            blendernc_dict = self.inputs[0].links[0].from_node.blendernc_dict
            if blendernc_dict:
                dataset = blendernc_dict[self.blendernc_dataset_identifier]["Dataset"]
                coords = list(dataset.coords)
                if len(coords) >= 3:
                    # Dataset is 3D.
                    if "time" in coords:
                        dataset_time = dataset["time"]
                        if "datetime64" in str(dataset_time.dtype):

                            layout.label(text="Date Format:")
                            row = layout.row(align=True)

                            # split = row.split(factor=0.25,align=True)
                            # split.prop(self, 'hour',text='')
                            split = row.split(factor=0.30, align=True)
                            split.prop(self, "day", text="")
                            split = split.split(factor=0.40, align=True)
                            split.prop(self, "month", text="")
                            split.prop(self, "year", text="")

                        else:
                            layout.prop(self, "step", text="")
                    else:
                        pass
                        # m_ini = "Dataset coords are"
                        # m_end = ", only 'time' coordinate name is supported."
                        # text_format = (m_ini, coords[0], coords[1], m_end)
                        # text = "{0} ({1}, {2}) {3}".format(**text_format)
                        # self.report({'ERROR'}, text)
                else:
                    pass
                    # m_ini = "Dataset coords are 2D"
                    # text = "{0} ({1}, {2})".format(m_ini, coords[0], coords[1])
                    # self.report({'ERROR'}, text)

    # Detail buttons in the sidebar.
    # If this function is not defined,
    # the draw_buttons function is used instead
    def draw_buttons_ext(self, context, layout):
        pass

    # Optional: custom label
    # Explicit user label overrides this,
    # but here we can define a label dynamically
    def draw_label(self):
        return "Select Time"

    @NodesDecorators.node_connections
    def update(self):
        unique_identifier = self.blendernc_dataset_identifier
        unique_data_dict_node = self.blendernc_dict[unique_identifier]
        dataset = unique_data_dict_node["Dataset"]
        node_tree = self.rna_type.id_data.name
        if self.day and self.month and self.year and self.selected_time:
            unique_data_dict_node["Dataset"] = dataset.sel(
                time=self.selected_time
            ).drop("time")
            update_datetime_text(
                bpy.context, self.name, node_tree, 0, self.selected_time
            )
        elif self.selected_time and self.selected_time == self.step:
            unique_data_dict_node["Dataset"] = dataset.isel(
                time=int(self.selected_time)
            ).drop("time")
            update_datetime_text(
                bpy.context, self.name, node_tree, 0, self.selected_time
            )
        else:
            # TODO Add extra conditions to avoid issues if reusing a
            # node for multiple datasets.
            pass
        if self.pre_selected != self.selected_time:
            refresh_cache(
                node_tree,
                self.blendernc_dataset_identifier,
                bpy.context.scene.frame_current,
            )
            update_node_tree(self, bpy.context)
            self.pre_selected = self.selected_time
