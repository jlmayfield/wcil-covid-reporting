#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat April 3

@author: jlmayfield
"""

from math import ceil
import pandas as pd

from plotly.subplots import make_subplots
import plotly.graph_objects as go
from plotly.offline import plot
import plotly.express as px


import cvdataprep as cvdp
import cvdataanalysis as cvda


#%%

idphnums = cvdp.loadidphdaily()
wchdcases,wchddemos,wchddeaths = cvdp.loadwchd()
populations,usafcases,usafdeaths = cvdp.loadusafacts()


#%%
# from IL DPH site for vaccine data (1/31/21)
p = 17032


today = pd.to_datetime('2021-04-10')
dayone = pd.to_datetime('2020-04-10')
wchd_lastdaily = pd.to_datetime('2021-01-24')


# site table margins
margs = go.layout.Margin(l=0, #left margin
                         r=0, #right margin
                         b=25, #bottom margin
                         t=75  #top margin
                         )                          


#%%

# daily numbers from IDPH
idph_daily = cvda.expandIDPHDaily(cvdp.prepidphdaily(idphnums),p)
idph_daily = idph_daily.loc[:,17,17187]

# daily numbers from WCHD up until they shifted to weekly reporting
wchd_daily = cvda.expandWCHDData(cvdp.prepwchd(wchdcases),p)
wchd_daily = wchd_daily.loc[:,17,17187]

#%%

wchd = wchd_daily[['New Tests','New Positive','New Deaths']]
yearone_weekly = wchd.groupby(pd.Grouper(level='date',
                                         freq='W-SUN',
                                         closed='left',
                                         label='left')).sum()


vax = idph_daily.loc[dayone:today][['New Vaccinated']]
vax = vax.reindex(wchd.index).fillna(0)
vax_weekly = vax.groupby(pd.Grouper(level='date',
                                    freq='W-SUN',
                                    closed='left',
                                    label='left')).sum()


week_idx = [ yearone_weekly.index[i] for i in range(0,len(yearone_weekly.index),2) ]


#%% 

# Weekly Totals (bar graph) Cases and Deaths

wchd_cases_weekly = px.bar(yearone_weekly,
                           x=yearone_weekly.index,y='New Positive',
                           title='One Year of Covid-19: New Cases by Week',)
wchd_cases_weekly.update_xaxes(tickvals=week_idx,title='')
caseticks = list(yearone_weekly['New Positive'].describe()[1:].sort_values().astype(int).drop(['std','50%']))
wchd_cases_weekly.update_yaxes(tickvals=caseticks,title='New Cases')
#plot(wchd_cases_weekly,filename='graphics/yearone-cases-weekly.html')


deathticks = list(range(int(yearone_weekly['New Deaths'].min()),
                        int(yearone_weekly['New Deaths'].max())+1))
wchd_deaths_weekly = px.bar(yearone_weekly,
                            x=yearone_weekly.index,y='New Deaths',
                            title='One Year of Covid-19: New Covid Related Deaths by Week')
wchd_deaths_weekly .update_xaxes(tickvals=week_idx,title='')
wchd_deaths_weekly .update_yaxes(tickvals=deathticks,title='New Deaths')
#plot(wchd_deaths_weekly ,filename='graphics/yearone-deaths-weekly.html')


idph_vax_weekly = px.bar(vax_weekly,
                         x=vax_weekly.index,y='New Vaccinated',
                         title='One Year of Covid-19: New People Fully Vaccinated by Week')
idph_vax_weekly.update_xaxes(tickvals=week_idx,title='')
idph_vax_weekly.update_yaxes(title='New People Vaccinated')
#plot(idph_vax_weekly,filename='graphics/yearone-vaccinated-weekly.html')

#%%

# Cummulative Totals (area graph) Cases, Deaths, Vaccinations

casetotals = yearone_weekly['New Positive'].cumsum()
wchd_cases_total = px.area(casetotals,
                           x=casetotals.index,y='New Positive',
                           title='One Year of Covid-19: Total Cases by Week',)
wchd_cases_total.update_xaxes(tickvals=week_idx,title='')
ticks = list(range(0,int(casetotals.max())+1,100)) + [int(casetotals.max())]
wchd_cases_total.update_yaxes(title='Total Cases',tickvals=ticks)
#plot(wchd_cases_total,filename='graphics/yearone-cases-total.html')

deathtotals = yearone_weekly['New Deaths'].cumsum()
wchd_deaths_total = px.area(deathtotals,
                            x=deathtotals.index,y='New Deaths',
                            title='One Year of Covid-19: Total Related Deaths by Week')
wchd_deaths_total .update_xaxes(tickvals=week_idx,title='')
ticks = list(range(0,int(deathtotals.max())+1,5)) + [int(deathtotals.max())]
wchd_deaths_total .update_yaxes(title='Total Deaths',tickvals=ticks)
#plot(wchd_deaths_total ,filename='graphics/yearone-deaths-total.html')

vaxtotals = vax_weekly.cumsum()
idph_vax_total = px.area(vaxtotals,
                         x=vaxtotals.index,y='New Vaccinated',
                         title='One Year of Covid-19: Total People Fully Vaccinated by Week')
idph_vax_total.update_xaxes(tickvals=week_idx,title='')
ticks = list(range(0,int(vaxtotals.max())+1,250)) + [int(vaxtotals.max())]
idph_vax_total.update_yaxes(title='New People Vaccinated',tickvals=ticks)
#plot(idph_vax_total,filename='graphics/yearone-vaccinated-total.html')

#%%

# Totals and Weekly Multiples: Cases, Deaths, Vaccinations

clr = px.colors.qualitative.D3[0]

fig = make_subplots(rows=3,cols=2,
                    shared_yaxes=False,
                    shared_xaxes=True,
                    subplot_titles=['Total Cases','New Cases',
                                    'Total Deaths','New Deaths',
                                    'Total Vaccinations','New Vaccinations']
                    )
fig.add_trace(go.Scatter(x=casetotals.index,
                         y=casetotals,
                         name = 'Cases',
                         showlegend=False,
                         fill='tozeroy',
                         mode='lines',
                         marker_color=clr
                         ),
              row=1,col=1)
fig.add_trace(go.Scatter(x=deathtotals.index,
                         y=deathtotals,
                         name = 'Deaths',
                         showlegend=False,
                         fill='tozeroy',
                         mode='lines',
                         marker_color=clr),
              row=2,col=1)
fig.add_trace(go.Scatter(x=vaxtotals.index,
                         y=vaxtotals['New Vaccinated'],
                         name = 'People Vaccinated',
                         showlegend=False,
                         fill='tozeroy',
                         mode='lines',
                         marker_color=clr),
              row=3,col=1)
fig.add_trace(go.Bar(x=yearone_weekly.index,
                     y=yearone_weekly['New Positive'],
                     name = 'Cases',
                     showlegend=False,
                     marker_color=clr
                    ),
              row=1,col=2)
fig.add_trace(go.Bar(x=yearone_weekly.index,
                     y=yearone_weekly['New Deaths'],
                     name = 'Deaths',
                     showlegend=False,
                     marker_color=clr
                         ),
              row=2,col=2)
fig.add_trace(go.Bar(x=vax_weekly.index,
                     y=vax_weekly['New Vaccinated'],
                     name = 'People Vaccinated',
                     showlegend=False,
                     marker_color=clr
                     ),
              row=3,col=2)
fig.update_xaxes(tickvals=week_idx,title='')
caseticks = list(range(0,int(casetotals.max())+1,500)) + [int(casetotals.max())]
weeklycaseticks = list(yearone_weekly['New Positive'].describe()[1:].sort_values().astype(int).drop(['std','50%']))
deathticks = list(range(0,int(deathtotals.max())+1,10)) + [int(deathtotals.max())]
weeklydeathticks = list(range(int(yearone_weekly['New Deaths'].min()),
                              int(yearone_weekly['New Deaths'].max())+1,
                              2))
vaxticks = list(range(0,int(vaxtotals.max())+1,1000)) + [int(vaxtotals.max())]
weeklyvaxticks = list(range(int(vax_weekly.min()),
                            int(vax_weekly.max())+1,
                            200)) + [int(vax_weekly.max())]
fig.update_layout(title="A Week-by-Week Look at One Year of COVID-19 in Warren County, IL",
                  yaxis={'tickvals':caseticks},
                  yaxis2={'tickvals':weeklycaseticks},
                  yaxis3={'tickvals':deathticks},
                  yaxis4={'tickvals':weeklydeathticks},
                  yaxis5={'tickvals':vaxticks},
                  yaxis6={'tickvals':weeklyvaxticks},)
plot(fig,filename='graphics/yearone-CasesDeathsVax.html')
div_casedeathvax = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/yearone-CasesDeathsVax.txt','w') as f:
    f.write(div_casedeathvax)
    f.close()


#%%

## DEMOGRAPHIC ANALYSIS

# clear daily numbers by each category
demo_daily = wchddemos.copy().reorder_levels([1,0],axis=1)
demo_daily = demo_daily.reindex(sorted(demo_daily.columns),axis=1)
demo_daily.columns = [i[1]+ ' ' + i[0] for i in demo_daily.columns]
demo_daily.index.name = 'date'
demo_daily = demo_daily.loc[dayone:today]

# weekly totals
demo_weeks = demo_daily.groupby(pd.Grouper(level='date',
                                           freq='W-SUN',
                                           closed='left',
                                           label='left')).sum() 
# cumulative totals
demo_total = demo_weeks.cumsum()

# same but for deaths rather than cases
death_daily = wchddeaths.copy().reorder_levels([1,0],axis=1)
death_daily = death_daily.reindex(sorted(death_daily.columns),axis=1)
death_daily.columns = [i[1]+ ' ' + i[0] for i in death_daily.columns]
death_daily.index.name = 'date'
death_daily = death_daily.loc[dayone:today]
death_daily = death_daily.reindex(demo_daily.index).fillna(0)

death_weeks = death_daily.groupby(pd.Grouper(level='date',
                                             freq='W-SUN',
                                             closed='left',
                                             label='left')).sum() 

death_total = death_weeks.cumsum()

# demographic category -> color
clrs = px.colors.sequential.algae
cmap = {demo_daily.columns[i]:clrs[i] for i in range(len(demo_daily.columns))}

# Demographic Groups that have recorded Deaths
deathcats = death_total.iloc[-1]
deathcats = (deathcats[ deathcats > 0 ]).index

death_daily = death_daily[deathcats].astype(int)
death_total = death_total[deathcats].astype(int)
death_weeks = death_weeks[deathcats].astype(int)

#%%

# Cummulative Totals Multiples

cumsum_order = demo_total.iloc[-1].sort_values(ascending=False).index
curtot = int(demo_total.iloc[-1].sum())
catmax = int(demo_total.max().max())

fig = make_subplots(rows=6,cols=3,
                    shared_yaxes=False,
                    shared_xaxes=True,
                    specs = [[{},{},{}],
                             [{},{},{}],
                             [{},{},{}],
                             [{},{},{}],
                             [{'colspan':3,'rowspan':2},None,None],
                             [None,None,None]],
                    subplot_titles=list(cumsum_order)+['All Demographics']                   
                    )
for i in range(len(cumsum_order)):
    cat = cumsum_order[i]
    clr = cmap[cat]
    fig.add_trace(go.Scatter(x=demo_total.index,
                             y=demo_total[cat],
                             name=cat,
                             showlegend=False,
                             fill='tozeroy',
                             mode='lines',
                             marker_color=clr
                             ),
                  row = int(i/3)+1,col=int(i%3)+1)
    curmax = int(demo_total[cat].max())
    tickvals = list(range(0,curmax+1,100)) + [curmax]
    fig.update_layout({'yaxis'+ (str(i+1) if i > 0 else ''):{'tickvals':tickvals}})
        
cats = demo_total.columns
for i in range(0,len(cats)):
    fig.add_trace(go.Scatter(x=demo_total.index,
                         y=demo_total[cats[i]],
                         mode='lines',
                         name=cats[i],
                         marker_color=cmap[cats[i]],
                         fill='tonexty',
                         stackgroup='one',
                         showlegend=False
                         ),
                  row=5,col=1)
    

fig.update_yaxes(range=(0,catmax+10))
fig.update_yaxes(range=(0,curtot + 25),row=5)
          
              
fig.update_layout(title="One Year of COVID-19 in Warren County, IL: Total Cases by Demographic Groups",
                  width= 1200,
                  height= 800,
                  margin=margs,
                  xaxis10={'tickvals': []},
                  xaxis11={'tickvals': []},
                  xaxis12={'tickvals': []},
                  xaxis13={'tickvals':week_idx},
                  yaxis13={'tickvals':list(range(0,curtot+25,500))+[curtot]})
plot(fig,filename='graphics/yearone-demototals.html')
div_casetotal = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/yearone-DemoTotals.txt','w') as f:
    f.write(div_casetotal)
    f.close()

#%%

complete_weeks = demo_weeks
weekmean_order = complete_weeks.mean().sort_values(ascending=False).index
catmax = complete_weeks.max().max()

fig = make_subplots(rows=6,cols=3,
                    shared_yaxes=False,
                    shared_xaxes=True,
                    specs = [[{},{},{}],
                             [{},{},{}],
                             [{},{},{}],
                             [{},{},{}],
                             [{'colspan':3,'rowspan':2},None,None],
                             [None,None,None]],
                    subplot_titles= list(weekmean_order) + ['All Demographics'])
for i in range(len(weekmean_order)):
    cat = weekmean_order[i]
    clr = cmap[cat]
    fig.add_trace(go.Bar(x=complete_weeks.index,
                         y=complete_weeks[cat],
                         name=cat,
                         showlegend=False,
                         #fill='tozeroy',
                         #mode='lines',
                         marker_color=clr
                         ),
                  row = int(i/3)+1,col=int(i%3)+1)
    curmax = int(complete_weeks[cat].max())
    tickvals = list(range(0,curmax+1,15)) + [curmax]
    fig.update_layout({'yaxis'+ (str(i+1) if i > 0 else ''):{'tickvals':tickvals}})
    
cats = complete_weeks.columns
for i in range(0,len(cats)):
    cat = cats[i]
    fig.add_trace(go.Bar(x=complete_weeks.index,
                         y=complete_weeks[cat],
                         #mode='lines',
                         name=cat,
                         marker_color=cmap[cat],
                         #fill='tonexty',
                         showlegend=False,
                         #stackgroup='one'                             
                         ),row=5,col=1)

tot= int(complete_weeks.sum(axis=1).max())
fig.update_yaxes(range=(0,catmax+5))
fig.update_yaxes(range=(0,tot+10),row=5)
fig.update_layout(title="One Year of COVID-19 in Warren County, IL: Weekly Cases by Demographic Groups",
                  width=1200,height=800,margin=margs,
                  xaxis10={'tickvals': []},
                  xaxis11={'tickvals': []},
                  xaxis12={'tickvals': []},
                  xaxis13={'tickvals':week_idx},
                  yaxis13={'tickvals':list(range(0,tot+25,50))+[tot]},
                  barmode='stack'
                  )
plot(fig,filename='graphics/yearone-demoweekly_multiples.html')
div_caseweek = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/yearone-DemoWeekly.txt','w') as f:
    f.write(div_caseweek)
    f.close()


#%%

# Death Demographics

cumsum_order = death_total.iloc[-1].sort_values(ascending=False).index
curtot = int(death_total.iloc[-1].sum())
catmax = death_total.max().max()

R = ceil(len(deathcats) / 3 )
fig = make_subplots(rows=R+2,cols=3,
                    specs=[[{},{},{}]] * R +
                    [[{'colspan':3,'rowspan':2},None,None],
                     [None,None,None]],                    
                    shared_yaxes=False,
                    shared_xaxes=True,
                    subplot_titles= list(cumsum_order)+
                    ([''] * (3-len(deathcats)%3)) + 
                    ['All Demographics']
                    )
for i in range(len(cumsum_order)):
    cat = cumsum_order[i]
    clr = cmap[cat]
    fig.add_trace(go.Scatter(x=death_total.index,
                             y=death_total[cat],
                             name=cat,
                             showlegend=False,
                             fill='tozeroy',
                             mode='lines',
                             marker_color=clr
                             
                             ),
                  row = int(i/3)+1,col=int(i%3)+1)
    curmax = int(death_total[cat].max())
    tickvals = list(range(0,curmax+1,10)) + [curmax]
    fig.update_layout({'yaxis'+ (str(i+1) if i > 0 else ''):{'tickvals':tickvals}})
    
cats = death_total.columns
for i in range(0,len(cats)):
    fig.add_trace(go.Scatter(x=death_total.index,
                             y=death_total[cats[i]],
                             mode='lines',
                             name=cats[i],
                             marker_color=cmap[cats[i]],
                             fill='tonexty',
                             stackgroup='one',
                             showlegend=False
                         ),row=R+1,col=1)    

fig.update_yaxes(range=(0,catmax+3))
tot = death_daily.sum().sum()
fig.update_yaxes(range=(0,tot+2), row=R+1)
fig.update_layout(title="One Year of COVID-19 in Warren County, IL: Total Deaths by Demographic Groups",
                  width=1200,height=800,margin=margs,
                  xaxis4={'tickvals': []},
                  xaxis5={'tickvals': []},
                  xaxis6={'tickvals': []},
                  xaxis7={'tickvals':week_idx},
                  yaxis7={'tickvals':list(range(0,curtot,10))+[curtot]})
plot(fig,filename='graphics/yearone_deaths_multiples.html')
div_deathtotal = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/yearone-DemoDeathTotals.txt','w') as f:
    f.write(div_deathtotal)
    f.close()

#%%

#### END WCHD/IDPH REPORT, START USAF COMPARISON REPORT

#%%

# breakout of state of IL
usafcases_noZero = usafcases.drop([0])
usafcases_zeros = usafcases.loc[0]
usafdeaths_noZero = usafdeaths.drop([0])
usafdeaths_zeros = usafdeaths.loc[0]
IL = usafcases_noZero[usafcases_noZero['State'] == 'IL']
ILd = usafdeaths_noZero[usafdeaths_noZero['State'] == 'IL']


tots = cvdp.prepusafacts(usafcases_noZero,usafdeaths_noZero).loc[:today + pd.Timedelta(1,unit='D')]
tots_il = cvdp.prepusafacts(IL,ILd).loc[:today + pd.Timedelta(1,unit='D')]

#%%

# National Data (with rankings)
usaf_weekly = cvda.expandUSFData_Weekly(tots,populations)
# State Data (state of IL only rankings)
usaf_IL_weekly = cvda.expandUSFData_Weekly(tots_il, populations)


#%%

# day for first reported case for every county
firstreports = tots['Total Positive'].mask(tots['Total Positive']==0).groupby('countyFIPS').idxmin()
firstreports = firstreports.sort_values().dropna().map(lambda r: r[0])

# which batch they were in
batchnum = firstreports.rank(method='dense').astype(int)
counties_before = len(batchnum[batchnum < batchnum[17187]])

# first reported case, last instance of first case in the county
print("Cases: National")
print(firstreports.iloc[0].date(),firstreports.iloc[-1].date())
# WCIL: first case, batch #, # counties that reported cases before 
print(firstreports[17187].date(),batchnum[17187],counties_before,counties_before/3142)

firstreports_il = tots_il['Total Positive'].mask(tots_il['Total Positive']==0).groupby('countyFIPS').idxmin()
firstreports_il = firstreports_il.sort_values().dropna().map(lambda r: r[0])
# which batch they were in
batchnum_il = firstreports_il.rank(method='dense').astype(int)
counties_before_il = len(batchnum_il[batchnum_il < batchnum_il[17187]])

# first reported case, last instance of first case in the county
print("Cases: IL")
print(firstreports_il.iloc[0].date(),firstreports_il.iloc[-1].date())
# WCIL: first case, batch #, # counties that reported cases before 
print(firstreports_il[17187].date(),batchnum_il[17187],counties_before_il,counties_before_il/102)

#%%

# day for first reported deaths for every county
firstdeaths = tots['Total Deaths'].mask(tots['Total Deaths']==0).groupby('countyFIPS').idxmin()
firstdeaths = firstdeaths.sort_values().dropna().map(lambda r: r[0])
# which batch they were in
batchnum = firstdeaths.rank(method='dense')
counties_before = len(batchnum[batchnum < batchnum[17187]])

# first reported case, last instance of first case in the county
print("Deaths: National")
print(firstdeaths.iloc[0],firstdeaths.iloc[-1])
# WCIL: first case, batch #, # counties that reported cases before 
print(firstdeaths[17187],batchnum[17187],counties_before,counties_before/3142)

firstdeaths_il = tots_il['Total Deaths'].mask(tots_il['Total Deaths']==0).groupby('countyFIPS').idxmin()
firstdeaths_il = firstdeaths_il.sort_values().dropna().map(lambda r: r[0])
# which batch they were in
batchnum_il = firstdeaths_il.rank(method='dense')
counties_before_il = len(batchnum_il[batchnum_il < batchnum_il[17187]])

# first reported case, last instance of first case in the county
print("Deaths: IL")
print(firstdeaths_il.iloc[0],firstdeaths_il.iloc[-1])
# WCIL: first case, batch #, # counties that reported cases before 
print(firstdeaths_il[17187],batchnum_il[17187],counties_before_il,counties_before_il/102)

#%%

firstweek = week_idx[0]
wcil_usa = usaf_weekly.loc[:,17,17187].loc[firstweek:]
wcil_il = usaf_IL_weekly.loc[:,17,17187].loc[firstweek:]


#%%

# USAFacts vs WCHD 

clr0 = px.colors.qualitative.D3[0]
clr1 = px.colors.qualitative.D3[1]

fig = make_subplots(rows=2,cols=2,
                    shared_yaxes=False,
                    shared_xaxes=True,
                    subplot_titles=['Total Cases: WCHD','New Cases: WCHD',
                                    'Total Cases: USAFacts','New Cases: USAFacts']
                    )
fig.add_trace(go.Scatter(x=casetotals.index,
                         y=casetotals,
                         name = 'WCHD',
                         showlegend=False,
                         fill='tozeroy',
                         mode='lines',
                         marker_color=clr0
                         ),
              row=1,col=1)
fig.add_trace(go.Scatter(x=wcil_il['Total Positive'].index,
                         y=wcil_il['Total Positive'],
                         name = 'USAFacts',
                         showlegend=False,
                         fill='tozeroy',
                         mode='lines',
                         marker_color=clr1
                         ),
              row=2,col=1)
fig.add_trace(go.Bar(x=yearone_weekly.index,
                     y=yearone_weekly['New Positive'],
                     name = 'WCHD',
                     showlegend=False,
                     marker_color=clr0
                    ),
              row=1,col=2)
fig.add_trace(go.Bar(x=wcil_il['New Positive'].index,
                     y=wcil_il['New Positive'],
                     name = 'USAFacts',
                     showlegend=False,
                     marker_color=clr1
                         ),
              row=2,col=2)
fig.update_xaxes(tickvals=week_idx,title='')
caseticks = list(range(0,int(casetotals.max())+1,500)) + [int(casetotals.max())]
weeklycaseticks = list(yearone_weekly['New Positive'].describe()[1:].sort_values().astype(int).drop(['std','50%']))
usafcaseticks = list(range(0,int(wcil_il['Total Positive'].max())+1,500)) + [int(wcil_il['Total Positive'].max())]
usafweeklycaseticks = list(wcil_il['New Positive'].describe()[1:].sort_values().astype(int).drop(['std','50%']))
fig.update_layout(title='A Comparison of WCHD Reporting vs. USAFacts.org Reporting',
                  yaxis={'tickvals':caseticks},
                  yaxis2={'tickvals':weeklycaseticks},
                  yaxis3={'tickvals':usafcaseticks},
                  yaxis4={'tickvals':usafweeklycaseticks},
                  )
plot(fig,filename='graphics/yearone-WCHDvUSAF.html')
div_wchdusaf = plot(fig, include_plotlyjs=False, output_type='div')
with open('graphics/yearone-WCHDvUSAF.txt','w') as f:
    f.write(div_wchdusaf)
    f.close()

#%%

# five hightest new case weeks and how they compared

topfiveweeks_idx = wcil_il['New Positive'].sort_values(ascending=False).index[:5]   
cols = ['New Positive','New Positive per 100k','New Positive per 100k rank','New Positive per 100k percentile']
topfive_usa = wcil_usa.loc[topfiveweeks_idx][cols]
topfive_il = wcil_il.loc[topfiveweeks_idx][cols]

#%%

broke90ptile_usa_idx = wcil_usa['New Positive per 100k percentile'][wcil_usa['New Positive per 100k percentile'] > .9].sort_values(ascending=False).index
broke90ptile_il_idx = wcil_il['New Positive per 100k percentile'][wcil_il['New Positive per 100k percentile'] > .9].sort_values(ascending=False).index
