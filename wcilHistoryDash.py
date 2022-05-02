#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Nov  7 21:18:27 2020

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
from math import ceil

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
# site table margins
margs = go.layout.Margin(l=0, #left margin
                         r=0, #right margin
                         b=25, #bottom margin
                         t=75  #top margin
                         )                          
#%%

# 17187,17 <-- Warren County, IL
warren = [17187]
p = 17032


idphnums = cvdp.loadidphdaily()
idph_daily = cvda.expandIDPHDaily(cvdp.prepidphdaily(idphnums)).loc[:,17,17187]


#%%


def weekly(daydata,nweeks=1):
    basis = daydata[['New Positive','New Positive per 100k','New Deaths']]
    weeks = basis.groupby(pd.Grouper(level='date',
                                      freq=str(nweeks)+'W-SUN',
                                      closed='left',
                                      label='left')).sum()    
    tots = weeks.cumsum().rename(columns={'New Positive':'Total Positive',
                                          'New Positive per 100k':'Total Positive per 100k',
                                          'New Deaths':'Total Deaths'})
    return pd.concat([weeks,tots],axis=1)

def monthly(daydata):
    months = daydata.groupby(pd.Grouper(level='date',
                                       freq='MS',
                                       closed='left',
                                       label='left')).sum()  
    tots = months.cumsum().rename(columns={'New Positive':'Total Positive',
                                          'New Positive per 100k':'Total Positive per 100k',
                                          'New Deaths':'Total Deaths'})
    return pd.concat([months,tots],axis=1)

    
#%%

by_week = weekly(idph_daily)
day1 = (idph_daily['Total Positive'] > 0).idxmax()

lastday = idph_daily.index[-1]
currweekdays = lastday.isoweekday()+1
if currweekdays < 7:
    complete_weeks = by_week.iloc[:-1]
else:
    complete_weeks = by_week


#%%

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

#%%

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=by_week.index,
                         y=by_week['Total Positive'],
                         fill='tozeroy',      
                         marker_color=px.colors.qualitative.Vivid[6],
                         name="Total Positive",
                         showlegend=False
                         ),
    secondary_y=True)
fig.add_trace(go.Bar(x=by_week.index, y=by_week['New Positive'],
                         name="New Positive",                         
                         showlegend=False,                         
                         marker_color=px.colors.qualitative.Alphabet[10]),               
              secondary_y=False)

newmax_id = by_week['New Positive'].idxmax()
totmax_id = by_week['Total Positive'][::-1].idxmax()
ticks = by_week.index[[0]].append(by_week.index[2:-2:2]).append(by_week.index[[-1]])
y1 = set(range(0,int(by_week['New Positive'].max()),25))
y1sig = set([int(by_week['New Positive'].max()),
             int(by_week['New Positive'].loc[totmax_id])])
y1_ticks = cleanTicks(y1,y1sig,10)
y1_ttext = ticktext(y1_ticks,y1sig,lambda t:'<b>{}</b>'.format(t))
y2 = set(range(0,int(by_week['Total Positive'].max()+250),250))
y2sig = set([by_week['Total Positive'].max(),
             by_week['Total Positive'].loc[newmax_id]])
y2_ticks = cleanTicks(y2,y2sig,100)
y2_ttext = ticktext(y2_ticks,y2sig,lambda t:'<b>{:.0f}</b>'.format(t))

                                                              
fig.update_layout(margin=margs,
                  title='New and Total Positive Cases by Week',
                  xaxis=dict(tickmode='array',
                             tickvals=ticks),
                  width=800)
fig.update_yaxes(range = (0,by_week['New Positive'].max()*2),
                 secondary_y=False,
                 title='New Positive',
                 tickmode='array',
                 tickvals=y1_ticks,
                 ticktext=y1_ttext,
                 showgrid=False)
fig.update_yaxes(range = (0,by_week['Total Positive'].max()+250),
                 secondary_y=True,
                 title='Total Positive',
                 tickmode='array',
                 tickvals=y2_ticks,
                 ticktext=y2_ttext,
                 showgrid=False)


tots = plot(fig,include_plotlyjs=False,output_type='div')
#plot(fig,filename='graphics/totalcases.html')

#%%


fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=by_week.index,
                         y=by_week['Total Deaths'],
                         fill='tozeroy',      
                         marker_color=px.colors.qualitative.Vivid[6],
                         name="Total Deaths",
                         showlegend=False),
    secondary_y=True)
