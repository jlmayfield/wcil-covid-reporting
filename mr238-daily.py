#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 17 10:24:53 2020

@author: jlmayfield
"""



import pandas as pd
import numpy as np

from plotly.subplots import make_subplots
import plotly.graph_objects as go
from plotly.offline import plot


import cvdataprep as cvdp
import cvdataanalysis as cvda

#%%

# Data from WCHD
reports_wchd,demo_wchd,_ = cvdp.loadwchd()
#tests_wchd = cvda.expandWCHDData(cvdp.prepwchd(reports_wchd))

# Data from IDPH
idphnums = cvdp.loadidphdaily()
idph_daily = cvda.expandIDPHDaily(cvdp.prepidphdaily(idphnums))

# from IL DPH site for vaccine data (1/31/21)
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


def schooldaily(wchd_data):
    keepers = ['New Positive','New Tests','% New Positive']
    school = wchd_data.loc[:,17,17187][keepers]
    #school['Youth Cases'] = (wchd_demo.T.loc[(slice(None),['0-10','10-20']),:].T).sum(axis=1).astype(int)
    school['Cases per 100k'] = school['New Positive'] * 100000 / p
    school['Case Increases in 10 days'] = increased(school['New Positive']).rolling(10,min_periods=0).sum().astype(int)
    #school['Youth Increases in 10 days'] = increased(school['Youth Cases']).rolling(10,min_periods=0).sum().astype(int)
    school['Positivity Rate Increases in 10 days'] = increased(school['% New Positive']).rolling(10,min_periods=0).sum().astype(int)
    return school

#%%
def schoolweekly(daily,demo,nweeks=1):
    basis = daily[['New Positive','New Tests']]
    ycases = (demo.T.loc[(slice(None),['0-10','10-20']),:].T).sum(axis=1).astype(int)
    ycases = ycases.rename('Youth Cases')
    ycases.index = ycases.index.rename('date')
    basis = pd.concat([basis, ycases],axis=1)    
    school = basis.groupby(pd.Grouper(level='date',
                                      freq=str(nweeks)+'W-SUN',
                                      closed='left',
                                      label='left')).sum()
    school['Cases per 100k'] = school['New Positive'] * 100000 / p
    school['% New Positive'] = school['New Positive']/school['New Tests']
    school['New Positive Change'] = school['New Positive'].pct_change()
    school['New Youth Change'] = school['Youth Cases'].pct_change()
    school['Consecutive Case Increases'] = increase_streak(school['New Positive'])
    school['Consecutive Youth Increases'] = increase_streak(school['Youth Cases'])
    return school

#%%

def schoolmonthly(daily):
    basis = daily[['New Positive','New Tests','New Deaths','Youth Cases']]
    school = basis.groupby(pd.Grouper(level='date',freq='MS',
                                      closed='left',label='left')).sum()
    # assume official test dates are a day prior to align with state
    school['Cases per 100k'] = school['New Positive'] * 100000 / p
    school['% New Positive'] = school['New Positive']/school['New Tests']
    return school


#%%


all_the_days = schooldaily(idph_daily)    

# get week start date
today = pd.to_datetime('today')
this_sunday = pd.to_datetime(today - pd.offsets.Week(weekday=6)).date() if today.dayofweek != 6 else today.date() 
this_week = all_the_days.loc[this_sunday:]
ndays = len(this_week)

#%%

# weekly numbers for this week and two prior
threeweeks = schoolweekly(all_the_days,demo_wchd,nweeks=1).iloc[-3:]




#%%
margs = go.layout.Margin(l=0, #left margin
                         r=0, #right margin
                         b=0, #bottom margin
                         t=25  #top margin
                         )                          

#%%

df = this_week.reset_index().sort_values('date',ascending=False)
thisweek = go.Table(header={'values':['<b>Date</b>',
                                      #'<b>Positivity Rate</b>',
                                      '<b>New Cases<br>per 100k (actual)</b>'
                                      ],
                                  'align':'left',
                                  'fill_color':'gainsboro'},
                             cells={'values':[df['date'].apply(lambda d: d.strftime("%A, %B %d")),
                                             # styleprate_text(df['% New Positive']),
                                              stylecp100k_text( df[['Cases per 100k','New Positive']])
                                              ],
                                    'align':'left',
                                    'fill_color':['whitesmoke',
                                              #    styleprate_cell(df['% New Positive']),
                                                  stylecp100k_cell(df['Cases per 100k']),
                                                 ],
                                    'height': 30 }
                           )

fig = go.Figure(data=thisweek)
fig.update_layout(title="This Week",
                  margin = margs,
                  height= (ndays*40 + 150))
weekdiv = plot(fig, include_plotlyjs=False, output_type='div')


#%%

df = threeweeks.reset_index().sort_values('date',ascending=False)
vals = [df['date'].apply(lambda d: d.strftime("%B %d")),
        #styleprate_text(df['% New Positive']),
        stylecp100k_text(df[['Cases per 100k','New Positive']]),
        stylestreak_text(df['Consecutive Case Increases']),
        styleyouth_text(df[['Youth Cases','Consecutive Youth Increases']])]        
# style current week to flag provisional data
vals[0].iloc[0] = '<i>' + vals[0].iloc[0] + '<i>' 
# cell colors
clrs = ['whitesmoke',
        #styleprate_cell(df['% New Positive']),
        stylecp100k_cell(df['Cases per 100k']),
        stylestreak_cell(df['Consecutive Case Increases']),        
        styleyouth_cell(df[['Youth Cases','Consecutive Youth Increases']])]
weekly_table = go.Table(header={'values':['<b>Week Start Date</b>',
         #                                 '<b>Positivity Rate</b>',
                                          '<b>New Cases<br>per 100k (actual)</b>',                                                                                     
                                          '<b>Consecutive Weeks<br>New Case Increases</b>',
                                          '<b>Youth Cases<br>Current (Increases)</b>',
                                          ],
                                 'align':'left',
                                 'fill_color':'gainsboro'},
                        cells={'values': vals,
                                 'align': 'left',
                                 'fill_color': clrs,
                                 'height':30})

fig = go.Figure(data=weekly_table)
fig.update_layout(title="Weekly Metrics",
                  margin = margs,
                  height= 250)
weeklydiv = plot(fig, include_plotlyjs=False, output_type='div')
    

#%%

fig = make_subplots(rows=2, cols=1,
                    vertical_spacing=0.1,
                    #horizontal_spacing=0.05,
                    specs=[[{"type": "table"}],[{"type": "table"}]],
                    subplot_titles=('Weekly Metrics',
                                    'This Week'))

fig.add_trace(thisweek,row=2,col=1)
fig.add_trace(weekly_table,row=1,col=1)

fig.update_layout(title_text="MR-238 Daily Dashboard",                  
                  height=800)

#plot(fig,filename='graphics/MR238-Daily.html')
#div = plot(fig, include_plotlyjs=False, output_type='div')
#with open('mr238/MR238-Daily.txt','w') as f:
#    f.write(div)
#    f.close()

#%%


mdpage = ""
header = """---
layout: page
title: MR 238 COVID-19 Metric Report
permalink: /mr238-metrics/
---

