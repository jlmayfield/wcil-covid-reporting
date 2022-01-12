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
import plotly.express as px


import cvdataprep as cvdp
import cvdataanalysis as cvda
import cvdataviz as cvdv

#%%

margs = go.layout.Margin(l=0, #left margin
                         r=0, #right margin
                         b=35, #bottom margin
                         t=50  #top margin
                         )       

idphnums = cvdp.loadidphdaily('Warren')
age,race,gender = cvdp.loadidphdemos('Warren')
idphnums_k = cvdp.loadidphdaily('Knox')
age_k,race_k,gender_k = cvdp.loadidphdemos('Knox')

#%%
# from IL DPH site for vaccine data (1/31/21)
p = 17032

idph_daily = cvda.expandIDPHDaily(cvdp.prepidphdaily(idphnums),p)
idph_daily_knox = cvda.expandIDPHDaily(cvdp.prepidphdaily(idphnums_k),50112)


gbyweek = pd.Grouper(level='date',
                     freq='W-SUN',
                     closed='left',
                     label='left')

gbymonth = pd.Grouper(level='date',
                      freq='MS')

#%%

def dailytoweekly(daily):
    daily = daily[['New Positive','New Tests','New Deaths','New Positive per 100k']]
    weekly = daily.groupby(gbyweek).sum()
    tots = weekly.cumsum()
    tots.columns = ['Total Positive','Total Tests','Total Deaths','Total Positive per 100k']
    return pd.concat([weekly,tots],axis=1)
    
def dailytomonthly(daily):
    daily = daily[['New Positive','New Tests','New Deaths','New Positive per 100k']]
    monthly = daily.groupby(gbymonth).sum()
    tots = monthly.cumsum()
    tots.columns = ['Total Positive','Total Tests','Total Deaths','Total Positive per 100k']
    return pd.concat([monthly,tots],axis=1)   


def demoexpand_daily(tots):
    demo_name = tots.index.names[1]
    news = tots.groupby(level=demo_name).diff().fillna(0)
    news.columns = ['New Positive','New Tests','New Deaths']
    
    return pd.concat([tots,news],axis=1)


def demoexpand(tots):
    demo_name = tots.index.names[1]
    news = tots.groupby(level=demo_name).diff().fillna(0)
    news.columns = ['New Positive','New Tests','New Deaths']
    new_weekly = news.unstack().groupby(pd.Grouper(level='date',
                                                  freq='W-SUN',
                                                  closed='left',
                                                  label='left')).sum().stack()
    return new_weekly

def demoexpand_monthly(tots):
    demo_name = tots.index.names[1]
    news = tots.groupby(level=demo_name).diff().fillna(0)
    news.columns = ['New Positive','New Tests','New Deaths']
    new_monthly = news.unstack().groupby(pd.Grouper(level='date',
                                                    freq='MS')).sum().stack()
    return new_monthly

#%%
age_daily = demoexpand_daily(age)
age_weekly = demoexpand(age)
age_monthly = demoexpand_monthly(age)
race_weekly = demoexpand(race)
gender_weekly = demoexpand(gender)

age_daily_k = demoexpand_daily(age_k)
age_weekly_k = demoexpand(age_k)
age_monthly_k = demoexpand_monthly(age_k)
race_weekly_k = demoexpand(race_k)
gender_weekly_k = demoexpand(gender_k)

#%%

warren_weekly = dailytoweekly(idph_daily)
knox_weekly = dailytoweekly(idph_daily_knox)


warren_monthly = dailytomonthly(idph_daily)
knox_monthly = dailytomonthly(idph_daily_knox)

#%%

weekly_sorted = warren_weekly[['New Positive','New Tests','New Deaths']].sort_values('New Positive',ascending=False)
idx = weekly_sorted.iloc[:10].index

weekly_topten = weekly_sorted.loc[idx]
age_toptwo = age_weekly.loc[idx[:2]][['New Positive','New Tests']]
gender_toptwo = gender_weekly.loc[idx[:2]][['New Positive','New Tests']]
race_toptwo = race_weekly.loc[idx[:2]][['New Positive','New Tests']]

weekly_topten['% positive'] = weekly_topten['New Positive'] / weekly_topten['New Tests']
age_toptwo['% positive'] = age_toptwo['New Positive'] / age_toptwo['New Tests']

age_toptwo = age_toptwo.loc[(slice(None),age_order),:].rename(index={'<20':'0-20'}).loc[idx[:2]]

#%%

octmax_w = warren_weekly.loc["2020-09-27":"2020-10-25"]['New Positive'].max()
octmax_k = knox_weekly.loc["2020-09-27":"2020-10-25"]['New Positive'].max()

augmax_w = warren_weekly.loc["2021-08-01":"2021-08-29"]['New Positive'].max()
augmax_k = knox_weekly.loc["2021-08-01":"2021-08-29"]['New Positive'].max()