fig.add_trace(go.Bar(x=by_week.index, y=by_week['New Deaths'],
                         name="New Deaths",                         
                         showlegend=False,
                         marker_color=px.colors.qualitative.Alphabet[10]),               
              secondary_y=False)

newmax_id = by_week['New Deaths'].idxmax()
totmax_id = by_week['Total Deaths'][::-1].idxmax()
ticks = by_week.index[[0]].append(by_week.index[2:-2:2]).append(by_week.index[[-1]])
y1 = set(range(0,int(by_week['New Deaths'].max()),2))
y1sig = set([int(by_week['New Deaths'].max()),
             int(by_week['New Deaths'].loc[totmax_id])])
y1_ticks = cleanTicks(y1,y1sig,.9)
y1_ttext = ticktext(y1_ticks,y1sig,lambda t:'<b>{}</b>'.format(t))
y2 = set(range(0,int(by_week['Total Deaths'].max()+10),10))
y2sig = set([by_week['Total Deaths'].max(),
             by_week['Total Deaths'].loc[newmax_id]])
y2_ticks = cleanTicks(y2,y2sig,3)
y2_ttext = ticktext(y2_ticks,y2sig,lambda t:'<b>{:.0f}</b>'.format(t))


fig.update_layout(margin=margs,
                  title='New and Total Deaths by Week',
                  xaxis=dict(tickmode='array',
                             tickvals=ticks),
                  width=800)
fig.update_yaxes(range = (0,by_week['New Deaths'].max()*2),
                 secondary_y=False,
                 title='New Deaths',
                 tickmode='array',
                 tickvals=y1_ticks,
                 ticktext=y1_ttext,
                 showgrid=False)
fig.update_yaxes(#range = (0,by_week['Total Deaths'].max()+10),
                 secondary_y=True,
                 title='Total Deaths',
                 tickmode='array',
                 tickvals=y2_ticks,
                 ticktext=y2_ttext,
                 showgrid=False)


totsdeath = plot(fig,include_plotlyjs=False,output_type='div')
#plot(fig,filename='graphics/totaldeaths.html')

#%%

pvacs = idph_daily['% Vaccinated']
nvacs = idph_daily['New Vaccinated']
vday1 = pvacs[ pvacs != 0 ].index[0]
idx = pd.date_range(start = day1, end = pvacs.index[-1], freq='D')
pvacs = pvacs.reindex(idx).fillna(0)
nvacs = nvacs.reindex(idx).fillna(0)

nvacs = nvacs.groupby(pd.Grouper(level=0,
                                 freq='W-SUN',
                                 closed='left',
                                 label='left')).sum()    
pvacs = pvacs.groupby(pd.Grouper(level=0,
                                 freq='W-SUN',
                                 closed='left',
                                 label='left')).max()    
vac_week = pd.concat([nvacs,pvacs],axis=1)

#%%

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=vac_week.index,
                         y=vac_week['% Vaccinated'],
                         fill='tozeroy',      
                         marker_color=px.colors.qualitative.D3[9],
                         name="% Population Vaccinated",
                         showlegend=False),
    secondary_y=True)
fig.add_trace(go.Bar(x=vac_week.index, y=vac_week['New Vaccinated'],
                         name="New Vaccinations",                         
                         showlegend=False,
                         marker_color=px.colors.qualitative.G10[0]),               
              secondary_y=False)



newmax_id = vac_week['New Vaccinated'][::-1].idxmax()
totmax_id = vac_week['% Vaccinated'][::-1].idxmax()
ticks = vac_week.index[[0]].append(vac_week.index[1:-1:2]).append(vac_week.index[[-1]])
y1 = set(range(0,int(vac_week['New Vaccinated'].max()),100))
y1sig = set([int(vac_week['New Vaccinated'].max()),
             int(vac_week['New Vaccinated'].loc[totmax_id])])
y1_ticks = cleanTicks(y1,y1sig,50)
y1_ttext = ticktext(y1_ticks,y1sig,lambda t:'<b>{}</b>'.format(t))
y2 = set(np.arange(0,0.5,0.05))
y2sig = set([vac_week['% Vaccinated'].max(),
             vac_week['% Vaccinated'].loc[newmax_id]])
y2_ticks = cleanTicks(y2,y2sig,0.025)
y2_ttext = ticktext(y2_ticks,y2sig,
                    lambda t:'<b>{:.2%}</b>'.format(t),
                    lambda t:'{:.2%}'.format(t))
                                                              
