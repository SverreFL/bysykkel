import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import panel as pn
from ipyleaflet import Map, Marker, FullScreenControl, basemaps, Popup
from ipywidgets import HTML

from utilities.plotting import some_plot_function

path = Path('resources/data')

def main(center=[60.388197,5.328564], zoom=13):
    '''
    Ny versjon der jeg ikke plotter linjer på kart... kun bruker marker som slags widget for å bestemme current stasjons id,
    lager dynamisk plott for current stasjons id for current subset av observasjoner
    '''    
    # laster inn data
    stations = pd.read_pickle(path / 'stations')
    #trips = pd.read_csv(path / 'trips.csv')
    #arrivals = pd.read_csv(path / 'arrivals.csv')
    num_trips_per_hour = pd.read_pickle(path / 'num_trips_per_hour')
    num_arrivals_per_hour = pd.read_pickle(path / 'num_arrivals_per_hour')

    # globals
    HAS_CLICKED = False # vet ikke om jeg trenger å holde oversikt over dette lenger
    CURRENT_SUBSET = 'all'
    CURRENT_STATION_ID = None
        
    # callbacks
    def callback_radio_group(*args, **kwargs):
        '''
        Endrer global value for subset av observasjon (alle dager, hverdag eller helg).
        Vil også at den skal generere plot for nytt subset av observasjon for CURRENT_STATION_ID
        '''
        nonlocal CURRENT_SUBSET
        table = {'Alle dager':'all', 'Hverdager':'weekdays', 'Helg':'weekends'}
        CURRENT_SUBSET = table[radio_group.value]
        
        plot_pane.object = some_plot_function(CURRENT_STATION_ID, CURRENT_SUBSET,
                             num_arrivals_per_hour, num_trips_per_hour)
    
    def callback_reset_button(*args, **kwargs):
        nonlocal CURRENT_STATION_ID
        CURRENT_STATION_ID = None
        radio_group.value = 'Alle dager'
        plot_pane.object = some_plot_function(CURRENT_STATION_ID, CURRENT_SUBSET,
                             num_arrivals_per_hour, num_trips_per_hour)
    
    def callback_marker_click(*args, **kwargs):
        nonlocal HAS_CLICKED, CURRENT_STATION_ID
        #HAS_CLICKED.value = 1
        # hacky løsning for å finne stasjonsid som er nærmest koordinat...
        y, x = kwargs['coordinates']
        num_idx = (np.abs(stations.latitude-y)+np.abs(stations.longitude-x)).argmin()
        station_id = stations.index[num_idx]
        
        CURRENT_STATION_ID = station_id
        plot_pane.object = some_plot_function(CURRENT_STATION_ID, CURRENT_SUBSET,
                             num_arrivals_per_hour, num_trips_per_hour)
    
    def handle_mouseover(**kwargs):
        # hacky løsning for å finne stasjonsid som er nærmest koordinat...
        y, x = kwargs['coordinates']
        num_idx = (abs(stations.latitude-y)).argmin()
        station_id = stations.index[num_idx]

        msg = HTML(value=stations.loc[station_id, 'name'])
        popup = Popup(location=[y,x], child=msg)
        # m.add_layer(popup)

    def handle_mouseout(**kwargs):
        # Må finnes smartere måter ...
        for x in m.layers:
            if isinstance(x,Popup):
                m.remove_layer(x)   

    # widgets og deres callbacks
    radio_group = pn.widgets.RadioButtonGroup(options=['Alle dager', 'Hverdager', 'Helg'])
    radio_group.param.watch(callback_radio_group, 'value')
    
    reset_button = pn.widgets.Button(name='Nullstill')
    reset_button.on_click(callback_reset_button)

    

    # Make map 
    def make_markers(stations):
        '''
        returnere series med stasjons_id : CircleMarker objekt
        '''
        # node_ids = get_node_ids(stations) # series
        markers = pd.Series(index=stations.index, dtype='object')
        for idx in stations.index:
        #   node_id = node_ids[idx]
            location = stations.loc[idx, ['latitude','longitude']].to_list()
            marker = Marker(location=location, radius=4, weight=3,
                                title = stations.loc[idx,'name'],
                                color='green', fill_opacity=0.2)
            marker.on_click(callback_marker_click)
            marker.on_mouseover(handle_mouseover)
            marker.on_mouseout(handle_mouseout)
            markers.loc[idx] = marker
        return markers        
        
    def initialize_map():
        m = Map(center=center, zoom=zoom)
        m.add_control(FullScreenControl())
        markers = make_markers(stations)

        for marker in markers:
            m.add_layer(marker)
        
        return m
    m = initialize_map()
    fig = some_plot_function(CURRENT_STATION_ID, CURRENT_SUBSET,
                             num_arrivals_per_hour, num_trips_per_hour)
    # Lager eksplisitt pane objekter, deretter plasser de i layout
    title_pane = pn.pane.Markdown('## Bergen bysykkel 2020')
    map_pane = pn.pane.ipywidget.IPyLeaflet(m, width=500)
    plot_pane = pn.pane.plot.Matplotlib(fig)
    layout = pn.Column(title_pane, pn.Row(radio_group, reset_button), pn.Row(map_pane, plot_pane))
    
    return layout

 