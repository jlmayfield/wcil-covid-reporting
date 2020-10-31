#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 31 09:16:58 2020

@author: jlmayfield
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct  7 12:31:03 2020

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

dayoff = pd.to_datetime('2020-10-01') - pd.Timedelta(1,unit='D')
day1 = pd.to_datetime('2020-10-01')
lastday = pd.to_datetime('2020-10-31')
themonth = pd.date_range(day1,lastday)
theslice = pd.date_range(dayoff,lastday)

# 17187,17 <-- Warren County, IL

population,cases = cvdp.loadusafacts()
reports_wchd,demo_wchd,death_wchd = cvdp.loadwchd()
reports_mc = cvdp.loadmcreports()
#%%

usaf = cvdp.prepusafacts(cases)
usaf = cvda.expandUSFData(usaf.loc[(theslice,17,slice(None)),:],
                          population).loc[ (themonth,slice(None),slice(None)), :]

wchd = cvdp.prepwchd(reports_wchd)
wchd = cvda.expandWCHDData(wchd.loc[(theslice,17,slice(None)),:],
                           population.loc[17187,'population']).loc[ (themonth,slice(None),slice(None)), :]

reports_mc = cvda.expandMCData(reports_mc)

#%%

all_of_il = usaf[['Total Positive','New Positive']].groupby(level='date').sum()
all_of_il = pd.concat([all_of_il,
                       cvda._mc7day(all_of_il['New Positive'])]
                      ,axis=1)
