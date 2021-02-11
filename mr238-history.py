#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 17 10:24:53 2020

@author: jlmayfield
"""



import pandas as pd

from plotly.subplots import make_subplots
import plotly.graph_objects as go
from plotly.offline import plot

import cvdataprep as cvdp
import cvdataanalysis as cvda

#%%

wchd_last_sat = pd.to_datetime('2021-01-23')
# Data from WCHD & IDPH
reports_wchd,demo_wchd,_ = cvdp.loadwchd()
idphnums = cvdp.loadidphdaily()
# cutoff at date WCHD stopped daily reports
reports_wchd = reports_wchd.loc[:wchd_last_sat]
idphnums = idphnums[wchd_last_sat:]

tests_wchd = cvda.expandWCHDData(cvdp.prepwchd(reports_wchd))
idph_daily = cvda.expandIDPHDaily(cvdp.prepidphdaily(idphnums))


p = 17032


#%%
# '#3498DB'
RISK_COLORS = {'Minimal':'whitesmoke','Moderate':'rgba(255,215,0,0.5)','Substantial':'rgba(205,92,92,0.5)'}


# 50 cases/100k (9 actual) is the warning cutoff
def stylecp100k_cell(cp100k):    
    def val2color(c):        
        if round(c) < 50:
            return RISK_COLORS['Minimal']        
        else:
            return RISK_COLORS['Substantial']
    return [val2color(v) for v in cp100k]

# bold the number to stand out in the color
def stylecp100k_text(cp100k):
    def val2txt(i):
        p100k = cp100k.loc[i][0]
        actual = cp100k.loc[i][1]        
        txt = "{:<8.1f} ({:d})".format(p100k,int(actual))
        if round(p100k) < 50:
            return txt
        else:
            return '<b>' + txt + '</b>'
    return [val2txt(v) for v in cp100k.index]

# 5% or greater is the cutoff
def styleprate_cell(prates):
    def val2color(val):
        if val < .05:
            return RISK_COLORS['Minimal']        
        else:
            return RISK_COLORS['Substantial']
    return [val2color(v) for v in prates]

def styleprate_text(prates):
    def val2txt(val):
        if val < .05:
            return "{:.1%}".format(val)
        else:
            return "<b>{:.1%}</b>".format(val)
    return [val2txt(v) for v in prates]

# 3 or more youth cases is the cutoff
def styleyouth_cell(youths):
    def val2color(i):
        val = int(youths.loc[i][0])
        streak = int(youths.loc[i][1])
        if val < 3 and streak < 1:
            return RISK_COLORS['Minimal']
        elif val < 3 and streak < 2:
            return RISK_COLORS['Moderate']
        else: #val >= 3 or streak >= 2
            return RISK_COLORS['Substantial']
    return [val2color(i) for i in youths.index]

# 3 or more youth cases is the cutoff
def styleyouth_text(youths):
    def val2color(i):
        val = youths.loc[i]['Youth Cases']
        streak = youths.loc[i]['Consecutive Youth Increases']
        txt = "{:<8}".format(val)        
        if streak > 0:
            txt += "({})".format(streak)
        if val > 3:
            txt = '<b>' + txt + "</b>"
        return txt
    return [val2color(v) for v in youths.index]        
    
   
def stylestreak_text(streak):
    def val2txt(s):            
        txt= "{}".format(s)
        if s < 2:
            return txt
        else:
            return "<b>" + txt +"</b>"
    return [val2txt(s) for s in streak]

def stylestreak_cell(cases):
    def val2color(streak):        
        if streak < 1:
            return RISK_COLORS['Minimal']
        elif streak < 2:
            return RISK_COLORS['Moderate']
        else:
            return RISK_COLORS['Substantial']
    return [val2color(i) for i in cases]



#%%

def increased(col):
    return (col.diff() > 0).astype(int)

def increase_streak(col):
    did_increase = increased(col)
    tot_increase = did_increase.cumsum()
    offsets = tot_increase.mask(did_increase != 0).ffill()
    streaks = (tot_increase - offsets).astype(int)
    return streaks.rename(col.name + " Increase Streak")


def schooldaily(wchd_data,wchd_demo):
    keepers = ['New Positive','New Tests','New Deaths','% New Positive']
    school = wchd_data.loc[:,17,17187][keepers]
    school['Youth Cases'] = (wchd_demo.T.loc[(slice(None),['0-10','10-20']),:].T).sum(axis=1).astype(int)
    school['Cases per 100k'] = school['New Positive'] * 100000 / p
    school['Case Increases in 10 days'] = increased(school['New Positive']).rolling(10,min_periods=0).sum().astype(int)
    school['Youth Increases in 10 days'] = increased(school['Youth Cases']).rolling(10,min_periods=0).sum().astype(int)
    school['Positivity Rate Increases in 10 days'] = increased(school['% New Positive']).rolling(10,min_periods=0).sum().astype(int)
    return school

def schoolweekly(daily,nweeks=1):
    basis = daily[['New Positive','New Tests','Youth Cases']]
    school = basis.groupby(pd.Grouper(level='date',
                                      freq=str(nweeks)+'W-SUN',
                                      closed='left',
                                      label='left')).sum()
    school.loc[:,'Cases per 100k'] = school['New Positive'] * 100000 / p
    school.loc[:,'% New Positive'] = school['New Positive']/school['New Tests']
    school.loc[:,'New Positive Change'] = school['New Positive'].pct_change()
    school.loc[:,'New Youth Change'] = school['Youth Cases'].pct_change()
    school.loc[:,'Consecutive Case Increases'] = increase_streak(school['New Positive'])
    school.loc[:,'Consecutive Youth Increases'] = increase_streak(school['Youth Cases'])
    return school

#%%

def schooldaily_new(wchd_data,wchd_demo):
    keepers = ['New Positive','New Tests','% New Positive']
    school = wchd_data.loc[:,17,17187][keepers]
    school.loc[:,'Youth Cases'] = (wchd_demo.T.loc[(slice(None),['0-10','10-20']),:].T).sum(axis=1).astype(int)
    school.loc[:,'Cases per 100k'] = school['New Positive'] * 100000 / p
    #school['Case Increases in 10 days'] = increased(school['New Positive']).rolling(10,min_periods=0).sum().astype(int)
    #school['Youth Increases in 10 days'] = increased(school['Youth Cases']).rolling(10,min_periods=0).sum().astype(int)
    #school['Positivity Rate Increases in 10 days'] = increased(school['% New Positive']).rolling(10,min_periods=0).sum().astype(int)
    return school

#%%


all_the_days = schooldaily_new(tests_wchd, demo_wchd)
all_the_new_days = schooldaily_new(idph_daily,demo_wchd).fillna(0)

really_all_the_days = pd.concat([all_the_days,all_the_new_days])

# get week start date
today = pd.to_datetime('today')
this_sunday = pd.to_datetime(today - pd.offsets.Week(weekday=6)).date() if today.dayofweek != 6 else today.date() 

completeweeks = really_all_the_days.loc[pd.to_datetime('2020-05-03'):this_sunday-pd.Timedelta(1,unit='D')]
all_the_weeks = schoolweekly(completeweeks,nweeks=1)




#%%

df = all_the_weeks.reset_index().sort_values('date',ascending=False)
vals = [df['date'].apply(lambda d: d.strftime("%B %d")),
        styleprate_text(df['% New Positive']),
        stylecp100k_text(df[['Cases per 100k','New Positive']]),
        stylestreak_text(df['Consecutive Case Increases']),
        styleyouth_text(df[['Youth Cases','Consecutive Youth Increases']])]        
# cell colors
clrs = ['whitesmoke',
        styleprate_cell(df['% New Positive']),
        stylecp100k_cell(df['Cases per 100k']),
        stylestreak_cell(df['Consecutive Case Increases']),        
        styleyouth_cell(df[['Youth Cases','Consecutive Youth Increases']])]

weekly_table = go.Table(header={'values':['<b>Week Start Date</b>',
                                          '<b>Positivity Rate</b>',
                                          '<b>New Cases<br>per 100k (actual)</b>',                                                                                     
                                          '<b>Consecutive Weeks of<br>New Case Increases</b>',
                                          '<b>Youth Cases<br>Current (Increases)</b>',
                                          ],
                                 'align':'left',
                                 'fill_color':'gainsboro'},
                        cells={'values': vals,
                                 'align': 'left',
                                 'fill_color': clrs,
                                 'height':30})

#%%

fig = go.Figure(data=weekly_table)

fig.update_layout(title_text="MR-238 Metric History",
                  margin = go.layout.Margin(l=0, #left margin
                                            r=0, #right margin
                                            b=0, #bottom margin
                                            t=25  #top margin
                                            ),
                  height=1000,
                  width=650
                  )


plot(fig,filename='graphics/MR238-Historical.html')
div = plot(fig, include_plotlyjs=False, output_type='div')
#with open('mr238/MR238-Historical.txt','w') as f:
#    f.write(div)
#    f.close()
   


#%%

mdpage = ""
header = """---
layout: page
title: MR238 - Historical Report
permalink: /mr238/history/
---

<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>

"""

timestamp = pd.to_datetime('today').strftime('%H:%M %Y-%m-%d')
header = header + '<p><small>last updated:  ' + timestamp + '</small><p>\n\n'
mdpage = header + '\n\n\n' + div

if today.dayofweek == 6:
    with open('docs/MR238History.md','w') as f:
        f.write(mdpage)
        f.close()
