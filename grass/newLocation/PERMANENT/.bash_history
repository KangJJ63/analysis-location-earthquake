v.import input=C:\earthquake\result\Earthquake-EMERGENCY_ASSEMBLY_AREA\population.shp layer=population output=population
v.import input=C:\earthquake\result\Earthquake-EMERGENCY_ASSEMBLY_AREA\population.shp layer=population output=population
v.import input=C:\earthquake\result\Earthquake-EMERGENCY_ASSEMBLY_AREA\refuge.shp layer=refuge output=refuge
v.out.ogr input=population@PERMANENT output=C:\earthquake\result\Earthquake-EMERGENCY_ASSEMBLY_AREA\start format=ESRI_Shapefile
v.out.ogr input=refuge@PERMANENT output=C:\earthquake\result\Earthquake-EMERGENCY_ASSEMBLY_AREA\end format=ESRI_Shapefile
v.import input=C:\earthquake\result\Earthquake-EMERGENCY_ASSEMBLY_AREA\population.shp layer=population output=population
v.import input=C:\earthquake\result\Earthquake-EMERGENCY_ASSEMBLY_AREA\refuge.shp layer=refuge output=refuge
