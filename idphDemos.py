#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 12 12:33:10 2022

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
                         b=25, #bottom margin
                         t=75  #top margin
                         )                  

gbyweek = pd.Grouper(level='date',
                     freq='W-SUN',
                     closed='left',
                     label='left')

gbymonth = pd.Grouper(level='date',
                      freq='MS')

def demoexpand_daily(tots):
    demo_name = tots.index.names[1]
    news = tots.groupby(level=demo_name).diff().fillna(0)
    news.columns = ['New Positive','New Tests','New Deaths']
    
    return pd.concat([tots,news],axis=1)

def demo_weekly(dailies):
    demo_name = dailies.index.names[1]
    news = dailies[['New Positive','New Tests']]
    news = news.groupby([gbyweek,demo_name]).sum()
    tots = dailies[['Total Positive', 'Total Tested']]
    tots = tots.groupby([gbyweek,demo_name]).max().fillna(0)
    return pd.concat([news,tots],axis=1)


def cleanTicks(init, sig, d):
    """
    Produce a clean, no two are so close that they'd overlap, set of tick values

    Parameters
    ----------
    init : sequence of values
        Basic set of tick values (think range(n,m,s))
    sig : sequence of values
        Significant values to be added to init
    d : Int or Float
        Min difference between tick values

    Returns
    -------
    List[Numbers]
        Cleaned up, sorted intersection of init and sig

    """
    a = [{y for y in init if abs(y-s) > d} for s in sig]
    ticks = a[0]
    for s in a[1:]:
        ticks = ticks.intersection(s) 
    ticks = ticks.union(sig)
    return list(ticks)

def ticktext(ticks,sig,f,g=lambda t:str(t)):
    """
    Convert tick values to text, making sig values bold.

    Parameters
    ----------
    ticks : Sequence of values
        The tick values (ideally cleaned)
    sig : sequence of values
        significat value (to be bolded)
    f : function
        text formatting function to apply to members of sig
    g : TYPE, optional
        text formatting function to apply to members of (ticks - sig). default 
        is lambda t:str(t).

    Returns
    -------
    List of strings
        The formatted tick values

    """
    def stringify(t):
        if t in sig:
            return f(t)
        else:
            return g(t)
    ts = [stringify(t) for t in ticks]
    return ts

#%%%

idph_daily = cvda.expandIDPHDaily(cvdp.prepidphdaily(cvdp.loadidphdaily()))

# from IL DPH site for vaccine data (1/31/21)
p = 17032

idph_age_cats = ['20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+', '<20']
age,race,gender = cvdp.loadidphdemos('Warren')
agedemos = demoexpand_daily(age)
agedemos = agedemos.loc[(slice(None),idph_age_cats),:].sort_index()
age_weekly = demo_weekly(agedemos)

demo_groups = age_weekly.index.get_level_values('age_group').unique()
dates =  age_weekly.index.get_level_values('date').unique()
last_date = dates[-1]
last_week = dates[-2]

#%%

# demographic category -> color
clrs = px.colors.sequential.algae
cmap = {demo_groups[i]:clrs[i] for i in range(len(demo_groups))}

#%%

# multiples: cumulative Cases 
#  ticks: col1--> by 100 with current. col 2,3 --> current

cumsum_order = age_weekly.loc[last_date]['Total Positive'].sort_values(ascending=False).index
curtot = age_weekly.loc[last_date]['Total Positive'].sum()
catmax = age_weekly.loc[last_date]['Total Positive'].max().max()

#%%
fig = make_subplots(rows=5,cols=3,
                    #shared_yaxes=True,
                    shared_xaxes=True,
                    specs = [[{},{},{}],
                             [{},{},{}],
                             [{},{},None],                             
                             [{'colspan':3,'rowspan':2},None,None],
                             [None,None,None]],
                    subplot_titles=list(cumsum_order)+['All Demographics']
                    )
for i in range(len(cumsum_order)):
    cat = cumsum_order[i]
    clr = cmap[cat]
    r = int(i/3)+1
    c = int(i%3)+1
    ys = age_weekly.loc[(dates,cat),'Total Positive']
    fig.add_trace(go.Scatter(x=dates,
                             y=ys,
                             name=cat,
                             showlegend=False,
                             fill='tozeroy',
                             mode='lines',
                             marker_color=clr                             
                             ),
                  row = r,col=c)
    if c == 1:
        tsigs = [int(ys.max())]
        tvals = cleanTicks(list(range(0,int(catmax)+10,100)),
                           tsigs,
                           50)
        ttext = ticktext(tvals,tsigs,
                         lambda v: "<b>{}</b>".format(v))
    else:
        tsigs = [int(ys.max())]
        tvals = cleanTicks([],tsigs,50)
        ttext = ticktext(tvals,tsigs,
                         lambda v: "<b>{}</b>".format(v))        
    fig.update_yaxes(tickmode='array',
                     tickvals=tvals,
                     ticktext=ttext,
                     showgrid = False,
                     row=r,col=c)  
    fig.update_xaxes(showgrid=False,row=r,col=c)
