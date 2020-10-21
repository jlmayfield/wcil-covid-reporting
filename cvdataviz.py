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
from plotly.subplots import make_subplots




from urllib.request import urlopen
import json
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

import cvdataanalysis as cvda
    
MB_TOKEN = open(".mapbox_token").read()

#%%

# Colors Used to Indicate different levels of community spread
RISK_COLORS = {'Minimal':'whitesmoke','Moderate':'rgba(255,215,0,0.5)','Substantial':'rgba(205,92,92,0.5)'}

def style_casenum(cdata):
    """
    Style Actual and per 100k case numbers for tabluar output. Bold if the number
    indicates moderate or substantial community spread 

    Parameters
    ----------
    cdata : DataFrame
        Daily New Cases and Cases per 100k

    Returns
    -------
    list
        Formatted strings for each day as 'actual (per 100k)'

    """
    def val2txt(vals):
        act = vals['New Positive']
        p100k = vals['New Positive per 100k']
        text = "{:.0f} ({:.1f})".format(act,p100k)
        if p100k > 50:
            text = '<b>'+text+'</b>'
        return text            
    return [val2txt(cdata.loc[i]) for i in cdata.index]

# Like above but cases per 100k only
def stylecp100k_text(cp100k):
    def val2txt(val):
        if round(val) <= 50:
            return "{:.1f}".format(val)
        else:
            return "<b>{:.1f}<b>".format(val)
    return [val2txt(v) for v in cp100k]

def stylecp100k_cell(cp100k):
    """
    Determine cell color for case data based on cases per 100k

    Parameters
    ----------
    cp100k : Series
        Cases per 100k per day

    Returns
    -------
    list
        List of RISK_COLORS values

    """
    def val2color(val):
        if round(val) <= 50:
            return RISK_COLORS['Minimal']
        elif round(val) <= 100:
            return RISK_COLORS['Moderate']
        else:
            return RISK_COLORS['Substantial']
    return [val2color(v) for v in cp100k]


def styleprate_text(prates):
    def val2txt(val):
        if val <= .05:
            return "{:.1%}".format(val)
        else:
            return "<b>{:.1%}<b>".format(val)
    return [val2txt(v) for v in prates]

def styleprate_cell(prates):
    def val2color(val):
        if val <= .05:
            return RISK_COLORS['Minimal']
        elif val <= .08:
            return RISK_COLORS['Moderate']
        else:
            return RISK_COLORS['Substantial']
    return [val2color(v) for v in prates]


def stylecase_text(cases_streak):
    def val2txt(i):
        streak = cases_streak.loc[i][1]
        val = round(cases_streak.loc[i][0])
        chg = cases_streak.loc[i][2]
        if np.isinf(chg):
            return"{:<6} (+)".format(val)
        if np.isnan(chg):
            return"{:<6} (None)".format(val)
        elif streak < 2:
            return "{:<6} ({:+.1%})".format(val,chg)
        else:
            return "<b>{:<6} ({:+.1%})</b>".format(val,chg)
    return [val2txt(i) for i in cases_streak.index]

def stylecase_cell(cases_streak):
    def val2color(val):
        if val < 2:
            return RISK_COLORS['Minimal']
        else:
            return "rgba(255, 140, 0, 0.5)"
    return [val2color(v) for v in cases_streak]



#%%

def get_fips_dict(fips,pop):
    return {i : pop.loc[i]['County Name'] +
            ', '+ pop.loc[i]['State'] for i in fips }    
    
