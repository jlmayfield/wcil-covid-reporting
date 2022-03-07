#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sep 10 10:09:58 2021

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

idphnums = cvdp.loadidphdaily()
idph_daily = cvda.expandIDPHDaily(cvdp.prepidphdaily(idphnums))

age,race,gender = cvdp.loadidphdemos('Warren')

pops,usafcases,usafdeaths, = cvdp.loadusafacts()
usafnums = cvdp.prepusafacts(usafcases,usafdeaths)


# from IL DPH site for vaccine data (1/31/21)
p = 17032

#%%

margs = go.layout.Margin(l=0, #left margin
                         r=0, #right margin
                         b=35, #bottom margin
                         t=65  #top margin
                         )      

def demoexpand_daily(tots):
    demo_name = tots.index.names[1]
    news = tots.groupby(level=demo_name).diff().fillna(0)
    news.columns = ['New Positive','New Tests','New Deaths']    
    return pd.concat([tots,news],axis=1)


gbyweek = pd.Grouper(level='date',
                     freq='W-SUN',
                     closed='left',
                     label='left')

gbymonth = pd.Grouper(level='date',
                      freq='MS')

day_one = '2020-04-11'
first_1k = '2020-11-24' 
day_one_2k = '2020-11-25'
second_1k = '2021-08-29'
day_one_3k = '2021-08-30'
third_1k = '2021-12-31'
day_one_4k = '2022-01-01'

#%%

cols = ['New Tests', 'New Positive', 'New Negative',
       'New Positive per 100k', '% New Positive', '7 Day Avg New Positive',
       '7 Day Avg % New Positive', 'Positive Test Rate 7 Day Window',
       'New Deaths', 'Total Tests', 'Total Positive', 'Total Negative',
       'Total Deaths']
by_day = idph_daily.loc[:,17,17187][cols]
by_day = by_day[day_one:]
firstk = by_day[day_one:first_1k]
secondk = by_day[day_one_2k:second_1k]
thirdk = by_day[day_one_3k:third_1k]

agedemos = demoexpand_daily(age)
racedemos = demoexpand_daily(race)

#%%


# Time till ... Cases Analysis

thresholds = pd.Index([1]+list(range(0,4000,1000))[1:]).rename('Threshold')
#%% 


reached = pd.Series(data = [by_day['Total Positive'].ge(t).idxmax() for t in thresholds],index=thresholds).rename('Date Reached')
reached = reached.to_frame()
reached['Time to Accumulate'] = reached['Date Reached'].diff()
actuals = by_day['Total Positive'].loc[reached['Date Reached']].astype(int)
actuals.index = reached.index
reached['Total On Date'] = actuals
ptotals = reached['Total On Date'].diff().fillna(0).astype(int)
reached['Period Total'] = ptotals


#%%

headers=['<b>Threshold</b>','<b>Date Crossed</b>','<b> Cummulative Total </b>',
         '<b>Period Total</b>','<b>Time to Accumulate</b>']

vals = [reached.index,
        reached['Date Reached'].apply(lambda d: str(d.date())),
        reached['Total On Date'],
        reached['Period Total'],
        reached['Time to Accumulate'].apply(lambda d: str(d.days) + ' days'),
        ]
vals[4].iloc[0] = '--'
vals[3].iloc[0] = 1

tt100 = go.Table(header={'values':headers,
                                 'align':'left',
                                 'fill_color':'gainsboro'},
                        cells={'values': vals,
                                 'align': 'left',
                                 'fill_color': 'whitesmoke',
                                 'height':30})

fig = go.Figure(data=tt100)

fig.update_layout(title_text="Time to Accumulate 1000 Cases",
                  margin = go.layout.Margin(l=0, #left margin
                                            r=0, #right margin
                                            b=0, #bottom margin
                                            t=25  #top margin
                                            ),
                  height = 250
                  )                  
plot(fig,filename='graphics/timeto1000.html')
div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/WCIL-TimeTo1000.txt','w') as f:
    f.write(div)
    f.close()


#%%

# Daily case counts with 7 day average and 'by thousand' groups

firstmax = by_day.loc[day_one:first_1k]['New Positive'].max()
secondmax = by_day.loc[day_one_2k:second_1k]['New Positive'].max()
thirdmax = by_day.loc[day_one_3k:third_1k]['New Positive'].max()
fourthmax = by_day.loc[day_one_4k:]['New Positive'].max()
maxmax = by_day['New Positive'].max()
minmin = by_day['New Positive'].min()

fig = go.Figure()
fig.add_trace(go.Bar(name='Daily Cases',
                     x=by_day.index,
                     y=by_day['New Positive'],
                     showlegend=False,
                     marker_color='blue')              
             )
fig.add_trace(go.Scatter(name='7 Day Average',
                         x=by_day.index,
                         y=by_day['7 Day Avg New Positive'],
                         showlegend=False,
                         mode='lines',
                         marker_color='darkblue'))
fig.update_yaxes(range=(minmin,maxmax+5))
totrange = maxmax+5-minmin

fig.add_vrect(x0=day_one, x1=first_1k, y1=(firstmax-minmin)/totrange,
              annotation_text="First 1000 Cases", annotation_position='top left',
              fillcolor="gray", opacity=0.2, line_width=0)
