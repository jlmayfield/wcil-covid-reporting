#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun 28 10:15:33 2021

@author: jlmayfield
"""


import pandas as pd
import numpy as np
import math

from plotly.subplots import make_subplots
import plotly.graph_objects as go
from plotly.offline import plot
import plotly.express as px


import cvdataprep as cvdp
import cvdataanalysis as cvda
import cvdataviz as cvdv


# site table margins
margs = go.layout.Margin(l=0, #left margin
                         r=0, #right margin
                         b=35, #bottom margin
                         t=25  #top margin
                         )      

#%%

dist = pd.read_csv('sf12010countydistancemiles.csv',
                   dtype={'county1':np.int64,
                          'mi_to_county':np.float64,
                          'county2':np.int64})

def countiesWithin(fips,d):
    county = dist[(dist['county1'] == fips) & (dist['mi_to_county'] <= d)]
    return pd.Index(county['county2'])

#%%

cinfo = pd.read_csv('IDPH_Totals/IDPH_County_Info.csv',
                             header=[0],index_col=0).set_index('County')

#names = cinfo[~cinfo['County'].isin(['Illinois','Unknown','Out Of State'])]
#%%

counties = cvdp.IDPHDataCollector.getCountyData()
nopop = counties[-2:].set_index('County')
counties = counties[:-2].set_index('County')

populations, _, _ = cvdp.loadusafacts()

IL = populations[populations['State']=='IL']
IL = IL[IL.index != 0]
names = IL['County Name'].apply(lambda n : n[:-7]).reset_index().set_index('County Name')
names = names['countyFIPS'].to_dict()
names['Illinois'] = 17
names['Chicago'] = 171
r_names = {v:k for k,v in names.items()}

t = pd.Series(names).astype(int)
t.name = 'countyFIPS'

counties = pd.concat([counties,t],axis=1)
counties = counties.rename(columns={'Population':'population'})
c = counties.reset_index().set_index('countyFIPS').rename(columns={'index':'Name'})

#%%

def firstCase(df):
    fstidx = (df > 0).idxmax()
    if fstidx is tuple:
        return fstidx[0]
    else:
        return fstidx    

def totfilename(county):
    return 'IDPH_DAILY_'+county.upper()+'.csv'

def loadAndExpand(cname):
    if cname in names.keys():
        fips = names[cname]
    else:
        fips = cname
    tots = pd.read_csv('IDPH_Totals/'+totfilename(cname),
                        header=[0],index_col=0,
                        parse_dates=True)
    pop = counties.loc[cname]['population']
    tots.loc[:,'countyFIPS'] = fips
    tots.loc[:,'stateFIPS'] = 17
    tots = tots.reset_index().set_index(['date','stateFIPS','countyFIPS'])
    expanded = cvda.expandIDPHDaily(tots,pop) 
    expanded = pd.concat([expanded,
                          cvda._per100k(expanded['7 Day Avg New Positive'], c),
                          cvda._per100k(expanded['New Vaccinated'], c),
                          cvda._per100k(expanded['7 Day Avg New Vaccinated'], c),
                          ],
                          axis=1)                           
    return expanded.reset_index()

#%%

# build IL wide stats!
allofit = pd.concat([loadAndExpand(f) for f in counties.index]).set_index(['date','stateFIPS','countyFIPS']).sort_index()   
outTots = cvdp.IDPHDataCollector.getNonCountyData()

#%%

lastday = allofit.index[-1][0]
lastvac = lastday - pd.Timedelta(1,'D')
firstvac = (allofit['New Vaccinated'] > 0).idxmax()[0]

#%%
vacdata = allofit[['Total Vaccinated','% Vaccinated','7 Day Avg New Vaccinated']].loc[lastvac,:,:]
vacdata = vacdata.reset_index().drop(['stateFIPS','date'],axis=1).set_index('countyFIPS')
statewide = vacdata.loc[17]
vacdata = vacdata[vacdata.index != 17]
#%%

vacdata.loc[:,'% Vac Rank'] = vacdata['% Vaccinated'].rank(ascending=False,method='dense')

#%%
summary = vacdata['% Vaccinated'].describe()
fig = px.histogram(vacdata,x='% Vaccinated',
                   nbins=int(np.ceil((summary['max']-summary['min'])/.02))
                   )
fig.update_layout(bargap=0.1)
#plot(fig)

#%%

def addNormedCaseVacPlot(fig,row,col,df):
    fig.add_trace(go.Scatter(x=df.index, y=df['7 Day Avg New Positive per 100k'],
                             name="New Cases per 100k(7 day avg)",
                             showlegend=False,
                             marker_color=px.colors.qualitative.Plotly[1]),               
                  row=row,col=col,secondary_y=False,
                  )
    fig.add_trace(go.Scatter(x=df.index, y=df['% Vaccinated'],
                             name="Percent Population Vaccinated",
                             showlegend=False,
                             marker_color=px.colors.qualitative.Plotly[0]),
                  row=row,col=col,secondary_y=True,
                  )
    
def addFullVacPlot(fig,row,col,df):
    fig.add_trace(
    go.Scatter(x=df.index,
               y=df['% Vaccinated'],
               fill='tozeroy',
               fillcolor = 'rgba(9,75,81,0.2)',
               marker_color=px.colors.qualitative.D3[9],
               name="% Population Vaccinated",
               showlegend=False),
    secondary_y=True,row=row,col=col
    )
    fig.add_trace(go.Bar(x=df.index,
                         y=df['New Vaccinated per 100k'],
                         marker_color=px.colors.qualitative.G10[0],
                         name="New Full Vaccinations",
                         showlegend=False),               
        secondary_y=False,row=row,col=col
    )
    fig.add_trace(go.Scatter(x=df.index,
                     y=df['7 Day Avg New Vaccinated per 100k'],
                     marker_color=px.colors.qualitative.G10[9],
                     name="New Full Vaccinations (7 Day Avg)",
                     showlegend=False),               
    secondary_y=False,row=row,col=col
    )




#%%
# get 50 mile radius
aoi_fips = countiesWithin(17187, 50).append(pd.Index([17187]))
aoi_fips = aoi_fips[ aoi_fips >= 17000][ aoi_fips < 18000 ]
aoi_df = allofit.loc[:,17,aoi_fips]
# get current vac % and cases. Sort vac % in decreasing order
currvac = (aoi_df.loc[lastvac,17,:]['% Vaccinated']).sort_values(ascending=False)
currcase = aoi_df.loc[lastday,17,:]['7 Day Avg New Positive per 100k']
currvac2 = aoi_df.loc[lastday,17,:]['7 Day Avg New Vaccinated per 100k']
     
# get names (aoi) and name:fips dict for % vac order
aoi = [r_names[f] for f in currvac.index]
aoi_names = { c:names[c] for c in aoi}

# all time max on cases and % vac for y ranges
y1max = aoi_df['7 Day Avg New Positive per 100k'].max()
y1bmax = aoi_df['New Vaccinated'].max()
y2max = aoi_df['% Vaccinated'].max()


ncols = 2
nrows = int(math.ceil(len(aoi)/ncols))
specs = [[{"secondary_y": True},{"secondary_y": True}]]*nrows
if nrows * ncols > len(aoi):
    specs = [[{"secondary_y": True},{"secondary_y": True}]]*(nrows-1) +\
        [[{'secondary_y':True},{}]]
        
title_info = zip(aoi,currvac,currcase.loc[currvac.index])
titles = [f'<b>{n} County</b> ({v:,.1%} , {c:.1f} cases per 100k)' for n,v,c in title_info]    


title_info2 = zip(aoi,currvac,currvac2.loc[currvac.index])
titles2 = [f'<b>{n} County</b> ({v:,.1%}, {c:.1f} vaccinations)' for n,v,c in title_info2]      
        
#%%
fig = make_subplots(rows=nrows,cols=ncols,
                    #shared_yaxes=True,
                    #shared_xaxes=True,
                    specs=specs,
                    subplot_titles=titles)

for i in range(len(aoi)):
    county = aoi_names[aoi[i]]
    addNormedCaseVacPlot(fig,i//ncols + 1,i%ncols + 1,
                         aoi_df.loc[:,17,county])


# site margins
margs = go.layout.Margin(l=0, #left margin
                         r=0, #right margin
                         b=35, #bottom margin
                         t=175  #top margin
                         )                          

# Add figure title
fig.update_layout(
    title_text="<b>New Cases per 100k (7 Day Avg) and Percent Vaccinated</b><br>" +\
        "<i>Warren County Region</i><br>"+\
            "Updated on " + str(lastday.date())
        ,    
    margin = margs,
    width= 1200,
    height= 800  
)
fig.update_yaxes(#title_text="<b>New Cases per 100k(7 day avg)</b>", 
                 range = (0,y1max+5),
                 secondary_y=False)
fig.update_yaxes(#title_text="<b>% Vaccinated</b>", 
                 range = (0,y2max+.025),
                 tickformat = ',.0%',
                 secondary_y=True)

#plot(fig,filename='graphics/vacCaseRegional.html')
vaccasereport = plot(fig, include_plotlyjs=False, output_type='div')

#%%

fig = make_subplots(rows=nrows,cols=ncols,
                    #shared_yaxes=True,
                    #shared_xaxes=True,
                    specs=specs,
                    subplot_titles=titles2)

for i in range(len(aoi)):
    county = aoi_names[aoi[i]]
    addFullVacPlot(fig,i//ncols + 1,i%ncols + 1,
                   aoi_df.loc[:,17,county].loc[firstvac:])


# site margins
margs = go.layout.Margin(l=0, #left margin
                         r=0, #right margin
                         b=35, #bottom margin
                         t=175  #top margin
                         )                          

# Add figure title
fig.update_layout(
    title_text="<b>New Vaccinations per 100k (with 7 Day Avg) and Percent Vaccinated</b><br>" +\
        "<i>Warren County Region</i><br>"+\
            "Updated on " + str(lastday.date())
        ,    
    margin = margs,
    width= 1200,
    height= 800  
)
fig.update_yaxes(#title_text="<b>New Cases per 100k(7 day avg)</b>", 
                 range = (0,y1bmax+5),
                 secondary_y=False)
fig.update_yaxes(#title_text="<b>% Vaccinated</b>", 
                 range = (0,y2max+.025),
                 tickformat = ',.0%',
                 secondary_y=True)

#plot(fig,filename='graphics/vacOnlyRegional.html')
vaconlyreport = plot(fig, include_plotlyjs=False, output_type='div')


#%%

pgraph = '<p></p>'
mdpage = ""
header = """---
layout: page
title: Warren County - Regional
permalink: /wcil-regional-report/
---
<script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
"""
timestamp = pd.to_datetime('today').strftime('%H:%M %Y-%m-%d')
header = header + '<p><small>last updated:  ' + timestamp + '</small><p>\n\n'
howto = """
<p>The first graphic below reports on two metrics: the seven day average of new cases per 
100,000 people and the percent of the population that is full vaccinated. 
Data comes from the Illinois Department of Public Health and is updated Monday 
through friday. The graphs are sorted by the percent of the population that 
is vaccinated and each title lists the current percentage as well as the 
current seven day average of new cases per 100,000 people. The graphs themselves 
show the case average in red and the percent vaccinated in blue and cover the
entire history of the pandemic.</p> 
<p>
The second graphic reports on vaccine data only and scales vaccination counts per 100,000
people. The titles list percent of the population vaccinated and the current seven
day average of new fully vaccinated individuals for each count. Bars are the daily 
new fully vaccinationated people (per 100k) and the dark blue line is the seven day average of
that statistic. In general, you can look at the dark line and bars to compare vacciantation 
rates in each county. 
</p>
"""


mdpage = header + howto + pgraph + vaccasereport + pgraph + vaconlyreport

with open('docs/wcilRegion.md','w') as f:
    f.write(mdpage)
    f.close()