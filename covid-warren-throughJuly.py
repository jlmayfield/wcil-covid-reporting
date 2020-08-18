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


tests_wchd = pd.read_csv('WCHD_Reports.csv',
                         header=[0],index_col=0,
                         parse_dates=True).fillna(0)

dates = list(tests_wchd.index)


def which_phase(d):
    LAST_PHASE2 = pd.to_datetime('05-28-2020')
    LAST_PHASE3 = pd.to_datetime('06-25-2020')
    if d <= LAST_PHASE2:
        return 'Phase 2'
    elif d <= LAST_PHASE3:
        return 'Phase 3'
    else:
        return 'Phase 4'
    
   

tests_wchd['Phase'] = tests_wchd.index.to_series().apply(which_phase)

#%% 

demo_wchd = pd.read_csv('WCHD_Demographics.csv',
                       skiprows=[2],
                       header=[0,1],index_col=0,
                       parse_dates=True).fillna(0).iloc[:,0:13]

sexes = list(demo_wchd.columns.get_level_values(level=0).unique())
ages = list(demo_wchd.columns.get_level_values(level=1).unique())
dates = list(demo_wchd.index)

#%%

cases = cvdp.datefix(cases)
cases = cvdp.prune_data(cases)

#%%

# clear out August Forward

cases_dates = [ d for d in cases.columns[3:] if pd.to_datetime(d) < pd.to_datetime('2020-08-01') ]
casescols = list(cases.columns[:3]) + cases_dates
cases = cases[casescols]

testsidx = [ d for d in tests_wchd.index if d < pd.to_datetime('2020-08-01') ]
tests_wchd = tests_wchd.loc[testsidx]
demo_wchd = demo_wchd.loc[testsidx]

#%%


totals_men = demo_wchd['Male'].sum()
totals_women = demo_wchd['Female'].sum()

totals = pd.DataFrame([],columns=['age','sex','cases'])
for a in totals_men.index:
    totals = totals.append(pd.Series([a,'Male',totals_men[a]],
                                     index=['age','sex','cases']),
                           ignore_index=True)
for a in totals_women.index:
    totals = totals.append(pd.Series([a,'Female',totals_women[a]],
                                     index=['age','sex','cases']),
                           ignore_index=True)



#%%

aoi_fips = region2 + ia_select
aoi = cvdp.prune_data(cases.loc[aoi_fips])

aoi_daily = cvda.to_new_daily(aoi)
aoi_7day = cvda.to_sevenDayAvg(aoi_daily)

aoi_normed_daily = cvda.to_for100k(aoi_daily,population)
aoi_nd_7day = cvda.to_sevenDayAvg(aoi_normed_daily)

days = len(aoi.columns) - 3

#%%

warren_7day = cvdp.prune_data(aoi_7day.loc[warren])
warren_daily = cvdp.prune_data(aoi_daily.loc[warren])


#%%

day = cvdv.plot_prep(warren_daily)
day['Phase'] = day.index.to_series().apply(which_phase)
p2 = day[ day['Phase'] == 'Phase 2']
p3 = day[ day['Phase'] == 'Phase 3']
p4 = day[ day['Phase'] == 'Phase 4']
avg=cvdv.plot_prep(warren_7day)

#%%

# Daily New Cases w/ Phase colors

fig = go.Figure()
fig.add_trace(go.Bar(x = list(p2.index),y = list(p2.iloc[:,0]),
                     name='Recovery Phase 2',
                     hovertemplate='New Cases: %{y}<extra></extra>'))
fig.add_trace(go.Bar(x = list(p3.index),y = list(p3.iloc[:,0]),
                     name='Recovery Phase 3',
                     hovertemplate='New Cases: %{y}<extra></extra>'))
fig.add_trace(go.Bar(x = list(p4.index),y = list(p4.iloc[:,0]),
                     name='Recovery Phase 4',
                     hovertemplate='New Cases: %{y}<extra></extra>'))
fig.add_trace(go.Scatter(x=list(avg.index),y=list(avg.iloc[:,0]),                         
                         mode="lines",name='Seven Day Average',
                         hovertemplate='Current Avg: %{y:.2f}<extra></extra>'))
