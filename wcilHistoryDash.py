#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov  7 21:18:27 2020

@author: jlmayfield
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  7 12:31:03 2020

@author: jlmayfield
"""

import pandas as pd
import numpy as np

import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot
from plotly.subplots import make_subplots

from urllib.request import urlopen
import json
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

MB_TOKEN = open(".mapbox_token").read()

import cvdataprep as cvdp
import cvdataanalysis as cvda
import cvdataviz as cvdv

#%%
# site table margins
margs = go.layout.Margin(l=0, #left margin
                         r=0, #right margin
                         b=25, #bottom margin
                         t=25  #top margin
                         )                          
#%%

# 17187,17 <-- Warren County, IL
warren = [17187]
p = 16981

#population,cases,deaths = cvdp.loadusafacts()
reports_wchd,demo_wchd,death_wchd = cvdp.loadwchd()
#reports_mc = cvdp.loadmcreports()


#reports_mc = cvda.expandMCData(reports_mc)

#%%


def daily(basis,demo):
    #basis = basis.loc[:,17,17187]
    demo_sum = pd.DataFrame(index=basis.index)
    demo_sum['Age 0-10'] = (demo.T.loc[(slice(None),['0-10']),:].T).sum(axis=1).astype(int)
    demo_sum['Age 10-20'] = (demo.T.loc[(slice(None),['10-20']),:].T).sum(axis=1).astype(int)
    demo_sum['Age 20-40'] = (demo.T.loc[(slice(None),['20-40']),:].T).sum(axis=1).astype(int)
    demo_sum['Age 40-60'] = (demo.T.loc[(slice(None),['40-60']),:].T).sum(axis=1).astype(int)
    demo_sum['Age 60-80'] = (demo.T.loc[(slice(None),['60-80']),:].T).sum(axis=1).astype(int)
    demo_sum['Age 80-100'] = (demo.T.loc[(slice(None),['80-100']),:].T).sum(axis=1).astype(int)
    basis = pd.concat([basis,demo_sum],axis=1)
    return basis
    

def weekly(daydata,nweeks=1):
    basis = daydata[['New Tests','New Positive',
                     'New Positive per 100k','New Deaths',
                     'Age 0-10','Age 10-20','Age 20-40',
                     'Age 40-60','Age 60-80', 'Age 80-100']]
    weeks = basis.groupby(pd.Grouper(level='date',
                                      freq=str(nweeks)+'W-SUN',
                                      closed='left',
                                      label='left')).sum()    
    weeks['Week Number'] = weeks.index.isocalendar().week
    weeks = pd.concat([weeks,
                       cvda._newposrate(weeks)],
                       axis=1)
    return weeks[['Week Number','New Tests','New Positive','% New Positive',
                  'New Positive per 100k','New Deaths',
                  'Age 0-10','Age 10-20','Age 20-40','Age 40-60',
                  'Age 60-80','Age 80-100']]


def monthly(daydata):
    months = daydata.groupby(pd.Grouper(level='date',
                                       freq='MS',
                                       closed='left',
                                       label='left')).sum()    
    months['Month Number'] = months.index.map(lambda d: d.month)
    months = pd.concat([months,
                        cvda._newposrate(months)],
                        axis=1)
    return months[['Month Number','New Tests','New Positive','% New Positive',
                  'New Positive per 100k','New Deaths',
                  'Age 0-10','Age 10-20','Age 20-40','Age 40-60',
                  'Age 60-80','Age 80-100']]

#%%

full_tests_wchd = cvda.expandWCHDData(cvdp.prepwchd(reports_wchd))
# current viz routines assume single date index and do not handle the s
# index that includes state/county fips
tests_wchd = full_tests_wchd.loc[:,17,17187]

by_day = daily(tests_wchd,demo_wchd)
by_week = weekly(by_day).iloc[3:]
by_month = monthly(by_day)


#%%

fig = px.bar(by_week,x=by_week.index,
             y=['Age 0-10','Age 10-20','Age 20-40',
                'Age 40-60','Age 60-80','Age 80-100'],
             labels={'variable':'Age Range','date':'Week Start Date',
                     'value':'New Cases'},
             title="New Cases Per Week",             
             color_discrete_sequence=px.colors.qualitative.Safe,
             )
fig.update_xaxes(tickvals=by_week.index,tickangle=-45)
fig.update_traces(hovertemplate='%{y} cases<extra></extra>')
fig.update_layout(legend=dict(
                     yanchor="top",
                     y=0.99,
                     xanchor="left",
                     x=0.01),
    hovermode='x unified',
    margin=margs)
plot(fig,filename='graphics/WCIL-AllWeeksDemos.html')
weeklydiv = plot(fig, include_plotlyjs=False, output_type='div')

    #%%

fig = px.bar(by_month,x=[d.month_name() for d in by_month.index],
             y=['Age 0-10','Age 10-20','Age 20-40',
                'Age 40-60','Age 60-80','Age 80-100'],
             labels={'variable':'Age Range','x':'Month','value':'New Cases'},             
             title="New Cases Per Month",
             color_discrete_sequence=px.colors.qualitative.Safe
             )
fig.update_xaxes(tickvals=[d.month_name() for d in by_month.index])
fig.update_traces(hovertemplate='%{y} cases<extra></extra>')
fig.update_layout(legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01),
    hovermode='x unified',
    margin=margs)
plot(fig,filename='graphics/WCIL-AllMonthsDemos.html')
monthlydiv = plot(fig, include_plotlyjs=False, output_type='div')

#%%


fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=by_day.index, y=by_day['7 Day Avg New Positive'],
               name="New Cases (7 day avg)"),               
    secondary_y=False,
)

forpos = by_day.loc[pd.to_datetime('2020-04-30'):]
fig.add_trace(
    go.Scatter(x=forpos.index, y=forpos['7 Day Avg % New Positive'],
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

lymax = by_day['7 Day Avg New Positive'].max()
# Set y-axes titles
fig.update_yaxes(title_text="<b>New Cases (7 day avg)</b>", 
                 range = (0,lymax+2),
                 secondary_y=False)
fig.update_yaxes(title_text="<b>Positivity (7 day avg)</b>", 
                 range = (0,.5),
                 tickformat = ',.0%',
                 secondary_y=True)
fig.update_layout(margin=margs)
casetrends = plot(fig, include_plotlyjs=False, output_type='div')
plot(fig,filename='graphics/7daytrends-alltime.html')

#%%

fig = px.line(by_day,x=by_day.index,y='Total Positive',
                 title='Total Positive Tests')
fig.update_layout(margin=margs,
                  yaxis=dict(range=(0,by_day['Total Positive'].max()+100))),
tots = plot(fig,include_plotlyjs=False,output_type='div')
plot(fig,filename='graphics/totalcases.html')
#%%

fig = px.line(by_day,x=by_day.index,y='Total Deaths',
                 title='Total COVID Related Deaths')
fig.update_layout(margin=margs,
                  yaxis=dict(range=(0,by_day['Total Deaths'].max()+5))),
totsdeath = plot(fig,include_plotlyjs=False,output_type='div')
plot(fig,filename='graphics/totaldeaths.html')

    #%%

pgraph = '<p></p>'
mdpage = ""
header = """---
layout: page
title: Warren County Historical COVID-19 Report
permalink: /wcil-history-report/
---
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
"""
timestamp = pd.to_datetime('today').strftime('%H:%M %Y-%m-%d')
header = header + '<p><small>last updated:  ' + timestamp + '</small><p>\n\n'

mdpage = header + tots + pgraph + totsdeath + pgraph + casetrends+ pgraph + weeklydiv + pgraph + monthlydiv

with open('docs/wcilHistory.md','w') as f:
    f.write(mdpage)
    f.close()
