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

from urllib.request import urlopen
import json
with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

MB_TOKEN = open(".mapbox_token").read()

import cvdataprep as cvdp
import cvdataanalysis as cvda
import cvdataviz as cvdv

#%%


# 17187,17 <-- Warren County, IL
warren = [17187]
p = 16981

population = pd.read_csv('covid_county_population_usafacts.csv',
                         dtype={'countyFIPS':np.int64,
                                'County Name':str, 'State':str,
                                'population':np.int64},
                         index_col = 'countyFIPS')

cases = pd.read_csv('covid_confirmed_usafacts.csv',
                         dtype={'countyFIPS':np.int64,'stateFIPS':np.int64,
                                'County Name':str, 'State':str},                         
                         index_col = 'countyFIPS')

reports_wchd = pd.read_csv('WCHD_Reports.csv',
                         header=[0],index_col=0,
                         parse_dates=True).fillna(0)

demo_wchd = pd.read_csv('WCHD_Case_Demographics.csv',
                       skiprows=[2],
                       header=[0,1],index_col=0,
                       parse_dates=True).fillna(0).iloc[:,0:12]

death_wchd = pd.read_csv('WCHD_Death_Demographics.csv',
                       skiprows=[2],
                       header=[0,1],index_col=0,
                       parse_dates=True).fillna(0).iloc[:,0:12]

#%%

def daily(basis,demo,pop):
    basis = pd.concat([basis,
                       cvda._per100k(basis['New Positive'], pop)
                       ],                       
                      axis=1)
    basis = basis.loc[:,17,17187]
    basis['Cases 0-10'] = (demo.T.loc[(slice(None),['0-10']),:].T).sum(axis=1).astype(int)
    basis['Cases 10-20'] = (demo.T.loc[(slice(None),['10-20']),:].T).sum(axis=1).astype(int)
    basis['Cases 20-40'] = (demo.T.loc[(slice(None),['20-40']),:].T).sum(axis=1).astype(int)
    basis['Cases 40-60'] = (demo.T.loc[(slice(None),['40-60']),:].T).sum(axis=1).astype(int)
    basis['Cases 60-80'] = (demo.T.loc[(slice(None),['60-80']),:].T).sum(axis=1).astype(int)
    basis['Cases 80-100'] = (demo.T.loc[(slice(None),['80-100']),:].T).sum(axis=1).astype(int)
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

by_day = daily(full_tests_wchd,demo_wchd,population)
by_week = weekly(by_day).iloc[3:]
by_month = monthly(by_day)


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

vals = [top_ten['Week Number'],
        top_ten['date'].apply(lambda d: d.strftime("%B %d")),        
        top_ten['New Positive'],
        top_ten['Cases 0-10'],
        top_ten['Cases 10-20'],        
        top_ten['Cases 20-40'],
        top_ten['Cases 40-60'],
        top_ten['Cases 60-80'],
        top_ten['Cases 80-100']]
headers = ['<b>Week Number</b>',
           '<b>Week Start Date</b>',           
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



#%%


fig = px.bar(by_week,x=by_week.index,
             y=['Cases 0-10','Cases 10-20','Cases 20-40',
                'Cases 40-60','Cases 60-80','Cases 80-100'],
             labels={'variable':'Age Range','date':'Week Start Date',
                     'value':'New Cases'},             
             title="New Cases Per Week (with Demographics)",
             color_discrete_sequence=px.colors.qualitative.Safe
             )
fig.update_xaxes(tickvals=by_week.index)
plot(fig,filename='graphics/WCIL-AllWeeksDemos.html')
div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/WCIL-AllWeeksDemos.txt','w') as f:
    f.write(div)
    f.close()



