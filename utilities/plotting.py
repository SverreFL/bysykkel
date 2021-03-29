import pandas as pd
from pathlib import Path
import numpy as np
import geopandas as gpd
from shapely.geometry import LineString

import osmnx as ox
import networkx as nx

from ipyleaflet import Map, Marker, CircleMarker, basemaps, Path, GeoData, Polyline
from ipywidgets import HTML

'''
1. Initialiserer graf med endelig antall nodes samt kanter mellom nodes (merk: kantene har geometri med koordinater)
2. For hver origin_id finner jeg korteste sti til hver destinastion_id. Gir meg route som er sekvens av node_ids
3. Ikke tilstrekkelig å ha rette linjer mellom nodes i route; får ut alle koordinater til kanter mellom nodene i route
4. Bruker sekvens av (x,y)-tupler til å lage LineString mellom origin og destination
5. Vil large LineString objektet i trips_dataframen
6. Tror også jeg vil ha marker-objekt i denne.. litt usikker på dette. Uansett, viktig at jeg bruker node i graf i stedet
for koordinat slik at matcher med kartet mitt :-)
'''

# putt dette i funksjon
graph = ox.graph_from_point([60.38819667374428, 5.328564137089416], dist=2500, network_type='bike')
nodes, edges = ox.graph_to_gdfs(graph)
edges = edges.sort_index()

def make_geometries(stations, trips):
    '''
    Main funksjon. Samme index som trips. Hvis observert kobling så skal det ha geopandas objekt med lineplot, ellers nan.
    '''
    geometries = pd.Series(index=trips.index, dtype='object', name='geometry')
    for origin_id in stations.index:
        print(origin_id)
        paths = make_paths(origin_id, stations, trips)
        geometries.loc[origin_id] = paths.values
    return geometries


def make_paths(origin_id, stations, trips):
    '''
    Lager series med geopandas objekt fra gitt stasjons_id og til alle med observert kobling
    '''
    origin = stations.loc[origin_id, ['latitude', 'longitude']].to_list()
    origin_node = ox.get_nearest_node(graph, origin) # id til node i graf
    
    # må huske å lagre litt id og sånn her fordi jeg vil legge til geometri i dataframe til slutt... vil ha det i mine trips
    destination_nodes = get_destination_nodes(origin_id, stations, trips) # series med (stasjons_id, node_id)
    routes = get_routes(origin_node, destination_nodes) # series med (stasjons_id, [liste med node_id])
    paths = get_paths(routes)
    return paths
    

def get_destination_nodes(origin_id, stations, trips):
    '''
    For gitt stasjons_id så looper den over alle statsjons_id til destinasjoner der folk har syklet til. 
    Finner korresponderende id til nodes i grafen og returnerer en liste av disse.

    returnerer series med end_station_id og node
    '''
    destination_nodes = pd.Series(index=trips.loc[origin_id].index, dtype='object')
    for idx in destination_nodes.index:
        if idx == origin_id or trips.loc[(origin_id,idx)].isna().all(): # ta vekk rundtur og stasjoner som ikke har blitt kjørt til
            continue
        destination = stations.loc[idx,['latitude', 'longitude']].to_list()
        destination_node = ox.get_nearest_node(graph, destination)
        destination_nodes[idx] = destination_node
    return destination_nodes

def get_routes(origin_node, destination_nodes):
    '''
    Har en origin node og liste av destination nodes. Bruker algoritme til å finne sekvens av noder som kobler origin og ulike
    destinations. Returnerer en liste av lister.

    destination_nodes er series med (station_id, node_id)
    '''
    routes = pd.Series(index=destination_nodes.index, dtype='object')
    for idx in routes.index:
        if np.isnan(destination_nodes[idx]): # ta vekk stasjons_id uten korresponderende node_id fordi ikke blitt kjørt til
            continue
        destination_node = destination_nodes[idx]
        routes[idx] = nx.shortest_path(graph, origin_node, destination_node, weight='distance')
    return routes

def get_paths(routes):
    '''
    routes er series 
    '''
    paths = pd.Series(index=routes.index, dtype='object')
    for idx in paths.index:
        if isinstance(routes[idx], list):
            xs, ys = get_coords(routes[idx], edges)
            paths[idx] = gpd.GeoDataFrame([LineString(zip(xs,ys))], columns=['geometry'])
    return paths 

def get_coords(route, edges=edges):
    '''
    Takes list of node_ids, returns tuple ([xs], [ys]) of coordinates for all points in geometry of vertices between all nodes
    '''
    x_coords = []
    y_coords = []
    for u, v in zip(route, route[1:]):
        geom = edges.loc[(u,v)].geometry.values[0]
        xs, ys = geom.xy
        x_coords.extend(xs.tolist())
        y_coords.extend(ys.tolist())
    return x_coords, y_coords