octmax_p100k = max(warren_weekly.loc["2020-09-27":"2020-10-25"]['New Positive per 100k'].max(),
             knox_weekly.loc["2020-09-27":"2020-10-25"]['New Positive per 100k'].max())
augmax_p100k = max(warren_weekly.loc["2021-08-01":"2021-08-29"]['New Positive per 100k'].max(),
             knox_weekly.loc["2021-08-01":"2021-08-29"]['New Positive per 100k'].max())


weeklymax = max(warren_weekly['New Positive'].max(),
                knox_weekly['New Positive'].max())
weeklymax_p100k = max(warren_weekly['New Positive per 100k'].max(),
                      knox_weekly['New Positive per 100k'].max())


fig = make_subplots(rows=2,cols=2,
                    subplot_titles=('Warren County','Knox County',
                                    'Warren County (per 100k)','Knox County (per 100k)'),
                    shared_xaxes=True,
                    vertical_spacing=0.1
                    )
fig.add_trace(go.Bar(name='Warren',
                     x=warren_weekly.index,
                     y=warren_weekly['New Positive'],
                     showlegend=False,
                     marker_color='darkblue'),
              row=1,col=1
             )
fig.add_trace(go.Bar(name='Knox',
                     x=knox_weekly.index,
                     y=knox_weekly['New Positive'],
                     showlegend=False,
                     marker_color='darkcyan'),
              row=1,col=2)
fig.add_trace(go.Bar(name='Warren (per 100k)',
                     x=warren_weekly.index,
                     y=warren_weekly['New Positive per 100k'],
                     showlegend=False,
                     marker_color='darkblue'),
              row=2,col=1
             )
fig.add_trace(go.Bar(name='Knox (per 100k)',
                     x=knox_weekly.index,
                     y=knox_weekly['New Positive per 100k'],
                     showlegend=False,
                     marker_color='darkcyan'),
              row=2,col=2)
fig.update_yaxes(range=(0,weeklymax+10),row=1,col=1)
fig.update_yaxes(range=(0,weeklymax+10),row=1,col=2)
fig.update_yaxes(range=(0,weeklymax_p100k+10),row=2,col=1)
fig.update_yaxes(range=(0,weeklymax_p100k+10),row=2,col=2)

fig.add_vrect(x0="2020-09-27", x1="2020-10-25", 
              y1=(octmax_w+10)/(weeklymax+10),
              row=1, col=1,
              #annotation_text="October '20", annotation_position="top left",
              fillcolor="firebrick", opacity=0.3, line_width=0)
fig.add_vrect(x0="2020-09-27", x1="2020-10-25", 
              y1=(octmax_k+10)/(weeklymax+10),
              row=1, col=2,
              #annotation_text="October '20", annotation_position="top left",
              fillcolor="firebrick", opacity=0.3, line_width=0)
fig.add_vrect(x0="2021-08-01", x1="2021-08-29", 
              y1=(augmax_w+10)/(weeklymax+10),
              row=1, col=1,
              #annotation_text="August '21", annotation_position="top left",
              fillcolor="firebrick", opacity=0.3, line_width=0)
fig.add_vrect(x0="2021-08-01", x1="2021-08-29", 
              y1=(augmax_k+10)/(weeklymax+10),
              row=1, col=2,
              #annotation_text="August '21", annotation_position="top left",
              fillcolor="firebrick", opacity=0.3, line_width=0)

fig.add_vrect(x0="2020-09-27", x1="2020-10-25", 
              y1=(octmax_p100k+10)/(weeklymax_p100k+10),
              row=2, col='all',
              #annotation_text="October '20", annotation_position="top left",
              fillcolor="firebrick", opacity=0.3, line_width=0)
fig.add_vrect(x0="2021-08-01", x1="2021-08-29", 
              y1=(augmax_p100k+10)/(weeklymax_p100k+10),
              row=2, col='all',
              #annotation_text="August '21", annotation_position="top left",
              fillcolor="firebrick", opacity=0.3, line_width=0)


fig.update_layout(title_text='New COVID Cases per Week',
                  height=600,width=1200,
                  margin=margs)


hist = plot(fig,include_plotlyjs=False,output_type='div')
with open('graphics/aug2021post.txt','w') as f:
    f.write(hist)
    f.close()
plot(fig,filename='graphics/aug2021post.html')


#%%



top8_w = warren_monthly[['New Positive','New Positive per 100k']].sort_values('New Positive',ascending=False)[:8]
top8_k = knox_monthly[['New Positive','New Positive per 100k']].sort_values('New Positive',ascending=False)[:8]

top8_tab_w = go.Table(header={'values':['<b>Month</b>',
                                            '<b>Cases</b>',
                                            '<b>Cases per 100k</b>'                                            
                                            ],
                                      'align':'left',
                                  'fill_color':'gainsboro'},
                          cells={'values':[top8_w.index.strftime('%b %Y'),
                                           top8_w['New Positive'],
                                           top8_w['New Positive per 100k'].map(u"{:.1f}".format)],
                                 'align':'left',
                                 'fill_color':
                                     [['whitesmoke']*2+['papayawhip']*2+['whitesmoke']*4,
                                      ['whitesmoke']*2+['papayawhip']*2+['whitesmoke']*4,
                                      ['whitesmoke']*2+['papayawhip']*2+['whitesmoke']*4
                                      ]
                                 })

