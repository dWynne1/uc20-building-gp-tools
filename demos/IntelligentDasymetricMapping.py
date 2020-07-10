# -*- coding: utf-8 -*-

# Intelligent Dasymetric Mapping
# Method developed by Jeremy Mennis, Tirrin Hultgren
# https://astro.temple.edu/~jmennis/pubs/mennis_cagis06.pdf

import os
import arcpy

# Set environment
arcpy.env.overwriteOutput = True

# Private internal tool variables
_dasymetric_estimate = "Dasymetric_Estimate"
_weighted_area = "Weighted_Area"

# Get parameters for IDM
source_statistic_geometry = arcpy.GetParameterAsText(0)
source_geometry_id = arcpy.GetParameterAsText(1)
source_statistic = arcpy.GetParameterAsText(2)
ancillary_geometry = arcpy.GetParameterAsText(3)
ancillary_density = arcpy.GetParameterAsText(4)
output_dasymetric_mapping = arcpy.GetParameterAsText(5)

# Intersect source statistic geometry with ancillary density geometry
arcpy.AddMessage("Intersecting source statistic geometry with ancillary density geometry..")
intersect = arcpy.analysis.Intersect(
    [source_statistic_geometry,
    ancillary_geometry],
    r"in_memory\intersect")

# Find the weighed area of intersected features based on anciallary weighting scheme
arcpy.AddMessage("Weighting intersected features based on anciallary densities..")
arcpy.management.AddField(intersect, _weighted_area, "DOUBLE")
arcpy.management.CalculateField(
    intersect,
    _weighted_area,
    f"!{ancillary_density}! * !SHAPE.AREA!"
    )
sum_weighted_area = arcpy.analysis.Statistics(
    intersect, 
    r"in_memory\sum_weighted_area",
    [[_weighted_area, "SUM"]],
    source_geometry_id
    )
arcpy.management.JoinField(
    intersect,
    source_geometry_id,
    sum_weighted_area,
    source_geometry_id,
    [f"SUM_{_weighted_area}"]
    )

# Calculate intelligent dasymetric mapping estimate
arcpy.AddMessage("Calculating intelligent dasymetric mapping estimate..")
arcpy.management.AddField(intersect, _dasymetric_estimate, "DOUBLE")
arcpy.management.CalculateField(
    intersect,
    _dasymetric_estimate,
    f"!{source_statistic}! * (!{_weighted_area}! / !SUM_{_weighted_area}!)"
    )

# Write output dasymetric mapping features
arcpy.AddMessage("Writing output dasymetric mapping features..")
#Specify the fields to be carried to the output dataset from in_memory\intersect
field_map_1 = arcpy.FieldMap()
field_map_2 = arcpy.FieldMap()
field_map_1.addInputField(intersect, source_geometry_id)
field_map_2.addInputField(intersect, _dasymetric_estimate)
field_mappings = arcpy.FieldMappings()
field_mappings.addFieldMap(field_map_1)
field_mappings.addFieldMap(field_map_2)
#Write in_memory\intersect to disk at location specified by user
outfc = arcpy.conversion.FeatureClassToFeatureClass(
    intersect, 
    os.path.dirname(output_dasymetric_mapping), 
    os.path.basename(output_dasymetric_mapping),
    field_mapping=field_mappings
    )

