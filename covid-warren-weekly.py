#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  2 15:07:17 2020

@author: jlmayfield
"""


import pandas as pd
import numpy as np

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



#%%

# 17187,17 <-- Warren County, IL
warren = [17187]
neighbors = [17095, 17071, 17109, 17057, 17131]
il_select = [17113, 17107, 17167, 17195, 17031]
ia_select = [19163, 19139, 19045, 19031, 19115, 19057]
region2 = warren + neighbors + [17161, 17073, 17011, 17175, 17143, 17179,
                                17155, 17123, 17203, 17099, 17113, 17105,
                                17093, 17063]

 

nhood = warren+neighbors
allthethings = nhood + il_select + ia_select



#%% 

population = pd.read_csv('covid_county_population_usafacts.csv',
                         dtype={'countyFIPS':np.int64,
                                'County Name':str, 'State':str,
                                'population':np.int64},
                         index_col = 'countyFIPS')

cases = pd.read_csv('covid_confirmed_usafacts.csv',
                         dtype={'countyFIPS':np.int64,'stateFIPS':np.int64,
                                'County Name':str, 'State':str},
                         index_col = 'countyFIPS')

reports_wchd = pd.read_csv('WCHD_Reports.csv',
                         header=[0],index_col=0,
                         parse_dates=True).fillna(0)

demo_wchd = pd.read_csv('WCHD_Case_Demographics.csv',
                       skiprows=[2],
                       header=[0,1],index_col=0,
                       parse_dates=True).fillna(0).iloc[:,0:12]

death_wchd = pd.read_csv('WCHD_Death_Demographics.csv',
                       skiprows=[2],
                       header=[0,1],index_col=0,
                       parse_dates=True).fillna(0).iloc[:,0:12]


#%%

full_tests_wchd = cvda.expandWCHDData(cvdp.prepwchd(reports_wchd))
# current viz routines assume single date index and do not handle the s
# index that includes state/county fips
tests_wchd = full_tests_wchd.loc[:,17,17187]
#tests_wchd.to_csv('WCHD_Expanded_Reports.csv')

#%%

# Daily Pos Rate with Avg and Regional Avg
fig = cvdv.wcposratereport(tests_wchd)

poscases_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/WC-PosRate-ThreeWeek-DIV.txt','w') as f:
    f.write(poscases_div)
    f.close()
plot(fig,filename='graphics/WC-PosRate-ThreeWeek.html')



#%%

# Daily Test Results
fig = cvdv.wcdailytestsreport(tests_wchd)


tests_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/WC-Tests-ThreeWeeks-DIV.txt','w') as f:
    f.write(tests_div)
    f.close()
plot(fig,filename='graphics/WC-Tests-ThreeWeeks.html')



    #%%

# Case Status Stacked Bars

fig = cvdv.wccasestatusreport(tests_wchd)
                   
status_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/WC-CaseStatus-Threeweeks-DIV.txt','w') as f:
    f.write(status_div)
    f.close()
plot(fig,filename='graphics/WC-CaseStatus-Threeweeks.html')


#%%

# Demographics Stacked Bars
fig = cvdv.wcdemoreport(demo_wchd)


demo_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/WC-Demographics-Threeweeks-DIV.txt','w') as f:
    f.write(demo_div)
    f.close()
plot(fig,filename='graphics/WC-Demographics-Threeweeks.html')


#%%

cases = cvdp.datefix(cases)
cases = cvdp.prune_data(cases)


#%%

aoi_fips = region2 + ia_select
aoi = cvdp.prune_data(cases.loc[aoi_fips])

aoi_daily = cvda.to_new_daily(aoi)
aoi_7day = cvda.to_sevenDayAvg(aoi_daily)

aoi_normed_daily = cvda.to_for100k(aoi_daily,population)
aoi_nd_7day = cvda.to_sevenDayAvg(aoi_normed_daily)


#%%

warren_7day = cvdp.prune_data(aoi_7day.loc[warren])
warren_daily = cvdp.prune_data(aoi_daily.loc[warren])

daily_max =  warren_daily.iloc[:,3:].max().max()


#%%

d = cvdv.prep_for_animate(aoi.iloc[:,[0,1,2,-1]])
d_off = cvdv.prep_for_animate(aoi.iloc[:,[0,1,2,-8]])
cnames = cvdv.get_fips_dict(aoi)
d['County'] = d['fips'].apply( lambda f : cnames[f] )
d['Cases'] = d['Cases'] - d_off['Cases']


fig = go.Figure(go.Choroplethmapbox(geojson=counties, 
                                    locations= d['fips'],
                                    z = d['Cases'],
                                    text = d['County'],
                                    colorscale="rdylgn_r",
                                    marker_opacity = 0.2,
                                    hovertemplate='%{text}<br>Total Cases: %{z}<extra></extra>'))
fig.update_layout(mapbox_style='streets', mapbox_accesstoken=MB_TOKEN,                  
                  mapbox_zoom = 6,
                  mapbox_center = {'lon':-89.8130, 'lat': 41.0796},
                  title="Total Confirmed COVID-19 Cases for <br>" +
                  aoi.columns[-7] + ' to ' + aoi.columns[-1])

totmap_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/Region-Map-Total-OneWeek-DIV.txt','w') as f:
    f.write(totmap_div)
    f.close()
plot(fig,filename='graphics/Region-Map-OneWeek.html')

#%%

# Taking a Regional Look

reg_total = aoi_daily.iloc[:,-27:].sum().to_frame().transpose()
dates = list(reg_total.columns)
reg_total['County Name'] = 'Local Region'
reg_total['State'] = 'IL & IA'
reg_total['StateFIPS'] = 0 
reg_total = reg_total[['County Name', 'State', 'StateFIPS'] + dates]

reg_7day = cvda.to_sevenDayAvg(reg_total)

day = cvdv.plot_prep(reg_total.iloc[:,[0,1,2]+list(range(9,30))])
avg=cvdv.plot_prep(reg_7day)


#%%


# Region - Total Cases

fig = go.Figure()
fig.add_trace(go.Bar(x = list(day.index),y = list(day.iloc[:,0]),
                     name='New Cases',
                     hovertemplate='New Cases: %{y}<extra></extra>',
                     marker_color=px.colors.qualitative.Safe[1])
              )
fig.add_trace(go.Scatter(x=list(avg.index),y=list(avg.iloc[:,0]),                         
                         mode="lines",name='Seven Day Average',
                         hovertemplate='Current Avg: %{y:.2f}<extra></extra>',
                         marker_color=px.colors.qualitative.Safe[0]))
fig.update_layout(title='Daily Confirmed Cases of COVID-19 in Region<br>'+
                  str(day.index[0])[:10] + ' to ' + str(day.index[-1])[:10],                  
                  xaxis = dict(
                      tickmode = 'array',
                      tickvals = list(day.index[[0,7]])+list(day.index[-7:]),
                      tickangle=45),                  
                  yaxis = dict(
                      range=(-0.1,day.iloc[:,0].max()+5),
                      tickmode = 'linear',
                      tick0=0, dtick=25),                     
                  xaxis_showgrid=False, 
                  yaxis_showgrid=False,
                  legend=dict(
                      orientation="h",
                      yanchor="bottom",
                      y=1.02,
                      xanchor="right",
                      x=1)
                  )
                   
fig.update_layout(hovermode="x unified")

newcases_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/Region-NewCases-ThreeWeeks-DIV.txt','w') as f:
    f.write(newcases_div)
    f.close()
plot(fig,filename='graphics/Region-NewCases-ThreeWeeks.html')

#%%

# map with total cases per 100000 as of 7/31

# map with total cases as of 7/31
d = cvdv.prep_for_animate(cvda.to_for100k(aoi.iloc[:,[0,1,2,-1]],population))
# stuff to take out
d_off = cvdv.prep_for_animate(cvda.to_for100k(aoi.iloc[:,[0,1,2,-8]],population))
cnames = cvdv.get_fips_dict(aoi)
d['County'] = d['fips'].apply( lambda f : cnames[f] )
d['Cases'] = d['Cases'] - d_off['Cases']

# IL gets twitchy at 50+ cases per week
# Harvard Groups uses [0,1),[1,10),[10,25),25+ 
# So Let's just go yellow at the IL mark and Red at the Harvard High mark. 
yl_cutoff = 50 / d['Cases'].max() 
rd_cutoff = 175 / d['Cases'].max()


fig = go.Figure(go.Choroplethmapbox(geojson=counties, 
                                    locations= d['fips'],
                                    z = d['Cases'],
                                    text = d['County'],                                    
                                    marker_opacity = 0.2,
                                    hovertemplate='%{text}<br>Total Cases per 100000: %{z}<extra></extra>',
                                    colorscale = [
                                        [0,'green'],
                                        [yl_cutoff,'yellow'],
                                        [rd_cutoff,'red'],
                                        [1,'darkred']])
                )
fig.update_layout(mapbox_style='streets', mapbox_accesstoken=MB_TOKEN,                  
                  mapbox_zoom = 6,
                  mapbox_center = {'lon':-89.8130, 'lat': 41.0796},
                  title="Total Confirmed COVID-19 Cases per 100,000 people for<br>"+
                  aoi.columns[-7] + ' to ' + aoi.columns[-1])

totmap_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/Region-Map-NormedTotal-OneWeek-DIV.txt','w') as f:
    f.write(totmap_div)
    f.close()
plot(fig,filename='graphics/Region-Map-NormedTotal-OneWeeks.html')

#%%

# daily actual moving bars

allofit = cvdp.prune_data(aoi_daily)
fig  = cvdv.animated_bars(allofit,21,
                          "Daily COVID-19 Cases by County")
dailybars_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/Region-Bars-ThreeWeeks-DIV.txt','w') as f:
    f.write(dailybars_div)
    f.close()
plot(fig,filename='graphics/Region-Bars-ThreeWeeks.html')

#%%

# daily per 100,000 moving bars

allofit = cvdp.prune_data(aoi_normed_daily)
fig  = cvdv.animated_bars(allofit,21,
                          "Daily COVID-19 Cases per 100,000 by County")
dailybars_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/Region-BarsNormed-ThreeWeeks-DIV.txt','w') as f:
    f.write(dailybars_div)
    f.close()
plot(fig,filename='graphics/Region-BarsNormed-ThreeWeeks.html')

#%%

# daily Seven Day Average per 100,000

allofit = cvdp.prune_data(aoi_nd_7day)
fig  = cvdv.animated_bars(allofit,21,
                          "Seven Day Average of COVID-19 Cases per 100,000 by County")
dailybars_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/Region-BarsNormed7Day-ThreeWeeks-DIV.txt','w') as f:
    f.write(dailybars_div)
    f.close()
plot(fig,filename='graphics/Region-BarsNormed7Day-THreeWeeks.html')

