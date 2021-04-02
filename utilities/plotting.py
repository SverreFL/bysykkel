import matplotlib.pyplot as plt
import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np 
import pandas as pd
import warnings
warnings.simplefilter("ignore")

from pathlib import Path
path = Path('resources/data')
stations = pd.read_pickle(path / 'stations')

def some_plot_function(current_station_id, current_subset, num_arrivals_per_hour,
                        num_trips_per_hour, start_hour=5):
    
   fig, ax = plt.subplots(figsize=(12,6))
   if not current_station_id:
      negative_data = num_trips_per_hour.loc[current_subset].groupby('hour').avg_trips.sum().values
      positive_data = num_arrivals_per_hour.loc[current_subset].groupby('hour').avg_trips.sum().values
   else:
      negative_data = num_trips_per_hour.loc[(current_subset, current_station_id)].values.ravel()
      positive_data = num_arrivals_per_hour.loc[(current_subset, current_station_id)].values.ravel()
   max_value = get_max_value(current_station_id, num_arrivals_per_hour, num_trips_per_hour)

   ax.bar(range(start_hour,23+1), positive_data, width=0.8,
         color='tab:blue', label='turer til', align='edge')
   ax.bar(range(start_hour,23+1), -negative_data, width=0.8,
         color='tab:red', label='turer fra', align='edge')
   if current_station_id:
      ax.plot(range(start_hour,23+1), positive_data-negative_data, '-o', color='black')
    
   ax = handle_xticks(ax, start_hour)
   ax = handle_yticks(ax, current_station_id, max_value)
   ax = handle_title(ax, current_station_id)
   
   ax.legend()
   plt.close()
   return fig

def get_max_value(current_station_id, num_arrivals_per_hour, num_trips_per_hour):
   if not current_station_id:
      max_trips = num_trips_per_hour.groupby(['subset','hour']).avg_trips.sum().max()
      max_arrivals = num_arrivals_per_hour.groupby(['subset','hour']).avg_trips.sum().max()
   else:
      max_trips = num_arrivals_per_hour.loc[:,current_station_id,:].max().max()
      max_arrivals = num_arrivals_per_hour.loc[:,current_station_id,:].max().max()
   return max(max_trips, max_arrivals)

def handle_xticks(ax, start_hour):
   ax.set_xlim(start_hour-.25, 24)
   ax.set_xticks(range(start_hour,23+1))
   x_vals = ax.xaxis.get_ticklocs()
   ax.set_xticklabels([str(x)+':00' for x in x_vals])
   return ax

def handle_yticks(ax, current_station_id, max_value):
   buffer = 0.2*max_value
   if current_station_id:
      ax.set_ylim(-max_value-buffer, max_value+buffer)
   else:
      ax.set_ylim(-max_value-buffer, max_value+buffer) 

   yvals = ax.get_yticks()
   if np.array([str(y).endswith('0') for y in yvals]).all():
      ax.set_yticklabels([abs(int(y)) for y in yvals])
   else:
      ax.set_yticklabels([f'{abs(y):.2f}' for y in yvals])
   return ax

def handle_title(ax, current_station_id):
   if current_station_id:
      ax.set_title(f'{stations.loc[(current_station_id, "name")]}', fontsize=14)
   else:
      ax.set_title('Gjennomsnittlig antall turer per time', fontsize=14)
   return ax