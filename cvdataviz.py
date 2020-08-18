#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  9 14:54:26 2020

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

import cvdataanalysis as cvda
    
MB_TOKEN = open(".mapbox_token").read()

#%%

def plot_prep(casedata):
    """
    Prepare case data for plotting as a line graph

    Parameters
    ----------
    casedata : DataFrame
        Case dataset. Assumed 3 columns of state/county/fips data followed by
        day-to-day data. 

    Returns
    -------
    bydate : DataFrame
        Date x County dataset suitable for line plotting. County fips codes
        are replaced by county name, state strings.

    """
    labels = {code : casedata.loc[code]['County Name'] +
              ', ' + casedata.loc[code]['State'] for code in casedata.index}
    bydate=casedata.iloc[:,3:].transpose()
    bydate.index = pd.to_datetime(bydate.index)
    bydate.columns = [labels[c] for c in bydate.columns]
    return bydate

def plot_timeseries(casedata,days,title):
    """
    Plot the days most recent dates worth of case data found in casedata dataset.
    Title is used as the plot's title. Provide more than 24 counties will 
    cause colors to cycle. The legend lists counties based on highest recorded
    cases. 

    Parameters
    ----------
    casedata : DataFrame
        Covid case dataset (3 columns of state/count/fips followed by day-to-day)
    days : int
        Number of days to plot
    title : str
        plot title

    Returns
    -------
    None.[str((f - pd.Timedelta(n,unit='D')).date()) for n in range(4,0,-1)]

    """
    d = plot_prep(casedata)
    cut = d.iloc[-1*days:]
    cut = cut[ cut.iloc[-1].sort_values(ascending=False).index ]
    ymax = max(35,cut.max().max())    
    fig = px.line(cut,
                  color_discrete_sequence=px.colors.qualitative.Dark24)
    fig.update_layout(title=title,
                      xaxis_title='Date',
                      yaxis_title='Cases (per 100000',
                      legend_title_text='',
                      yaxis=dict(range=[0,ymax]))
    fig.update_layout(hovermode="x unified")
    fig.update_traces(hovertemplate='<b>%{y}</b>')
    plot(fig)

def three_week_report(casedata,group_name):
    """
    Report the most recent three weeks of the given casedata and report as 
    a line graph exported as html. All the counties in the given data set
    will be aggregated into a 

    Parameters
    ----------
    casedata : DataFrame
        Covid case dataset (3 columns of state/count/fips followed by day-to-day).       

    Returns
    -------
    None.

    """
    pruned_cols = list(casedata.columns[:3]) + list(casedata.columns[-21:])
    pruned = casedata[pruned_cols]
    agg = pruned.iloc[:,3:].sum(axis=0).to_frame().transpose()
    dates = list(agg.columns)
    agg['County Name'] = group_name
    agg['State'] = ''
    agg['stateFIPS'] = -1
    agg = agg[['County Name','State','stateFIPS']+dates]
    
    r_7day = cvda.to_sevenDayAvg(agg)
    aoi_7day = cvda.to_sevenDayAvg(pruned)
    
    #
    withcounties = pd.concat([r_7day,aoi_7day])    
    d = plot_prep(withcounties)    
    d = d[ d.iloc[-1].sort_values(ascending=False).index ]
    #
    day1 = str(d.index[0])[:10]
    day21 = str(d.index[-1])[:10]
    
    ymax = max(35,d.max().max())    
    fig = px.line(d,
                  color_discrete_sequence=px.colors.qualitative.Dark24)
    fig.update_layout(title="Seven Day Average of New Covid Cases for "+ group_name +
                      "<br>" + day1 + ' to ' + day21,
                      xaxis_title='Date',
                      yaxis_title='Cases',
                      legend_title_text='',
                      yaxis=dict(range=[0,ymax]))
    fig.update_layout(hovermode="x unified")
    fig.update_traces(hovertemplate='<b>%{y}</b>')
    fig.add_trace()
    
    
    plot(fig,filename=group_name+'_'+day1+'_'+day21)

#%%
def get_day(casedata,date):
    counts = casedata[date]
    counts = counts.to_frame()
    counts.reset_index(level=0,inplace=True)
    counts = counts.rename(columns={date:'Cases','countyFIPS':'fips'})
    counts.update(counts['fips'].apply(str))
    return counts

def plot_map(day):
    fig = px.choropleth(day, geojson=counties, locations='fips', color='Cases',
                                               color_continuous_scale="Reds",
                                               range_color=(0, day['Cases'].max()),
                                               scope="usa",
                                               labels={'Cases':'Total Cases of Covid-19'})
    fig.update_geos(fitbounds="locations")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    plot(fig)


