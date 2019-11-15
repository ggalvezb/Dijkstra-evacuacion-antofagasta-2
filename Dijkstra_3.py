import geopandas as gpd
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import geog
import numpy as np
from shapely import geometry
from shapely.geometry import Point,LineString
import fiona
from fiona import drivers
import sys
import itertools
import igraph
import csv



#Leer datos
streets=gpd.read_file('C:/Users/ggalv/Google Drive/Respaldo/TESIS MAGISTER/tsunami/Shapefiles/Corrected_Road_Network/Antofa_nodes_cut_edges/Antofa_edges.shp')
nodes=gpd.read_file('C:/Users/ggalv/Google Drive/Respaldo/TESIS MAGISTER/tsunami/Shapefiles/Corrected_Road_Network/Antofa_nodes_cut_edges/Antofa_nodes.shp')
houses_to_evacuate=gpd.read_file('C:/Users/ggalv/Google Drive/Respaldo/TESIS MAGISTER/tsunami/Shapefiles/Individual_Houses/House_to_evacuate/Houses_to_evacuate.shp')
points_of_evacuation=gpd.read_file('C:/Users/ggalv/Google Drive/Respaldo/TESIS MAGISTER/tsunami/Shapefiles/Tsunami/Puntos_Encuentro/Puntos_Encuentro_Antofagasta/puntos_de_encuentro.shp')
nodes_without_buildings=gpd.read_file('C:/Users/ggalv/Google Drive/Respaldo/TESIS MAGISTER/tsunami/Shapefiles/Corrected_Road_Network/Antofa_nodes_cut_edges/sin_edificios/Antofa_nodes.shp')
nodes_without_cut=gpd.read_file('C:/Users/ggalv/Google Drive/Respaldo/TESIS MAGISTER/tsunami/Shapefiles/Corrected_Road_Network/Antofa_nodes_subset2/Antofa_nodes_subset2.shp')
buildings=gpd.read_file('C:/Users/ggalv/Google Drive/Respaldo/TESIS MAGISTER/tsunami/Shapefiles/Edificios/Edificios_zona_inundacion.shp')
#ID mayor a 2219 en nodos es un edificio!!!!!
#ID mayor a 4439 en streets es una calle de edificio!!!!!


#Creacion de grafo
g = igraph.Graph(directed = True)
g.add_vertices(list(nodes.id))
g.add_edges(list(zip(streets.u, streets.v)))
g.es['id']=list(streets['id'])
g.es['length']=list(streets['length'])


def min_dist(point, gpd2):
    gpd2['Dist'] = gpd2.apply(lambda row:  point.distance(row.geometry),axis=1)
    geoseries = gpd2.iloc[gpd2['Dist'].argmin()]
    return geoseries

def graficador(id_house,home_to_mt):
    ruta_bug=[]
    print(home_to_mt[str(id_house)])
    for id in home_to_mt[str(id_house)]:
        ruta_bug.append(streets.loc[streets['id']==str(id)]['geometry'])   
    f, ax = plt.subplots()
    # ax.set_prop_cycle(color=['red', 'green', 'blue'])
    color=['c', 'm', 'y','r','b','g','w','c', 'm', 'y','r','b','g','w']
    for i in range(len(ruta_bug)):
        gpd.plotting.plot_linestring_collection(ax, ruta_bug[i], linewidth=2,color=color[i])
    plt.show()