def animated_bars(casedata,numDays,title,pop):
    colname = casedata.columns[0]
    lastday = casedata.index.get_level_values('date').unique()[-1]
    firstday = lastday - pd.Timedelta(numDays+1,unit='D')    
    xmax=casedata.max()[0] #all time max
    fips = list(casedata.index.get_level_values('countyFIPS').unique())
    names = get_fips_dict(fips,pop)    
    d = casedata.loc[firstday:,:,:].reset_index().set_index('date')
    d = d.replace(names)
    names = d['countyFIPS'].unique()    
    days = d.index.unique()
    cmap = {names[i] : px.colors.qualitative.Dark24[i%24] 
            for i in range(0,len(names))}   
    def case_to_text(curr):
        def get_text(val):                    
            return str(val) if isinstance(val,(int)) else str(round(val,2))         
        return ['<b>'+get_text(curr.loc[r][colname])+'</b>' if r == 17187 else
                get_text(curr.loc[r][colname]) for r in curr.index ]
    # compute a single frame given the day. 
    def oneday_bar(day):
        theday = d.loc[day].sort_values(colname).set_index('countyFIPS')              
        frm = go.Frame(
            data=go.Bar(x=theday[colname],
                        y=theday.index,
                        text=case_to_text(theday),
                        textposition='outside',                        
                        marker_color = [cmap[c] for c in theday.index],
                        orientation='h'),
            name = str(day.date()))
        return frm
    # compute slider step from day    
    def one_step(d):
        d = str(d.date())
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
    day1=d.loc[firstday].sort_values(colname).set_index('countyFIPS')
    fig = go.Figure(
        data = [go.Bar(x=day1[colname],
                       y=day1.index,
                       text=case_to_text(day1),
                       textposition='outside',                       
                       marker_color = [cmap[c] for c in day1.index],
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

#%%

def wcposratereport(wchd_data):
    '''
    Produce the Postive Test Rate Report for the Warren County Data. This report
    shows the past three weeks with an empahsis on the last week. The dates for 
    the past week are listed with only one day per week show prior to that. 

    Parameters
    ----------
    wchd_data : DataFrame
        Assumed to be the warren county report. TODO:DOCUMENT STRUCTURE NEEDED

    Returns
    -------
    fig : Figure
        The report graphic 

    '''    
    threeweeks = wchd_data.iloc[-21:,:]
    regrate =  threeweeks[ threeweeks['Region 2 Pos Rate'] > 0 ]    
    colors = ["lightcoral" if p < 0.08 else "crimson"
              for p in threeweeks['% New Positive']]
    fig = go.Figure()
    fig.add_trace(go.Bar(x = list(threeweeks.index),
                         y = list(threeweeks['% New Positive']),
                         name='Postive Rate',
                         marker_color=colors,showlegend=False,
                         hovertemplate='% Positive: %{y:.2%}<extra></extra>'))
    fig.add_trace(go.Scatter(x=list(threeweeks.index),
                             y=list(threeweeks['7 Day Avg % New Positive']),                         
                             mode="lines",name='Seven Day Average',
                             line=dict(color='gold'),
                             hovertemplate='Current Avg: %{y:.2%}<extra></extra>'))
    fig.add_trace(go.Scatter(x=list(regrate.index),
                             y=list(regrate['Region 2 Pos Rate']),                         
                             mode="lines",name='Region 2 Seven Day Average',
                             hovertemplate='Regional Avg: %{y:.2%}<extra></extra>',
                             line=dict(dash='dash',color='royalblue')))
    fig.update_layout(title='Postive Test Rate for COVID-19 in Warren County, IL<br>' + 
                      str(threeweeks.index[0])[:10] + ' to ' + str(threeweeks.index[-1])[:10],
                       xaxis = dict(
                           tickmode = 'array',
                           tickvals = list(threeweeks.index[[0,6]])+list(threeweeks.index[-7:]),
                           tickangle=45),                  
                       yaxis = dict(
                           range=(0,0.5),
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
    return fig

#%%

def wcdailytestsreport(wchd_data):
    '''
    

    Parameters
    ----------
    wchd_data : TYPE
        DESCRIPTION.

    Returns
    -------
    fig : TYPE
        DESCRIPTION.

    '''
    threeweeks = wchd_data.iloc[-21:,:]
    max_tests = threeweeks['New Tests'].max()
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
                           range=(0,max(80,max_tests+2)),
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
    return fig

#%%

def wccasestatusreport(wchd_data):
    threeweeks = wchd_data.iloc[-21:,:]
    fig = go.Figure()
    fig.add_trace(go.Bar(x = list(threeweeks.index),y = list(threeweeks['Active Cases']),
                         name='Active Cases',marker_color=px.colors.qualitative.Set1[0],
                         hovertemplate = 'Active: %{y}<extra></extra>'))
    fig.add_trace(go.Bar(x = list(threeweeks.index),y = list(threeweeks['Total Deaths']),
                         name='Deaths',marker_color=px.colors.qualitative.Set1[3],
                         hovertemplate = 'Deaths: %{y}<extra></extra>'))
    fig.add_trace(go.Bar(x = list(threeweeks.index),y = list(threeweeks['Total Recovered']),
                         name='Symptoms Resolved',marker_color=px.colors.qualitative.Set1[1],
                         hovertemplate = 'Resolved: %{y}<extra></extra>'))    
    fig.update_layout(title='Status of COVID-19 Cases in Warren County, IL<br>' +
                      str(threeweeks.index[0])[:10] + ' to ' + str(threeweeks.index[-1])[:10],
                       xaxis = dict(
                           tickmode = 'array',
                           tickvals = list(threeweeks.index[[0,6]]) + list(threeweeks.index[-7:]),
                           tickangle=45),                  
                       yaxis = dict(
                           tickmode = 'linear',
                           tick0=0, dtick=20,
                           title = 'Cases'
                           ),
                       #colorway=px.colors.qualitative.Set1,
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
    return fig

#%%

def wcdemoreport(wchd_demo_data):
    totals_prev2 = cvda.demographic_totals(wchd_demo_data,start=21,end=7)
    totals_thisweek = cvda.demographic_totals(wchd_demo_data)
    wk2start = str(wchd_demo_data.index[-21])[:10] 
    wk2end = str(wchd_demo_data.index[-8])[:10] 
    twstart = str(wchd_demo_data.index[-7])[:10] 
    twend = str(wchd_demo_data.index[-1])[:10] 
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
                      wk2start + ' to ' + twend,                                      
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
                           dtick = 2,
                           title = "Individuals",
                           range=(0,max(totals_prev2.groupby('age').sum().max()[0],
                                        totals_thisweek.groupby('age').sum().max()[0])+2)    
                           )
                       )    
    return fig