#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  2 15:07:17 2020

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

population = pd.read_csv('covid_county_population_usafacts.csv',
                         dtype={'countyFIPS':np.int64,
                                'County Name':str, 'State':str,
                                'population':np.int64},
                         index_col = 'countyFIPS')

cases = pd.read_csv('covid_confirmed_usafacts.csv',
                         dtype={'countyFIPS':np.int64,'stateFIPS':np.int64,
                                'County Name':str, 'State':str,
                                'date': np.datetime64},
                         index_col = 'countyFIPS')

usaf = cvdp.prepusafacts(cases)
il = usaf.loc[(slice(None),17,slice(None)),:]
il = cvda.expandUSFData(il, population)
il_pop = population[population['State'] == 'IL']
#%%

# combine add recovery regions to IL counties list
regions = il.loc[pd.to_datetime('2020-09-11'),17,:].reset_index()[['countyFIPS','Recovery Region']].set_index('countyFIPS')
regions = pd.concat([il_pop,regions],axis=1)
# get regional populations
reg_pop = regions[['Recovery Region','population']].groupby('Recovery Region').sum()

#%% 


per100k = (il.reset_index())[['date','Recovery Region','New Positive','New Positive per 100k']]
#regiontots = per100k.groupby([pd.Grouper(key='date',freq='W-SAT'),'Recovery Region']).sum()
regiontots = per100k.groupby(['date','Recovery Region']).sum()
lastday = regiontots.index.get_level_values('date').unique()[-1]