top8_tab_k = go.Table(header={'values':['<b>Month</b>',
                                            '<b>Cases</b>',
                                            '<b>Cases per 100k</b>'                                            
                                            ],
                                  'align':'left',
                                  'fill_color':'gainsboro'},
                          cells={'values':[top8_k.index.strftime('%b %Y'),
                                           top8_k['New Positive'],
                                           top8_k['New Positive per 100k'].map(u"{:.1f}".format)],
                                 'align':'left',
                                 'fill_color':
                                     [['whitesmoke']*2+['papayawhip']+['whitesmoke']+['papayawhip']+['whitesmoke']*3,
                                      ['whitesmoke']*2+['papayawhip']+['whitesmoke']+['papayawhip']+['whitesmoke']*3,
                                      ['whitesmoke']*2+['papayawhip']+['whitesmoke']+['papayawhip']+['whitesmoke']*3
                                      ]
                                 })
    
fig = make_subplots(rows=1,cols=2,
                    subplot_titles=('Warren County','Knox County'),
                    specs=[[{"type": "table"},{"type": "table"}]]
                   )
fig.add_trace(top8_tab_w,row=1,col=1)
fig.add_trace(top8_tab_k,row=1,col=2)

fig.update_layout(title="Top Eight Months for New Covid Cases",
                  margin = go.layout.Margin(l=0, #left margin
                                            r=0, #right margin
                                            b=35, #bottom margin
                                            t=75  #top margin
                                            ),
                  height=400,width=1000)

top8_tab = plot(fig,include_plotlyjs=False,output_type='div')
with open('graphics/aug2021post_tab.txt','w') as f:
    f.write(top8_tab)
    f.close()
plot(fig,filename='graphics/aug2021post_tab.html')

#%%

oct_age_w = age_monthly.loc['2020-10-01']['New Positive'].sort_values(ascending=False).reset_index().set_index('age_group').drop('date',axis=1)
oct_age_k = age_monthly_k.loc['2020-10-01']['New Positive'].sort_values(ascending=False).reset_index().set_index('age_group').drop('date',axis=1)
aug_age_w = age_monthly.loc['2021-08-01']['New Positive'].sort_values(ascending=False).reset_index().set_index('age_group').drop('date',axis=1)
aug_age_k = age_monthly_k.loc['2021-08-01']['New Positive'].sort_values(ascending=False).reset_index().set_index('age_group').drop('date',axis=1)

#%%

def agetab(df):
    fig = go.Table(header={'values':['<b>Age Group</b>',
                                        '<b>Cases</b>',
                                        '<b>Percent of Total</b>'                                            
                                            ],
                                      'align':'left',
                                  'fill_color':'gainsboro'},
                          cells={'values':[df.index,
                                           df['New Positive'],
                                           (df['New Positive']/df['New Positive'].sum()).map(u"{:.1%}".format)],
                                 'align':'left',
                                 'fill_color':
                                     ['whitesmoke','whitesmoke','whitesmoke']
                                 })
    return fig

#%%

oct_tab_w = agetab(oct_age_w)
oct_tab_k = agetab(oct_age_k)
aug_tab_w = agetab(aug_age_w)
aug_tab_k = agetab(aug_age_k)

#%%    

fig = make_subplots(rows=2,cols=2,
                    subplot_titles=('Warren County, October 2020','Warren County, Auguset 2021',
                                    'Knox County, October 2020','Knox County, August 2021'),
                    specs=[[{"type": "table"},{"type": "table"}],
                           [{"type": "table"},{"type": "table"}]],
                    vertical_spacing = 0.05
                   )
fig.add_trace(oct_tab_w,row=1,col=1)
fig.add_trace(aug_tab_w,row=1,col=2)
fig.add_trace(oct_tab_k,row=2,col=1)
fig.add_trace(aug_tab_k,row=2,col=2)

fig.update_layout(title="Covid Case Age Demographics",
                  margin = go.layout.Margin(l=0, #left margin
                                            r=0, #right margin
                                            b=35, #bottom margin
                                            t=75  #top margin
                                            ),
                  height=675,width=1000)
demo_tab = plot(fig,include_plotlyjs=False,output_type='div')
with open('graphics/aug2021post_demo.txt','w') as f:
    f.write(demo_tab)
    f.close()
plot(fig,filename='graphics/aug2021post_demo.html')

#%%

fig = px.bar(oct_age_w)
plot(fig)
fig = px.bar(aug_age_w)
plot(fig)
fig = px.bar(oct_age_k)
plot(fig)
fig = px.bar(aug_age_k)
plot(fig)

