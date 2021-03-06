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

population,cases,deaths = cvdp.loadusafacts()
reports_wchd,demo_wchd,death_wchd = cvdp.loadwchd()
reports_mc = cvdp.loadmcreports()


reports_mc = cvda.expandMCData(reports_mc)

#%%

def daily(basis,demo):
    #basis = basis.loc[:,17,17187]
    demo_sum = pd.DataFrame(index=basis.index)
    demo_sum['Cases 0-10'] = (demo.T.loc[(slice(None),['0-10']),:].T).sum(axis=1).astype(int)
    demo_sum['Cases 10-20'] = (demo.T.loc[(slice(None),['10-20']),:].T).sum(axis=1).astype(int)
    demo_sum['Cases 20-40'] = (demo.T.loc[(slice(None),['20-40']),:].T).sum(axis=1).astype(int)
    demo_sum['Cases 40-60'] = (demo.T.loc[(slice(None),['40-60']),:].T).sum(axis=1).astype(int)
    demo_sum['Cases 60-80'] = (demo.T.loc[(slice(None),['60-80']),:].T).sum(axis=1).astype(int)
    demo_sum['Cases 80-100'] = (demo.T.loc[(slice(None),['80-100']),:].T).sum(axis=1).astype(int)
    basis = pd.concat([basis,demo_sum],axis=1)
    return basis
    

def weekly(daydata,nweeks=1):
    basis = daydata[['New Tests','New Positive',
                     'New Positive per 100k','New Deaths',
                     'Cases 0-10','Cases 10-20','Cases 20-40','Cases 40-60',
                     'Cases 60-80','Cases 80-100']]
    weeks = basis.groupby(pd.Grouper(level='date',
                                      freq=str(nweeks)+'W-SUN',
                                      closed='left',
                                      label='left')).sum()    
    weeks['Week Number'] = weeks.index.isocalendar().week
    weeks = pd.concat([weeks,
                       cvda._newposrate(weeks)],
                       axis=1)
    return weeks[['Week Number','New Tests','New Positive','% New Positive',
                  'New Positive per 100k','New Deaths',
                  'Cases 0-10','Cases 10-20','Cases 20-40','Cases 40-60',
                  'Cases 60-80','Cases 80-100']]


def monthly(daydata):
    months = daydata.groupby(pd.Grouper(level='date',
                                       freq='MS',
                                       closed='left',
                                       label='left')).sum()    
    months['Month Number'] = months.index.map(lambda d: d.month)
    months = pd.concat([months,
                        cvda._newposrate(months)],
                        axis=1)
    return months[['Month Number','New Tests','New Positive','% New Positive',
                  'New Positive per 100k','New Deaths',
                  'Cases 0-10','Cases 10-20','Cases 20-40','Cases 40-60',
                  'Cases 60-80','Cases 80-100']]

#%%

full_tests_wchd = cvda.expandWCHDData(cvdp.prepwchd(reports_wchd))
# current viz routines assume single date index and do not handle the s
# index that includes state/county fips
tests_wchd = full_tests_wchd.loc[:,17,17187]

by_day = daily(tests_wchd,demo_wchd)
by_week = weekly(by_day).iloc[3:]
by_month = monthly(by_day)

#%%
full_cases_usaf = cvdp.prepusafacts(cases,deaths)
aoi = [17187,17095,17109]
aoi_cases_usaf = cvda.expandUSFData(full_cases_usaf.loc[:,:,aoi], population)

#%%


top_ten = by_day.sort_values('New Positive',ascending=False).iloc[:10].reset_index()
vals = [top_ten['date'].apply(lambda d: d.strftime("%B %d")),        
        top_ten['New Positive'],
        top_ten['New Tests'],        
        top_ten['% New Positive'].apply(lambda n: "{:.1%}".format(n)),
        top_ten['New Positive per 100k'].apply(lambda n: "{:.1f}".format(n)),
        top_ten['New Deaths']]
headers = ['<b>Week Start Date</b>',           
           '<b>Positive</b>',
           '<b>Tests</b>',
           '<b>Pos. Rate</b>',
           '<b>Cases per 100k</b>',
           '<b>Deaths</b>']
daily_table = go.Table(header={'values':headers,
                                 'align':'left',
                                 'fill_color':'gainsboro'},
                        cells={'values': vals,
                                 'align': 'left',
                                 'fill_color': 'whitesmoke',
                                 'height':30})
fig = go.Figure(data=daily_table)

