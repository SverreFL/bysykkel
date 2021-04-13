'''
Gammel main. Kart med interaktive CircleMarkers på hver stasjon

TODO: Bytt button til radiogroup for å velge subset av observasjon (alle, hverdag, helg). Kopiere ting fra new main. Forsøke
å få operativ i jupyter i hvertfall..
'''
import pandas as pd
import numpy as np

from pathlib import Path
from ipyleaflet import Map, CircleMarker, GeoData, FullScreenControl, basemaps, Popup
from ipywidgets import HTML
from utilities.data import load_data, make_stations, make_trips, make_arrivals

path = Path('resources/data')

stations = pd.read_pickle(path / 'stations')
trips = pd.read_pickle(path / 'trips')

geometries = pd.read_pickle('resources/geometry/geometries')
def main(stations, trips, center=[60.388197,5.328564], zoom=13):
    '''
    .....
    '''
    # laste inn data
    stations = pd.read_pickle(path / 'stations')
    trips_per_hour = pd.read_pickle(path / 'trips')

    # globals
    HAS_CLICKED = False # Tror ikke jeg trenger å holde oversikt over dette lenger
    CURRENT_SUBSET = 'all'
    CURRENT_STATION_ID = None


    
    def callback_all(event):
        nonlocal CURRENT_SUBSET
        CURRENT_SUBSET = 'all'
        if HAS_CLICKED.value:
            remove_paths()
            add_paths(CURRENT_STATION_ID.value)

    def callback_weekdays(event):
        nonlocal CURRENT_SUBSET
        CURRENT_SUBSET = 'weekdays'
        if HAS_CLICKED.value:
            remove_paths()
            add_paths(CURRENT_STATION_ID.value)

    def callback_weekends(event):
        nonlocal CURRENT_SUBSET
        CURRENT_SUBSET = 'weekends'
        if HAS_CLICKED.value:
            remove_paths()
            add_paths(CURRENT_STATION_ID.value)
    
    ALLDAYS.on_click(callback_all)
    WEEKDAYS.on_click(callback_weekdays)
    WEEKENDS.on_click(callback_weekends)
    


    RESET = pn.widgets.Button(name='Nullstill')
    geometries = pd.read_pickle('resources/geometries_walk_37')
    
    #----------#
    # HANDLERS #
    #----------#
    def handle_click(*args, **kwargs):
        nonlocal HAS_CLICKED, CURRENT_STATION_ID
        HAS_CLICKED.value = 1
        y, x = kwargs['coordinates']
        # hacky løsning for å finne stasjonsid som er nærmest koordinat...
        num_idx = (np.abs(stations.latitude-y)+np.abs(stations.longitude-x)).argmin()
        station_id = stations.index[num_idx]
        
        CURRENT_STATION_ID.value = int(station_id)

        remove_paths()
        add_paths(int(station_id))
    
    def handle_mouseover(**kwargs):
        y, x = kwargs['coordinates']
        # hacky løsning for å finne stasjonsid som er nærmest koordinat...
        num_idx = (abs(stations.latitude-y)).argmin()
        station_id = stations.index[num_idx]

        trips_sub = trips[CURRENT_SUBSET]
        if not HAS_CLICKED.value:
            msg = HTML(value=stations.loc[station_id, 'name'])
            popup = Popup(location=[y,x], child=msg)
            m.add_layer(popup)
        if HAS_CLICKED.value:
            line1 = stations.loc[station_id, 'name']
            line2 = f'Antall reiser: {trips_sub.loc[(CURRENT_STATION_ID.value, station_id),"count"]}'
            line3 = f'Gj.snitt tid: {get_duration(CURRENT_STATION_ID.value, station_id)}'
            value = '<br>'.join(line for line in [line1, line2, line3])
            
            msg = HTML(value=value)
            popup = Popup(location=[y,x], child=msg)
            m.add_layer(popup)

    def handle_mouseout(**kwargs):
        # Må finnes smartere måter ...
        for x in m.layers:
            if isinstance(x,Popup):
                m.remove_layer(x)   
    
    def add_paths(station_id):
        '''
        helper som legger til paths fra stasjon når clicker på marker
        '''
        trips_sub = trips[CURRENT_SUBSET]
        bins = pd.cut(trips_sub.loc[station_id, 'count'], bins=10, labels=range(10)) 
        for idx in geometries.loc[station_id].index:
            if trips_sub.loc[(station_id, idx)]['count'] < 1:
                continue
            geom = geometries.loc[(station_id, idx)]
            if not isinstance(geom, float): # hacky måte å sjekke om nan...
                weight = 1 + 0.2*bins[idx]
                path_layer = GeoData(geo_dataframe = geom, style={'color':'black', 'weight':weight})
                m.add_layer(path_layer)

    def remove_paths():
        '''
        helper som fjerne eksisterende paths når clicker på ny marker
        '''
        for x in m.layers:
            if isinstance(x, GeoData):
                m.remove_layer(x)

    #--------------#
    # END HANDLERS #
    #--------------#

    def get_duration(origin, destination):
        '''
        returnerer formatert string med gj.snitt reisetid
        '''
        trips_sub = trips[CURRENT_SUBSET]
        obs = trips_sub.loc[(origin, destination)].astype(int)
        if obs['count'] == 0: # kanskje ikke smart å bruke navn på metode som kolonnenanv. ....
            string_out = ''
        elif obs.hours > 0:
            string_out = 'Over 60 min'
        else:
            minutes = '0' + str(obs.minutes) if len(str(obs.minutes)) == 1 else str(obs.minutes)
            seconds = '0' + str(obs.seconds) if len(str(obs.seconds)) == 1 else str(obs.seconds)
            string_out = minutes + ':' + seconds
        return string_out
    
    def make_markers(stations):
        '''
        returnere series med stasjons_id : CircleMarker objekt
        '''
        # node_ids = get_node_ids(stations) # series
        markers = pd.Series(index=stations.index, dtype='object')
        for idx in stations.index:
        #   node_id = node_ids[idx]
            location = stations.loc[idx, ['latitude','longitude']].to_list()
            marker = CircleMarker(location=location, radius=4, weight=3,
                                title = stations.loc[idx,'name'],
                                color='green', fill_opacity=0.2)
            marker.on_click(handle_click)
            
            marker.on_mouseover(handle_mouseover)
            marker.on_mouseout(handle_mouseout)
            markers.loc[idx] = marker
        return markers        
    
    #------------------------#
    # håndtere panel sjit.. map i pane 
    #------------------------#



    def reset_callback(event):
        HAS_CLICKED.value = 0
        remove_paths()
    
    RESET.on_click(reset_callback)

    def initialize_map():
        m = Map(center=center, zoom=zoom)
        m.add_control(FullScreenControl())
        markers = make_markers(stations)

        for marker in markers:
            m.add_layer(marker)
        
        return m
    m = initialize_map()
        
    # set up panel layout, må jobbe direkte med pane i stedet for m tror jeg ...
    gui = pn.Column(pn.Row(ALLDAYS, WEEKDAYS, WEEKENDS, RESET), m)
    return gui