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
    
   
# tag recovery phase
tests_wchd['Phase'] = tests_wchd.index.map(which_phase)
# tag for day of the week
DAY_OF_WEEK = {0:'Monday',1:'Tuesday',2:'Wednesday',3:'Thursday',4:'Friday',
               5:'Saturday',6:'Sunday'}
tests_wchd['DayOfWeek'] = tests_wchd.index.map(lambda d: d.dayofweek)

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

# Daily Pos Rate with Avg and Regional Avg

threeweeks = tests_wchd.iloc[-21:,:]
regrate =  threeweeks[ threeweeks['Region 2 pos rate'] > 0 ]

fig = go.Figure()
fig.add_trace(go.Bar(x = list(threeweeks.index),y = list(threeweeks['% New Positive']),
                     name='Postive Rate',
                     hovertemplate='% Positive: %{y:.2%}<extra></extra>'))
fig.add_trace(go.Scatter(x=list(threeweeks.index),y=list(threeweeks['7 Day Avg PosRate']),                         
                         mode="lines",name='Seven Day Average',
                         hovertemplate='Current Avg: %{y:.2%}<extra></extra>'))
fig.add_trace(go.Scatter(x=list(regrate.index),y=list(regrate['Region 2 pos rate']),                         
                         mode="lines",name='Region 2 Seven Day Average',
                         hovertemplate='Regional Avg: %{y:.2%}<extra></extra>'))