fig.update_layout(title_text="Ten Highest Daily Case Counts",
                  margin = go.layout.Margin(l=0, #left margin
                                            r=0, #right margin
                                            b=0, #bottom margin
                                            t=25  #top margin
                                            ),
                  #height=1000,
                  #width=650
                  )


plot(fig,filename='graphics/WCIL-TopTenDays.html')
div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/WCIL-TopTenDays.txt','w') as f:
    f.write(div)
    f.close()



#%%

top_ten = by_week.sort_values('New Positive',ascending=False).iloc[:10].reset_index()
vals = [top_ten['Week Number'],
        top_ten['date'].apply(lambda d: d.strftime("%B %d")),        
        top_ten['New Positive'],
        top_ten['New Tests'],        
        top_ten['% New Positive'].apply(lambda n: "{:.1%}".format(n)),
        top_ten['New Positive per 100k'].apply(lambda n: "{:.1f}".format(n)),
        top_ten['New Deaths']]
headers = ['<b>Week Number</b>',
           '<b>Week Start Date</b>',           
           '<b>Positive</b>',
           '<b>Tests</b>',
           '<b>Pos. Rate</b>',
           '<b>Cases per 100k</b>',
           '<b>Deaths</b>']
weekly_table = go.Table(header={'values':headers,
                                 'align':'left',
                                 'fill_color':'gainsboro'},
                        cells={'values': vals,
                                 'align': 'left',
                                 'fill_color': 'whitesmoke',
                                 'height':30})
fig = go.Figure(data=weekly_table)

fig.update_layout(title_text="Ten Highest Single Week Case Counts",
                  margin = go.layout.Margin(l=0, #left margin
                                            r=0, #right margin
                                            b=0, #bottom margin
                                            t=25  #top margin
                                            ),
                  #height=1000,
                  #width=650
                  )


plot(fig,filename='graphics/WCIL-TopTenWeeks.html')
div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/WCIL-TopTenWeeks.txt','w') as f:
    f.write(div)
    f.close()


#%%

vals = [top_ten['date'].apply(lambda d: d.strftime("%B %d")),        
        top_ten['New Positive'],
        top_ten['Cases 0-10'],
        top_ten['Cases 10-20'],        
        top_ten['Cases 20-40'],
        top_ten['Cases 40-60'],
        top_ten['Cases 60-80'],
        top_ten['Cases 80-100']]
headers = ['<b>Week Start Date</b>',           
           '<b>Positive</b>',
           '<b>Cases 0-10</b>',
           '<b>Cases 10-20</b>',
           '<b>Cases 20-40</b>',
           '<b>Cases 40-60</b>',
           '<b>Cases 60-80</b>',
           '<b>Cases 80-100</b>']
weekly_table = go.Table(header={'values':headers,
                                 'align':'left',
                                 'fill_color':'gainsboro'},
                        cells={'values': vals,
                                 'align': 'left',
                                 'fill_color': 'whitesmoke',
                                 'height':30})
fig = go.Figure(data=weekly_table)

fig.update_layout(title_text="Ten Highest Single Week Case Counts (Age Demographics)",
                  margin = go.layout.Margin(l=0, #left margin
                                            r=0, #right margin
                                            b=0, #bottom margin
                                            t=25  #top margin
                                            ),
                  #height=1000,
                  #width=650
                  )


plot(fig,filename='graphics/WCIL-TopTenWeeksDemo.html')
div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/WCIL-TopTenWeeksDemo.txt','w') as f:
    f.write(div)
    f.close()


#%%%

# Time till 100 Cases Analysis

thresholds = pd.Index([1] + list(range(0,1501,100))[1:]).rename('Threshold')
reached = pd.Series(data = [by_day['Total Positive'].ge(t).idxmax() for t in thresholds],index=thresholds).rename('Date Reached')
reached = reached.to_frame()
reached['Time From Previous'] = reached['Date Reached'].diff()
next_thresh = reached['Time From Previous'].iloc[1:].gt(pd.Timedelta(0,unit="D")).idxmin()
tdays = reached['Date Reached'].loc[reached.index[ reached.index < next_thresh ]]
reached = reached.loc[:next_thresh-100]
actuals = by_day['Total Positive'].loc[tdays].astype(int)
actuals.index = tdays.index
reached['Total On Date'] = actuals

#%%

