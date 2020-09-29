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


def stylecp100k_cell(cp100k):
    def val2color(val):
        if round(val) <= 50:
            return RISK_COLORS['Minimal']
        elif round(val) <= 100:
            return RISK_COLORS['Moderate']
        else:
            return RISK_COLORS['Substantial']
    return [val2color(v) for v in cp100k]

def stylecp100k_text(cp100k):
    def val2txt(val):
        if round(val) <= 50:
            return "{:.1f}".format(val)
        else:
            return "<b>{:.1f}<b>".format(val)
    return [val2txt(v) for v in cp100k]

def styleprate_cell(prates):
    def val2color(val):
        if val <= .05:
            return RISK_COLORS['Minimal']
        elif val <= .08:
            return RISK_COLORS['Moderate']
        else:
            return RISK_COLORS['Substantial']
    return [val2color(v) for v in prates]

def styleprate_text(prates):
    def val2txt(val):
        if val <= .05:
            return "{:.1%}".format(val)
        else:
            return "<b>{:.1%}<b>".format(val)
    return [val2txt(v) for v in prates]

def stylecase_text(cases_streak):
    def val2txt(i):
        streak = cases_streak.loc[i][1]
        val = round(cases_streak.loc[i][0])
        chg = cases_streak.loc[i][2]
        if np.isinf(chg):
            return"{:<6} (+)".format(val)
        if np.isnan(chg):
            return"{:<6} (None)".format(val)
        elif streak < 2:
            return "{:<6} ({:+.1%})".format(val,chg)
        else:
            return "<b>{:<6} ({:+.1%})</b>".format(val,chg)
    return [val2txt(i) for i in cases_streak.index]

def stylecase_cell(cases_streak):
    def val2color(val):
        if val < 2:
            return RISK_COLORS['Minimal']
        else:
            return "rgba(255, 140, 0, 0.5)"
    return [val2color(v) for v in cases_streak]



#%%

def increased(col):
    return (col.diff() > 0).astype(int)

def increase_streak(col):
    did_increase = increased(col)
    tot_increase = did_increase.cumsum()
    offsets = tot_increase.mask(did_increase != 0).ffill()
    streaks = (tot_increase - offsets).astype(int)
    return streaks.rename(col.name + " Increase Streak")


def daily(wchd_data,wchd_demo):
    keepers = ['New Positive','New Tests','New Deaths',
               '% New Positive','7 Day Avg % New Positive']
    wcil = wchd_data.loc[:,17,17187][keepers]
    wcil['Youth Cases'] = (wchd_demo.T.loc[(slice(None),['0-10','10-20']),:].T).sum(axis=1).astype(int)
    wcil['Cases per 100k'] = wcil['New Positive'] * 100000 / p
    wcil['Case Increases in 10 days'] = increased(wcil['New Positive']).rolling(10,min_periods=0).sum().astype(int)
    wcil['Youth Increases in 10 days'] = increased(wcil['Youth Cases']).rolling(10,min_periods=0).sum().astype(int)
    wcil['Positivity Rate Increases in 10 days'] = increased(wcil['% New Positive']).rolling(10,min_periods=0).sum().astype(int)
    return wcil

def weekly(daily,nweeks=1):
    basis = daily[['New Positive','New Tests','New Deaths','Youth Cases']]
    wcil = basis.groupby(pd.Grouper(level='date',
                                      freq=str(nweeks)+'W-SUN',
                                      closed='left',
                                      label='left')).sum()
    wcil['Cases per 100k'] = wcil['New Positive'] * 100000 / p
    wcil['% New Positive'] = wcil['New Positive']/wcil['New Tests']
    wcil['New Positive Change'] = wcil['New Positive'].pct_change()
    wcil['New Youth Change'] = wcil['Youth Cases'].pct_change()
    wcil['Consecutive Case Increases'] = increase_streak(wcil['New Positive'])
    wcil['Consecutive Youth Increases'] = increase_streak(wcil['Youth Cases'])
    return wcil

def monthly(daily):
    basis = daily[['New Positive','New Tests','New Deaths','Youth Cases']]
    wcil = basis.groupby(pd.Grouper(level='date',freq='MS',
                                      closed='left',label='left')).sum()
    # assume official test dates are a day prior to align with state
    wcil['Cases per 100k'] = wcil['New Positive'] * 100000 / p
    wcil['% New Positive'] = wcil['New Positive']/wcil['New Tests']
    return wcil


