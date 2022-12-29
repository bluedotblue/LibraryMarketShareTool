#Rebecca O'Keeffe
import arcpy

#run tool and overwrite output feature class indefinite times
arcpy.env.overwriteOutput = True

#initial user specified parameters
in_Point_Features = arcpy.GetParameterAsText(0)
in_Polygon_Features = arcpy.GetParameterAsText(1)
in_Polygon_Join_Field = arcpy.GetParameterAsText(2)
in_Area_Field = arcpy.GetParameterAsText(3)
in_Data_Table_For_Polygons = arcpy.GetParameterAsText(4)
in_Data_Table_Join_Field = arcpy.GetParameterAsText(5)
in_Data_Table_Field = arcpy.GetParameterAsText(6)
in_Number_Of_Classes = arcpy.GetParameterAsText(7)
in_Drawn_Map_Type = arcpy.GetParameterAsText(8)
output_feature_class = arcpy.GetParameterAsText(9)


#communicate parameters to user in tool messages tab
arcpy.AddMessage('''Here are the specified -
+ Parameter 0: {0}
+ Parameter 1: {1}
+ Parameter 2: {2}
+ Parameter 3: {3}
+ Parameter 4: {4}
+ Parameter 5: {5}
+ Parameter 6: {6}
+ Number of Classes: {7}
+ Parameter 8: {8}
+ Output features: {9}'''\
.format(in_Point_Features,in_Polygon_Features, in_Polygon_Join_Field, \
in_Area_Field, in_Data_Table_For_Polygons,in_Data_Table_Join_Field, \
in_Data_Table_Field, in_Number_Of_Classes, in_Drawn_Map_Type, output_feature_class))

#report runtime parameters to user also in tool environments tab
arcpy.AddMessage('''Environments -
+ Workspace: {0}
+ Overwrite: {1}
+ Scratch GDB: {2}
+ Package workspace: {3}'''\
.format(arcpy.env.workspace, arcpy.env.overwriteOutput, \
arcpy.env.scratchGDB, arcpy.env.packageWorkspace))

#create thiessen polygons based on library locations
arcpy.env.extent = in_Polygon_Features
thiessen_output_features = 'thiessen'
output_fields = 'ALL'
thiessen_polygons = arcpy.CreateThiessenPolygons_analysis(in_Point_Features, thiessen_output_features, output_fields)

#intersect the thiessen polygons with the tracts
intersect_output_features = 'intersection'
arcpy.analysis.Intersect([in_Polygon_Features,thiessen_polygons], intersect_output_features)

#join the intersection output with the population table
intersection_joinedtable = arcpy.JoinField_management(intersect_output_features, in_Polygon_Join_Field, in_Data_Table_For_Polygons, in_Data_Table_Join_Field, [in_Data_Table_Field])

#get the population proportions in each polygon after intersection and get population total
arcpy.management.AddField(intersection_joinedtable, 'NewPop', 'DOUBLE')
update_cursor = arcpy.da.UpdateCursor(intersection_joinedtable,[in_Area_Field, 'Shape_Area', in_Data_Table_Field,'NewPop'])
total_pop = 0
for row in update_cursor:
    popproportion = (row[1]/row[0])*row[2]
    total_pop = total_pop + popproportion
    row[3] = popproportion
    update_cursor.updateRow(row)

#dissolve the joined layer with the new fields and compute the total population and then the percent of population
dissolved_featureclass = output_feature_class
arcpy.management.Dissolve(intersection_joinedtable, dissolved_featureclass, ['NAME'], [["NewPop", "SUM"]])
arcpy.management.AddField(dissolved_featureclass, 'PercentPop', 'DOUBLE')
update_cursor = arcpy.da.UpdateCursor(dissolved_featureclass,['SUM_NewPop','PercentPop'])
for row in update_cursor:
    row[1] = (row[0]/total_pop)*100
    update_cursor.updateRow(row)

#mapping
aprx = arcpy.mp.ArcGISProject('CURRENT')
layer = aprx.activeMap.addDataFromPath(dissolved_featureclass)
symbology = layer.symbology
if (in_Drawn_Map_Type == 'Graduated Colors'):
    symbology.updateRenderer('GraduatedColorsRenderer')
    symbology.renderer.classificationField = 'PercentPop'
elif (in_Drawn_Map_Type == 'Graduated Symbols'):
    symbology.updateRenderer('GraduatedSymbolsRenderer')
    symbology.renderer.classificationField = 'SUM_NewPop'

symbology.renderer.breakCount = float(in_Number_Of_Classes)
layer.symbology = symbology
   
    


