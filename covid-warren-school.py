#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 17 10:24:53 2020

@author: jlmayfield
"""



import pandas as pd
import numpy as np

from plotly.subplots import make_subplots
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


# !Unknown values filled in with zeros (early reports were incomplete)
reports_wchd = pd.read_csv('WCHD_Reports.csv',
                         header=[0],index_col=0,
                         parse_dates=True).fillna(0)

demo_wchd = pd.read_csv('WCHD_Case_Demographics.csv',
                       skiprows=[2],
                       header=[0,1],index_col=0,
                       parse_dates=True).fillna(0).iloc[:,0:12]

tests_wchd = cvda.expandWCHDData(cvdp.prepwchd(reports_wchd))
# from IL DPH site based on cases vs casesper100k data
p = 16981


#%%

# needs actual and per 100k counts
def ildph_per100k(counts):
    def assign_risk(d):
        if counts.loc[d]['New Positive'] < 10 or \
            counts.loc[d]['Cases per 100k'] <= 50: 
            return 'Minimal'
        elif counts.loc[d]['Cases per 100k'] < 100: 
            return 'Moderate'
        else:
            return 'Substantial'
    risk = counts.index.map(assign_risk).to_series()
    risk.index = counts.index
    return risk.rename('Cases per 100k Risk')

def ildph_posrate(rates):
    def assign_risk(d):
        rate = rates.loc[d]['Positive Test Rate']
        if rate <= 0.05:
            return 'Minimal'
        elif rate <= 0.08:
            return 'Moderate'
        else:
            return 'Substantial'
    risk = rates.index.map(assign_risk).to_series()
    risk.index = rates.index
    return risk.rename('Positive Test Rate Risk')


# works for both cases and youth cases
# These categories are ... awkward .
#  
def ildph_cases(actuals):    
    def assign_risk(d):
        if d == actuals.index[0]:
            return ''
        weeks = np.array(actuals.loc[d],
                         actuals.loc[d-pd.Timedelta(1,unit='W')])
        if np.isnan(weeks).any() or np.isinf(weeks).any():
            return '???? (Non-numerical values)'            
        elif (weeks < 0).any():
            return 'Minimal (Some Decrease)'
        elif (weeks < .05).all():
            return 'Minimal (Under 5%)'
        elif (weeks >= .05).all() and (weeks <= .10).all():
            return 'Minimal'
        elif (weeks > .10).all() and (weeks <= .20).all():
            return 'Moderate'
        elif (weeks > .20).all():
            return 'Substantial'
        else:
            return '???? (mixed risk levels)'
    risk = actuals.index.map(assign_risk).to_series()
    risk.index = actuals.index
    return risk.rename(actuals.columns[0] + ' Risk')
        
        
    

RISK_COLORS = {'Minimal':'Green','Moderate':'Yellow','Substantial':'Red'}
#%%

# weekly cases per 100k
# weekly cases actual
# weekly % change in # of cases week to week 
# weekly youth (age < 20) cases actual
# weekly % change in youth cases
# pos rate weekly

school_metrics = tests_wchd.loc[:,17,17187][['New Positive','New Tests']]
school_metrics['Youth Cases'] = (demo_wchd.T.loc[(slice(None),['0-10','10-20']),:].T).sum(axis=1)
school_metrics = school_metrics.groupby(pd.Grouper(level='date',freq='W-SUN')).sum()
# ILDPH data for date d/m/y get reported on (d+1)/m/y (one day later) 
# shift dates to align with state reporting
school_metrics.index = school_metrics.index.map(lambda d : d - pd.Timedelta(1,unit='D'))

school_metrics['Positive Test Rate'] = school_metrics['New Positive']/school_metrics['New Tests']
school_metrics['Cases per 100k'] = school_metrics['New Positive']/p*100000
school_metrics['New Positive Change'] = school_metrics['New Positive'].pct_change()
school_metrics['New Youth Change'] = school_metrics['Youth Cases'].pct_change()
school_metrics = pd.concat([school_metrics,
                            ildph_per100k(school_metrics[['New Positive','Cases per 100k']]),
                            ildph_posrate(school_metrics[['Positive Test Rate']]),
                            ildph_cases(school_metrics[['New Positive Change']]),
                            ildph_cases(school_metrics[['New Youth Change']])],
                            axis=1)

#%%

fig = make_subplots(specs=[[{"secondary_y": True}]])

# Add traces
fig.add_trace(
    go.Scatter(x=school_metrics.index,
               y=school_metrics['Cases per 100k'],
               name="Cases per 100k"),
    secondary_y=False,
)

fig.add_trace(
    go.Scatter(x=school_metrics.index,
               y=school_metrics['Positive Test Rate'],
               name="Positive Test Rate"),
    secondary_y=True,
)

# Set x-axis title
fig.update_xaxes(title_text="Week Ending Date")

# Set y-axes titles
fig.update_yaxes(title_text="<b>primary</b> yaxis title", secondary_y=False)
fig.update_yaxes(title_text="<b>secondary</b> yaxis title", secondary_y=True)

plot(fig)

#%%

df = school_metrics[['New Positive','Cases per 100k','Cases per 100k Risk']].iloc[-13:-1].reset_index()
fig = go.Figure(data=go.Table(
         header={'values':['Week Ending Date',
                           'Actual Cases',
                           'Cases per 100k',
                           'State Risk Assessment'],                      
                 'align':'left'},
             cells={'values':[df['date'].apply(lambda d: str(d.date())),
                              df['New Positive'],
                              df['Cases per 100k'].apply(lambda c : '{:.2f}'.format(c)),
                              df['Cases per 100k Risk']],
                    'align':'left'}))

cp100kWC_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/cp100kWC-DIV.html','w') as f:
    f.write(cp100kWC_div)
    f.close()
plot(fig)   
#%%



#%%
df = school_metrics[['New Positive','New Tests','Positive Test Rate','Positive Test Rate Risk']].iloc[-13:-1].reset_index()
fig = go.Figure(data=go.Table(
         header={'values':['Week Ending Date',
                           'Positive Tests',
                           'Total Tests Administered',
                           'Positivity Rate',
                           'State Risk Assessment'],                      
                 'align':'left'},
             cells={'values':[df['date'].apply(lambda d: str(d.date())),
                              df['New Positive'],
                              df['New Tests'],
                              df['Positive Test Rate'].apply(lambda c : '{:.2%}'.format(c)),
                              df['Positive Test Rate Risk']],
                    'align':'left'}))

posRateWC_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/posRateWC-DIV.html','w') as f:
    f.write(posRateWC_div)
    f.close()
plot(fig)   

#%%

df = school_metrics[['Youth Cases','New Youth Change','New Youth Change Risk']].iloc[-13:-1].reset_index()
fig = go.Figure(data=go.Table(
         header={'values':['Week Ending Date',
                           'New Youth (age < 20) Cases ',
                           'Change from Last Week',
                           'State Risk Assessment'],
                 'align':'left'},
             cells={'values':[df['date'].apply(lambda d: str(d.date())),
                              df['Youth Cases'],
                              df['New Youth Change'].apply(lambda p: '{:.2%}'.format(p)),
                              df['New Youth Change Risk']],                              
                    'align':'left'}))

youthChangeWC_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/youthChangeWC-DIV.html','w') as f:
    f.write(youthChangeWC_div)
    f.close()
plot(fig)   

    #%%
df = school_metrics[['New Positive','New Positive Change','New Positive Change Risk']].iloc[-13:-1].reset_index()
fig = go.Figure(data=go.Table(
         header={'values':['Week Ending Date',
                           'New Cases',
                           'Change from Last Week',
                           'State Risk Assessment'],
                 'align':'left'},
             cells={'values':[df['date'].apply(lambda d: str(d.date())),
                              df['New Positive'],
                              df['New Positive Change'].apply(lambda p: '{:.2%}'.format(p)),
                              df['New Positive Change Risk']],                              
                    'align':'left'}))

posChangeWC_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/posChangeWC-DIV.html','w') as f:
    f.write(posChangeWC_div)
    f.close()
plot(fig)   