#%%

all_the_days = daily(tests_wchd, demo_wchd)
# 1 day lag between state attribution and public release
#all_the_days.index = all_the_days.index - pd.Timedelta(1,unit='D')


ndays = 10 # fixed at 10 for now

# get window dates
today = pd.to_datetime('today')
tenago = today - pd.Timedelta(ndays,unit='D')

# 10 days 
dailywindow = all_the_days.loc[tenago:]
# this week + 4
fiveweeks = weekly(all_the_days,nweeks=1).iloc[-5:]
# this week + 2
threemonths = monthly(all_the_days).iloc[-3:]


# %%

# site table margins
margs = go.layout.Margin(l=0, #left margin
                         r=0, #right margin
                         b=0, #bottom margin
                         t=25  #top margin
                         )                          

#%%

df = dailywindow.reset_index().sort_values('date',ascending=False)
daily = go.Table(header={'values':['<b>Date</b>',
                                            '<b>New Tests</b>',
                                            '<b>New Cases</b>',
                                            '<b>New Cases per 100k</b>',
                                            '<b>Positivity Rate</b>',
                                            '<b>Youth Cases</b>'
                                            ],
                                  'align':'left',
                                  'fill_color':'gainsboro'},
                           cells={'values':[df['date'].apply(lambda d: d.strftime("%A, %B %d")),
                                            df['New Tests'],
                                            df['New Positive'],                                                                                        
                                            df['Cases per 100k'].apply(lambda c:'{:.1f}'.format(c)),
                                            styleprate_text(df['% New Positive']),                                            
                                            df['Youth Cases']
                                            ],                                            
                                  'align':'left',
                                  'fill_color':['whitesmoke',
                                                'whitesmoke',
                                                'whitesmoke',
                                                'whitesmoke',
                                                styleprate_cell(df['% New Positive']),                                                
                                                'whitesmoke'
                                                ],
                                  })

fig = go.Figure(data=daily)
fig.update_layout(title="Daily Case Reports",
                  margin = margs,
                  height= (ndays*50 + 100)
                  )
weekdiv = plot(fig, include_plotlyjs=False, output_type='div')


#%%

daily_trends = go.Table(#columnwidth = [10,10,10,10,10,10,10],
                           header={'values':['<b>Date</b>',
                                            '<b>Day-to-Day Increases<br><em>New Cases</em><br>10 day Window</b>',                                            
                                            '<b>Day-to-Day Increases<br><em>Youth Cases</em><br>10 day Window</b>',                                            
                                            '<b>Positivity Rate<br>7 Day Window</b>',
                                            '<b>Day-to-Day Increases<br><em>Positivity Rate</em><br>10 day Window</b>'
                                            ],
                                  'align':'left',
                                  'fill_color':'gainsboro'},
                           cells={'values':[df['date'].apply(lambda d: d.strftime("%A, %B %d")),                                            
                                            df['Case Increases in 10 days'],
                                            df['Youth Increases in 10 days'],
                                            styleprate_text(df['7 Day Avg % New Positive']),
                                             df['Positivity Rate Increases in 10 days']
                                           ],
                                  'align':'left',
                                  'fill_color':['whitesmoke',
                                                'whitesmoke',
                                                'whitesmoke',
                                                styleprate_cell(df['7 Day Avg % New Positive']),
                                                'whitesmoke'
                                                ],
                                  })


fig = go.Figure(data=daily_trends)
fig.update_layout(title="Daily Trends",
                  margin = margs,
                  height= (ndays*50 + 100)
                  )
trenddiv = plot(fig, include_plotlyjs=False, output_type='div')



