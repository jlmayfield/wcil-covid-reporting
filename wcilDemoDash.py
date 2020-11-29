#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  7 12:31:03 2020

@author: jlmayfield
"""
from math import ceil
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot
from plotly.subplots import make_subplots

import cvdataprep as cvdp

#%%


reports_wchd,demo_wchd,death_wchd = cvdp.loadwchd()


#%% 

# clear daily numbers by each category
demo_daily = demo_wchd.copy().reorder_levels([1,0],axis=1)
demo_daily = demo_daily.reindex(sorted(demo_daily.columns),axis=1)
demo_daily.columns = [i[1]+ ' ' + i[0] for i in demo_daily.columns]
demo_daily.index.name = 'date'

# cumulative totals
demo_total = demo_daily.cumsum()
# weekly totals
demo_weeks = demo_daily.groupby(pd.Grouper(level='date',
                                           freq='W-SUN',
                                           closed='left',
                                           label='left')).sum() 

# same but for deaths rather than cases
death_daily = death_wchd.copy().reorder_levels([1,0],axis=1)
death_daily = death_daily.reindex(sorted(death_daily.columns),axis=1)
death_daily.columns = [i[1]+ ' ' + i[0] for i in death_daily.columns]
death_daily.index.name = 'date'
death_total = death_daily.cumsum()
death_weeks = death_daily.groupby(pd.Grouper(level='date',
                                             freq='W-SUN',
                                             closed='left',
                                             label='left')).sum() 

# demographic category -> color
clrs = px.colors.sequential.algae
cmap = {demo_daily.columns[i]:clrs[i] for i in range(len(demo_daily.columns))}

# Demographic Groups that have recorded Deaths
deathcats = death_total.iloc[-1]
deathcats = (deathcats[ deathcats > 0 ]).index

death_daily = death_daily[deathcats].astype(int)
death_total = death_total[deathcats].astype(int)
death_weeks = death_weeks[deathcats].astype(int)


#%%

# Cumulative Cases with demographic categories

fig = go.Figure()

cats = demo_total.columns
for i in range(0,len(cats)):
    fig.add_trace(go.Scatter(x=demo_total.index,
                         y=demo_total[cats[i]],
                         mode='lines',
                         name=cats[i],
                         marker_color=cmap[cats[i]],
                         fill='tonexty',
                         stackgroup='one'                         
                         ))
fig.update_layout(title="Total COVID-19 Cases in Warren County",
                  legend=dict(
                      yanchor="top",                     
                      y=0.99,
                      xanchor="left",
                      x=0.01)                  
                      )    
    
#plot(fig,filename='graphics/CumulativeCases_demos.html')    

#%%

# Cumulative Deaths 

fig = go.Figure()

cats = death_total.columns
for i in range(0,len(cats)):
    fig.add_trace(go.Scatter(x=death_total.index,
                         y=death_total[cats[i]],
                         mode='lines',
                         name=cats[i],
                         marker_color=cmap[cats[i]],
                         fill='tonexty',
                         stackgroup='one'                         
                         ))
fig.update_layout(title="Total COVID-19 Related Deaths in Warren County",
                  legend=dict(
                      yanchor="top",
                      y=0.99,
                      xanchor="left",
                      x=0.01)                  
                      )    
    
#plot(fig,filename='graphics/CumulativeDeaths_demos.html')    
    
#%%

# weekly case totals

fig = go.Figure()

cats = demo_weeks.columns
for i in range(0,len(cats)):
    fig.add_trace(go.Scatter(x=demo_weeks.index,
                         y=demo_weeks[cats[i]],
                         mode='lines',
                         name=cats[i],
                         marker_color=cmap[cats[i]],
                         fill='tonexty',
                         stackgroup='one'                         
                         ))
fig.update_layout(title="Weekly Case Totals",
                  legend=dict(
                      yanchor="top",
                      y=0.99,
                      xanchor="left",
                      x=0.01)
                      )    
    
#plot(fig,filename='graphics/weeklyCases_demos.html')    

#%%

# weekly death totals

fig = go.Figure()

cats = death_weeks.columns
for i in range(1,len(cats)):
    fig.add_trace(go.Scatter(x=death_weeks.index,
                         y=death_weeks[cats[i]],
                         mode='lines',
                         name=cats[i],
                         marker_color=cmap[cats[i]],
                         fill='tonexty',
                         stackgroup='one'                         
                         ))
fig.update_layout(title="Weekly Case Totals",
                  legend=dict(
                      yanchor="top",
                      y=0.99,
                      xanchor="left",
                      x=0.01)
                      )    
    
#plot(fig,filename='graphics/weeklyDeaths_demos.html')    
    

#%%

# site table margins
margs = go.layout.Margin(l=0, #left margin
                         r=0, #right margin
                         b=25, #bottom margin
                         t=75  #top margin
                         )                          

#%%

# multiples: cumulative Cases 

cumsum_order = demo_total.iloc[-1].sort_values(ascending=False).index
curtot = demo_total.iloc[-1].sum()
catmax = demo_total.max().max()

fig = make_subplots(rows=6,cols=3,
                    shared_yaxes=True,
                    shared_xaxes=True,
                    specs = [[{},{},{}],
                             [{},{},{}],
                             [{},{},{}],
                             [{},{},{}],
                             [{'colspan':3,'rowspan':2},None,None],
                             [None,None,None]],
                    subplot_titles=list(cumsum_order)+['All Demographics']
                    )
for i in range(len(cumsum_order)):
    cat = cumsum_order[i]
    clr = cmap[cat]
    fig.add_trace(go.Scatter(x=demo_total.index,
                             y=demo_total[cat],
                             name=cat,
                             showlegend=False,
                             fill='tozeroy',
                             mode='lines',
                             marker_color=clr
                             ),
                  row = int(i/3)+1,col=int(i%3)+1)
cats = demo_total.columns
for i in range(0,len(cats)):
    fig.add_trace(go.Scatter(x=demo_total.index,
                         y=demo_total[cats[i]],
                         mode='lines',
                         name=cats[i],
                         marker_color=cmap[cats[i]],
                         fill='tonexty',
                         stackgroup='one'                         
                         ),
                  row=5,col=1)    

fig.update_yaxes(range=(0,catmax+10))
fig.update_yaxes(range=(0,demo_daily.sum().sum() + 25),row=5)
fig.update_layout(title="Total COVID-19 Cases by Demographic Groups",
                  width= 1200,
                  height= 800,
                  margin=margs)
plot(fig,filename='graphics/demototals_multiples.html')
div_casetotal = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/WCIL-DemoTotals.txt','w') as f:
    f.write(div_casetotal)
    f.close()


#%%
# multiples: weekly Cases 
complete_weeks = demo_weeks.iloc[0:-1]
currweek_order = complete_weeks.iloc[-1].sort_values(ascending=False).index
catmax = complete_weeks.max().max()

fig = make_subplots(rows=6,cols=3,
                    shared_yaxes=True,
                    shared_xaxes=True,
                    specs = [[{},{},{}],
                             [{},{},{}],
                             [{},{},{}],
                             [{},{},{}],
                             [{'colspan':3,'rowspan':2},None,None],
                             [None,None,None]],
                    subplot_titles= list(currweek_order) + ['All Demographics'])
for i in range(len(currweek_order)):
    cat = currweek_order[i]
    clr = cmap[cat]
    fig.add_trace(go.Scatter(x=complete_weeks.index,
                             y=complete_weeks[cat],
                             name=cat,
                             showlegend=False,
                             fill='tozeroy',
                             mode='lines',
                             marker_color=clr
                             ),
                  row = int(i/3)+1,col=int(i%3)+1)
cats = complete_weeks.columns
for i in range(0,len(cats)):
    fig.add_trace(go.Scatter(x=complete_weeks.index,
                         y=complete_weeks[cats[i]],
                         mode='lines',
                         name=cats[i],
                         marker_color=cmap[cats[i]],
                         fill='tonexty',
                         #showlegend=False,
                         stackgroup='one'                             
                         ),row=5,col=1)

tot=complete_weeks.sum(axis=1).max()
fig.update_yaxes(range=(0,catmax+5))
fig.update_yaxes(range=(0,tot+10),row=5)
fig.update_layout(title="Weekly COVID-19 Cases by Demographic Groups",
                  width=1200,height=800,margin=margs
                  )
plot(fig,filename='graphics/demoweekl_multiples.html')
div_caseweek = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/WCIL-DemoWeekly.txt','w') as f:
    f.write(div_caseweek)
    f.close()


#%%

# multiples : cumlative deaths

cumsum_order = death_total.iloc[-1].sort_values(ascending=False).index
curtot = death_total.iloc[-1].sum()
catmax = death_total.max().max()
R = ceil(len(deathcats) / 3 )
fig = make_subplots(rows=R+2,cols=3,
                    specs=[[{},{},{}]] * R +
                    [[{'colspan':3,'rowspan':2},None,None],
                     [None,None,None]],                    
                    shared_yaxes=True,
                    shared_xaxes=True,
                    subplot_titles= list(cumsum_order)+
                    ([''] * (3-len(deathcats)%3)) + 
                    ['All Demographics']
                    )
for i in range(len(cumsum_order)):
    cat = cumsum_order[i]
    clr = cmap[cat]
    fig.add_trace(go.Scatter(x=death_total.index,
                             y=death_total[cat],
                             name=cat,
                             showlegend=False,
                             fill='tozeroy',
                             mode='lines',
                             marker_color=clr
                             ),
                  row = int(i/3)+1,col=int(i%3)+1)
cats = death_total.columns
for i in range(0,len(cats)):
    fig.add_trace(go.Scatter(x=death_total.index,
                         y=death_total[cats[i]],
                         mode='lines',
                         name=cats[i],
                         marker_color=cmap[cats[i]],
                         fill='tonexty',
                         stackgroup='one'                         
                         ),row=R+1,col=1)    

fig.update_yaxes(range=(0,catmax+3))
tot = death_daily.sum().sum()
fig.update_yaxes(range=(0,tot+2), row=R+1)
fig.update_layout(title="Total Deaths by Demographic Groups",
                  width=1200,height=800,margin=margs)
plot(fig,filename='graphics/demototals_deaths_multiples.html')
div_deathtotal = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/WCIL-DemoDeathTotals.txt','w') as f:
    f.write(div_deathtotal)
    f.close()
    
#%%

pgraph = '<p></p>'
mdpage = ""
header = """---
layout: page
title: Warren County COVID-19 Demographic Report
permalink: /wcil-demographics-report/
---
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
"""
timestamp = pd.to_datetime('today').strftime('%H:%M %Y-%m-%d')
header = header + '<p><small>last updated:  ' + timestamp + '</small><p>\n\n'

mdpage = header + div_casetotal + pgraph + \
    div_caseweek + pgraph + div_deathtotal

with open('docs/wcilDemographics.md','w') as f:
    f.write(mdpage)
    f.close()
    