fig.update_layout(margin=margs,
                  title='New Vacciantions and Percent of Population Vaccianted by Week',
                  xaxis=dict(tickmode='array',
                             tickvals=ticks),
                  width=800)
fig.update_yaxes(range = (0,vac_week['New Vaccinated'].max()*1.5),
                 secondary_y=False,
                 title='New Vaccinations',
                 tickmode='array',
                 tickvals=y1_ticks,
                 ticktext=y1_ttext,
                 showgrid=False)
fig.update_yaxes(#range = (0,by_week['Total Deaths'].max()+10),
                 secondary_y=True,
                 title='Percent of Population Vaccinated',
                 tickmode='array',
                 tickvals=y2_ticks,
                 ticktext=y2_ttext,
                 showgrid=False
                 )


pvac = plot(fig,include_plotlyjs=False,output_type='div')
#plot(fig,filename='graphics/pcentvaccinated.html')

#%%

def demoexpand_daily(tots):
    demo_name = tots.index.names[1]
    news = tots.groupby(level=demo_name).diff().fillna(0)
    news.columns = ['New Positive','New Tests','New Deaths']
    
    return pd.concat([tots,news],axis=1)

def demo_weekly(dailies):
    gbyweek = pd.Grouper(level='date',
                         freq='W-SUN',
                         closed='left',
                         label='left')
    demo_name = dailies.index.names[1]
    news = dailies[['New Positive','New Tests']]
    news = news.groupby([gbyweek,demo_name]).sum()
    tots = dailies[['Total Positive', 'Total Tested']]
    tots = tots.groupby([gbyweek,demo_name]).max().fillna(0)
    return pd.concat([news,tots],axis=1)
#%%

idph_age_cats = ['<20','20-29', '30-39', '40-49', '50-59', '60-69', '70-79', '80+']
age,race,gender = cvdp.loadidphdemos('Warren')
agedemos = demoexpand_daily(age)
agedemos = agedemos.loc[(slice(None),idph_age_cats),:].sort_index()
age_weekly = demo_weekly(agedemos).astype(int)
age_weekly = age_weekly.reset_index().set_index(['date','age_group']).sort_index()

#%%

# demographic category -> color
clrs = px.colors.sequential.algae
cmap = {idph_age_cats[i]:clrs[i] for i in range(len(idph_age_cats))}

#%%

# multiples: cumulative Cases 
#  ticks: col1--> by 100 with current. col 2,3 --> current
demo_total = age_weekly['Total Positive'].unstack()

cumsum_order = demo_total.iloc[-1].sort_values(ascending=False).index
curtot = demo_total.iloc[-1].sum()
catmax = demo_total.iloc[-1].max()

fig = make_subplots(rows=5,cols=3,
                    #shared_yaxes=True,
                    shared_xaxes=True,
                    specs = [[{},{},{}],
                             [{},{},{}],
                             [{},{},{}],                             
                             [{'colspan':3,'rowspan':2},None,None],
                             [None,None,None]],
                    subplot_titles=list(cumsum_order)+['All Demographics']
                    )
for i in range(len(cumsum_order)):
    cat = cumsum_order[i]
    clr = cmap[cat]
    r = int(i/3)+1
    c = int(i%3)+1
    fig.add_trace(go.Scatter(x=demo_total.index,
                             y=demo_total[cat],
                             name=cat,
                                 showlegend=False,
                                 fill='tozeroy',
                                 mode='lines',
                             marker_color=clr                             
                             ),
                  row = r,col=c)
    if c == 1:
        tsigs = [int(demo_total[cat].max())]
        tvals = cleanTicks(list(range(0,int(catmax)+10,150)),
                           tsigs,
                           80)
        ttext = ticktext(tvals,tsigs,
                         lambda v: "<b>{}</b>".format(v))
    else:
        tsigs = [int(demo_total[cat].max())]
        tvals = cleanTicks([],tsigs,50)
        ttext = ticktext(tvals,tsigs,
                         lambda v: "<b>{}</b>".format(v))        
    fig.update_yaxes(tickmode='array',
                     tickvals=tvals,
                     ticktext=ttext,
                     showgrid = False,
                     row=r,col=c)  
    fig.update_xaxes(showgrid=False,row=r,col=c)