cats = demo_groups
for i in range(0,len(cats)):
    fig.add_trace(go.Scatter(x=dates,
                             y=age_weekly.loc[(dates,cats[i]),'Total Positive'],
                             mode='lines',
                             name=cats[i],
                             marker_color=cmap[cats[i]],
                             fill='tonexty',
                             stackgroup='one'                         
                         ),
                  row=4,col=1)
    tsigs = [curtot]
    tvals = cleanTicks(range(0,int(curtot) + 25,500),
                       tsigs,
                       250)
    ttext = ticktext(tvals,tsigs,
                         lambda v: "<b>{}</b>".format(v))   
    fig.update_yaxes(showgrid=False,
                     tickmode='array',
                     tickvals=tvals,
                     ticktext=ttext,
                     row=5,col=1)    
    fig.update_xaxes(showgrid=False,row=5,col=1)

fig.update_yaxes(range=(0,catmax+10))
fig.update_yaxes(range=(0,curtot + 25),row=4)
fig.update_layout(title="Total COVID-19 Cases by IDPH Age Demographic Groups",
                  width= 1200,
                  height= 800,
                  margin=margs,
                  plot_bgcolor='floralwhite')
plot(fig,filename='graphics/idphagedemototals_multiples.html')
div_casetotal = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/WCIL-IDPHAgeDemoTotals.txt','w') as f:
    f.write(div_casetotal)
    f.close()

#%%


# multiples: weekly Cases 
complete_weeks = age_weekly[['New Positive']].loc[:last_week]
complete_dates = complete_weeks.index.get_level_values('date').unique()
currweek_order = complete_weeks.loc[last_week]['New Positive'].sort_values(ascending=False).index
# all time high in a single cat
catmax = complete_weeks.max()
# all time high week
tot=complete_weeks.groupby(level='date').sum().max()

#%%

fig = make_subplots(rows=5,cols=3,
                    #shared_yaxes=True,
                    shared_xaxes=True,
                    specs = [[{},{},{}],
                             [{},{},{}],
                             [{},{},None],                             
                             [{'colspan':3,'rowspan':2},None,None],
                             [None,None,None]],
                    subplot_titles= list(currweek_order) + ['All Demographics'])
for i in range(len(currweek_order)):
    cat = currweek_order[i]
    clr = cmap[cat]
    r = int(i/3)+1
    c = int(i%3)+1
    curr = complete_weeks.loc[(slice(None),cat),'New Positive']
    fig.add_trace(go.Scatter(x=complete_dates,
                             y=curr,
                             name=cat,
                             showlegend=False,
                             fill='tozeroy',
                             mode='lines',
                             marker_color=clr
                             ),
                  row = r, col=c )
    if c == 1:
        tsigs = cleanTicks([int(curr.max())],
                           [int(curr[-1])],
                           3)
        tvals = cleanTicks(list(range(0,int(catmax)+5,10)),
                           tsigs,
                           5)
        ttext = ticktext(tvals,tsigs,
                         lambda v: "<b>{}</b>".format(v))
    else:
        tsigs = cleanTicks([int(curr.max())],
                           [int(curr[-1])],
                           3)
        tvals = cleanTicks([],tsigs,2)
        ttext = ticktext(tvals,tsigs,
                         lambda v: "<b>{}</b>".format(v))        
    fig.update_yaxes(tickmode='array',
                     tickvals=tvals,
                     ticktext=ttext,
                     showgrid = False,
                     row=r,col=c)  
    fig.update_xaxes(showgrid=False,row=r,col=c)
cats = demo_groups
for i in range(0,len(cats)):
    fig.add_trace(go.Scatter(x=complete_dates,
                         y=complete_weeks.loc[(slice(None),cats[i]),'New Positive'],
                         mode='lines',
                         name=cats[i],
                         marker_color=cmap[cats[i]],
                         fill='tonexty',
                         #showlegend=False,
                         stackgroup='one'                             
                         ),row=4,col=1)
    tsigs = cleanTicks([int(tot)],
                       [int(complete_weeks.groupby(level='date').sum()['New Positive'][-1])],
                       10)
    tvals = cleanTicks(range(0,int(tot)+10,25),
                       tsigs,
                       10)
    ttext = ticktext(tvals,tsigs,
                         lambda v: "<b>{}</b>".format(v))   
    fig.update_yaxes(showgrid=False,
                     tickmode='array',
                     tickvals=tvals,
                     ticktext=ttext,
                     row=4,col=1)    
    fig.update_xaxes(showgrid=False,row=4,col=1)

fig.update_yaxes(range=(0,catmax+5))
fig.update_yaxes(range=(0,tot+10),row=5)
fig.update_layout(title="Weekly COVID-19 Cases by IDPH Age Demographic Groups",
                  width=1200,height=800,margin=margs,
                  plot_bgcolor='floralwhite'
                  )
plot(fig,filename='graphics/idphagedemoweekly_multiples.html')
div_caseweek = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/WCIL-IDPHAgeDemoWeekly.txt','w') as f:
    f.write(div_caseweek)
    f.close()

