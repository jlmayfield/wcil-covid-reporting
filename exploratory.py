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


# 17187,17 <-- Warren County, IL
warren = [17187]
p = 16981

population,cases = cvdp.loadusafacts()
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
full_cases_usaf = cvdp.prepusafacts(cases)
aoi = [17187,17095,17109]
aoi_cases_usaf = cvda.expandUSFData(full_cases_usaf.loc[:,:,aoi], population)

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

    #%%

fig = px.bar(by_month,x=[d.month_name() for d in by_month.index],
             y=['Cases 0-10','Cases 10-20','Cases 20-40',
                'Cases 40-60','Cases 60-80','Cases 80-100'],
             labels={'variable':'Age Range','x':'Month','value':'New Cases'},             
             title="New Cases Per Month (with Demographics)",
             color_discrete_sequence=px.colors.qualitative.Safe
             )
fig.update_xaxes(tickvals=[d.month_name() for d in by_month.index])
plot(fig,filename='graphics/WCIL-AllMonthsDemos.html')
div = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/WCIL-AllMondsDemos.txt','w') as f:
    f.write(div)
    f.close()

#%%

# plot 4 weeks of new case averages and positivity averages
weeks = 27
threeweeks = by_day.iloc[weeks*-7:]

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=threeweeks.index, y=threeweeks['7 Day Avg New Positive'],
               name="New Cases (7 day avg)"),               
    secondary_y=False,
)


fig.add_trace(
    go.Scatter(x=threeweeks.index, y=threeweeks['7 Day Avg % New Positive'],
               name="Positivity (7 day avg)"),
    secondary_y=True,
)

# Add figure title
fig.update_layout(
    title_text="New Cases and Positivity: 7 Day Rolling Averages",
    #margin = margs,
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01),
    height = 400
)

# Set x-axis title
fig.update_xaxes(title_text="Date")

# Set y-axes titles
fig.update_yaxes(title_text="<b>New Cases (7 day avg)</b>", 
                 range = (0,15),
                 secondary_y=False)
fig.update_yaxes(title_text="<b>Positivity (7 day avg)</b>", 
                 range = (0,.5),
                 tickformat = ',.0%',
                 secondary_y=True)

plot(fig,filename='graphics/dailycaseavg.html')

#%%


# plot 4 weeks of new case averages and positivity averages
weeks = 16
threeweeks = by_day.iloc[weeks*-7:]

fig = go.Figure()
fig.add_trace(go.Scatter(x=threeweeks.index, 
                         y=threeweeks['7 Day Avg New Positive'],
                         name="WC",
                         hovertemplate="%{y:.1f}"
              ))

fig.add_trace(go.Scatter(x=threeweeks.index, 
                         y=reports_mc['7 Day Avg Everyone'].loc[threeweeks.index],
                         name="MC",
                         hovertemplate="%{y:.1f}"
              ))

# Add figure title
fig.update_layout(
    title_text="New Cases in Warren County and Monmouth College (7 Day Averages)",
    #margin = margs,
    legend=dict(
        yanchor="top",
        y=0.99,
        xanchor="left",
        x=0.01),
    height = 400,
    hovermode='x unified'
)

# Set x-axis title
fig.update_xaxes(title_text="Date")
# Set y-axes titles
fig.update_yaxes(title_text="<b>New Cases (7 day avg)</b>", 
                 range = (0,15),
                 )

plot(fig,filename='graphics/wcil_mc_dailyavg.html')


#%%

age_groups = ['Cases 0-10','Cases 10-20', 'Cases 20-40',
       'Cases 40-60', 'Cases 60-80', 'Cases 80-100']
demo_daily = by_day[['Cases 0-10','Cases 10-20', 'Cases 20-40',
       'Cases 40-60', 'Cases 60-80', 'Cases 80-100']]

sda = [cvda._mc7day(demo_daily[a]) for a in age_groups]
demo_daily = pd.concat([demo_daily,*sda],axis=1)
demo_avgs = demo_daily[['7 Day Avg '+ a for a in age_groups]]    

#%%

fig = go.Figure()
for c in demo_avgs.columns:
    fig.add_trace(go.Scatter(x=demo_avgs.index,
                             y=demo_avgs[c],
                             name=c))
plot(fig,filename='graphics/dailyDemoAvgs.html')   

#%%

kw = population[population['County Name'].isin(['Warren County', 'Knox County'])]
kw = kw[kw['State'] == 'IL'] 
# warren --> knox  = 2.95
# knox --> warren = 0.33

data_idph = pd.read_csv('ILDPH_Reports.csv',
                        header=[0],index_col=0,
                        parse_dates=True).fillna(0)

kw_cases = data_idph[['New Positive','New Tests','Knox New Positive','Knox New Tests']]
kw_cases['New Negative'] = kw_cases['New Tests'] - kw_cases['New Positive']
kw_cases['Knox New Negative'] = kw_cases['Knox New Tests'] - kw_cases['Knox New Positive']
kw_cases = kw_cases.iloc[:-3]
w2k = kw['population'].iloc[0] / kw['population'].iloc[1]