cats = demo_total.columns
for i in range(0,len(cats)):
    fig.add_trace(go.Scatter(x=demo_total.index,
                         y=demo_total[cats[i]],
                         mode='lines',
                         name=cats[i],
                         marker_color=cmap[cats[i]],
                         fill='tonexty',
                         stackgroup='one'                         
                         ),
                  row=4,col=1)
    tsigs = [int(curtot)]
    tvals = cleanTicks(range(0,int(curtot) + 25,500),
                       tsigs,
                       250)
    ttext = ticktext(tvals,tsigs,
                         lambda v: "<b>{}</b>".format(v))   
    fig.update_yaxes(showgrid=False,
                     tickmode='array',
                     tickvals=tvals,
                     ticktext=ttext,
                     row=4,col=1)    
    fig.update_xaxes(showgrid=False,row=4,col=1)

fig.update_yaxes(range=(0,catmax+25))
fig.update_yaxes(range=(0,curtot + 50),row=4)
fig.update_layout(title="Total COVID-19 Cases by IDPH Demographic Groups",
                  width= 1200,
                  height= 800,
                  margin=margs,
                  plot_bgcolor='floralwhite')
#plot(fig,filename='graphics/demototals_multiples.html')
div_casetotal = plot(fig, include_plotlyjs=False, output_type='div')
#with open('graphics/WCIL-DemoTotals.txt','w') as f:
#    f.write(div_casetotal)
#    f.close()


#%%

if currweekdays < 7:
    lastfull = age_weekly.index.get_level_values('date').unique()[-2]
    complete_weeks = age_weekly.loc[:lastfull,:]
# multiples: weekly Cases 
complete_weeks = age_weekly['New Positive'].unstack()
currweek_order = complete_weeks.iloc[-1].sort_values(ascending=False).index
catmax = complete_weeks.max().max()
tot=complete_weeks.sum(axis=1).max()

fig = make_subplots(rows=5,cols=3,
                    #shared_yaxes=True,
                    shared_xaxes=True,
                    specs = [[{},{},{}],
                             [{},{},{}],
                             [{},{},{}],
                             [{'colspan':3,'rowspan':2},None,None],
                             [None,None,None]],
                    subplot_titles= list(currweek_order) + ['All Demographics'])
