#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 28 10:15:33 2021

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


# site table margins
margs = go.layout.Margin(l=0, #left margin
                         r=0, #right margin
                         b=35, #bottom margin
                         t=25  #top margin
                         )      

#%%

dist = pd.read_csv('sf12010countydistancemiles.csv',
                   dtype={'county1':np.int64,
                          'mi_to_county':np.float64,
                          'county2':np.int64})

def countiesWithin(fips,d):
    county = dist[(dist['county1'] == fips) & (dist['mi_to_county'] <= d)]
    return pd.Index(county['county2'])

#%%

cinfo = pd.read_csv('IDPH_Totals/IDPH_County_Info.csv',
                             header=[0],index_col=0).set_index('County')

#names = cinfo[~cinfo['County'].isin(['Illinois','Unknown','Out Of State'])]
#%%

counties = cvdp.IDPHDataCollector.getCountyData()
nopop = counties[-2:].set_index('County')
counties = counties[:-2].set_index('County')

populations, _, _ = cvdp.loadusafacts()

IL = populations[populations['State']=='IL']
IL = IL[IL.index != 0]
names = IL['County Name'].apply(lambda n : n[:-7]).reset_index().set_index('County Name')
names = names['countyFIPS'].to_dict()
names['Illinois'] = 17
names['Chicago'] = 171

t = pd.Series(names).astype(int)
t.name = 'countyFIPS'

counties = pd.concat([counties,t],axis=1)
counties = counties.rename(columns={'Population':'population'})
c = counties.reset_index().set_index('countyFIPS').rename(columns={'index':'Name'})
#%%
# Scrape all IL counties for totals
#cvdp.IDPHDataCollector.writeTotalsAll(counties.index)
# Gets all the county data. Only changes if population counts are 
#  updated
#cvdp.IDPHDataCollector.writeCountyData(counties.index)

#cvdp.IDPHDataCollector.writeTotalsAll(nopop.index)-
#cvdp.IDPHDataCollector.writeCountyData(nopop.index)


#%%

def firstCase(df):
    fstidx = (df > 0).idxmax()
    if fstidx is tuple:
        return fstidx[0]
    else:
        return fstidx    

def totfilename(county):
    return 'IDPH_DAILY_'+county.upper()+'.csv'

def loadAndExpand(cname):
    if cname in names.keys():
        fips = names[cname]
    else:
        fips = cname
    tots = pd.read_csv('IDPH_Totals/'+totfilename(cname),
                        header=[0],index_col=0,
                        parse_dates=True)
    pop = counties.loc[cname]['population']
    tots.loc[:,'countyFIPS'] = fips
    tots.loc[:,'stateFIPS'] = 17
    tots = tots.reset_index().set_index(['date','stateFIPS','countyFIPS'])
    expanded = cvda.expandIDPHDaily(tots,pop) 
    expanded = pd.concat([expanded,
                           cvda._per100k(expanded['New Vaccinated'], c),
                           cvda._per100k(expanded['7 Day Avg New Vaccinated'], c)],
                          axis=1)                           
    return expanded.reset_index()

#%%

# build IL wide stats!
allofit = pd.concat([loadAndExpand(f) for f in counties.index]).set_index(['date','stateFIPS','countyFIPS']).sort_index()   
outTots = cvdp.IDPHDataCollector.getNonCountyData()

#%%

lastday = allofit.index[-1][0]
lastvac = lastday - pd.Timedelta(1,'D')

#%%
vacdata = allofit[['Total Vaccinated','% Vaccinated','7 Day Avg New Vaccinated']].loc[lastvac,:,:]
vacdata = vacdata.reset_index().drop(['stateFIPS','date'],axis=1).set_index('countyFIPS')
statewide = vacdata.loc['17']
vacdata = vacdata[vacdata.index != '17']
#%%

vacdata.loc[:,'% Vac Rank'] = vacdata['% Vaccinated'].rank(ascending=False,method='dense')

#%%
summary = vacdata['% Vaccinated'].describe()
fig = px.histogram(vacdata,x='% Vaccinated',
                   nbins=int(np.ceil((summary['max']-summary['min'])/.02))
                   )
fig.update_layout(bargap=0.1)
plot(fig)