def routing():
    home_to_mt={}
    home_to_bd={}
    bd_to_mt={}
    # len(houses_to_evacuate)
    for i in range(10):
        #Ruta de hogar a punto de encuentro
        point=houses_to_evacuate.loc[i]['geometry'] 
        inicio_id=min_dist(point, nodes_without_buildings)['id']
        inicio_vertex=g.vs.find(name=str(inicio_id)).index
        final=min_dist(point, points_of_evacuation) #Calculo punto de encuentro mas cercano
        fin_point=final['geometry'] 
        fin_id=min_dist(fin_point, nodes_without_cut)['id']
        fin_vertex=g.vs.find(name=str(fin_id)).index
        shortest_path=g.get_shortest_paths(inicio_vertex, to=fin_vertex, weights=g.es['length'], mode=igraph.OUT, output="epath")[0]
        path_id=[]
        for j in range(len(shortest_path)):
            path_id.append(g.es[shortest_path[j]]['id'])
            home_to_mt[str(int(houses_to_evacuate.loc[i]['OBJECTID']))]=[path_id,final['OBJECTID']]
        #Ruta de hogar a edificio
        final=min_dist(point, buildings)
        fin_point_bd=final['geometry'] #Calculo edificio mas cercano
        fin_id_bd=min_dist(fin_point_bd, nodes)['id']
        fin_vertex_bd=g.vs.find(name=str(fin_id_bd)).index
        shortest_path=g.get_shortest_paths(inicio_vertex, to=fin_vertex_bd, weights=g.es['length'], mode=igraph.OUT, output="epath")[0]
        path_id=[]
        for j in range(len(shortest_path)):
            path_id.append(g.es[shortest_path[j]]['id'])
            home_to_bd[str(int(houses_to_evacuate.loc[i]['OBJECTID']))]=[path_id,final['fid']]  
        #Ruta de edificio a punto de encuentro
        point=fin_point_bd
        inicio_vertex=fin_vertex_bd
        final=min_dist(point, points_of_evacuation)
        fin_point=final['geometry'] #Calculo punto de encuentro mas cercano
        fin_id=min_dist(fin_point, nodes_without_cut)['id']
        fin_vertex=g.vs.find(name=str(fin_id)).index
        shortest_path=g.get_shortest_paths(inicio_vertex, to=fin_vertex, weights=g.es['length'], mode=igraph.OUT, output="epath")[0]
        path_id=[]
        for j in range(len(shortest_path)):
            path_id.append(g.es[shortest_path[j]]['id'])
            bd_to_mt[str(int(houses_to_evacuate.loc[i]['OBJECTID']))]=[path_id,final['OBJECTID']]
    return(home_to_mt,home_to_bd,bd_to_mt) 


home_to_mt,home_to_bd,bd_to_mt=routing()
print(len(home_to_mt))
print(len(home_to_bd))
print(len(bd_to_mt))


"""
#tester para verificar que todos tengan camino de casa a punto de encuentro
sin_camino=[]
for i in range(len(houses_to_evacuate)):
    id_a_buscar=str(int(houses_to_evacuate.loc[i]['OBJECTID']))
    if id_a_buscar in list(home_to_mt.keys()):
        a=1
    else:
        sin_camino.append(id_a_buscar)


def second_min_dist(point, gpd2):
    gpd2['Dist'] = gpd2.apply(lambda row:  point.distance(row.geometry),axis=1)
    min_distance=sorted(gpd2['Dist'])[1]
    geoseries = gpd2.loc[gpd2['Dist']==min_distance,'id'].item()
    return geoseries    


def corrector_rutas_1():
    for i in range(len(sin_camino)):
        point=houses_to_evacuate.loc[houses_to_evacuate['OBJECTID']==int(sin_camino[i])]['geometry']
        inicio_id=min_dist(point, nodes_without_buildings)['id']
        inicio_vertex=g.vs.find(name=str(inicio_id)).index
        fin_point=min_dist(point, points_of_evacuation)['geometry']
        fin_id=second_min_dist(fin_point, nodes_without_cut)
        fin_vertex=g.vs.find(name=str(fin_id)).index
        shortest_path=g.get_shortest_paths(inicio_vertex, to=fin_vertex, weights=g.es['length'], mode=igraph.OUT, output="epath")[0]
        path_id=[]
        for j in range(len(shortest_path)):
            path_id.append(g.es[shortest_path[j]]['id'])
            home_to_mt[str(int(houses_to_evacuate.loc[houses_to_evacuate['OBJECTID']==int(sin_camino[i])]['OBJECTID']))]=path_id

corrector_rutas_1()
print("home_to_mt: ",len(home_to_mt))




# save 2.0
np.save('C:/Users/ggalv/Desktop/caminos/home_to_mt.npy', home_to_mt)
np.save('C:/Users/ggalv/Desktop/caminos/home_to_bd.npy', home_to_bd) 
np.save('C:/Users/ggalv/Desktop/caminos/bd_to_mt.npy', bd_to_mt) 

# load 2.0
home_to_mt_load = np.load('C:/Users/ggalv/Desktop/caminos/home_to_mt.npy').item()
home_to_bd_load = np.load('C:/Users/ggalv/Desktop/caminos/home_to_bd.npy').item()
bd_to_mt_load = np.load('C:/Users/ggalv/Desktop/caminos/bd_to_mt.npy').item()
print(len(home_to_mt_load))
print(len(home_to_bd_load))
print(len(bd_to_mt_load))



#TEster
point=houses_to_evacuate.loc[0]['geometry'] 
inicio_id=min_dist(point, nodes_without_buildings)['id']
inicio_vertex=g.vs.find(name=str(inicio_id)).index
fin_point=min_dist(point, points_of_evacuation)['geometry']

"""