for i in range(len(currweek_order)):
    cat = currweek_order[i]
    clr = cmap[cat]
    r = int(i/3)+1
    c = int(i%3)+1
    fig.add_trace(go.Scatter(x=complete_weeks.index,
                             y=complete_weeks[cat],
                             name=cat,
                             showlegend=False,
                             fill='tozeroy',
                             mode='lines',
                             marker_color=clr
                             ),
                  row = r, col=c )
    if c == 1:
        tsigs = cleanTicks([int(complete_weeks[cat].max())],
                           [int(complete_weeks[cat][-1])],
                           3)
        tvals = cleanTicks(list(range(0,int(catmax)+5,10)),
                           tsigs,
                           5)
        ttext = ticktext(tvals,tsigs,
                         lambda v: "<b>{}</b>".format(v))
    else:
        tsigs = cleanTicks([int(complete_weeks[cat].max())],
                           [int(complete_weeks[cat][-1])],
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
cats = complete_weeks.columns
for i in range(0,len(cats)):
    fig.add_trace(go.Scatter(x=complete_weeks.index,
                         y=complete_weeks[cats[i]],
                         mode='lines',
                         name=cats[i],
                         marker_color=cmap[cats[i]],
                         fill='tonexty',
                         #showlegend=False,
                         stackgroup='one'                             
                         ),row=4,col=1)
    tsigs = cleanTicks([int(tot)],
                       [int(complete_weeks.sum(axis=1)[-1])],
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
                     row=5,col=1)    
    fig.update_xaxes(showgrid=False,row=4,col=1)

fig.update_yaxes(range=(0,catmax+5))
fig.update_yaxes(range=(0,tot+10),row=4)
fig.update_layout(title="Weekly COVID-19 Cases by IDPH Demographic Groups",
                  width=1200,height=800,margin=margs,
                  plot_bgcolor='floralwhite'
                  )
#plot(fig,filename='graphics/demoweekl_multiples.html')
div_caseweek = plot(fig, include_plotlyjs=False, output_type='div')
#with open('graphics/WCIL-DemoWeekly.txt','w') as f:
#    f.write(div_caseweek)
#    f.close()


#%%

# multiples : cumlative deaths
"""
cumsum_order = death_total.iloc[-1].sort_values(ascending=False).index
curtot = death_total.iloc[-1].sum()
catmax = death_total.max().max()
R = ceil(len(deathcats) / 3 )
fig = make_subplots(rows=R+2,cols=3,
                    specs=[[{},{},{}]] * R +
                    [[{'colspan':3,'rowspan':2},None,None],
                     [None,None,None]],                    
                    #shared_yaxes=True,
                    shared_xaxes=True,
                    subplot_titles= list(cumsum_order)+
                    ([''] * (3-len(deathcats)%3)) + 
                    ['All Demographics']
                    )
for i in range(len(cumsum_order)):
    cat = cumsum_order[i]
    clr = cmap[cat]
    r = int(i/3)+1
    c=int(i%3)+1
    fig.add_trace(go.Scatter(x=death_total.index,
                             y=death_total[cat],
                             name=cat,
                             showlegend=False,
                             fill='tozeroy',
                             mode='lines',
                             marker_color=clr
                             ),
                  row = r, col = c)
    if c == 1:
        tsigs = [int(death_total[cat].max())]
        tvals = cleanTicks(list(range(0,int(catmax)+3,5)),
                           tsigs,
                           4)
        ttext = ticktext(tvals,tsigs,
                         lambda v: "<b>{}</b>".format(v))
    else:
        tsigs = [int(death_total[cat].max())]
        tvals = cleanTicks([],tsigs,0)        
        ttext = ticktext(tvals,tsigs,
                         lambda v: "<b>{}</b>".format(v))        
    fig.update_yaxes(tickmode='array',
                     tickvals=tvals,
                     ticktext=ttext,
                     showgrid = False,
                     row=r,col=c)  
    fig.update_xaxes(showgrid=False,row=r,col=c)
cats = death_total.columns
for i in range(0,len(cats)):
    fig.add_trace(go.Scatter(x=death_total.index,
                         y=death_total[cats[i]],
                         mode='lines',
                         name=cats[i],
                         marker_color=cmap[cats[i]],
                         fill='tonexty',
                         stackgroup='one'                         
                         ),row=R+1,col=1)
    tsigs = [curtot]
    tvals = cleanTicks(range(0,int(curtot) + 2,10),
                       tsigs,
                       5)
    ttext = ticktext(tvals,tsigs,
                         lambda v: "<b>{}</b>".format(v))   
    fig.update_yaxes(showgrid=False,
                     tickmode='array',
                     tickvals=tvals,
                     ticktext=ttext,
                     row=R+1,col=1)    
    fig.update_xaxes(showgrid=False,row=R+1,col=1)    

fig.update_yaxes(range=(0,catmax+3))
fig.update_yaxes(range=(0,curtot+2), row=R+1)
fig.update_layout(title="Total Deaths by Demographic Groups",
                  width=1200,height=800,margin=margs,
                  plot_bgcolor='floralwhite')
#plot(fig,filename='graphics/demototals_deaths_multiples.html')
div_deathtotal = plot(fig, include_plotlyjs=False, output_type='div')
#with open('graphics/WCIL-DemoDeathTotals.txt','w') as f:
#    f.write(div_deathtotal)
#    f.close()
"""

#%%

pgraph = '<p></p>'
mdpage = ""
header = """---
layout: page
title: Warren County Illinois - History Report
permalink: /wcil-history-report/
---
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
"""
timestamp = pd.to_datetime('today').strftime('%H:%M %Y-%m-%d')
header = header + '<p><small>last updated:  ' + timestamp + '</small><p>\n\n'

front = """
<small><p> Data for this page comes from reports issued by the 
Illinois Department of Public Health (IDPH) </p>
<p>
All the graphics report the data on weekly increments. In the first three 
graphics the bars are weekly nubmers and the area graph shows a cummulative total.
For these charts, numbers listed in bold are either maximums 
or values reported on the day of the other y-axis's maximum. For example, 
on the positive case graph the bold numbers on the first y-axis are the max
number of new cases reported in a single week and the number of cases reported
along with the current total (i.e. the max total cases). They pair effectively gives you
the current value and historal maximum value on the first y-axis and the 
current value and a historically notable value for the second y-axis.
</p>
"""

mdpage = header + front + pgraph + tots + pgraph + totsdeath + pgraph +\
    pvac + pgraph +\
    div_casetotal + pgraph + div_caseweek 

with open('docs/wcilHistory.md','w') as f:
    f.write(mdpage)
    f.close()
