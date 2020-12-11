#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  7 12:31:03 2020

@author: jlmayfield
"""

import pandas as pd

import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot
from plotly.subplots import make_subplots

import cvdataprep as cvdp
import cvdataanalysis as cvda

#%%

population, actuals, deaths = cvdp.loadusafacts()
actuals = cvdp.prepusafacts(actuals, deaths)

#%%

def getCountyActuals(fips,usafdata=actuals,population=population):
    df = usafdata.loc[(slice(None),slice(None),fips),:]
    df = cvda.expandUSFData(df, population)
    statefips = df.index.get_level_values(1).unique()[0]
    df = df.loc[(slice(None),statefips,fips)]
    firstcase = df['Total Positive'].ne(0).idxmax()
    firstsunday = firstcase - pd.Timedelta((firstcase.weekday()+1)%7,unit='D')
    return df.loc[firstsunday:]
    


def countyTotalGraph(data,name):
    ## total cases via usafacts.org
    tot = data['Total Positive'].max()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index,
                             y=data['Total Positive'],
                             mode='lines',
                             fill='tozeroy'))
    fig.update_layout(yaxis={'range':(0,tot+50)},
                      title="Total Cases in "+name)
    fname = 'graphics/'+name.replace(' ','_')+'_usafacts_total.html'
    plot(fig,filename=fname)

def countyTotalGraphPer100k(data,name):
    ## total cases via usafacts.org
    tot = data['Total Positive per 100k'].max()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index,
                             y=data['Total Positive per 100k'],
                             mode='lines',
                             fill='tozeroy'))
    fig.update_layout(yaxis={'range':(0,tot+50)},
                      title="Total Cases per 100,00 People in "+name)
    fname = 'graphics/'+name.replace(' ','_')+'_usafacts_totalp100k.html'
    plot(fig,filename=fname)

#%%

wcil_actual = getCountyActuals(17187)
kcil_actual = getCountyActuals(17095)

#countyTotalGraph(wcil_actual, 'Warren County')
#countyTotalGraph(kcil_actual, 'Knox County')
#countyTotalGraphPer100k(wcil_actual, 'Warren County')
#countyTotalGraphPer100k(kcil_actual, 'Knox County')



#%%


reported = ['report_2.5','report_25','report_50','report_75','report_97.5']
newtotal = ['total_2.5','total_25','total_50','total_75','total_97.5']
reff = ['Re_median','Re_2.5pct','Re_97.5pct','totalcases']

def readREffective(dates,scenes):
    def readone(d):
        projs = [None] * len(scenes)
        for i in range(len(scenes)):
            df = pd.read_csv(d+'R_effective.csv',
                             dtype={'FIPS':'int64'}) 
            df['scenario'] = scenes[i]
            df['date'] = d
            projs[i] = df
        projs = pd.concat(projs)
        projs = projs.set_index(['FIPS','scenario','date'])
        return projs.sort_index()            
    dir = '../COVID-19Projection/'
    dirs = [dir+'Projection_'+m+'/' for m in dates]    
    projs = [readone(d) for d in dirs]
    idxs = [p.index for p in projs]
    keeps_idx = [idxs[i].difference(idxs[i+1]) for i in range(0,len(idxs)-1)] +\
        [idxs[-1]]
    keeps = [projs[i].loc[keeps_idx[i]] for i in range(0,len(keeps_idx))]
    return pd.concat(keeps).sort_index()
    

def readLatest():
    def readone(case):
        df = pd.read_csv(dir+'Projection_'+case+'.csv',
                     #index_col='fips',
                     parse_dates=['Date'],
                     dtype={'fips':'int64'})
        df['scenario'] = case
        return df        
    dir = '../COVID-19Projection/LatestProjections/'
    cases = ['low','mid','high','nochange']
    projs = [readone(c) for c in cases]
    projs = pd.concat(projs)
    projs = projs.set_index(['fips','scenario','Date'])
    return projs.sort_index()

def readDataset(dates,scenes):
    def readone(d):
        projs = [None] * len(scenes)
        for i in range(len(scenes)):
            df = pd.read_csv(d+'Projection_'+scenes[i]+'.csv',
                           parse_dates=['Date'], dtype={'fips':'int64'}) 
            df['scenario'] = scenes[i]
            projs[i] = df
        projs = pd.concat(projs)
        projs = projs.set_index(['fips','scenario','Date'])
        return projs.sort_index()            
    dir = '../COVID-19Projection/'
    dirs = [dir+'Projection_'+m+'/' for m in dates]    
    projs = [readone(d) for d in dirs]
    idxs = [p.index for p in projs]
    keeps_idx = [idxs[i].difference(idxs[i+1]) for i in range(0,len(idxs)-1)] +\
        [idxs[-1]]
    keeps = [projs[i].loc[keeps_idx[i]] for i in range(0,len(keeps_idx))]
    return pd.concat(keeps).sort_index()


#%%

# Load Projections 

# not currently used but fit within the current modeling 
oldnames = ['October1','October4','October8',
            'October11','October15']

# 5_1xhold,5_2xhold
prev_models = ['October18','October22','October25',
               'October29','November1','November5','November8']            
current_models = ['November12','November15','November19',
                  'November22','November29',
                  'December3','December06','December10'] #5_1xbeta,5_2xbeta      
cur = oldnames[-1]

# Most recent models
curr = readDataset(current_models,['5_1xbeta','5_2xbeta','season4','nochange'] )
# previous set of models. Some are missing season4 ?
prev = readDataset(prev_models, ['5_1xhold','5_2xhold','nochange'])   
#%%

reffect = readREffective(current_models, reff)

#%%

def totalsProjections(actual,projection,name):
    lowertotal = projection['report_2.5'].cumsum().rename('report_2.5_total')
    uppertotal = projection['report_97.5'].cumsum().rename('report_97.5_total')
    medtotal = projection['report_50'].cumsum().rename('report_50_total')
    start_proj = projection.index[0]
    tot_at_start = actual.loc[start_proj-pd.Timedelta(1,unit='D')]['Total Positive']
    proj_max_total = uppertotal[-1] + tot_at_start
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=actual.index,
                             y=actual['Total Positive'],
                             mode='lines',
                             fill=None,
                             line_color=px.colors.sequential.Blues[5],
                             name = 'Actual Case Totals',
                             showlegend=False
                             ))
    fig.add_trace(go.Scatter(x=lowertotal.index,
                             y=lowertotal+tot_at_start,
                             mode='lines',
                             fill=None,
                             line_color=px.colors.sequential.Blues[3],
                             showlegend=False
                             ))
    fig.add_trace(go.Scatter(x=uppertotal.index,
                             y=uppertotal+tot_at_start,
                             mode='lines',
                             fill='tonexty',
                             line_color=px.colors.sequential.Blues[3],
                             showlegend=False                         
                             ))
    fig.add_trace(go.Scatter(x=medtotal.index,
                             y=medtotal+tot_at_start,
                             mode='lines',
                             fill=None,
                             line_color=px.colors.sequential.Blues[4],
                             showlegend=False                         
                             ))
    fig.update_layout(yaxis={'range':(0,proj_max_total+50)},
                      title="Total Case Projections for " + name)
    fname = 'graphics/'+name.replace(' ','_')+'_totalprojections.html'
    plot(fig,filename=fname)
    

#%%

# Total Cases with Projections
wcil_curr = curr.loc[17187,'5_2xbeta']
kcil_curr = curr.loc[17095,'5_2xbeta']

totalsProjections(wcil_actual, wcil_curr, 'Warren County')
totalsProjections(kcil_actual, kcil_curr, 'Knox County')


#%%


# last day in actual data set
end_actual = wcil_actual.index[-1]
# where to cutoff projection data set (+2 weekes of projects)
end_proj = end_actual + pd.to_timedelta(14,unit='D')

# WC, IL projections
wcil_proj = curr.loc[17187]
wcil_5x2 = wcil_proj.loc['5_2xbeta']
# older
old = prev.loc[17187,'5_2xhold']
keep = old.index.difference(wcil_5x2.index)
wcil_5x2 = pd.concat([old.loc[keep],wcil_5x2])

proj = wcil_5x2.loc[:end_proj]
# actual reported numbers from usafacts
fig = go.Figure()
fig.add_trace(go.Scatter(x=proj.index,
                         y=proj['report_2.5'],
                         mode='lines',
                         name='2.5 percentile',
                         showlegend=False,
                         fill=None,
                         line_color=px.colors.sequential.Blues[3],
                         opacity=0.25
                         ))
fig.add_trace(go.Scatter(x=proj.index,
                         y=proj['report_25'],
                         fill='tonexty',
                         mode='lines',
                         name='25th percentile',
                         showlegend=False,
                         line_color=px.colors.sequential.Blues[3],
                         opacity=0.5
                         ))
fig.add_trace(go.Scatter(x=proj.index,
                         y=proj['report_25'],
                         fill=None,
                         mode='lines',
                         name='25th percentile',
                         showlegend=False,
                         line_color=px.colors.sequential.Blues[6]
                         ))
fig.add_trace(go.Scatter(x=proj.index,
                         y=proj['report_75'],
                         fill='tonexty',
                         mode='lines',
                         name='75th percentile',
                         showlegend=False,
                         line_color=px.colors.sequential.Blues[6],
                         opacity=0.5
                         ))
fig.add_trace(go.Scatter(x=proj.index,
                         y=proj['report_97.5'],
                         fill='tonexty',
                         mode='lines',
                         name='97.5 percentile',
                         showlegend=False,
                         line_color=px.colors.sequential.Blues[3],
                         opacity=0.25
                         ))                         

#fig.add_trace(go.Scatter(x=proj.index,
#                         y=proj['report_50'],                         
#                         mode='lines',
#                         name='50th percentile',
#                         line_color=px.colors.sequential.Blues[8],
#                         showlegend=False
#                         ))

act = wcil_actual[-31:]
fig.add_trace(go.Bar(x=act.index,
                         y=act['New Positive'],
                         name='New Cases',
                         marker_color=px.colors.sequential.Blues[5],
                         #mode='markers'
                         ))
fig.add_trace(go.Scatter(x=act.index,
                         y=act['7 Day Avg New Positive'],
                         name='7 Day Average',
                         line_color=px.colors.sequential.Blues[8]))
fig.update_layout(title="Number of Reported Cases per Day with Forecasts",
                  yaxis_range=(0,40),
                  xaxis_range=(act.index[0], proj.index[-1])
                  )
plot(fig,filename='graphics/wc_usafacts_daily.html')

#%%

