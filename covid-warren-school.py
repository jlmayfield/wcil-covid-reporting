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
            return"{:<10} (+)".format(val)
        if np.isnan(chg):
            return"{:<10} (None)".format(val)
        elif streak < 2:
            return "{:<10} ({:+.1%})".format(val,chg)
        else:
            return "<b>{:<10} ({:+.1%})</b>".format(val,chg)
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


def schooldaily(wchd_data,wchd_demo):
    keepers = ['New Positive','New Tests','New Deaths',
               '% New Positive','7 Day Avg % New Positive']
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
# 1 day lag between state attribution and public release
all_the_days.index = all_the_days.index - pd.Timedelta(1,unit='D')

this_sunday = pd.to_datetime(pd.to_datetime('today') - pd.offsets.Week(weekday=6)).date()

this_week = all_the_days.loc[this_sunday:]
fourweeks = schoolweekly(all_the_days,nweeks=1).iloc[-4:]
twomonths = schoolmonthly(all_the_days).iloc[-2:]

#%%

df = this_week.reset_index().sort_values('date',ascending=False)
thisweek_table1 = go.Table(#columnwidth = [10,10,10,10,10,10,10],
                           header={'values':['<b>Date</b>',
                                            '<b>New Cases</b>',
                                            '<b>New Youth Cases<b>',
                                            '<b>New Cases per 100k</b>',
                                            '<b>Positivity Rate</b>'
                                            ],
                                  'align':'left',
                                  'fill_color':'gainsboro'},
                           cells={'values':[df['date'].apply(lambda d: d.strftime("%A, %B %d")),
                                            df['New Positive'],
                                            df['Youth Cases'],
                                            df['Cases per 100k'].apply(lambda c:'{:.2f}'.format(c)),
                                            styleprate_text(df['% New Positive'])
                                           ],
                                  'align':'left',
                                  'fill_color':['whitesmoke',
                                                'whitesmoke',
                                                'whitesmoke',
                                                'whitesmoke',
                                                styleprate_cell(df['% New Positive']),
                                                ],
                                  'height': 30 },
                           name = 'State Metrics This Week')

thisweek_table2 = go.Table(#columnwidth = [10,10,10,10,10,10,10],
                          header={'values':['<b>Date</b>',
                                            '<b>Day-to-Day Increases in<br><em>New Cases</em><br>10 day Window</b>',
                                            '<b>Day-to-Day Increases in<br><em>Youth Cases</em><br>10 day Window</b>',
                                            '<b>Positivity Rate<br>7 Day Window</b>',
                                            '<b>Day-to-Day Increases in<br><em>Positivity Rate</em><br>10 day Window</b>'
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
                                 'fill_color':
                                     ['whitesmoke',
                                      'whitesmoke',
                                      'whitesmoke',
                                      styleprate_cell(df['7 Day Avg % New Positive']),
                                      'whitesmoke'
                                      ],
                                 'height':30},
                              name='Trajectory Metrics This Week')

#%%
df = fourweeks.reset_index().sort_values('date',ascending=False)
weekly_table = go.Table(#columnwidth = [10,10,10,10,10,10,10],
                          header={'values':['<b>Week Start Date</b>',
                                            '<b>Cases per 100k</b>',
                                            '<b>Positivity Rate</b>',
                                            '<b>New Cases</b>',
                                            '<b>Youth Cases</b>',
                                            ],
                                  'align':'left',
                                  'fill_color':'gainsboro'},
                          cells={'values':[df['date'].apply(lambda d: d.strftime("%B %d")),
                                           stylecp100k_text(df['Cases per 100k']),
                                           styleprate_text(df['% New Positive']),
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
                                      stylecase_cell(df['Consecutive Case Increases']),
                                      stylecase_cell(df['Consecutive Youth Increases']),
                                      ],
                                 'height':30})

#%%

df = twomonths.reset_index().sort_values('date',ascending=False)
monthly_table = go.Table(#columnwidth = [10,10,10,10,10,10,10],
                          header={'values':['<b>Month</b>',
                                            '<b>Cases per 100k</b>',
                                            '<b>Positivity Rate</b>',
                                            '<b>New Cases</b>',
                                            '<b>Youth Cases</b>',
                                            '<b>New Deaths</b>'],
                                  'align':'left',
                                  'fill_color':'gainsboro'},
                          cells={'values':[df['date'].apply(lambda d: d.strftime("%B")),
                                           df['Cases per 100k'].apply(lambda c:'{:.2f}'.format(c)),
                                           styleprate_text(df['% New Positive']),
                                           df['New Positive'],
                                           df['Youth Cases'],
                                           df['New Deaths']],
                                 'align':'left',
                                 'fill_color':['whitesmoke',
                                               'whitesmoke',
                                               styleprate_cell(df['% New Positive']),
                                               'whitesmoke',
                                               'whitesmoke',
                                               'whitesmoke'],
                                 'height':30})


#%%

fig = make_subplots(rows=4, cols=1,
                    vertical_spacing=0.1,
                    horizontal_spacing=0.05,
                    specs=[[{"type": "table"}],[{"type": "table"}],
                            [{"type": "table"}],[{"type": "table"}]],
                    subplot_titles=('State Metrics: This Week (Daily)',
                                    'State Metrics: Four Weeks (Weekly)',
                                    'Day-to-Day Trends',
                                    'This Month vs. Last Month'))

fig.add_trace(thisweek_table1,row=1,col=1)
fig.add_trace(thisweek_table2,row=3,col=1)
fig.add_trace(weekly_table,row=2,col=1)
fig.add_trace(monthly_table,row=4,col=1)

fig.update_layout(title_text="Warren County School's Daily Dashboard",
                  #autosize=False,
                  #width=1200,
                  height=1200
                  )

plot(fig,filename='graphics/WC-School-Daily.html')
div = plot(fig, include_plotlyjs=False, output_type='div')
with open('school-report/WC-School-Daily.txt','w') as f:
    f.write(div)
    f.close()
