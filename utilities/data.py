'''
Lager dataframes:
1. stations
- har id, navn, lat, long
- kun informasjon om stasjonene, helt uavhengig av antall reiser
2. trips
- df med multiindex der hver origin viser antall reiser og gj.snitt. tid til alle destination.
- øverste level i multiindex viser hvilket subset av observasjoner som er brukt (all, weekdays, weekend)
3. num_per_hour for trips og arrivals
- df med multiindex med [(subset, station_id, hour)] som angir gjennomsnittlig antall turer til (arrivals) og fra (trips)
for timen som begynner i hour for hver stasjon for hver subset.

Lagrer disse til disk med .to_pickle()
'''
import pandas as pd
from pathlib import Path
import os

def load_data(start, end):
    '''
    Laster inn alle .csv og filtrer på start og end i 'yyyy-mm-dd' format
    Lager også variabel som indikerer om sykkelturen startet i helg
    '''
    path = Path('./data/bysykkel/')
    dfs = []
    for filename in os.listdir(path):
        if filename.endswith('.csv'):
            dfs.append(pd.read_csv(path/filename))
    df = pd.concat(dfs)
    df = parse_time_columns(df)
    df = df.sort_values('started_at')
    df = df[(df.started_at >= start) & (df.ended_at <= end)]
    df['weekend'] = df.started_at.dt.weekday >= 5
    return df

def parse_time_columns(df):
    df['started_at'] = pd.to_datetime(df['started_at'])
    df['ended_at'] = pd.to_datetime(df['ended_at'])
    return df

def make_stations(df):
    '''
    Lager dataframe som mapper station_id til navn, latitude og longitude
    '''
    cols = ['start_station_name', 'start_station_latitude', 'start_station_longitude']
    df_out = df.groupby('start_station_id')[cols].first()
    df_out.columns = ['name', 'latitude', 'longitude']
    df_out = df_out.sort_index()
    return df_out

def make_trips(df):
    '''
    Lager dataframe med multiindex med tre nivåer:
    1. hvilket subset av observasjoner som er brukt (all, weekdays, weekend)
    2. hvilken stasjon sykkeltur startet fra
    3. hvilken stasjon den sluttet

    For kombinasjon (subset, start, slutt) er det kolonne med verdi for antall reiser og gjennomsnittlig reisetid i
    sekunder. Har i tillegg kolonner der gjennomsnittlig reisetid blir representert med antall timer, minutter og sekunder.
    '''
    
    keys = ['all', 'weekdays', 'weekends']
    dfs = []
    for key in keys:
        df_sub = df.copy()
        if key == 'weekdays':
            df_sub = df_sub[df_sub.weekend==False]
        elif key == 'weekends':
            df_sub = df_sub[df_sub.weekend==True]
        else:
            df_sub = df_sub            
        df_sub['subset'] = key
        
        out_index = pd.MultiIndex.from_product([df.start_station_id.unique()]*2)
        df_out = (df_sub.groupby(['start_station_id', 'end_station_id']).
                     duration.
                     agg(['count', 'mean']).
                     rename(columns={'count':'num_trips', 'mean':'avg_duration'}).
                     reindex(out_index). # padde nans... må finnes smartere måte
                     sort_index())
        
        # legge til subset som level 0 i multiindex
        temp = out_index.to_frame()
        temp.insert(0, 'subset', key)
        out_index = pd.MultiIndex.from_frame(temp)
        df_out = df_out.set_index(out_index)
        
        df_out['num_trips'] = df_out['num_trips'].fillna(0).astype(int)

        components = pd.to_timedelta(df_out['avg_duration'], 'seconds').dt.components
        df_out['hours'] = components.hours
        df_out['minutes'] = components.minutes
        df_out['seconds'] = components.seconds
        
        dfs.append(df_out)
    return pd.concat(dfs)

def make_arrivals(trips):
    '''
    Samme utforming som trips. Har bare byttet levels i multiindex mellom opprinnelse og destinasjon.
    '''
    arrivals = trips.copy()
    arrivals.index = arrivals.index.swaplevel(i=-2,j=-1)
    arrivals = arrivals.sort_index()
    return arrivals

def make_num_per_hour(df, trips=True, start_hour=5):
    '''
    Gjennomsnittlig antall turer for hver time på dagen for hver stasjon. Trips hvis turer fra, ellers arrivals.
    '''
    df['day_of_year'] = df.started_at.dt.day_of_year
    keys = ['all', 'weekdays', 'weekends']
    dfs = []
    
    for key in keys:
        df_sub = df.copy()
        if key == 'weekdays':
            df_sub = df_sub[df_sub.weekend==False]
        elif key == 'weekends':
            df_sub = df_sub[df_sub.weekend==True]
        else:
            df_sub = df_sub
        
        num_days = len(df_sub['day_of_year'].unique())
        df_sub['hour'] = df_sub['ended_at'].dt.hour
        
        if trips:
            df_out = (df_sub.groupby(['start_station_id', 'hour']).
                            duration. # vilkårlig kolonne
                            count().
                            div(num_days).
                            sort_index().
                            to_frame().
                            rename(columns={'duration':'avg_num_trips'}))
        else:
            df_out = (df_sub.groupby(['end_station_id', 'hour']).
                            duration. # vilkårlig kolonne
                            count().
                            div(num_days).
                            sort_index().
                            to_frame().
                            rename(columns={'duration':'avg_num_arrivals'}))
            
        
        # legge til subset som level 0 i multiindex
        df_out = df_out.reindex(pd.MultiIndex.from_product(df_out.index.levels))
        temp = df_out.index.to_frame()
        temp.insert(0, 'subset', key)
        out_index = pd.MultiIndex.from_frame(temp)
        df_out = df_out.set_index(out_index)
        
        df_out = df_out[df_out.index.get_level_values(-1) >= start_hour]
        df_out.columns = ['avg_trips']
        dfs.append(df_out)
    return pd.concat(dfs)