#%%

# 7 Day Avg New Cases with Total Vaccinated 
df = allofit.loc[:,17,17187][['7 Day Avg New Positive',
                              'Total Vaccinated'
                              ]]
df = df.loc[firstCase(df['7 Day Avg New Positive']):]


fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=df.index, y=df['7 Day Avg New Positive'],
               name="New Cases (7 day avg)"),               
    secondary_y=False,
)

fig.add_trace(
    go.Scatter(x=df.index, y=df['Total Vaccinated'],
               name="Total Persons Vaccinated"),
    secondary_y=True,
)

# Add figure title
fig.update_layout(
    title_text="New Cases and Vaccinations",
    #margin = margs,
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01),
    height = 420
)

# Set x-axis title
fig.update_xaxes(title_text="Date")

ly_max = df['7 Day Avg New Positive'].max()
ry_max = df['Total Vaccinated'].max()
# Set y-axes titles
fig.update_yaxes(title_text="<b>New Cases (7 day avg)</b>", 
                 range = (0,ly_max+5),
                 secondary_y=False)
fig.update_yaxes(title_text="<b>Total Vaccinations</b>", 
                 range = (0,ry_max+20),
                 #tickformat = ',.0%',
                 secondary_y=True)
fig.update_layout(hovermode='x unified')

#casetrends = plot(fig, include_plotlyjs=False, output_type='div')
plot(fig)

#%%


# 7 Day Avg New Cases with Vaccinated (7 Day avg or Total)
df = allofit.loc[:,17,17187][['7 Day Avg New Vaccinated',
                              'Total Vaccinated'
                              ]]
df = df.loc[firstCase(df['7 Day Avg New Vaccinated']):]

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=df.index, y=df['7 Day Avg New Vaccinated'],
               name="New Vaccinations (7 day avg)"),               
    secondary_y=False,
)

fig.add_trace(
    go.Scatter(x=df.index, y=df['Total Vaccinated'],
               name="Total Persons Vaccinated"),
    secondary_y=True,
)

# Add figure title
fig.update_layout(
    title_text="New and Total Vaccinations",
    #margin = margs,
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01),
    height = 420
)

# Set x-axis title
fig.update_xaxes(title_text="Date")

ly_max = df['7 Day Avg New Vaccinated'].max()
ry_max = df['Total Vaccinated'].max()
# Set y-axes titles
fig.update_yaxes(title_text="<b>New Vaccinations (7 day avg)</b>", 
                 range = (0,ly_max+5),
                 secondary_y=False)
fig.update_yaxes(title_text="<b>Total Vaccinations</b>", 
                 range = (0,ry_max+20),
                 #tickformat = ',.0%',
                 secondary_y=True)
fig.update_layout(hovermode='x unified')

#casetrends = plot(fig, include_plotlyjs=False, output_type='div')
plot(fig)



#%%


# 7 Day Avg New Cases with Deaths
df = allofit.loc[:,17,17187][['7 Day Avg New Positive',
                              'Total Deaths'
                              ]]
df = df.loc[firstCase(df['7 Day Avg New Positive']):]


fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=df.index, y=df['7 Day Avg New Positive'],
               name="New Cases (7 day avg)"),               
    secondary_y=False,
)

fig.add_trace(
    go.Scatter(x=df.index, y=df['Total Deaths'],
               name="Total Deaths"),
    secondary_y=True,
)

# Add figure title
fig.update_layout(
    title_text="New Cases and Deaths",
    #margin = margs,
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01),
    height = 420
)

# Set x-axis title
fig.update_xaxes(title_text="Date")

ly_max = df['7 Day Avg New Positive'].max()
ry_max = df['Total Deaths'].max()
# Set y-axes titles
fig.update_yaxes(title_text="<b>New Cases (7 day avg)</b>", 
                 range = (0,ly_max+5),
                 secondary_y=False)
fig.update_yaxes(title_text="<b>Deaths</b>", 
                 range = (0,ry_max+20),
                 #tickformat = ',.0%',
                 secondary_y=True)
fig.update_layout(hovermode='x unified')

#casetrends = plot(fig, include_plotlyjs=False, output_type='div')
plot(fig)

#%%

