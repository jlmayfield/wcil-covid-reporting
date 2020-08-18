#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  2 15:07:17 2020

@author: jlmayfield
"""


import pandas as pd
import numpy as np

import cvdataprep as cvdp
import cvdataanalysis as cvda
import cvdataviz as cvdv



#%%

warren = [17187]
neighbors = [17095, 17071, 17109, 17057, 17131]
il_select = [ 17113, 17107, 17167, 17195, 17031]
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



#%%

cases = cvdp.datefix(cases)
cases = cvdp.prune_data(cases)


#%%

only_counties = list(cases.index[ ~cases.index.isin([0,1])] ) #remove unassigned
cases_normed = cvda.to_for100k(cases.loc[only_counties], population)
#cases_daily = to_new_daily(cases)
#cases_daily_normed = to_new_daily(cases_normed)

#%%

aoi_fips = region2 + ia_select
aoi = cvdp.prune_data(cases.loc[aoi_fips])
aoi_normed = cvda.to_for100k(aoi, population)
aoi_daily = cvda.to_new_daily(aoi)
aoi_normed_daily = cvda.to_for100k(aoi_daily,population)
aoi_nd_7day = cvda.to_sevenDayAvg(aoi_normed_daily)

#%%

days = 21
cvdv.plot_timeseries(aoi_nd_7day.loc[nhood], days,
                     'Seven Day Average of Daily Cases per 100000')

#%%
cvdv.animated_bars(aoi_nd_7day,days)
#cvdv.animate_per100k(aoi_nd_7day,days,'Seven Day Average of Daily Covid Cases per 100000')

#%%

# Collect region two daily totals and averages per 100000

r2 = aoi_daily.loc[region2]
cvdv.three_week_report(r2, "Illinois Region 2")
cvdv.three_week_report(aoi_daily.loc[nhood], "Warren County Neighborhood")


#%%


#%%

## all the things as bars
total_days = len(aoi_nd_7day.columns[3:])
cvdv.animated_bars(aoi_nd_7day,total_days)

#%%%

weekly = aoi_normed_daily.loc[region2].copy()
weekly_prep = cvdv.prep_for_animate(weekly)
today = pd.to_datetime(weekly.columns[-1])
weekly_prep['Week'] = weekly_prep['Date'].apply(lambda d: cvda.which_week(pd.to_datetime(d), today))
#%%
import plotly.express as px
from plotly.offline import plot

fig = px.box(weekly_prep,
             x='Date',y='Cases')
fig.update_layout(    
    yaxis=dict(
        range=(0,80)))
plot(fig)

#%%
