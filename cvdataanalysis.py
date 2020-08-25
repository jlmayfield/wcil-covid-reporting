#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  9 08:51:52 2020

@author: jlmayfield
"""


import pandas as pd
import numpy as np



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
    

# date to Illinois Recovery Phase
def which_phase(d):
    LAST_PHASE2 = pd.to_datetime('05-28-2020')
    LAST_PHASE3 = pd.to_datetime('06-25-2020')
    if d <= LAST_PHASE2:
        return 'Phase 2'
    elif d <= LAST_PHASE3:
        return 'Phase 3'
    else:
        return 'Phase 4'
    
# this week is week k, week d_zero is the first day of the dataset    
def which_week(d,d_zero):
    return str( (d - d_zero).days // 7 ) 

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
    