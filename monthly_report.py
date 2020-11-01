#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 31 09:16:58 2020

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


day1 = pd.to_datetime('2020-10-01')
lastday = pd.to_datetime('2020-10-31')
# grab the week before the start day to prime the rolling averages
dayoff = day1 - pd.Timedelta(8,unit='D')
themonth = pd.date_range(day1,lastday)
theslice = pd.date_range(dayoff,lastday)

# 17187,17 <-- Warren County, IL

population,cases = cvdp.loadusafacts()
reports_wchd,demo_wchd,death_wchd = cvdp.loadwchd()
reports_mc = cvdp.loadmcreports()


wchd = cvdp.prepwchd(reports_wchd)
wchd = cvda.expandWCHDData(wchd.loc[(theslice,17,slice(None)),:],
                           population.loc[17187,'population'])

reports_mc = cvda.expandMCData(reports_mc)


usaf = cvdp.prepusafacts(cases)
usaf = cvda.expandUSFData(usaf.loc[(slice(None),17,slice(None)),:],
                          population)

ilcounties = usaf[ usaf['Recovery Region'] != 17]
#%%

usaf_mnth = ilcounties.loc[ (themonth,slice(None),slice(None)), :]
wchd_mnth = wchd.loc[ (themonth,slice(None),slice(None)), :]
mc_mnth = reports_mc.loc[themonth]


#%%

# Whole State of IL
all_of_il = ilcounties[['Total Positive','New Positive']].groupby(level='date').sum()
all_of_il = pd.concat([all_of_il,
                       cvda._mc7day(all_of_il['New Positive'])]
                      ,axis=1).loc[themonth]

# By Recovery Region
regions = ilcounties[['Recovery Region','Total Positive','New Positive','New Positive per 100k']].groupby(by=['date','Recovery Region']).sum()
def roller(grp):
    return grp.rolling(7,min_periods=7).mean()
sda = regions[['New Positive']].groupby(by=['Recovery Region']).apply(roller)['New Positive'].rename('7 Day Avg New Positive')
sdap1k = regions[['New Positive per 100k']].groupby(by=['Recovery Region']).apply(roller)['New Positive per 100k'].rename('7 Day Avg New Positive per 100k')
regions = pd.concat([regions,sda,sdap1k],axis=1).loc[themonth]

#%%

fig = go.Figure()
fig.add_trace(go.Bar(x=all_of_il.index,
                    y=all_of_il['New Positive'],
                    name='New Cases',
                    hovertemplate='%{x}: %{y} cases<extra></extra>'
                    ))
fig.add_trace(go.Scatter(x=all_of_il.index,
                         y=all_of_il['7 Day Avg New Positive'],
                         name='7 Day Rolling Average',
                         hovertemplate='%{y} 7 Day Average<extra></extra>'
                         ))
fig.update_layout(title="October in Illinois: New Cases",
                  xaxis = dict(
                           tickmode = 'array',
                           tickvals = all_of_il.index[0::7],
                           tickangle=45),
                  xaxis_showgrid=False, 
                  yaxis_showgrid=False,
                  )
plot(fig,filename='graphics/october-IL.html')
             
#%%
region_idx = regions.index.get_level_values('Recovery Region').unique()
date_idx = regions.index.get_level_values('date').unique()
fig = go.Figure()
for r in region_idx:
    fig.add_trace(go.Scatter(x=date_idx,
                             y=regions['7 Day Avg New Positive per 100k'].loc[:,r],
                             name=r))
fig.update_layout(title="October in Illinois: Seven Day Average of New Cases per 100,000 people by Recovery Region",
                  xaxis = dict(
                           tickmode = 'array',
                           tickvals = all_of_il.index[0::7],
                           tickangle=45),
                  xaxis_showgrid=False, 
                  yaxis_showgrid=False,
                  )
plot(fig,filename='graphics/october-region100k.html')

#%%
colors = px.colors.sequential.Viridis
cscale = [[0.0,colors[0]],
          [10.0/420.0,colors[1]],
          [30.0/420.0,colors[2]],
          [50.0/420.0,colors[3]],
          [65.0/420.0,colors[4]],
          [85.0/420.0,colors[5]],
          [100.0/420.0,colors[6]],
          [150.0/420.0,colors[7]],
          [200.0/420.0,colors[8]],
          [1.0,colors[9]]
          ]
nostate = ilcounties.loc[:,17,:]
fips = nostate.index.get_level_values('countyFIPS').unique()
county_names = cvdv.get_fips_dict(fips, population)
firstday = nostate.loc[day1,:]

#%%
fig = go.Figure(go.Choroplethmapbox(geojson=counties, 
                                    locations= firstday.index,
                                    z = firstday['New Positive per 100k'],                                    
                                    zmin=0,zmax=420,
                                    text = [county_names[f] for f in firstday.index],
                                    colorscale=cscale,                                    
                                    marker_opacity = 0.2,
                                    hovertemplate='%{text}<br>Cases per 100k: %{z}<extra></extra>'))
fig.update_layout(mapbox_style='streets', mapbox_accesstoken=MB_TOKEN,                  
                  mapbox_zoom = 6,
                  #springfield,IL
                  mapbox_center = {'lon':-89.6501, 'lat': 39.7817},
                  title="October in Illinois: Cases per 100,000 people<br>" +
                  str(day1.date()))
plot(fig,filename='graphics/october-countymap.html') 
                  