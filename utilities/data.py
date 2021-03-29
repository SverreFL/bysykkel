import pandas as pd
from pathlib import Path
import os
'''
Målet er å få ut to dataframe:
1. stations
- har id, navn, lat, long
- kun informasjon om stasjonene, helt uavhengig av antall reiser
2. trips
- df med multiindex der hver origin viser antall reiser og gj.snitt. tid til alle destination.
- vil at den skal ha kolonne med geometri (LinePlot) for kobling mellom origin og destination.
- tror jeg vil lagen egen for subset av reiser i helg og hverdag. 
'''


def load_data(start, end):
    '''
    todo: add docstring
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
    todo: add docstring
    '''
    cols = ['start_station_name', 'start_station_latitude', 'start_station_longitude']
    df_out = df.groupby('start_station_id')[cols].first()
    df_out.columns = ['name', 'latitude', 'longitude']
    df_out = df_out.sort_index()
    return df_out

def make_trips(df):
    '''
    todo: add docstring. og clean opp koden. returnere dict med data frame
    '''
    
    keys = ['all', 'weekdays', 'weekends']
    out_dict = dict().fromkeys(keys)
    for key in keys:
        if key == 'weekdays':
            df_sub = df[df.weekend==False]
        elif key == 'weekends':
            df_sub = df[df.weekend==True]
        else:
            df_sub = df            
        gb = df_sub.groupby('start_station_id')[['end_station_id', 'duration']]
        station_ids = gb.groups.keys()
        index = pd.MultiIndex.from_product([station_ids, station_ids],
                                           names=['station_station_id', 'end_station_id'])

        df_out = pd.DataFrame(index=index, columns=['count', 'avg_duration'])

        for idx, group in gb:
            df_out.loc[idx] = (group.groupby('end_station_id').
                                     duration.
                                     agg(['count','mean']).
                                     reindex(index=station_ids). # padde nans for uobserverte
                                     sort_index().
                                     values) 
        df_out.columns = ['count', 'avg_duration']
        df_out['count'] = df_out['count'].fillna(0).astype(int)

        components = pd.to_timedelta(df_out['avg_duration'], 'seconds').dt.components
        df_out['hours'] = components.hours
        df_out['minutes'] = components.minutes
        df_out['seconds'] = components.seconds
        out_dict[key] = df_out

    return out_dict

def make_arrivals(trips):
    '''
    swap index og sorter
    '''
    keys = ['all', 'weekdays', 'weekends']
    out_dict = dict().fromkeys(keys)
    
    for key in keys:
        arrivals = trips[key].copy()
        arrivals.index = arrivals.index.swaplevel()
        arrivals = arrivals.sort_index()
        out_dict[key] = arrivals
    return out_dict

def make_num_per_hour(df, trips=True, start_hour=5):
    '''
    Gjennomsnittlig antall turer for hver time på dagen for hver stasjon. Trips hvis turer fra, ellers arrivals.
    '''
    df['day_of_year'] = df.started_at.dt.day_of_year
    keys = ['all', 'weekdays', 'weekends']
    out_dict = dict().fromkeys(keys)
    
    for key in keys:
        if key == 'weekdays':
            df_sub = df[df.weekend==False]
        elif key == 'weekends':
            df_sub = df[df.weekend==True]
        else:
            df_sub = df
        
        if trips:
            df_sub = df_sub.set_index('started_at')
            gb = df_sub.groupby('start_station_id')
        else:
            df_sub = df_sub.set_index('ended_at')
            gb = df_sub.groupby('end_station_id')

        station_ids = gb.groups.keys()

        num_days = len(df_sub['day_of_year'].unique())

        index = pd.MultiIndex.from_product([station_ids, range(0,23+1)])
        series_out = pd.Series(index=index, dtype='object')

        for idx, group in gb:
            series_out.loc[idx] = (group.groupby(group.index.hour).
                            duration. # vilkårlig kolonne
                            count().
                            div(num_days).
                            reindex(range(0,23+1)).
                            sort_index().
                            values)
        series_out = series_out[series_out.index.get_level_values(1) >= start_hour]
        series_out = series_out.fillna(0)
        out_dict[key] = series_out
    return out_dict