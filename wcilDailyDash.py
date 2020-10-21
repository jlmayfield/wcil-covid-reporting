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
    basis = daily[['New Positive','New Tests','New Deaths','Youth Cases']]
    wcil = basis.groupby(pd.Grouper(level='date',
                                      freq=str(nweeks)+'W-SUN',
                                      closed='left',
                                      label='left')).sum()
    wcil['Cases per 100k'] = wcil['New Positive'] * 100000 / p
    wcil['% New Positive'] = wcil['New Positive']/wcil['New Tests']
    wcil['New Positive Change'] = wcil['New Positive'].pct_change()
    wcil['New Youth Change'] = wcil['Youth Cases'].pct_change()
    wcil['Consecutive Case Increases'] = cvda._increaseStreak(wcil['New Positive'])
    wcil['Consecutive Youth Increases'] = cvda._increaseStreak(wcil['Youth Cases'])
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
                                            cvdv.styleprate_text(df['7 Day Avg % New Positive']),
                                             df['Positivity Rate Increases in 10 days']
                                           ],
                                  'align':'left',
                                  'fill_color':['whitesmoke',
                                                'whitesmoke',
                                                'whitesmoke',
                                                cvdv.styleprate_cell(df['7 Day Avg % New Positive']),
                                                'whitesmoke'
                                                ],
                                  })


fig = go.Figure(data=daily_trends)
fig.update_layout(title="Daily Trends",
                  margin = margs,
                  height= (ndays*45 + 100)
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
                                            '<b>New Deaths</b>'
                                            ],
                                  'align':'left',
                                  'fill_color':'gainsboro'},
                          cells={'values':[df['date'].apply(lambda d: d.strftime("%B %d")),
                                           cvdv.stylecp100k_text(df['Cases per 100k']),
                                           cvdv.styleprate_text(df['% New Positive']),
                                           df['New Tests'],
                                           cvdv.stylecase_text(df[['New Positive',
                                                              'Consecutive Case Increases',
                                                              'New Positive Change']]),
                                           cvdv.stylecase_text(df[['Youth Cases',
                                                              'Consecutive Youth Increases',
                                                              'New Youth Change']]),
                                           df['New Deaths']                                                          
                                           ],
                                 'align':'left',
                                 'fill_color':
                                     ['whitesmoke',
                                      cvdv.stylecp100k_cell(df['Cases per 100k']),
                                      cvdv.styleprate_cell(df['% New Positive']),
                                      'whitesmoke',
                                      cvdv.stylecase_cell(df['Consecutive Case Increases']),
                                      cvdv.stylecase_cell(df['Consecutive Youth Increases']),
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
             df['Cases per 100k'].apply(lambda c:'{:.1f}'.format(c)),
             cvdv.styleprate_text(df['% New Positive']),
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
                                               cvdv.styleprate_cell(df['% New Positive']),
                                               'whitesmoke',
                                               'whitesmoke',
                                               'whitesmoke',
                                               'whitesmoke']}
                          )

fig = go.Figure(data=monthly_table)
fig.update_layout(title="This Month vs. Prior Months",
                  margin = margs,
                  height= 250
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
