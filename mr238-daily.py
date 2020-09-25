#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 17 10:24:53 2020

@author: jlmayfield
"""



import pandas as pd
import numpy as np

from plotly.subplots import make_subplots
import plotly.graph_objects as go
from plotly.offline import plot

from urllib.request import urlopen
import json
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

MB_TOKEN = open(".mapbox_token").read()

import cvdataprep as cvdp
import cvdataanalysis as cvda

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
# '#3498DB'
RISK_COLORS = {'Minimal':'whitesmoke','Moderate':'rgba(255,215,0,0.5)','Substantial':'rgba(205,92,92,0.5)'}


# 50 cases/100k (9 actual) is the warning cutoff
def stylecp100k_cell(cp100k):    
    def val2color(c):        
        if round(c) < 50:
            return RISK_COLORS['Minimal']        
        else:
            return RISK_COLORS['Substantial']
    return [val2color(v) for v in cp100k]

# bold the number to stand out in the color
def stylecp100k_text(cp100k):
    def val2txt(i):
        p100k = cp100k.loc[i][0]
        actual = cp100k.loc[i][1]        
        txt = "{:<8.1f} ({:d})".format(p100k,int(actual))
        if round(p100k) < 50:
            return txt
        else:
            return '<b>' + txt + '</b>'
    return [val2txt(v) for v in cp100k.index]

# 5% or greater is the cutoff
def styleprate_cell(prates):
    def val2color(val):
        if val < .05:
            return RISK_COLORS['Minimal']        
        else:
            return RISK_COLORS['Substantial']
    return [val2color(v) for v in prates]

def styleprate_text(prates):
    def val2txt(val):
        if val < .05:
            return "{:.1%}".format(val)
        else:
            return "<b>{:.1%}</b>".format(val)
    return [val2txt(v) for v in prates]

# 3 or more youth cases is the cutoff
def styleyouth_cell(youths):
    def val2color(i):
        val = int(youths.loc[i][0])
        streak = int(youths.loc[i][1])
        if val < 3 and streak < 1:
            return RISK_COLORS['Minimal']
        elif val < 3 and streak < 2:
            return RISK_COLORS['Moderate']
        else: #val >= 3 or streak >= 2
            return RISK_COLORS['Substantial']
    return [val2color(i) for i in youths.index]

# 3 or more youth cases is the cutoff
def styleyouth_text(youths):
    def val2color(i):
        val = youths.loc[i]['Youth Cases']
        streak = youths.loc[i]['Consecutive Youth Increases']
        txt = "{:<8}".format(val)        
        if streak > 0:
            txt += "({})".format(streak)
        if val > 3:
            txt = '<b>' + txt + "</b>"
        return txt
    return [val2color(v) for v in youths.index]        
    
   
def stylestreak_text(streak):
    def val2txt(s):            
        txt= "{}".format(s)
        if s < 2:
            return txt
        else:
            return "<b>" + txt +"</b>"
    return [val2txt(s) for s in streak]

def stylestreak_cell(cases):
    def val2color(streak):        
        if streak < 1:
            return RISK_COLORS['Minimal']
        elif streak < 2:
            return RISK_COLORS['Moderate']
        else:
            return RISK_COLORS['Substantial']
    return [val2color(i) for i in cases]



#%%

def increased(col):
    return (col.diff() > 0).astype(int)

def increase_streak(col):
    did_increase = increased(col)
    tot_increase = did_increase.cumsum()
    offsets = tot_increase.mask(did_increase != 0).ffill()
    streaks = (tot_increase - offsets).astype(int)
    return streaks.rename(col.name + " Increase Streak")


def schooldaily(wchd_data,wchd_demo):
    keepers = ['New Positive','New Tests','New Deaths','% New Positive']
    school = wchd_data.loc[:,17,17187][keepers]
    school['Youth Cases'] = (wchd_demo.T.loc[(slice(None),['0-10','10-20']),:].T).sum(axis=1).astype(int)
    school['Cases per 100k'] = school['New Positive'] * 100000 / p
    school['Case Increases in 10 days'] = increased(school['New Positive']).rolling(10,min_periods=0).sum().astype(int)
    school['Youth Increases in 10 days'] = increased(school['Youth Cases']).rolling(10,min_periods=0).sum().astype(int)
    school['Positivity Rate Increases in 10 days'] = increased(school['% New Positive']).rolling(10,min_periods=0).sum().astype(int)
    return school

def schoolweekly(daily,nweeks=1):
    basis = daily[['New Positive','New Tests','New Deaths','Youth Cases']]
    school = basis.groupby(pd.Grouper(level='date',
                                      freq=str(nweeks)+'W-SUN',
                                      closed='left',
                                      label='left')).sum()
    school['Cases per 100k'] = school['New Positive'] * 100000 / p
    school['% New Positive'] = school['New Positive']/school['New Tests']
    school['New Positive Change'] = school['New Positive'].pct_change()
    school['New Youth Change'] = school['Youth Cases'].pct_change()
    school['Consecutive Case Increases'] = increase_streak(school['New Positive'])
    school['Consecutive Youth Increases'] = increase_streak(school['Youth Cases'])
    return school

def schoolmonthly(daily):
    basis = daily[['New Positive','New Tests','New Deaths','Youth Cases']]
    school = basis.groupby(pd.Grouper(level='date',freq='MS',
                                      closed='left',label='left')).sum()
    # assume official test dates are a day prior to align with state
    school['Cases per 100k'] = school['New Positive'] * 100000 / p
    school['% New Positive'] = school['New Positive']/school['New Tests']
    return school


#%%


all_the_days = schooldaily(tests_wchd, demo_wchd)
# adjust for 1 day lag between state attribution and public release
all_the_days.index = all_the_days.index - pd.Timedelta(1,unit='D')

# get week start date
this_sunday = pd.to_datetime(pd.to_datetime('today') - pd.offsets.Week(weekday=6)).date()


# weekly numbers for this week and two prior
threeweeks = schoolweekly(all_the_days,nweeks=1).iloc[-3:]
# daily numbers for the current week
this_week = all_the_days.loc[this_sunday:]



#%%

df = this_week.reset_index().sort_values('date',ascending=False)
thisweek = go.Table(header={'values':['<b>Date</b>',
                                      '<b>Positivity Rate</b>',
                                      '<b>New Cases<br>per 100k (actual)</b>',
                                      '<b>New Youth Cases<b>'],
                                  'align':'left',
                                  'fill_color':'gainsboro'},
                             cells={'values':[df['date'].apply(lambda d: d.strftime("%A, %B %d")),
                                              styleprate_text(df['% New Positive']),
                                              stylecp100k_text( df[['Cases per 100k','New Positive']]),
                                              df['Youth Cases']],
                                    'align':'left',
                                    'fill_color':['whitesmoke',
                                                  styleprate_cell(df['% New Positive']),
                                                  'whitesmoke',
                                                  'whitesmoke'],
                                    'height': 30 }
                           )

#%%

df = threeweeks.reset_index().sort_values('date',ascending=False)
vals = [df['date'].apply(lambda d: d.strftime("%B %d")),
        styleprate_text(df['% New Positive']),
        stylecp100k_text(df[['Cases per 100k','New Positive']]),
        stylestreak_text(df['Consecutive Case Increases']),
        styleyouth_text(df[['Youth Cases','Consecutive Youth Increases']])]        
# style current week to flag provisional data
vals[0].iloc[0] = '<i>' + vals[0].iloc[0] + '<i>' + '<sup><b>**</b></sup>'
# cell colors
clrs = ['whitesmoke',
        styleprate_cell(df['% New Positive']),
        stylecp100k_cell(df['Cases per 100k']),
        stylestreak_cell(df['Consecutive Case Increases']),        
        styleyouth_cell(df[['Youth Cases','Consecutive Youth Increases']])]
weekly_table = go.Table(header={'values':['<b>Week Start Date</b>',
                                          '<b>Positivity Rate</b>',
                                          '<b>New Cases<br>per 100k (actual)</b>',                                                                                     
                                          '<b>Consecutive Weeks of<br>New Case Increases</b>',
                                          '<b>Youth Cases<br>Current (Increases)</b>',
                                          ],
                                 'align':'left',
                                 'fill_color':'gainsboro'},
                        cells={'values': vals,
                                 'align': 'left',
                                 'fill_color': clrs,
                                 'height':30})

#%%

fig = make_subplots(rows=2, cols=1,
                    vertical_spacing=0.1,
                    #horizontal_spacing=0.05,
                    specs=[[{"type": "table"}],[{"type": "table"}]],
                    subplot_titles=('Weekly Metrics',
                                    'This Week'))

fig.add_trace(thisweek,row=2,col=1)
fig.add_trace(weekly_table,row=1,col=1)

fig.update_layout(title_text="MR-238 Daily Dashboard",                  
                  height=600)

plot(fig,filename='graphics/MR238-Daily.html')
div = plot(fig, include_plotlyjs=False, output_type='div')
with open('mr238/MR238-Daily.txt','w') as f:
    f.write(div)
    f.close()
