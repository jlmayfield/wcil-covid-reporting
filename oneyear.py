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

today = pd.to_datetime('2021-04-09')
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

# breakout of state of IL
IL = usafcases[usafcases['State'] == 'IL']
ILd = usafdeaths[usafdeaths['State'] == 'IL']

#%%

# National Data (with rankings)
usaf_daily = cvda.expandUSFData(cvdp.prepusafacts(usafcases,usafdeaths),
                                populations)
# State Data (state of IL only rankings)
usaf_IL_daily = cvda.expandUSFData(cvdp.prepusafacts(IL,ILd), populations)

lastday = usaf_daily.index[-1][0]
    

#%%
