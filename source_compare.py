#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 27 11:32:55 2020

@author: jlmayfield
"""

import pandas as pd


import plotly.express as px
import plotly.graph_objects as go
from plotly.offline import plot

from urllib.request import urlopen
import json
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

MB_TOKEN = open(".mapbox_token").read()

import cvdataprep as cvdp
import cvdataanalysis as cvda



#%%

# 17187,17 <-- Warren County, IL
warren = [17187]
p = 16981


#%%

def weekly(daily,nweeks=1):
    basis = daily[['New Positive']]
    wcil = basis.groupby(pd.Grouper(level='date',
                                      freq=str(nweeks)+'W-SUN',
                                      closed='left',
                                      label='left')).sum()
    #wcil['% New Positive'] = wcil['New Positive']/wcil['New Tests']
    return wcil


#%% 

population,cases,deaths = cvdp.loadusafacts()
reports_wchd, demo_wchd, death_wchd = cvdp.loadwchd()

data_idph = cvdp.loadidphdaily()

#%%
start_date = pd.to_datetime('2020-04-09')
end_date = pd.to_datetime('2022-01-01') #+ pd.Timedelta(1,unit='D')

wchd_last_daily = pd.to_datetime('2021-01-23')

#%%

full_tests_wchd = cvda.expandWCHDData(cvdp.prepwchd(reports_wchd)).loc[:,17,17187]
daily_wchd = full_tests_wchd.loc[:wchd_last_daily]
weekly_wchd = full_tests_wchd.loc[wchd_last_daily+pd.Timedelta(1,unit='D'):]

weekly_wchd = pd.concat([weekly(daily_wchd),weekly(weekly_wchd)])

#%%


full_tests_usafacts = cvdp.prepusafacts(cases,deaths).loc[:,:,[17187]]
tests_usaf = cvda.expandUSFData(full_tests_usafacts, population).loc[:,17,17187].loc[start_date:end_date]

weekly_usaf = weekly(tests_usaf)
#%%

tests_idph = cvda.expandIDPHDaily(cvdp.prepidphdaily(data_idph))
weekly_idph = weekly(tests_idph)

#%%

weekly_idph['source'] = 'IDPH'   
weekly_usaf['source'] = 'USAFacts'
weekly_wchd['source'] = 'WCHD'

idph = weekly_idph.reset_index().set_index(['date','source'])
usaf = weekly_usaf.reset_index().set_index(['date','source'])
wchd = weekly_wchd.reset_index().set_index(['date','source'])
all_sources = pd.concat([wchd,idph,usaf]).sort_index()


#%%


idph = all_sources.loc[(slice(None),'IDPH'),:]
wchd = all_sources.loc[(slice(None),'WCHD'),:]
usaf = all_sources.loc[(slice(None),'USAFacts'),:]
days = [ d.strftime('%m/%d') for d in idph.index.get_level_values('date') ]

#%%

df = all_sources.reset_index()
fig = px.bar(df, x="date", y="New Positive", color="source", 
             barmode="group",             
             )
fig.update_layout(title='Weekly Case Reports: WCHD vs IDPH vs USAFacts',                  
                  bargroupgap=.3)
plot(fig,filename='graphics/weekly-comparison-2.html')

#%%
clrs = px.colors.qualitative.Prism
fig = go.Figure(data=[
    go.Bar(name='WCHD',
           x=[days,['WCHD']*len(days)],
           y=wchd['New Positive'],
           marker_color=clrs[1]
           ),
    go.Bar(name='IDPH',
           x=[days,['IDPH']*len(days)],
           y=idph['New Positive'],
           marker_color=clrs[2]
           ),
    go.Bar(name='USAFacts.org',
           x=[days,['USAFacts']*len(days)],
           y=usaf['New Positive'],
           marker_color=clrs[3]
           )
    ])
fig.update_layout(barmode='stack',
                  title='Weekly Case Reports: WCHD vs IDPH vs USAFacts',                  
                  bargap=.2)
plot(fig,filename='graphics/weekly-comparison.html')
weeklydiv = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/source-comparison-weekly.txt','w') as f:
    f.write(weeklydiv)
    f.close()


#%%
RISK_COLORS = {'Minimal':'whitesmoke','Moderate':'rgba(255,215,0,0.5)','Substantial':'rgba(205,92,92,0.5)'}
def stylecp100k_cell(cp100k):
    def val2color(val):
        if round(val) <= 50:
            return RISK_COLORS['Minimal']
        elif round(val) <= 100:
            return RISK_COLORS['Moderate']
        else:
            return RISK_COLORS['Substantial']
    return [val2color(v) for v in cp100k]

def stylecp100k_text(cp100k):
    def val2txt(val):
        if round(val) <= 50:
            return "{:.1f}".format(val)
        else:
            return "<b>{:.1f}<b>".format(val)
    return [val2txt(v) for v in cp100k]

def styleprate_cell(prates):
    def val2color(val):
        if val <= .05:
            return RISK_COLORS['Minimal']
        elif val <= .08:
            return RISK_COLORS['Moderate']
        else:
            return RISK_COLORS['Substantial']
    return [val2color(v) for v in prates]

def styleprate_text(prates):
    def val2txt(val):
        if val <= .05:
            return "{:.1%}".format(val)
        else:
            return "<b>{:.1%}<b>".format(val)
    return [val2txt(v) for v in prates]

#%%
days = pd.to_datetime(weeks.index.get_level_values('date').unique())
vals =[ [''] + [ d.strftime('%m/%d') for d in days],       
        ['<b>WCHD</b>']+stylecp100k_text(weeks.loc['WCHD',:]['per 100k']),
        ['<b>IDPH</b>']+stylecp100k_text(weeks.loc['IDPH',:]['per 100k']),
        ['<b>WCHD</b>']+styleprate_text(weeks.loc['WCHD',:]['Positivity']),              
        ['<b>IDPH</b>']+styleprate_text( weeks.loc['IDPH',:]['Positivity']),           
        ['<b>WCHD</b>']+["{:.0f}".format(i) for i in weeks.loc['WCHD',:]['New Tests']],              
        ['<b>IDPH</b>']+["{:.0f}".format(i) for i in weeks.loc['IDPH',:]['New Tests']],           
        ['<b>WCHD</b>']+["{:.0f}".format(i) for i in weeks.loc['WCHD',:]['New Positive']],              
        ['<b>IDPH</b>']+["{:.0f}".format(i) for i in weeks.loc['IDPH',:]['New Positive']]
        ]
weekly_table = go.Table(header={'values':['<b>Week Start Date</b>',                                          
                                          '<b>Cases per 100k</b>',
                                          '',
                                          '<b>Positivity Rate</b>',                                          
                                          '',
                                          '<b>New Tests</b>',
                                          '',
                                          '<b>New Cases</b>',
                                          '',],
                                  'align':'left',
                                  'fill_color':'gainsboro'},
                          cells={'values':vals,
                                 'align':'left',
                                 'fill_color':[['gainsboro']+['whitesmoke']*len(days),
                                               ['gainsboro']+stylecp100k_cell(weeks.loc['WCHD',:]['per 100k']),
                                               ['gainsboro']+stylecp100k_cell(weeks.loc['IDPH',:]['per 100k']),
                                               ['gainsboro']+styleprate_cell(weeks.loc['WCHD',:]['Positivity']),
                                               ['gainsboro']+styleprate_cell(weeks.loc['IDPH',:]['Positivity']),
                                               ['gainsboro']+['whitesmoke']*len(days),
                                               ['gainsboro']+['whitesmoke']*len(days),
                                               ['gainsboro']+['whitesmoke']*len(days),
                                               ['gainsboro']+['whitesmoke']*len(days)]}
                          )
fig = go.Figure(data=weekly_table)
fig.update_layout(title="Weekly Covid Numbers: WCPH vs. IDPH")
plot(fig,filename='graphics/weekly-table.html')
weeklydiv = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/weekly-table.txt','w') as f:
    f.write(weeklydiv)
    f.close()

#%%
twchd = tests_wchd.iloc[-14:]
tidph = tests_idph.iloc[-14:]
tusaf = tests_usaf.iloc[-14:]
days = [ d.strftime('%m/%d') for d in twchd.index]
fig = go.Figure(data=[
    go.Bar(name='Positive',
           x=[days,['WCHD']*len(days)],
           y=twchd['New Positive'],
           marker_color='salmon'),
    go.Bar(name='Negative',
           x=[days,['WCHD']*len(days)],
           y=twchd['New Negative'],
           marker_color='deepskyblue'),
    go.Bar(name='Positive',
           x=[days,['IDPH']*len(days)],
           y=tidph['New Positive'],
           marker_color='salmon',
           showlegend=False),
    go.Bar(name='Negative',
           x=[days,['IDPH']*len(days)],
           y=tidph['New Negative'],
           marker_color='deepskyblue',
           showlegend=False),
    go.Bar(name='Positive',
           x=[days,['USAFacts']*len(days)],
           y=tusaf['New Positive'],
           marker_color='salmon',
           showlegend=False)    
    ])

fig.update_layout(barmode='stack',
                  title='Test Result Source Data Comparison')
                  


plot(fig,filename='graphics/source-comparison-daily.html')
dailydiv = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/source-comparison-daily.txt','w') as f:
    f.write(dailydiv)
    f.close()