fig.update_layout(title='Postive Test Rate for COVID-19 in Warren County, IL<br>' + 
                  str(threeweeks.index[0])[:10] + ' to ' + str(threeweeks.index[-1])[:10],
                   xaxis = dict(
                       tickmode = 'array',
                       tickvals = list(threeweeks.index[[0,6]])+list(threeweeks.index[-7:]),
                       tickangle=45),                  
                   yaxis = dict(
                       range=(0,1),
                       tickmode = 'linear',
                       tick0=0, dtick=0.1,
                       tickformat = '.0%'),
                   colorway=px.colors.qualitative.Set1,
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
with open('WC-PosRate-ThreeWeek-DIV.txt','w') as f:
    f.write(poscases_div)
    f.close()
plot(fig,filename='WC-PosRate-ThreeWeek.html')



#%%

# Daily Test Results
max_tests = tests_wchd['New Tests'].max()

fig = go.Figure()
fig.add_trace(go.Bar(x = list(threeweeks.index),y = list(threeweeks['New Positive']),
                     name='Positive Tests',
                     hovertemplate = 'Positive: %{y}<extra></extra>'))
fig.add_trace(go.Bar(x = list(threeweeks.index),y = list(threeweeks['New Negative']),
                     name='Negative Tests',
                     hovertemplate = 'Negative: %{y}<extra></extra>'))
fig.update_layout(title='Daily Test Results for COVID-19 in Warren County, IL<br>' +
                  str(threeweeks.index[0])[:10] + ' to ' + str(threeweeks.index[-1])[:10],
                   xaxis = dict(
                       tickmode = 'array',
                       tickvals = list(threeweeks.index[[0,6]]) + list(threeweeks.index[-7:]),
                       tickangle=45),               
                   yaxis = dict(
                       tickmode = 'linear',
                       tick0=0, dtick=10,                       
                       range=(0,max_tests+2),
                       title = 'Tests'                       
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
with open('WC-Tests-ThreeWeeks-DIV.txt','w') as f:
    f.write(tests_div)
    f.close()
plot(fig,filename='WC-Tests-ThreeWeeks.html')



#%%

# Case Status Stacked Bars

fig = go.Figure()
fig.add_trace(go.Bar(x = list(threeweeks.index),y = list(threeweeks['Active Cases']),
                     name='Active Cases',
                     hovertemplate = 'Active: %{y}<extra></extra>'))
fig.add_trace(go.Bar(x = list(threeweeks.index),y = list(threeweeks['Recoveries']),
                     name='Symptoms Resolved',
                     hovertemplate = 'Resolved: %{y}<extra></extra>'))
fig.update_layout(title='Status of COVID-19 Cases in Warren County, IL<br>' +
                  str(threeweeks.index[0])[:10] + ' to ' + str(threeweeks.index[-1])[:10],
                   xaxis = dict(
                       tickmode = 'array',
                       tickvals = list(threeweeks.index[[0,6]]) + list(threeweeks.index[-7:]),
                       tickangle=45),                  
                   yaxis = dict(
                       tickmode = 'linear',
                       tick0=0, dtick=10,
                       title = 'Cases'
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
with open('WC-CaseStatus-Threeweeks-DIV.txt','w') as f:
    f.write(status_div)
    f.close()
plot(fig,filename='WC-CaseStatus-Threeweeks.html')


#%%


totals_men = demo_wchd.iloc[-21:-7,:]['Male'].sum()
totals_women = demo_wchd.iloc[-21:-7,:]['Female'].sum()

totals = pd.DataFrame([],columns=['age','sex','cases'])
for a in totals_men.index:
    totals = totals.append(pd.Series([a,'Male',totals_men[a]],
                                     index=['age','sex','cases']),
                           ignore_index=True)
for a in totals_women.index:
    totals = totals.append(pd.Series([a,'Female',totals_women[a]],
                                     index=['age','sex','cases']),
                           ignore_index=True)

totals_prev2 = totals

totals_men = demo_wchd.iloc[-7:,:]['Male'].sum()
totals_women = demo_wchd.iloc[-7:,:]['Female'].sum()

totals = pd.DataFrame([],columns=['age','sex','cases'])
for a in totals_men.index:
    totals = totals.append(pd.Series([a,'Male',totals_men[a]],
                                     index=['age','sex','cases']),
                           ignore_index=True)
for a in totals_women.index:
    totals = totals.append(pd.Series([a,'Female',totals_women[a]],
                                     index=['age','sex','cases']),
                           ignore_index=True)

totals_thisweek = totals
    
#%%

# Demographics Stacked Bars

wk2start = str(threeweeks.index[0])[:10] 
wk2end = str(threeweeks.index[13])[:10] 
twstart = str(threeweeks.index[14])[:10] 
twend = str(threeweeks.index[-1])[:10] 
fig = make_subplots(rows=1,cols=2,
                    subplot_titles=(wk2start + ' to ' + wk2end,
                                    twstart + ' to ' + twend),
                    shared_yaxes=True)
fig.add_trace(go.Bar(x=totals_prev2[totals_prev2['sex']=='Male']['age'],
                     y=totals_prev2[totals_prev2['sex']=='Male']['cases'],
                     name = 'Male',
                     marker_color=(px.colors.qualitative.Vivid[0])),
              row=1,col=1)
fig.add_trace(go.Bar(x=totals_prev2[totals_prev2['sex']=='Female']['age'],
                     y=totals_prev2[totals_prev2['sex']=='Female']['cases'],
                     name = 'Female',
                     marker_color=(px.colors.qualitative.Vivid[1])),
              row=1,col=1)
fig.add_trace(go.Bar(x=totals_thisweek[totals_thisweek['sex']=='Male']['age'],
                     y=totals_thisweek[totals_thisweek['sex']=='Male']['cases'],
                     name = 'Male',
                     marker_color=(px.colors.qualitative.Vivid[0]),
                     showlegend=False),
              row=1,col=2)
fig.add_trace(go.Bar(x=totals_thisweek[totals_thisweek['sex']=='Female']['age'],
                     y=totals_thisweek[totals_thisweek['sex']=='Female']['cases'],
                     name = 'Female',
                     marker_color=(px.colors.qualitative.Vivid[1]),
                     showlegend=False),
              row=1,col=2)
fig.update_xaxes(showgrid=False,row=1,col=1)     
fig.update_xaxes(showgrid=False,row=1,col=2)
fig.update_yaxes(showgrid=False,row=1,col=1)     
fig.update_yaxes(showgrid=False,row=1,col=2)
fig.update_layout(title='COVID-19 Case Demographics in Warren County, IL<br>' +
                  str(threeweeks.index[0])[:10] + ' to ' + str(threeweeks.index[-1])[:10],                                      
                   barmode='stack',
                   legend=dict(
                       #orientation="h",
                       yanchor="bottom",
                       y=1.02,
                       xanchor="right",
                       x=1),
                   hovermode="x unified",
                   yaxis = dict(
                       tickmode = 'linear',
                       tick0 = 0,
                       dtick = 5,
                       title = "Individuals",
                       range=(0,max(totals_prev2.groupby('age').sum().max()[0],
                                    totals_thisweek.groupby('age').sum().max()[0])+2)    
                       )
                   )

demo_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('WC-Demographics-Threeweeks-DIV.txt','w') as f:
    f.write(demo_div)
    f.close()
plot(fig,filename='WC-Demographics-Threeweeks.html')


#%%


d = cvdv.prep_for_animate(aoi.iloc[:,[0,1,2,-1]])
d_off = cvdv.prep_for_animate(aoi.iloc[:,[0,1,2,-22]])
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
                  aoi.columns[-21] + ' to ' + aoi.columns[-1])

totmap_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('Region-Map-Total-Threeweeks-DIV.txt','w') as f:
    f.write(totmap_div)
    f.close()
plot(fig,filename='Region-Map-Threeweeks.html')

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
with open('Region-NewCases-ThreeWeeks-DIV.txt','w') as f:
    f.write(newcases_div)
    f.close()
plot(fig,filename='Region-NewCases-ThreeWeeks.html')

#%%

# map with total cases per 100000 as of 7/31

# map with total cases as of 7/31
d = cvdv.prep_for_animate(cvda.to_for100k(aoi.iloc[:,[0,1,2,-1]],population))
d_off = cvdv.prep_for_animate(cvda.to_for100k(aoi.iloc[:,[0,1,2,-22]],population))
cnames = cvdv.get_fips_dict(aoi)
d['County'] = d['fips'].apply( lambda f : cnames[f] )
d['Cases'] = d['Cases'] - d_off['Cases']


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
                  title="Total Confirmed COVID-19 Cases per 100,000 people for<br>"+
                  aoi.columns[-21] + ' to ' + aoi.columns[-1])

totmap_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('Region-Map-NormedTotal-ThreeWeeks-DIV.txt','w') as f:
    f.write(totmap_div)
    f.close()
plot(fig,filename='Region-Map-NormedTotal-ThreeWeeks.html')

#%%

# daily actual moving bars

allofit = cvdp.prune_data(aoi_daily)
fig  = cvdv.animated_bars(allofit,21,
                          "Daily COVID-19 Cases by County")
dailybars_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('Region-Bars-ThreeWeeks-DIV.txt','w') as f:
    f.write(dailybars_div)
    f.close()
plot(fig,filename='Region-Bars-ThreeWeeks.html')

#%%

# daily per 100,000 moving bars

allofit = cvdp.prune_data(aoi_normed_daily)
fig  = cvdv.animated_bars(allofit,21,
                          "Daily COVID-19 Cases per 100,000 by County")
dailybars_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('Region-BarsNormed-ThreeWeeks-DIV.txt','w') as f:
    f.write(dailybars_div)
    f.close()
plot(fig,filename='Region-BarsNormed-ThreeWeeks.html')

#%%

# daily Seven Day Average per 100,000

allofit = cvdp.prune_data(aoi_nd_7day)
fig  = cvdv.animated_bars(allofit,21,
                          "Seven Day Average of COVID-19 Cases per 100,000 by County")
dailybars_div = plot(fig, include_plotlyjs=False, output_type='div')
with open('Region-BarsNormed7Day-ThreeWeeks-DIV.txt','w') as f:
    f.write(dailybars_div)
    f.close()
plot(fig,filename='Region-BarsNormed7Day-THreeWeeks.html')


#%%

days = 21 #len(allofit.columns)-2
fig = cvdv.animate_per100k(allofit,days,'Seven Day Average New Cases per 100000')
plot(fig)