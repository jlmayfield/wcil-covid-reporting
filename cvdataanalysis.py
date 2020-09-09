#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  9 08:51:52 2020

@author: jlmayfield
"""


import pandas as pd
import numpy as np



#%%

#  *****Depends on Raw Data*****
def _phase(wchd_data):
    def which_phase(d):
        LAST_PHASE2 = pd.to_datetime('05-28-2020')
        LAST_PHASE3 = pd.to_datetime('06-25-2020')
        if d <= LAST_PHASE2:
            return 'Phase 2'
        elif d <= LAST_PHASE3:
            return 'Phase 3'
        else:
            return 'Phase 4'
    p = wchd_data.index.map(which_phase).to_series(index=wchd_data.index)
    return p.rename('Phase')

def _dayofweek(wchd_data):
    days = wchd_data.index.map(lambda d: d.dayofweek).to_series(index=wchd_data.index)
    return days.rename('DayOfWeek')

def _totalpos(wchd_data):
    totpos = wchd_data['New Positive'].cumsum()
    return totpos.rename('Total Positive')

def _newrecover(wchd_data):
    newrecov = wchd_data['Total Recovered'].diff().fillna(0).astype(int)
    return newrecov.rename('New Recovered')

def _totaldeaths(wchd_data):
    dead = wchd_data['New Deaths'].cumsum()
    return dead.rename('Total Deaths')       

#  **** Depends on one step computed data *** 

def _totaltests(wchd_data):
     tottests = wchd_data['Total Negative'] + wchd_data['Total Positive']
     return tottests.rename("Total Tests")

def _active(wchd_data):
    active = wchd_data['Total Positive'] - wchd_data['Total Recovered'] - wchd_data['Total Deaths']
    return active.rename('Active Cases')  

# **** Depends on two step computed data *** 

# WC had 23 new tests on 4/22
def _newtests(wchd_data,init=23):
    newtests = wchd_data['Total Tests'].diff()
    newtests.iloc[0] = wchd_data['New Positive'].iloc[0]
    newtests.loc[pd.to_datetime('04-22-2020')] = init
    return newtests.rename('New Tests')

# **** Depends on three step computed data

def _newneg(wchd_data):
    newneg = wchd_data['New Tests'] - wchd_data['New Positive']
    return newneg.rename('New Negative')

def _newposrate(wchd_data):
    posrate = wchd_data['New Positive'] / wchd_data['New Tests']
    return posrate.rename('% New Positive').fillna(0)

#%%%

## Fill initial values with 0?
def _sevenDayAvg(column):
    name = '7 Day Avg ' + column.name
    sda = column.rolling(7).mean().fillna(0)
    return sda.rename(name)

def _per100k(column,pop):
    c_frame = column.to_frame()
    cidx = c_frame.index
    newname = column.name + ' per 100k'
    adjusted = ( (c_frame.loc[ (slice(None),
                                slice(None),
                                cf), :] * 100000 / pop['population'].loc[cf]).iloc[:,0].rename(newname) 
                for cf in cidx.get_level_values('countyFIPS').unique() )
    return adjusted
    
    
    

#%%


def expandWCHDData(raw_wchd_data):
    """
    Expand upon raw data set.

    Parameters
    ----------
    raw_wchd_data : DataFrame
        Data from WCHD/IL DPH - New Postive, Total Negative, Total Recovered, and
        New Deaths, Region 2 Pos Rate        

    Returns
    -------
    None.

    """
    expanded = pd.concat([raw_wchd_data,
                          _phase(raw_wchd_data),
                          _dayofweek(raw_wchd_data),
                          _totalpos(raw_wchd_data),
                          _totaldeaths(raw_wchd_data),
                          _newrecover(raw_wchd_data)],
                          axis=1)
    expanded['countyFIPS'] = 17187
    expanded = pd.concat([expanded,
                          _totaltests(expanded),
                          _active(expanded)],
                         axis=1)
    expanded = pd.concat([expanded,
                          _newtests(expanded)],axis=1)
    expanded = pd.concat([expanded,
                          _newneg(expanded),                         
                          _newposrate(expanded)],
                         axis=1)
    expanded = pd.concat([expanded,
                          _sevenDayAvg(expanded['% New Positive'])],
                          axis = 1)
    cols = ['countyFIPS','DayOfWeek','Phase','New Tests',
            'New Positive','New Negative','% New Positive',
            '7 Day Avg % New Positive',
            'New Recovered','New Deaths','Active Cases',
            'Total Tests','Total Positive','Total Negative',
            'Total Recovered','Total Deaths', 'Region 2 Pos Rate'
            ]
    return expanded[cols]

#%%


def _ilregions(usf_cases,pop):
    regions = {'1':[17085,17177,17201,17007,17015,17141,17037,17195,17103], 
               '2':[17187, 17095, 17071, 17109, 17057, 17131, 17161, 17073, 17011,
                    17175, 17143, 17179, 17155, 17123, 17203, 17099, 17113, 17105,
                    17093, 17063],
               '3':[17067,17001,17149,17013,17169,17009,17137,17171,17061,17083,
                    17125,17017,17117,17167,17129,17107,17021,17135],
               '4':[17119,17163,17133,17157,17005,17027,17189],
               '5':[17003,17153,17127,17151,17069,17087,17181,17059,17165,
                    17199,17077,17145,17055,17065,17193,17185,17047,17191,
                    17121,17081],
               '6':[17019, 17023, 17025, 17029, 17033, 17035, 17039, 17041, 17045,
                    17049, 17051, 17053, 17075, 17079, 17101, 17139, 17147, 17159,
                    17173, 17183,17115],
               '7':[17197,17091],
               '8':[17089,17043],    
               '9':[17111,17097],
               #cook (chicago land) was artificially broken up into 2 regions      
               '10-11':[17031]}    
    def find_region(fips):
        for k in regions:
            if fips in regions[k]:
                return 'IL-'+ k
        if fips != 0:
            return pop.loc[fips]['State']
        else:
            return ''
    nonzeros = usf_cases.index.map(find_region).to_series(index=usf_cases.index)   
    return nonzeros


## Intended use is on previously selected subset of USFacts dataset
def expandUSFData(usf_cases,pop):
    reorg = usf_cases.drop(['County Name','State'],
                           axis=1).reset_index().set_index(['countyFIPS','stateFIPS'])
    reorg = reorg.stack().rename('Total Cases').to_frame()
    reorg.index.names = ['countyFIPS','stateFIPS','date']
    reorg = reorg.reorder_levels(['date','stateFIPS','countyFIPS'])
    #reorg = pd.concat([reorg,_per100k(reorg['Total Cases'],pop)])
    return reorg
    

#%%

def to_for100k(casedata,pop):
    """
    Convert case numbers to a per 100000 scale based on populations listed in
    pop.

    Parameters
    ----------
    casedata : DataFrame
        county level case data  
    pop : Dataframe
        county level population

    Returns
    -------
    normed : DataFrame
        Copy of casedata with all case numbers scaled to per 100000 people. 

    """
    normed = casedata.copy()
    dates = normed.columns[3:]
    for i in normed.index:
        cpop = pop.loc[i]['population']
        normed.update( (normed.loc[[i]][dates] * 100000) / cpop)
    return normed



def to_new_daily(casedata):
    """
    Compute new daily cases from total cases per day. At least one day of
    padding (zero cases) is assumed

    Parameters
    ----------
    casedata : DataFrame
        Dataset of total cases by date

    Returns
    -------
    daily : DataFrame
        Dataset of new cases per date

    """
    daily = casedata.copy()
    dates = casedata.columns[3:]    
    for i in range(1,len(dates)):
        yest = casedata[dates[i-1]]
        today = casedata[dates[i]]
        daily[dates[i]] = today - yest
    return daily


def to_sevenDayAvg(casedata):
    """
    Compute 7 day average for values in casedata. The first 6 dates in the 
    data set are used for averaging but dropped from the result. It's recommended
    that, when possible, these be days prior to verified cases. (see prune data)
    Parameters
    ----------
    casedata : DataFrame
        County level case data.

    Returns
    -------
    avgs : Dataframe
        7 day rolling averages of casedata

    """
    dates = casedata.columns[3:]
    not_dates = casedata.columns[0:3]
    avgs = casedata[list(not_dates)+list(dates[6:])].copy()
    for i in range(6,len(dates)):
        week = casedata[dates[i-6:i+1]]
        avg = week.mean(axis=1).round(decimals=2)
        avgs[dates[i]] = avg
    return avgs

#%%    

def demographic_totals(demo_daily,start=7,end=0):
    """
    Total new cases by demographic categories. 

    Parameters
    ----------
    demo_daily : DataFrame
        Daily Demographic data on new cases
    start : int, optional
        How many days ago to start the time window. The default is 7.
    end : int, optional
        How many days ago to end the time window. The default is 0.

    Returns
    -------
    totals : DataFrame
        totals for the specified time window

    """
    s_idx = len(demo_daily)-start
    e_idx = len(demo_daily)-end
    totals_men = demo_daily.iloc[s_idx:e_idx,:]['Male'].sum()
    totals_women = demo_daily.iloc[s_idx:e_idx,:]['Female'].sum()
    totals = pd.DataFrame([],columns=['age','sex','cases'])
    for a in totals_men.index:
        totals = totals.append(pd.Series([a,'Male',totals_men[a]],
                                         index=['age','sex','cases']),
                               ignore_index=True)
    for a in totals_women.index:
        totals = totals.append(pd.Series([a,'Female',totals_women[a]],
                                         index=['age','sex','cases']),
                               ignore_index=True)
    return totals