fig.update_layout(title='Daily Confirmed Cases of COVID-19 in Warren County, IL',                  
                  xaxis = dict(
                      tickmode = 'array',
                      tickvals = list(day.index)[0::7],
                      tickangle=45),                  
                  yaxis = dict(
                      range=(-0.1,day.iloc[:,0].max()+.1),
                      tickmode = 'linear',
                      tick0=0, dtick=1),   
                  colorway=px.colors.qualitative.Safe,
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
with open('WC-NewCases-Start_to_Aug-DIV.txt','w') as f:
    f.write(newcases_div)
    f.close()
plot(fig,filename='WC-NewCases-Start_to_Aug.html')


    #%%

p2 = tests_wchd[ tests_wchd['Phase'] == 'Phase 2']
p3 = tests_wchd[ tests_wchd['Phase'] == 'Phase 3']
p4 = tests_wchd[ tests_wchd['Phase'] == 'Phase 4']

#%%

# Daily Positivity Rate with Phase Colors

fig = go.Figure()
fig.add_trace(go.Bar(x = list(p2.index),y = list(p2['% New Positive']),
                     name='Recovery Phase 2',
                     hovertemplate='% Positive: %{y:.2%}<extra></extra>'))
fig.add_trace(go.Bar(x = list(p3.index),y = list(p3['% New Positive']),
                     name='Recovery Phase 3',
                     hovertemplate='% Positive: %{y:.2%}<extra></extra>'))
fig.add_trace(go.Bar(x = list(p4.index),y = list(p4['% New Positive']),
                     name='Recovery Phase 4',
                     hovertemplate='% Positive: %{y:.2%}<extra></extra>'))
fig.add_trace(go.Scatter(x=list(tests_wchd.index),y=list(tests_wchd['7 Day Avg PosRate']),                         
                         mode="lines",name='Seven Day Average',
                         hovertemplate='Current Avg: %{y:.2%}<extra></extra>'))
fig.update_layout(title='Postive Test Rate for COVID-19 in Warren County, IL',
                   xaxis = dict(
                       tickmode = 'array',
                       tickvals = list(tests_wchd.index)[0::7],
                       tickangle=45),                  
                   yaxis = dict(
                       range=(0,1),
                       tickmode = 'linear',
                       tick0=0, dtick=0.1),
                   colorway=px.colors.qualitative.Safe,
                   xaxis_showgrid=False, 
                   yaxis_showgrid=False,
                   legend=dict(
                       orientation="h",
                       yanchor="bottom",
                       y=1.02,
                       xanchor="right",
                       x=1))
                   
fig.update_layout(hovermode="x unified")

poscases_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('WC-PosRate-Start_to_Aug-DIV.txt','w') as f:
    f.write(poscases_div)
    f.close()
plot(fig,filename='WC-PosRate-Start_to_Aug.html')



#%%

# Daily Test Results

fig = go.Figure()
fig.add_trace(go.Bar(x = list(tests_wchd.index),y = list(tests_wchd['New Positive']),
                     name='Positive Tests',
                     hovertemplate = 'Positive: %{y}<extra></extra>'))
fig.add_trace(go.Bar(x = list(tests_wchd.index),y = list(tests_wchd['New Negative']),
                     name='Negative Tests',
                     hovertemplate = 'Negative: %{y}<extra></extra>'))
fig.update_layout(title='Daily Test Results for COVID-19 in Warren County, IL',
                   xaxis = dict(
                       tickmode = 'array',
                       tickvals = list(tests_wchd.index)[0::7],
                       tickangle=45),                  
                   yaxis = dict(
                       tickmode = 'linear',
                       tick0=0, dtick=10,
                       ),
                   colorway=px.colors.qualitative.Set1,
                   xaxis_showgrid=False, 
                   yaxis_showgrid=False,
                   barmode='stack',
                   legend=dict(
                       orientation="h",
                       yanchor="bottom",
                       y=1.02,
                       xanchor="right",
                       x=1))
                   
fig.update_layout(hovermode="x unified")

tests_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('WC-Tests-Start_to_Aug-DIV.txt','w') as f:
    f.write(tests_div)
    f.close()
plot(fig,filename='WC-Tests-Start_to_Aug.html')


#%%

# Cummulative Test Results

fig = go.Figure()
fig.add_trace(go.Bar(x = list(tests_wchd.index),y = list(tests_wchd['Total Positive']),
                     name='Positive Tests',
                     hovertemplate = 'Positive: %{y}<extra></extra>'))
fig.add_trace(go.Bar(x = list(tests_wchd.index),y = list(tests_wchd['Total Negative']),
                     name='Negative Tests',
                     hovertemplate = 'Negative: %{y}<extra></extra>'))
fig.update_layout(title='Cumulative Test Results for COVID-19 in Warren County, IL',
                   xaxis = dict(
                       tickmode = 'array',
                       tickvals = list(tests_wchd.index)[0::7],
                       tickangle=45),                  
                   yaxis = dict(
                       tickmode = 'linear',
                       tick0=0, dtick=100,
                       ),
                   colorway=px.colors.qualitative.Set1,
                   xaxis_showgrid=False, 
                   yaxis_showgrid=False,
                   barmode='stack',
                   legend=dict(
                       orientation="h",
                       yanchor="bottom",
                       y=1.02,
                       xanchor="right",
                       x=1))
                   
fig.update_layout(hovermode="x unified")

tottests_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('WC-TotalTests-Start_to_Aug-DIV.txt','w') as f:
    f.write(tottests_div)
    f.close()
plot(fig,filename='WC-TotalTests-Start_to_Aug.html')

#%%

# Case Status Stacked Bars

fig = go.Figure()
fig.add_trace(go.Bar(x = list(tests_wchd.index),y = list(tests_wchd['Active Cases']),
                     name='Active Cases',
                     hovertemplate = 'Active: %{y}<extra></extra>'))
fig.add_trace(go.Bar(x = list(tests_wchd.index),y = list(tests_wchd['Recoveries']),
                     name='Symptoms Resolved',
                     hovertemplate = 'Resolved: %{y}<extra></extra>'))
fig.update_layout(title='Status of COVID-19 Cases in Warren County, IL',
                   xaxis = dict(
                       tickmode = 'array',
                       tickvals = list(tests_wchd.index)[0::7],
                       tickangle=45),                  
                   yaxis = dict(
                       tickmode = 'linear',
                       tick0=0, dtick=10,
                       ),
                   colorway=px.colors.qualitative.Set1,
                   xaxis_showgrid=False, 
                   yaxis_showgrid=False,
                   barmode='stack',
                   legend=dict(
                       orientation="h",
                       yanchor="bottom",
                       y=1.02,
                       xanchor="right",
                       x=1),
                   hovermode="x unified"
                   )
                   
status_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('WC-CaseStatus-Start_to_Aug-DIV.txt','w') as f:
    f.write(status_div)
    f.close()
plot(fig,filename='WC-CaseStatus-Start_to_Aug.html')


#%%

# Demographics Stacked Bars

fig = go.Figure()

fig.add_trace(go.Bar(x=totals[totals['sex']=='Male']['age'],
                     y=totals[totals['sex']=='Male']['cases'],
                     name = 'Male'))
fig.add_trace(go.Bar(x=totals[totals['sex']=='Female']['age'],
                     y=totals[totals['sex']=='Female']['cases'],
                     name = 'Female'))
fig.update_layout(title='COVID-19 Demographics in Warren County, IL<br>April 2020 through July 2020',                   
                   colorway=px.colors.qualitative.Vivid,
                   xaxis_showgrid=False, 
                   yaxis_showgrid=False,
                   barmode='stack',
                   legend=dict(
                       orientation="h",
                       yanchor="bottom",
                       y=1.02,
                       xanchor="right",
                       x=1),
                   hovermode="x unified",
                   yaxis = dict(
                       tickmode = 'linear',
                       tick0 = 0,
                       dtick = 5)    
                   )

demo_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('WC-Demographics-Start_to_Aug-DIV.txt','w') as f:
    f.write(demo_div)
    f.close()
plot(fig,filename='WC-Demographics-Start_to_Aug.html')


#%%

# map with total cases as of 7/31

d = cvdv.prep_for_animate(aoi.iloc[:, [0,1,2,-1]])
cnames = cvdv.get_fips_dict(aoi)
d['County'] = d['fips'].apply( lambda f : cnames[f] )

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
                  title="Total Confirmed COVID-19 Cases as of 7/31/2020")

