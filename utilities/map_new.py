'''
Nytt main script etter at det forrige kartet gikk i vasken siden panel ikke håndterer CircleMarker og LinePlot i nettleser
(utenfor notebook)

TODO: kunne vært greit å flytte funksjonene `make_markers` og `initialize_map` til annen modul for å rendyrke logikken i dashbordet 
'''

import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
import panel as pn
from ipyleaflet import Map, Marker, Popup
from ipywidgets import HTML

from utilities.plotting import some_plot_function
path = Path('resources/data')

def main(center=[60.388197,5.328564], zoom=13):
    '''
    Initialiserer widgets, kobler de mot objekt som blir renderet i pane og plasserer de i layout til slutt. 
    Består av to hoveddeler:
    1. Ipyleaflet kart med interaktive Markers som angir stasjons_id og caller plot_funksjon når de blir trykket på
    2. Figur som viser plottet med data om angitte stasjons_id
    
    I tillegg er det en radiobutton som angir hvilken subset av observasjonene som benyttes til å lage plottet
    '''    
    # laster inn data
    stations = pd.read_pickle(path / 'stations')
    num_trips_per_hour = pd.read_pickle(path / 'num_trips_per_hour')
    num_arrivals_per_hour = pd.read_pickle(path / 'num_arrivals_per_hour')

    # globals
    HAS_CLICKED = False # Tror ikke jeg trenger å holde oversikt over dette lenger
    CURRENT_SUBSET = 'all'
    CURRENT_STATION_ID = None
        
    # callbacks
    def callback_radio_group(*args, **kwargs):
        '''
        Endrer global value for subset av observasjon (alle dager, hverdag eller helg).
        Generere plot for nytt subset av observasjon for CURRENT_STATION_ID
        '''
        nonlocal CURRENT_SUBSET
        table = {'Alle dager':'all', 'Hverdager':'weekdays', 'Helg':'weekends'}
        CURRENT_SUBSET = table[radio_group.value]
        
        plot_pane.object = some_plot_function(CURRENT_STATION_ID, CURRENT_SUBSET,
                             num_arrivals_per_hour, num_trips_per_hour)
    
    def callback_reset_button(*args, **kwargs):
        '''
        Resetter de globale variablene og generer plot.
        '''
        nonlocal CURRENT_STATION_ID
        CURRENT_STATION_ID = None
        radio_group.value = 'Alle dager'
        plot_pane.object = some_plot_function(CURRENT_STATION_ID, CURRENT_SUBSET,
                             num_arrivals_per_hour, num_trips_per_hour)
    
    def callback_marker_click(*args, **kwargs):
        '''
        Endrer global variabel `CURRENT_STATION_ID` til angitt stasjon og generer plot.
        '''
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
        '''
        Depreciated
        '''
        # hacky løsning for å finne stasjonsid som er nærmest koordinat...
        y, x = kwargs['coordinates']
        num_idx = (abs(stations.latitude-y)).argmin()
        station_id = stations.index[num_idx]

        msg = HTML(value=stations.loc[station_id, 'name'])
        popup = Popup(location=[y,x], child=msg)
        # m.add_layer(popup)

    def handle_mouseout(**kwargs):
        '''
        Depreciated
        '''
        # Må finnes smartere måter ...
        for x in m.layers:
            if isinstance(x,Popup):
                m.remove_layer(x)   

    # widgets og deres callbacks
    radio_group = pn.widgets.RadioButtonGroup(options=['Alle dager', 'Hverdager', 'Helg'])
    radio_group.param.watch(callback_radio_group, 'value')
    
    reset_button = pn.widgets.Button(name='Nullstill', width=100)
    reset_button.on_click(callback_reset_button)

    # Make map 
    def make_markers(stations):
        '''
        Returnere Series med (stasjons_id:Marker) mapping. 
        '''
        markers = pd.Series(index=stations.index, dtype='object')
        for idx in stations.index:
            location = stations.loc[idx, ['latitude','longitude']].to_list()
         
            markers.loc[idx] = Marker(location=location, radius=4, weight=3,
                                      title = stations.loc[idx,'name'],
                                      color='green', fill_opacity=0.2,
                                      draggable=False)
                
        return markers        
        
    def initialize_map():
        '''
        Lager kart og legger på markers med callbacks
        '''
        m = Map(center=center, zoom=zoom)
        # m.add_control(FullScreenControl())
        markers = make_markers(stations)
        
        for marker in markers:
            marker.on_click(callback_marker_click)
            # marker.on_mouseover(handle_mouseover) 
            # marker.on_mouseout(handle_mouseout)
            m.add_layer(marker)
        return m
    
    # lager default objekt
    m = initialize_map()
    fig = some_plot_function(CURRENT_STATION_ID, CURRENT_SUBSET,
                             num_arrivals_per_hour, num_trips_per_hour)
    
    # Lager eksplisitt pane objekter, deretter plasser de i layout
    title_pane = pn.pane.Markdown('## Bergen bysykkel 2020')
    map_pane = pn.pane.ipywidget.IPyLeaflet(m, width=500)
    plot_pane = pn.pane.plot.Matplotlib(fig)
    layout = pn.Column(title_pane, pn.Row(radio_group, reset_button), pn.Row(map_pane, plot_pane))
    
    return layout

 