# collect time till for each benchmark 
tot = reached.iloc[1:]['Time From Previous'].cumsum()
for bench in [300,500]:
    col = 'Time From Previous ('+str(bench) +')'
    reached[col] = None
    for t in range(bench,next_thresh,bench):
        reached.loc[t,col] = tot.loc[t]
        if t > bench:
            reached.loc[t,col] = reached.loc[t,col] - tot.loc[t-bench]
            

#%%

headers=['<b>Threshold</b>','<b>Date Crossed</b>','<b> Actual Total </b>',
         '<b>Days Since last 100</b>']
vals = [reached.index,
        reached['Date Reached'].apply(lambda d: str(d.date())),
        reached['Total On Date'],
        reached['Time From Previous'].apply(lambda d: str(d.days) + ' days')]
vals[3].loc[1] = '--'

tt100 = go.Table(header={'values':headers,
                                 'align':'left',
                                 'fill_color':'gainsboro'},
                        cells={'values': vals,
                                 'align': 'left',
                                 'fill_color': 'whitesmoke',
                                 'height':30})

fig = go.Figure(data=tt100)

fig.update_layout(title_text="Time to Accumulate 100 Cases",
                  margin = go.layout.Margin(l=0, #left margin
                                            r=0, #right margin
                                            b=0, #bottom margin
                                            t=25  #top margin
                                            )
                  )                  
plot(fig,filename='graphics/timeto100.html')
div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/WCIL-TimeTo100.txt','w') as f:
    f.write(div)
    f.close()


#%%
start_date = pd.to_datetime('2020-11-01')
end_date = pd.to_datetime('2020-11-30')
full_usaf = cvda.expandUSFData(full_cases_usaf.loc[start_date:end_date], population)

#%%

nov = full_usaf[['New Positive','New Deaths','New Positive per 100k','New Deaths per 100k']]
nov = nov.groupby('countyFIPS').sum()
il_idx = nov.index[ (nov.index / 1000).astype(int) == 17 ]
nov['Case Rank per 100k'] = nov['New Positive per 100k'].rank(ascending=False,method='min')
nov['Death Rank per 100k'] = nov['New Deaths per 100k'].rank(ascending=False,method='min')
il = nov.loc[il_idx].copy()
il['Case Rank per 100k'] = il['New Positive per 100k'].rank(ascending=False,method='min')
il['Death Rank per 100k'] = il['New Deaths per 100k'].rank(ascending=False,method='min')
wcil_usa = nov.loc[17187]
wcil_il = il.loc[17187]


#%%

lastday = full_usaf.index[-1][0]
lastdata = full_usaf.loc[lastday]
lastdata['Case Rank per 100k'] = lastdata['Total Positive per 100k'].rank(ascending=False,method='min')
lastdata['Death Rank per 100k'] = lastdata['Total Deaths per 100k'].rank(ascending=False,method='min')
il = lastdata.loc[17].copy()
il['Case Rank per 100k'] = il['Total Positive per 100k'].rank(ascending=False,method='min')
il['Death Rank per 100k'] = il['Total Deaths per 100k'].rank(ascending=False,method='min')
wcil_usa = lastdata.loc[17,17187]
wcil_il = il.loc[17187]

#%%

fig = px.histogram(il,y='Total Positive per 100k')
plot(fig)

#%%

day_counts = tests_wchd['New Positive'].reset_index()
day_counts['day'] = day_counts['date'].apply(lambda d: d.strftime("%A"))
day_counts['week'] = day_counts['date'].apply(lambda d : d.week)
day_counts = day_counts.pivot(index='day',columns='week',values='New Positive').T
day_counts = day_counts[['Monday','Tuesday','Wednesday',
                         'Thursday','Friday',
                         'Saturday','Sunday']]
#%%

past = day_counts.iloc[:-1,:].fillna(0).astype(int)
thisweek = day_counts.iloc[-1,:]
thisweek = thisweek[ thisweek.notna() ].astype(int)
fig = go.Figure()
for d in past.columns:
    fig.add_trace(go.Box(y=past[d],
                         showlegend=False,
                         name=d,
                         boxpoints='all',
                         jitter=0.25,
                         marker_color=px.colors.qualitative.Safe[0],
                         ))
fig.add_trace(go.Scatter(x=thisweek.index,y=thisweek.values,
                         mode='markers',
                         marker_color=px.colors.qualitative.Safe[9],
                         marker_size = 12,
                         name = 'This Week'))    
fig.update_yaxes(title='Number of Cases Reported')
fig.update_layout(title="New Cases by Day of the Week")    
plot(fig,filename='graphics/NewCasesByDay.html')