fig.add_vrect(x0=day_one_2k, x1=second_1k,y1=(secondmax-minmin)/totrange,
              annotation_text="Second 1000 Cases", annotation_position="top left",
              fillcolor="gray", opacity=0.2, line_width=0)
fig.add_vrect(x0=day_one_3k, x1=third_1k,y1=(thirdmax-minmin)/totrange,
              annotation_text="Third 1000 Cases", annotation_position="top left",
              fillcolor="gray", opacity=0.2, line_width=0)
fig.add_vrect(x0=day_one_4k, x1=third_1k,y1=(thirdmax-minmin)/totrange,
              annotation_text="Third 1000 Cases", annotation_position="top left",
              fillcolor="gray", opacity=0.2, line_width=0)

fig.update_layout(title_text='Daily New Positive COVID Tests <br> Warren County, IL',
                  height=600,width=1200,
                  hovermode='x unified',
                  margin = go.layout.Margin(l=0, #left margin
                                            r=0, #right margin
                                            b=25, #bottom margin
                                            t=65  #top margin
                                            )
                  )


hist = plot(fig,include_plotlyjs=False,output_type='div')
with open('graphics/dailyByThousands.txt','w') as f:
    f.write(hist)
    f.close()
plot(fig,filename='graphics/dailyByThousands.html')

#%%

cols = ['<20','20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+']
demos_1k = agedemos.loc[day_one:first_1k]['New Positive'].groupby(by='age_group').sum().loc[cols]
demos_2k = agedemos.loc[day_one_2k:second_1k]['New Positive'].groupby(by='age_group').sum().loc[cols]
demos_3k = agedemos.loc[day_one_3k:third_1k]['New Positive'].groupby(by='age_group').sum().loc[cols]
maxmax = max(demos_1k.max(),
             demos_2k.max(),
             demos_3k.max())

clrs = px.colors.sequential.Blues

fig = make_subplots(rows=1,cols=3,
                    subplot_titles=(day_one + ' to ' + first_1k,
                                    day_one_2k + ' to ' + second_1k,
                                    day_one_3k + ' to ' + third_1k),
                    shared_yaxes=True)

fig.add_trace(go.Bar(name='First 1000',
                     x=cols,
                     y=demos_1k,
                     marker_color=clrs[4],
                     showlegend=False),
              row=1,col=1)
fig.add_trace(go.Bar(name='Second 1000',
                     x=cols,
                     y=demos_2k,
                     marker_color=clrs[6],
                     showlegend=False),
              row=1,col=2)
fig.add_trace(go.Bar(name='Third 1000',
                     x=cols,
                     y=demos_3k,
                     marker_color=clrs[8],
                     showlegend=False),
              row=1,col=3)

fig.update_layout(title='Age Demographic Breakdown in ~1000 Case Increments',
                  margin = go.layout.Margin(l=0, #left margin
                                            r=0, #right margin
                                            b=20, #bottom margin
                                            t=65  #top margin
                                            ),
                  width=1200,
                  height=600)
hist = plot(fig,include_plotlyjs=False,output_type='div')
with open('graphics/first3kdemos.txt','w') as f:
    f.write(hist)
    f.close()
plot(fig,filename='graphics/first3kdemos.html')

#%%


cols = ['Hispanic', 'Asian', 'Black', 'Other', 'White', 'NH/PI*', 'AI/AN**',
       'Left Blank']
demos_1k = racedemos.loc[day_one:first_1k]['New Positive'].groupby(by='race_group').sum().loc[cols]
demos_2k = racedemos.loc[day_one_2k:second_1k]['New Positive'].groupby(by='race_group').sum().loc[cols]
demos_3k = racedemos.loc[day_one_3k:third_1k]['New Positive'].groupby(by='race_group').sum().loc[cols]
maxmax = max(demos_1k.max(),
             demos_2k.max(),
             demos_3k.max())

clrs = px.colors.sequential.Blues

fig = make_subplots(rows=1,cols=3,
                    subplot_titles=(day_one + ' to ' + first_1k,
                                    day_one_2k + ' to ' + second_1k,
                                    day_one_3k + ' to ' + third_1k),
                    shared_yaxes=True)

fig.add_trace(go.Bar(x=cols,
                     y=demos_1k,
                     marker_color=clrs[4],
                     showlegend=False),
              row=1,col=1)
fig.add_trace(go.Bar(x=cols,
                     y=demos_2k,
                     marker_color=clrs[6],
                     showlegend=False),
              row=1,col=2)
fig.add_trace(go.Bar(x=cols,
                     y=demos_3k,
                     marker_color=clrs[8],
                     showlegend=False),
              row=1,col=3)

fig.update_layout(title='Race Demographic Breakdown in ~1000 Case Increments',
                  margin = go.layout.Margin(l=0, #left margin
                                            r=0, #right margin
                                            b=20, #bottom margin
                                            t=65  #top margin
                                            )
                  )
hist = plot(fig,include_plotlyjs=False,output_type='div')
with open('graphics/first3kracedemos.txt','w') as f:
    f.write(hist)
    f.close()
plot(fig,filename='graphics/first3kracedemos.html')

