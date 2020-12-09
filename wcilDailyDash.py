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
import plotly.express as px


import cvdataprep as cvdp
import cvdataanalysis as cvda
import cvdataviz as cvdv

#%%


population,cases,deaths = cvdp.loadusafacts()

#%%
reports_wchd,demo_wchd,_ = cvdp.loadwchd()
#%%

tests_wchd = cvda.expandWCHDData(cvdp.prepwchd(reports_wchd))
# from IL DPH site based on cases vs casesper100k data
p = 16981


#%%


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

# WC Data Only, strip FIPS
wcil = tests_wchd.loc[:,17,17187]

ndays = 10 # fixed at 10 for now
# get window dates
today = pd.to_datetime('today')
last_day = wcil.index[-1] # last day in data
# ten days from last day
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
                         b=25, #bottom margin
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
                  height= (ndays*60)
                  )
weekdiv = plot(fig, include_plotlyjs=False, output_type='div')

#%%

# plot 4 weeks of new case averages and positivity averages
weeks = 4
threeweeks = wcil.iloc[weeks*-7:]

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
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01),
    height = 420
)

# Set x-axis title
fig.update_xaxes(title_text="Date")

ly_max = threeweeks['7 Day Avg New Positive'].max()
ry_max = threeweeks['7 Day Avg % New Positive'].max()
# Set y-axes titles
fig.update_yaxes(title_text="<b>New Cases (7 day avg)</b>", 
                 range = (0,ly_max+2),
                 secondary_y=False)
fig.update_yaxes(title_text="<b>Positivity (7 day avg)</b>", 
                 range = (0,.5),
                 tickformat = ',.0%',
                 secondary_y=True)
fig.update_layout(hovermode='x unified')

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

counts = wcil['New Positive'].value_counts()
x_max = counts.index[-1]
y_max = counts.max()

fig = go.Figure()
fig.add_trace(go.Bar(
    x=counts.index,
    y=counts,
    name='New Cases per Day', #
    hovertemplate="%{y} days with %{x} cases<extra></extra>",
    marker_color=px.colors.sequential.Viridis[0],
    opacity=0.75,
    showlegend=False
    ))    


points_x = dailywindow['New Positive']
points_y = [counts.loc[c] for c in points_x]
points_dates = [str(d.date()) for d in dailywindow.index]

fig.add_trace(go.Scatter(
    x=points_x[-1:],
    y=points_y[-1:],
    marker=dict(color=px.colors.sequential.Viridis[9],size=18),    
    text = points_dates[-1:],
    #showlegend=False,
    name=points_dates[-1],
    mode='markers',
    hovertemplate="%{text}: %{x} cases<extra></extra>",
    ))  


fig.add_trace(go.Scatter(
    x=points_x[3:9],
    y=points_y[3:9],
    marker=dict(color=px.colors.sequential.Viridis[7],size=14),    
    text = points_dates[3:9],
    #showlegend=False,
    name=points_dates[3]+' - '+points_dates[8],
    mode='markers',
    hovertemplate="%{text}: %{x} cases<extra></extra>",
    ))  

fig.add_trace(go.Scatter(
    x=points_x[0:3],
    y=points_y[0:3],
    marker=dict(color=px.colors.sequential.Viridis[5],size=10),    
    text = points_dates[0:3],
    #showlegend=False,
    name=points_dates[0]+' - '+points_dates[2],
    mode='markers',
    hovertemplate="%{text}: %{x} cases<extra></extra>",
    ))  

fig.update_layout(
    title_text='New Cases reported in a Single Day as of ' + points_dates[-1], # title of plot
    xaxis_title_text='Number of Cases', # xaxis label
    yaxis_title_text='Number of Days', # yaxis label
    bargap=0.1, # gap between bars of adjacent location coordinates
    xaxis = dict(tickmode = 'array',
                 tickvals = list(range(0,x_max+1))),                 
    yaxis_range = (0,y_max+5),
    hovermode='x unified',
    margin = margs,
    legend=dict(
        yanchor="top",        
        xanchor="right",
        x = .99,
        y = .99,        
    ),
    height=420   
)


plot(fig,filename='graphics/DailyCaseHisto.html') 
dailyhistodiv = plot(fig, include_plotlyjs=False, output_type='div')


#%%

pgraph = '<p></p>'
mdpage = ""
header = """---
layout: page
title: Warren County Daily COVID-19 Report
permalink: /wcil-daily-report/
---
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
"""
timestamp = pd.to_datetime('today').strftime('%H:%M %Y-%m-%d')
header = header + '<p><small>last updated:  ' + timestamp + '</small><p>\n\n'
tdaynote = """
<p><small> The WCHD did not issue a report on Thanksgiving (11/26). 
The daily totals reported here come from the IDPH reports. Both agencies reproted
the same two day total. Case demographics were more or less porportionally distributed
across the two days.</small></p> 
"""
mdpage = header + tdaynote + weekdiv + casetrends + pgraph +\
    dailyhistodiv + pgraph + weeklydiv + monthlydiv

with open('docs/wcilDaily.md','w') as f:
    f.write(mdpage)
    f.close()
