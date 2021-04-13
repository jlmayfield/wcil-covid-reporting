#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat April 3

@author: jlmayfield
"""


import pandas as pd

from plotly.subplots import make_subplots
import plotly.graph_objects as go
from plotly.offline import plot
import plotly.express as px


import cvdataprep as cvdp
import cvdataanalysis as cvda


#%%

idphnums = cvdp.loadidphdaily()
wchdcases,wchddemos,wchddeaths = cvdp.loadwchd()
populations,usafcases,usafdeaths = cvdp.loadusafacts()


#%%
# from IL DPH site for vaccine data (1/31/21)
p = 17032

today = pd.to_datetime('2021-04-10')
dayone = pd.to_datetime('2020-04-10')
wchd_lastdaily = pd.to_datetime('2021-01-24')

#%%

# daily numbers from IDPH
idph_daily = cvda.expandIDPHDaily(cvdp.prepidphdaily(idphnums),p)
idph_daily = idph_daily.loc[:,17,17187]

# daily numbers from WCHD up until they shifted to weekly reporting
wchd_daily = cvda.expandWCHDData(cvdp.prepwchd(wchdcases.loc[:wchd_lastdaily,:]),p)
wchd_daily = wchd_daily.loc[:,17,17187]

#%%

overlap = idph_daily.index.intersection(wchd_daily.index)
idph = idph_daily.loc[wchd_lastdaily + pd.Timedelta(1,unit='D'):][['New Tests','New Positive','New Vaccinated','New Deaths']]
wchd = wchd_daily[['New Tests','New Positive','New Deaths']]

yearone = pd.concat([wchd,idph]).fillna(0)
yearone_weekly = yearone.groupby(pd.Grouper(level='date',
                                           freq='W-SUN',
                                           closed='left',
                                           label='left')).sum()

#%%

fig = px.bar(yearone_weekly,
              x=yearone_weekly.index,y='New Positive',
              title='One Year of Covid-19: New Cases by Week')
plot(fig,filename='graphics/yearone-cases.html')

fig = px.bar(yearone_weekly,
              x=yearone_weekly.index,y='New Deaths',
              title='One Year of Covid-19: New Covid Related Deaths by Week')
plot(fig,filename='graphics/yearone-deaths.html')

fig = px.bar(yearone_weekly,
              x=yearone_weekly.index,y='New Vaccinated',
              title='One Year of Covid-19: New Fully Vaccinated People by Week')
plot(fig,filename='graphics/yearone-vaccinated.html')


#%%
# breakout of state of IL
usafcases_noZero = usafcases.drop([0])
usafcases_zeros = usafcases.loc[0]
usafdeaths_noZero = usafdeaths.drop([0])
usafdeaths_zeros = usafdeaths.loc[0]
IL = usafcases_noZero[usafcases_noZero['State'] == 'IL']
ILd = usafdeaths_noZero[usafdeaths_noZero['State'] == 'IL']

#%%

# National Data (with rankings)
usaf_daily = cvda.expandUSFData(cvdp.prepusafacts(usafcases_noZero,
                                                  usafdeaths_noZero),
                                populations)
# State Data (state of IL only rankings)
usaf_IL_daily = cvda.expandUSFData(cvdp.prepusafacts(IL,ILd), populations)


oneyear = usaf_daily.loc[:today]
    

#%%

# day for first reported case for every county
firstreports = oneyear['Total Positive'].mask(oneyear['Total Positive']==0).groupby('countyFIPS').idxmin()
firstreports = firstreports.sort_values().dropna().map(lambda r: r[0])
# which batch they were in
batchnum = firstreports.rank(method='dense')
ptile = firstreports.rank(ascending=True,pct=True)
#%%

# first reported case, last instance of first case in the county
print(firstreports.iloc[0],firstreports.iloc[-1])
# WCIL: first case, batch, % counties still without cases
print(firstreports[17187],batchnum[17187],ptile[17187])

#%%


