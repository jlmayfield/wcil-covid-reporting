#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 17 10:24:53 2020

@author: jlmayfield
"""


import pandas as pd

from plotly.subplots import make_subplots
import plotly.graph_objects as go
from plotly.offline import plot


import cvdataprep as cvdp
import cvdataanalysis as cvda
import cvdataviz as cvdv

#%%


population,cases = cvdp.loadusafacts()
reports_wchd,demo_wchd,_ = cvdp.loadwchd()


tests_wchd = cvda.expandWCHDData(cvdp.prepwchd(reports_wchd))
# from IL DPH site based on cases vs casesper100k data
p = 16981


#%%


def daily(wchd_data,wchd_demo):
    keepers = ['New Positive','New Tests','New Deaths',
               '% New Positive','7 Day Avg % New Positive']
    wcil = wchd_data.loc[:,17,17187][keepers]
    wcil['Youth Cases'] = (wchd_demo.T.loc[(slice(None),['0-10','10-20']),:].T).sum(axis=1).astype(int)
    wcil['Cases per 100k'] = wcil['New Positive'] * 100000 / p
    wcil['Case Increases in 10 days'] = cvda._increasesInNDays(wcil['New Positive'],10)
    wcil['Youth Increases in 10 days'] = cvda._increasesInNDays(wcil['Youth Cases'],10)
    wcil['Positivity Rate Increases in 10 days'] = cvda._increasesInNDays(wcil['% New Positive'],10)
    return wcil

def weekly(daily,nweeks=1):
    basis = daily[['New Positive','New Tests','New Deaths','New Positive per 100k']]
    wcil = basis.groupby(pd.Grouper(level='date',
                                      freq=str(nweeks)+'W-SUN',
                                      closed='left',
                                      label='left')).sum()
    wcil['% New Positive'] = wcil['New Positive']/wcil['New Tests']
    wcil['New Positive Change'] = wcil['New Positive'].pct_change()
    wcil['Consecutive Case Increases'] = cvda._increaseStreak(wcil['New Positive'])   
    return wcil

def monthly(daily):
    basis = daily[['New Positive','New Tests','New Deaths','New Positive per 100k']]
    wcil = basis.groupby(pd.Grouper(level='date',freq='MS',
                                      closed='left',label='left')).sum()
    # assume official test dates are a day prior to align with state
    wcil['% New Positive'] = wcil['New Positive']/wcil['New Tests']
    return wcil


#%%

wcil = tests_wchd.loc[:,17,17187]

ndays = 10 # fixed at 10 for now
# get window dates
today = pd.to_datetime('today')
last_day = wcil.index[-1]
tenago = last_day - pd.Timedelta(ndays-1,unit='D')

# 10 days 
dailywindow = wcil.loc[tenago:]

#%%
#all_the_days = daily(tests_wchd, demo_wchd)
# this week + 4
fiveweeks = weekly(wcil,nweeks=1).iloc[-5:]
# this week + 2
threemonths = monthly(wcil).iloc[-3:]


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
                                            '<b>New Cases (per 100k)</b>',                                           
                                            '<b>Positivity Rate</b>',                                           
                                            '<b>New Deaths</b>'
                                            ],
                                  'align':'left',
                                  'fill_color':'gainsboro'},
                           cells={'values':[df['date'].apply(lambda d: d.strftime("%A, %B %d")),
                                            df['New Tests'],
                                            cvdv.style_casenum(df[['New Positive','New Positive per 100k']]),
                                            cvdv.styleprate_text(df['% New Positive']),
                                            df['New Deaths']
                                            ],                                            
                                  'align':'left',
                                  'fill_color':['whitesmoke',
                                                'whitesmoke',
                                                cvdv.stylecp100k_cell(df['New Positive per 100k']),                                                                                                
                                                cvdv.styleprate_cell(df['% New Positive']),                                                
                                                'whitesmoke'
                                                ],
                                  })

fig = go.Figure(data=daily)
fig.update_layout(title="Daily Case Reports",
                  margin = margs,
                  height= (ndays*60 + 150)
                  )
weekdiv = plot(fig, include_plotlyjs=False, output_type='div')

#%%

# plot 4 weeks of new case averages and positivity averages

threeweeks = wcil.iloc[-28:]

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=threeweeks.index, y=threeweeks['7 Day Avg New Positive'],
               name="New Cases (7 day avg)"),               
    secondary_y=False,
)

fig.add_trace(
    go.Scatter(x=threeweeks.index, y=threeweeks['7 Day Avg % New Positive'],
               name="Positivity (7 day avg)"),
    secondary_y=True,
)

# Add figure title
fig.update_layout(
    title_text="New Cases and Positivity: 7 Day Rolling Averages",
    margin = margs,
)

# Set x-axis title
fig.update_xaxes(title_text="Date")

# Set y-axes titles
fig.update_yaxes(title_text="<b>New Cases (7 day avg)</b>", 
                 range = (0,15),
                 secondary_y=False)
fig.update_yaxes(title_text="<b>Positivity (7 day avg)</b>", 
                 range = (0,.5),
                 tickformat = ',.0%',
                 secondary_y=True)

casetrends = plot(fig, include_plotlyjs=False, output_type='div')


#%%
df = fiveweeks.reset_index().sort_values('date',ascending=False)
weekly_table = go.Table(#columnwidth = [10,10,10,10,10,10,10],
                          header={'values':['<b>Week Start Date</b>',
                                            '<b>New Cases</b>',
                                            '<b>Cases per 100k</b>',
                                            '<b>New Tests</b>',
                                            '<b>Positivity Rate</b>',
                                            '<b>New Deaths</b>'
                                            ],
                                  'align':'left',
                                  'fill_color':'gainsboro'},
                          cells={'values':[df['date'].apply(lambda d: d.strftime("%B %d")),
                                           cvdv.stylecase_text(df[['New Positive',
                                                              'Consecutive Case Increases',
                                                              'New Positive Change']]),
                                           cvdv.stylecp100k_text(df['New Positive per 100k']),
                                           df['New Tests'],
                                           cvdv.styleprate_text(df['% New Positive']),                                           
                                           df['New Deaths']                                                          
                                           ],
                                 'align':'left',
                                 'fill_color':
                                     ['whitesmoke',
                                      cvdv.stylecase_cell(df['Consecutive Case Increases']),
                                      cvdv.stylecp100k_cell(df['New Positive per 100k']),
                                      'whitesmoke',
                                      cvdv.styleprate_cell(df['% New Positive']),
                                      'whitesmoke'
                                      ]
                                 })

fig = go.Figure(data=weekly_table)
fig.update_layout(title="This Week vs Prior Weeks",
                  margin = margs,
                  height= 350
                  )
weeklydiv = plot(fig, include_plotlyjs=False, output_type='div')
    

#%%

df = threemonths.reset_index().sort_values('date',ascending=False)
cell_vals = [df['date'].apply(lambda d: d.strftime("%B")),
             df['New Positive'],
             df['New Positive per 100k'].apply(lambda c:'{:.1f}'.format(c)),
             df['New Tests'],
             cvdv.styleprate_text(df['% New Positive']),                         
             df['New Deaths']]
monthly_table = go.Table(#columnwidth = [10,10,10,10,10,10,10],
                          header={'values':['<b>Month</b>',
                                            '<b>New Cases</b>',
                                            '<b>Cases per 100k</b>',
                                            '<b>New Tests</b>',
                                            '<b>Positivity Rate</b>',
                                            '<b>New Deaths</b>'],
                                  'align':'left',
                                  'fill_color':'gainsboro'},
                          cells={'values':cell_vals,
                                 'align':'left',
                                 'fill_color':['whitesmoke',
                                               'whitesmoke',                                            
                                               'whitesmoke',
                                               'whitesmoke',
                                               cvdv.styleprate_cell(df['% New Positive']),
                                               'whitesmoke']}
                          )

fig = go.Figure(data=monthly_table)
fig.update_layout(title="This Month vs. Prior Months",
                  margin = margs,
                  height= 250
                  )
monthlydiv = plot(fig, include_plotlyjs=False, output_type='div')

#%%


fig = make_subplots(rows=3, cols=1,                    
                    vertical_spacing=0.02,                    
                    specs=[[{"type": "table"}],
                           #[{"type": "scatter"}],
                           [{"type": "table"}],
                           [{"type": "table"}],
                          ],
                    subplot_titles=('Daily Reports (10 Day Window)',
                                    #'Trend Data',
                                    'This Week vs Prior Weeks',                                    
                                    'This Month vs. Prior Months'))

fig.add_trace(daily,row=1,col=1)
#fig.add_trace(casetrends,row=2,col=1)
fig.add_trace(weekly_table,row=2,col=1)
fig.add_trace(monthly_table,row=3,col=1)

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

mdpage = header + weekdiv + casetrends + weeklydiv + monthlydiv

with open('docs/wcilDaily.md','w') as f:
    f.write(mdpage)
    f.close()