totmap_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('Region-Map-Total-Start_to_Aug-DIV.txt','w') as f:
    f.write(totmap_div)
    f.close()
plot(fig,filename='Region-Map-Total-Start_to_Aug.html')

#%%

# Taking a Regional Look

reg_total = aoi_daily.iloc[:,3:].sum().to_frame().transpose()
dates = list(reg_total.columns)
reg_total['County Name'] = 'Local Region'
reg_total['State'] = 'IL & IA'
reg_total['StateFIPS'] = 0 
reg_total = reg_total[['County Name', 'State', 'StateFIPS'] + dates]

reg_7day = cvda.to_sevenDayAvg(reg_total)

day = cvdv.plot_prep(cvdp.prune_data(reg_total))
day['Phase'] = day.index.to_series().apply(which_phase)
p2 = day[ day['Phase'] == 'Phase 2']
p3 = day[ day['Phase'] == 'Phase 3']
p4 = day[ day['Phase'] == 'Phase 4']

avg=cvdv.plot_prep(cvdp.prune_data(reg_7day))

#%%


# Region - Total Cases, Colored by Phase

fig = go.Figure()
fig.add_trace(go.Bar(x = list(p2.index),y = list(p2.iloc[:,0]),
                     name='Recovery Phase 2',
                     hovertemplate='New Cases: %{y}<extra></extra>'))