#%%
df = fiveweeks.reset_index().sort_values('date',ascending=False)
weekly_table = go.Table(#columnwidth = [10,10,10,10,10,10,10],
                          header={'values':['<b>Week Start Date</b>',
                                            '<b>Cases per 100k</b>',
                                            '<b>Positivity Rate</b>',
                                            '<b>New Tests</b>',
                                            '<b>New Cases</b>',
                                            '<b>Youth Cases</b>',
                                            ],
                                  'align':'left',
                                  'fill_color':'gainsboro'},
                          cells={'values':[df['date'].apply(lambda d: d.strftime("%B %d")),
                                           stylecp100k_text(df['Cases per 100k']),
                                           styleprate_text(df['% New Positive']),
                                           df['New Tests'],
                                           stylecase_text(df[['New Positive',
                                                              'Consecutive Case Increases',
                                                              'New Positive Change']]),
                                           stylecase_text(df[['Youth Cases',
                                                              'Consecutive Youth Increases',
                                                              'New Youth Change']])
                                           ],
                                 'align':'left',
                                 'fill_color':
                                     ['whitesmoke',
                                      stylecp100k_cell(df['Cases per 100k']),
                                      styleprate_cell(df['% New Positive']),
                                      'whitesmoke',
                                      stylecase_cell(df['Consecutive Case Increases']),
                                      stylecase_cell(df['Consecutive Youth Increases']),
                                      ]
                                 })

fig = go.Figure(data=weekly_table)
fig.update_layout(title="This Week vs Prior Weeks",
                  margin = margs,
                  height= 275
                  )
weeklydiv = plot(fig, include_plotlyjs=False, output_type='div')
    

#%%

df = threemonths.reset_index().sort_values('date',ascending=False)
cell_vals = [df['date'].apply(lambda d: d.strftime("%B")),
             df['Cases per 100k'].apply(lambda c:'{:.1f}'.format(c)),
             styleprate_text(df['% New Positive']),
             df['New Tests'],
             df['New Positive'],
             df['Youth Cases'],
             df['New Deaths']]
monthly_table = go.Table(#columnwidth = [10,10,10,10,10,10,10],
                          header={'values':['<b>Month</b>',
                                            '<b>Cases per 100k</b>',
                                            '<b>Positivity Rate</b>',
                                            '<b>New Tests</b>',
                                            '<b>New Cases</b>',
                                            '<b>Youth Cases</b>',
                                            '<b>New Deaths</b>'],
                                  'align':'left',
                                  'fill_color':'gainsboro'},
                          cells={'values':cell_vals,
                                 'align':'left',
                                 'fill_color':['whitesmoke',
                                               'whitesmoke',
                                               styleprate_cell(df['% New Positive']),
                                               'whitesmoke',
                                               'whitesmoke',
                                               'whitesmoke',
                                               'whitesmoke']}
                          )

fig = go.Figure(data=monthly_table)
fig.update_layout(title="This Month vs. Prior Months",
                  margin = margs,
                  height= 225
                  )
monthlydiv = plot(fig, include_plotlyjs=False, output_type='div')

#%%


fig = make_subplots(rows=4, cols=1,                    
                    vertical_spacing=0.02,                    
                    specs=[[{"type": "table"}],
                           [{"type": "table"}],
                           [{"type": "table"}],
                           [{"type": "table"}],
                          ],
                    subplot_titles=('Daily Reports (10 Day Window)',
                                    'Day-to-Day Trends (10 Day Window)',
                                    'This Week vs Prior Weeks',                                    
                                    'This Month vs. Prior Months'))

fig.add_trace(daily,row=1,col=1)
fig.add_trace(daily_trends,row=2,col=1)
fig.add_trace(weekly_table,row=3,col=1)
fig.add_trace(monthly_table,row=4,col=1)

fig.update_layout(title_text="Warren County Daily Dashboard",      
                  height=1400,
                  width=850,
                  margin = go.layout.Margin(l=20, #left margin
                                            r=20, #right margin
                                            b=10, #bottom margin
                                            t=50  #top margin
                                          )
                  )

plot(fig,filename='graphics/WC-Daily.html')

#%%

mdpage = ""
header = """---
layout: page
title: Warren County Daily Report
permalink: /wcil-daily-report/
---
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
"""
timestamp = pd.to_datetime('today').strftime('%H:%M %Y-%m-%d')
header = header + '<p><small>last updated:  ' + timestamp + '</small><p>\n\n'

mdpage = header + weekdiv + trenddiv + weeklydiv + monthlydiv

with open('docs/wcilDaily.md','w') as f:
    f.write(mdpage)
    f.close()
