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
                                'County Name':str, 'State':str},
                         index_col = 'countyFIPS')


# !Unknown values filled in with zeros (early reports were incomplete)
reports_wchd = pd.read_csv('WCHD_Reports.csv',
                         header=[0],index_col=0,
                         parse_dates=True).fillna(0)

demo_wchd = pd.read_csv('WCHD_Case_Demographics.csv',
                       skiprows=[2],
                       header=[0,1],index_col=0,
                       parse_dates=True).fillna(0).iloc[:,0:12]

death_wchd = pd.read_csv('WCHD_Death_Demographics.csv',
                       skiprows=[2],
                       header=[0,1],index_col=0,
                       parse_dates=True).fillna(0).iloc[:,0:12]

#%%

IL_FIPS = list(population[population['State'] == 'IL'].index)[1:]
warren = [17187]
neighbors = [17095, 17071, 17109, 17057, 17131]
il_select = [17113, 17107, 17167, 17195, 17031]
ia_select = [19163, 19139, 19045, 19031, 19115, 19057]

region1 = [17085,17177,17201,17007,17015,17141,17037,17195,17103] 
region2 = [17187, 17095, 17071, 17109, 17057, 17131, 17161, 17073, 17011,
           17175, 17143, 17179, 17155, 17123, 17203, 17099, 17113, 17105,
           17093, 17063]
region3 = [17067,17001,17149,17013,17169,17009,17137,17171,17061,17083,
           17125,17017,17117,17167,17129,17107,17021,17135]
region4 = [17119,17163,17133,17157,17005,17027,17189]
region5 = [17003,17153,17127,17151,17069,17087,17181,17059,17165,
           17199,17077,17145,17055,17065,17193,17185,17047,17191,
           17121,17081]
region6 = [17019, 17023, 17025, 17029, 17033, 17035, 17039, 17041, 17045,
           17049, 17051, 17053, 17075, 17079, 17101, 17139, 17147, 17159,
           17173, 17183,17115]
region7 = [17197,17091]
region8 = [17089,17043]

region9 = [17111,17097]
region10_11 = [17031] #cook (chicago land) was artificially broken up


nhood = warren+neighbors
allthethings = nhood + il_select + ia_select


#%%
tests_wchd = cvda.expandWCHDData(cvdp.prepwchd(reports_wchd))
wchd_only = tests_wchd.loc[:,17,17187]

#%%
pop = population.loc[17187]['population']
# just the deets for week + 1
t = wchd_only.iloc[-9:,2:10]
print(t[['New Tests','New Positive','New Deaths','% New Positive',
        '7 Day Avg % New Positive']])

#   Group into Weeks Ending on Sunday (Mon -> Sunday)
# tests_wchd.groupby(pd.Grouper(level=0,freq='W'))
#   Group into Sun to Sat Weeks
# tests_wchd.groupby(pd.Grouper(level=0,freq='W-SAT'))


agg_data = wchd_only[['New Tests','New Positive','New Deaths']]
weeks = agg_data.groupby(pd.Grouper(level=0,freq='W-SAT',label="right")).sum()
weeks['% New Positive'] = weeks['New Positive']/weeks['New Tests']
weeks['New Positive per 100k'] = weeks['New Positive'] * 100000 / pop 
print("Sunday to Saturday")
print(weeks.iloc[-4:])

agg_data = wchd_only[['New Tests','New Positive','New Deaths']]
weeks = agg_data.groupby(pd.Grouper(level=0,freq='W-FRI',label="right")).sum()
weeks['% New Positive'] = weeks['New Positive']/weeks['New Tests']
weeks['New Positive per 100k'] = weeks['New Positive'] * 100000 / pop 
print("Sat to Friday")
print(weeks.iloc[-4:])

months = agg_data.groupby(pd.Grouper(level=0,freq='MS')).sum()
months['% New Positive'] = months['New Positive']/months['New Tests']
months['New Positive per 100k'] = months['New Positive'] * 100000 / pop 





print(months)


  