fig.add_trace(go.Bar(x = list(p3.index),y = list(p3.iloc[:,0]),
                     name='Recovery Phase 3',
                     hovertemplate='New Cases: %{y}<extra></extra>'))
fig.add_trace(go.Bar(x = list(p4.index),y = list(p4.iloc[:,0]),
                     name='Recovery Phase 4',
                     hovertemplate='New Cases: %{y}<extra></extra>'))
fig.add_trace(go.Scatter(x=list(avg.index),y=list(avg.iloc[:,0]),                         
                         mode="lines",name='Seven Day Average',
                         hovertemplate='Current Avg: %{y:.2f}<extra></extra>'))
fig.update_layout(title='Daily Confirmed Cases of COVID-19 in Region',                  
                  xaxis = dict(
                      tickmode = 'array',
                      tickvals = list(day.index)[0::7],
                      tickangle=45),                  
                  yaxis = dict(
                      range=(-0.1,day.iloc[:,0].max()+.1),
                      tickmode = 'linear',
                      tick0=0, dtick=25),   
                  colorway=px.colors.qualitative.Safe,
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
with open('Region-NewCases-Start_to_Aug-DIV.txt','w') as f:
    f.write(newcases_div)
    f.close()
plot(fig,filename='Region-NewCases-Start_to_Aug.html')

#%%

# map with total cases per 100000 as of 7/31

d = cvdv.prep_for_animate(cvda.to_for100k(aoi.iloc[:, [0,1,2,-1]],
                                          population))
cnames = cvdv.get_fips_dict(aoi)
d['County'] = d['fips'].apply( lambda f : cnames[f] )

fig = go.Figure(go.Choroplethmapbox(geojson=counties, 
                                    locations= d['fips'],
                                    z = d['Cases'],
                                    text = d['County'],
                                    colorscale="rdylgn_r",
                                    marker_opacity = 0.2,
                                    hovertemplate='%{text}<br>Total Cases per 100000: %{z}<extra></extra>'))
fig.update_layout(mapbox_style='streets', mapbox_accesstoken=MB_TOKEN,                  
                  mapbox_zoom = 6,
                  mapbox_center = {'lon':-89.8130, 'lat': 41.0796},
                  title="Total Confirmed COVID-19 Cases per 100,000 people as of 7/31/2020")

totmap_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('Region-Map-NormedTotal-Start_to_Aug-DIV.txt','w') as f:
    f.write(totmap_div)
    f.close()
plot(fig,filename='Region-Map-NormedTotal-Start_to_Aug.html')

#%%

# daily actual moving bars

allofit = cvdp.prune_data(aoi_daily)
fig  = cvdv.animated_bars(allofit,len(allofit.columns)-2,
                          "Daily COVID-19 Cases by County")
dailybars_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('Region-Bars-Start_to_Aug-DIV.txt','w') as f:
    f.write(dailybars_div)
    f.close()
plot(fig,filename='Region-Bars-Start_to_Aug.html')

#%%

# daily per 100,000 moving bars

allofit = cvdp.prune_data(aoi_normed_daily)
fig  = cvdv.animated_bars(allofit,len(allofit.columns)-2,
                          "Daily COVID-19 Cases per 100,000 by County")
dailybars_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('Region-BarsNormed-Start_to_Aug-DIV.txt','w') as f:
    f.write(dailybars_div)
    f.close()
plot(fig,filename='Region-BarsNormed-Start_to_Aug.html')

#%%

# daily Seven Day Average per 100,000

allofit = cvdp.prune_data(aoi_nd_7day)
fig  = cvdv.animated_bars(allofit,len(allofit.columns)-2,
                          "Seven Day Average of COVID-19 Cases per 100,000 by County")
dailybars_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('Region-BarsNormed7Day-Start_to_Aug-DIV.txt','w') as f:
    f.write(dailybars_div)
    f.close()
plot(fig,filename='Region-BarsNormed7Day-Start_to_Aug.html')


#%%

days = 7 #len(allofit.columns)-2
fig = cvdv.animate_per100k(allofit,days,'Seven Day Average New Cases per 100000')
plot(fig)