def prep_for_animate(casedata):
    dates = casedata.columns[3:]
    def f(d):
        day = get_day(casedata,d)
        day['Date'] = pd.to_datetime(d)
        return day
    counts = pd.concat([f(d) for d in dates],ignore_index=True)
    counts = counts.sort_values(by='Date')
    counts['Date'] = counts.Date.apply(lambda x: x.date()).apply(str) 
    return counts

def animate_per100k(casedata,numDays,casetype):    
    zmax = casedata.iloc[:,3:].max().max()
    d = prep_for_animate(casedata).iloc[numDays*-1*len(casedata):]
    fig = px.choropleth_mapbox(d, geojson=counties, locations='fips', color='Cases',
                               color_continuous_scale=[(0,'forestgreen'),
                                                       (1/zmax,'gold'),
                                                       (17.5/zmax,'darkorange'),
                                                       (30/zmax,'red'),
                                                       (1,'darkred')],
                               range_color= (0,zmax),                                                                        
                               labels={'Cases':casetype},
                               opacity = 0.25,                               
                               animation_frame= d.Date.astype(str),
                               hovertemplate = '%{animation_frame}<br>' +
                               casetype + ': %{z}<br>')                        
    fig.update_layout(mapbox_style='streets', mapbox_accesstoken=MB_TOKEN,                  
                      mapbox_zoom = 7.5,
                      mapbox_center = {'lon':-89.8130, 'lat': 41.0796})
    return fig

#%%

def get_fips_dict(casedata):
    return {str(i) : casedata.loc[i]['County Name'] +
            ', '+ casedata.loc[i]['State'] for i in casedata.index }    
    
def animated_bars(casedata,numDays,title):
    xmax=casedata.iloc[:,3:].max().max()
    names = get_fips_dict(casedata)
    d = prep_for_animate(casedata).iloc[numDays*-1*len(casedata):]
    d = d.replace(names)
    names = d['fips'].unique()    
    days = d['Date'].unique()
    cmap = {names[i] : px.colors.qualitative.Dark24[i%24] 
            for i in range(0,len(names))}   
    def case_to_text(curr):
        def get_text(val):                    
            return str(val) if isinstance(val,(int)) else str(round(val,2))         
        return ['<b>'+get_text(curr.loc[r]['Cases'])+'</b>' if curr.loc[r]['fips']=='Warren County, IL' else
                get_text(curr.loc[r]['Cases']) for r in curr.index ]
    # compute a single frame given the day. 
    def oneday_bar(day):
        theday = d[ d['Date'] == day].sort_values('Cases')              
        frm = go.Frame(
            data=go.Bar(x=theday['Cases'],y=theday['fips'],
                        text=case_to_text(theday),
                        textposition='outside',                        
                        marker_color = [cmap[c] for c in theday['fips']],
                        orientation='h'),
            name = day)
        return frm
    # compute slider step from day    
    def one_step(d):
        slider_step = {"args": [
            [d],
            {"frame": {"duration": 1500, "redraw": True},
             "mode": "immediate",
             "transition": {"duration": 1000}}
            ],
            "label": d,
            "method": "animate"}
        return slider_step
    bar_frames = [oneday_bar(d) for d in days]   
    slider_steps = [one_step(d) for d in days] 
    day1=d[d['Date']==days[0]].sort_values('Cases')
    fig = go.Figure(
        data = [go.Bar(x=day1['Cases'],y=day1['fips'],
                       text=case_to_text(day1),
                       textposition='outside',                       
                       marker_color = [cmap[c] for c in day1['fips']],
                       orientation='h')],
        layout = go.Layout(
            title={'text':title },
            #width=400,
            height=800,
            xaxis=dict(range=[0, xmax+5], autorange=False),
            updatemenus=[dict(type="buttons",
                              buttons=[dict(label="Play",
                                            method="animate",
                                            args=[None,
                                                  {"frame": {"duration": 1500, "redraw": True},
                                                   "fromcurrent": True}]),                                         
                                       dict(args=[[None], {"frame": {"duration": 0, "redraw": True},
                                                           "mode": "immediate",
                                                           "transition": {"duration": 0}}],
                                            label="Pause",
                                            method="animate")],                                                      
                              x=-0.25, 
                              xanchor="left",
                              y=-0.05,
                              yanchor="top",
                              direction='left',                              
                              )],
            sliders = [{"active": 0,
                       "yanchor": "top",
                       "xanchor": "left",
                       "currentvalue": {
                               "font": {"size": 20},
                               "prefix": "Date: ",
                               "visible": True,
                               "xanchor": "right"
                               },
                       "transition": {"duration": 250},                       
                       "len": 1,
                       "x": 0,
                       "y": 0,
                       "steps": slider_steps
                       }]
                ),
        frames=bar_frames        
        )    
    return fig