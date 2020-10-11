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
p = 16981



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
start_date = pd.to_datetime('2020-09-13')
end_date = pd.to_datetime('2020-10-10') #+ pd.Timedelta(1,unit='D')

full_tests_wchd = cvda.expandWCHDData(cvdp.prepwchd(reports_wchd))
tests_wchd = full_tests_wchd.loc[:,17,17187].loc[start_date:end_date]
tests_wchd = tests_wchd[['New Positive','New Tests']]


full_tests_usafacts = cvdp.prepusafacts(cases).loc[:,:,[17187]]
tests_usaf = cvda.expandUSFData(full_tests_usafacts, population).loc[:,17,17187].loc[start_date:end_date]
tests_usaf = tests_usaf[['New Positive']]

tests_idph = data_idph[['New Positive','New Tests']].loc[start_date:end_date].astype(int)


#%%

tests_idph['New Negative'] = tests_idph['New Tests'] - tests_idph['New Positive']
tests_wchd['New Negative'] = tests_wchd['New Tests'] - tests_wchd['New Positive']
tests_idph['Positvity'] = tests_idph['New Positive']/tests_idph['New Tests']
tests_wchd['Positvity'] = tests_wchd['New Positive']/tests_wchd['New Tests']

tests_idph['source'] = 'IDPH'   
tests_usaf['source'] = 'USAFacts'
tests_wchd['source'] = 'WCHD'

idph = tests_idph.reset_index().set_index(['date','source'])
usaf = tests_usaf.reset_index().set_index(['date','source'])
wchd = tests_wchd.reset_index().set_index(['date','source'])
all_sources = pd.concat([wchd,idph,usaf])

#%%

wcVil = all_sources.loc[(slice(None),['WCHD','IDPH']),:]
tots = wcVil.iloc[:,0:3].groupby(level=1).sum()
tots['Positivity'] = tots['New Positive']/tots['New Tests']

weeks = wcVil.iloc[:,:3].groupby([pd.Grouper(level=1),
                       pd.Grouper(level=0,freq='W-SUN',
                                  closed='left',label='left')]).sum()

weeks['per 100k'] = weeks['New Positive'] * 100000 / p
weeks['Positivity'] = weeks['New Positive'] / weeks['New Tests']




#%%

days = [ str(d.date()) for d in tests_wchd.index]
fig = go.Figure(data=[
    go.Bar(name='Positive',
           x=[days,['WCHD']*len(days)],
           y=tests_wchd['New Positive'],
           marker_color='red'),
    go.Bar(name='Negative',
           x=[days,['WCHD']*len(days)],
           y=tests_wchd['New Negative'],
           marker_color='blue'),
    go.Bar(name='Positive',
           x=[days,['IDPH']*len(days)],
           y=tests_idph['New Positive'],
           marker_color='red',
           showlegend=False),
    go.Bar(name='Negative',
           x=[days,['IDPH']*len(days)],
           y=tests_idph['New Negative'],
           marker_color='blue',
           showlegend=False),
    go.Bar(name='Positive',
           x=[days,['USAFacts']*len(days)],
           y=tests_usaf['New Positive'],
           marker_color='red',
           showlegend=False)    
    ])

fig.update_layout(barmode='stack',
                  title='Test Result Source Data Comparison')


plot(fig,filename='graphics/source-comparison.html')