<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>

"""
tdaynote = """
<p><small> The WCHD did not issue a report on Thanksgiving (11/26). 
The daily totals reported here come from the IDPH reports. Both agencies reproted
the same two day total. Case demographics were more or less porportionally distributed
across the two days.</small></p> 
"""
note1208 = """
<p><small>
WCHD Did not report negative tests on 12/8. The number reported here
is taken from the IDPH numbers for that day. 
</small></p>"""
jan19note = """
<p><small> The WCHD did not issue a report on 1/19. The data show below
for 1/19 and 1/20 was generated by splitting the WCHD report from 1/20
based on data from IDPH. </small></p>"""
feb19note = """
<p><small> On 2/19 IDPH reported a case total one fewer than 2/18.
Presumably this is a retraction. The data for that day shows -1 
cases. It would seem there were 0 new cases on 2/19 and one 
fewer case in the days proceeding it. </small></p> """

apr22note = """
<p><small> On 4/22/22, the IDPH seemed to have stopped reporting the 
number of tests. This resulted in a loss of that data as a whole and 
makes postivity rate impossible to report. Starting on 4/25/22, both 
the test count and the positivity rating will no longer be reported here.</small></p>""" 


htmlblock = '{::options parse_block_html="true" /}\n\n'
timestamp = pd.to_datetime('today').strftime('%H:%M %Y-%m-%d')
header = header + '<p><small>last updated:  ' + timestamp + '</small></p>\n\n'
mdpage = header + jan19note + feb19note + apr22note + weeklydiv + '\n\n' + weekdiv  

with open('mr238/MR238-Daily.txt','w') as f:
    f.write(apr22note + '\n\n' + weeklydiv + '\n\n' + weekdiv )
    f.close()
    
#with open('mr238/03-explanations.md','r') as f:
#    with open('mr238/MR238Report.md','a',newline='') as g: 
#        g.write(f.read())
#        g.close()
#    f.close()
    


    
