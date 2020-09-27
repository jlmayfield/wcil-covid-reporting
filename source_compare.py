#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 27 11:32:55 2020

@author: jlmayfield
"""



import pandas as pd
import numpy as np

import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot

from urllib.request import urlopen
import json
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

MB_TOKEN = open(".mapbox_token").read()

import cvdataprep as cvdp
import cvdataanalysis as cvda
import cvdataviz as cvdv



#%%

# 17187,17 <-- Warren County, IL
warren = [17187]



#%% 

population = pd.read_csv('covid_county_population_usafacts.csv',
                         dtype={'countyFIPS':np.int64,
                                'County Name':str, 'State':str,
                                'population':np.int64},
                         index_col = 'countyFIPS')

cases = pd.read_csv('covid_confirmed_usafacts.csv',
                         dtype={'countyFIPS':np.int64,'stateFIPS':np.int64,
                                'County Name':str, 'State':str},                         
                         index_col = 'countyFIPS')

reports_wchd = pd.read_csv('WCHD_Reports.csv',
                         header=[0],index_col=0,
                         parse_dates=True).fillna(0)

data_idph = pd.read_csv('ILDPH_Reports.csv',
                        header=[0],index_col=0,
                        parse_dates=True).fillna(0)


#%%
start_date = pd.to_datetime('2020-09-16')
end_date = pd.to_datetime('2020-09-23') + pd.Timedelta(1,unit='D')

full_tests_wchd = cvda.expandWCHDData(cvdp.prepwchd(reports_wchd))
tests_wchd = full_tests_wchd.loc[:,17,17187].loc[start_date:end_date]
tests_wchd = tests_wchd[['New Positive','New Tests']]


full_tests_usafacts = cvdp.prepusafacts(cases).loc[:,:,[17187]]
tests_usaf = cvda.expandUSFData(full_tests_usafacts, population).loc[:,17,17187].loc[start_date:end_date]
tests_usaf = tests_usaf[['New Positive']]

tests_idph = data_idph[['New Positive','New Tests']].loc[start_date:end_date].astype(int)

#%%

days = tests_wchd.index
fig = go.Figure(data=[
    go.Bar(name='WCHD', x=days, y=tests_wchd['New Positive']),
    go.Bar(name='USAFacts', x=days, y=tests_usaf['New Positive']),
    go.Bar(name='IDPH', x=days, y=tests_idph['New Positive'])
])
# Change the bar mode
fig.update_layout(barmode='group')
plot(fig,filename='graphics/temp.html')

days = tests_wchd.index
fig = go.Figure(data=[
    go.Bar(name='WCHD', x=days, y=tests_wchd['New Tests']),    
    go.Bar(name='IDPH', x=days, y=tests_idph['New Tests'])
])
# Change the bar mode
fig.update_layout(barmode='group')
plot(fig,filename='graphics/temp.html')

