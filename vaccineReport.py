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
names = names.to_dict()

#%%
# Scrape all IL counties for totals
#cvdp.IDPHDataCollector.writeTotalsAll(counties.index)
# Gets all the county data. Only changes if population counts are 
#  updated
#cvdp.IDPHDataCollector.writeCountyData(counties.index)

#cvdp.IDPHDataCollector.writeTotalsAll(nopop.index)-
#cvdp.IDPHDataCollector.writeCountyData(nopop.index)


#%%

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
    pop = counties.loc[cname]['Population']
    tots.loc[:,'countyFIPS'] = fips
    tots.loc[:,'stateFIPS'] = 17
    tots = tots.reset_index().set_index(['date','stateFIPS','countyFIPS'])
    expanded = cvda.expandIDPHDaily(tots,pop)    
    return expanded.reset_index()

#%%

# build IL wide stats!
allofit = pd.concat([loadAndExpand(f) for f in counties.index]).set_index(['date','stateFIPS','countyFIPS']).sort_index()   
outTots = cvdp.IDPHDataCollector.getNonCountyData()

#%%

lastday = allofit.index[-1][0]
lastvac = lastday - pd.Timedelta(1,'D')

vacdata = allofit[['Total Vaccinated','% Vaccinated','7 Day Avg New Vaccinated']].loc[lastvac,:,:]

#%%

vacdata = vacdata.reset_index().drop(['stateFIPS','date'],axis=1).set_index('countyFIPS')
statewide = vacdata.loc['Illinois']
vacdata = vacdata[vacdata.index != 'Illinois']
#%%

vacdata.loc[:,'% Vac Rank'] = vacdata['% Vaccinated'].rank(ascending=False,method='dense')

#%%
summary = vacdata['% Vaccinated'].describe()
fig = px.histogram(vacdata,x='% Vaccinated',
                   nbins=int(np.ceil((summary['max']-summary['min'])/.02))
                   )
fig.update_layout(bargap=0.1)
plot(fig)