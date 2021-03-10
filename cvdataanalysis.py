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
    def which_phase(idx):
        d = idx[0]
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
    days = wchd_data.index.map(lambda idx: idx[0].dayofweek).to_series(index=wchd_data.index)
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
def _newtests_old(wchd_data,init=23):
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
    def roller(grp):
        return grp.rolling(7,min_periods=1).mean()
    sda = column.to_frame().groupby(level=['countyFIPS']).apply(roller)
    return sda[column.name].rename(name)

def _sevenDayPRate(testdata):
    name = 'Positive Test Rate 7 Day Window'
    def roller(grp):
        return grp.rolling(7,min_periods=1).sum()
    tots = testdata.groupby(level=['countyFIPS']).apply(roller)
    rates = tots['New Positive']/tots['New Tests']
    return rates.rename(name)

def _increasesInNDays(column,N):
    def increased(col):
        return (col.diff() > 0).astype(int)    
    name = column.name + ' Increase in {:d} Days'.format(N)
    ups = increased(column).rolling(N,min_periods=0).sum().astype(int)
    return ups.rename(name)

def _increaseStreak(col):
    def increased(col):
        return (col.diff() > 0).astype(int) 
    did_increase = increased(col)
    tot_increase = did_increase.cumsum()
    offsets = tot_increase.mask(did_increase != 0).ffill()
    streaks = (tot_increase - offsets).astype(int)
    return streaks.rename(col.name + " Increase Streak")                    

def _per100k(column,pop):
    '''
    Returns a generator for per100k 

    Parameters
    ----------
    column : TYPE
        DESCRIPTION.
    pop : TYPE
        DESCRIPTION.

    Returns
    -------
    adjusted : TYPE
        DESCRIPTION
    '''
    def scale(row):
        if row['countyFIPS'] in [0,1]:
            row[column.name] = 0
        elif pop['population'][row['countyFIPS']] == 0:
            row[column.name] = 0
        else:
            p = pop['population'][row['countyFIPS']]
            row[column.name] = row[column.name] / p * 100000.0 
        return row
    flat = column.to_frame().reset_index()
    newname = column.name + ' per 100k'   
    flat = flat.apply(scale,axis=1)
    newcol = flat.set_index(['date','stateFIPS','countyFIPS'])
    newcol = newcol[column.name].rename(newname)              
    return newcol

    

#%%
def _totalneg(raw_idph):
    tneg = raw_idph['Total Tests'] - raw_idph['Total Positive']
    tneg = tneg.rename('Total Negative')
    return tneg

def _newtests(raw_idph):
    daily = raw_idph.groupby(by=['stateFIPS','countyFIPS']).diff().fillna(0).astype(int)
    return daily.rename('New Tests')

def _newvacs(raw_idph):
    daily = raw_idph.groupby(by=['stateFIPS','countyFIPS']).diff().fillna(0).astype(int)
    return daily.rename('New Vaccinated')

def _pcentvac(raw_idph,pop):
    pvac = raw_idph.groupby(by=['stateFIPS','countyFIPS']).apply(lambda g : g / pop)
    return pvac.rename('% Vaccinated')
    

def expandIDPHDaily(raw_idph,pop=17032):
    expanded = pd.concat([raw_idph,
                          _phase(raw_idph),
                          _dayofweek(raw_idph),
                          _totalneg(raw_idph),
                          _newpos(raw_idph['Total Positive']),
                          _newdead(raw_idph['Total Deaths']),
                          _newtests(raw_idph['Total Tests']),
                          _newvacs(raw_idph['Total Vaccinated']),
                          _pcentvac(raw_idph['Total Vaccinated'],pop)
                          ],
                          axis=1)   
    expanded = pd.concat([expanded,
                          _newneg(expanded['Total Negative']),
                          _newposrate(expanded)
                         ],
                          axis=1)
    expanded = pd.concat([expanded,
                          _sevenDayAvg(expanded['% New Positive']),
                          _sevenDayAvg(expanded['New Positive']),
                          _sevenDayAvg(expanded['New Vaccinated']),
                          _sevenDayPRate(expanded[['New Tests','New Positive']])],
                          axis = 1)
    expanded['New Positive per 100k'] = expanded['New Positive'] * 100000 / pop
    cols = ['DayOfWeek','Phase',
            'New Tests', 'New Positive','New Negative',
            'New Positive per 100k', '% New Positive',
            '7 Day Avg New Positive','7 Day Avg % New Positive',
            'Positive Test Rate 7 Day Window',
            'New Deaths',
            'Total Tests','Total Positive','Total Negative',
            'Total Deaths',
            'New Vaccinated','Total Vaccinated',
            '7 Day Avg New Vaccinated','% Vaccinated'
            ]
    return expanded[cols]
        
#%%

def expandWCHDData(raw_wchd_data,pop=17032):
    """
    Expand upon raw data set.

    Parameters
    ----------
    raw_wchd_data : DataFrame
        Data from WCHD/IL DPH - New Postive, Total Negative, Total Recovered, and
        New Deaths, Region 2 Pos Rate      
    pop : int
        Population of Warren County, IL. Default 17032.

    Returns
    -------
    DataFrame. Expanded daily dataset for WCIL

    """
    expanded = pd.concat([raw_wchd_data,
                          _phase(raw_wchd_data),
                          _dayofweek(raw_wchd_data),
                          _totalpos(raw_wchd_data),
                          _totaldeaths(raw_wchd_data),
                          _newrecover(raw_wchd_data)],
                          axis=1)      
    expanded = pd.concat([expanded,
                          _totaltests(expanded),
                          _active(expanded)],
                         axis=1)
    expanded = pd.concat([expanded,
                          _newtests_old(expanded)],axis=1)
    expanded = pd.concat([expanded,
                          _newneg(expanded['Total Negative']),                         
                          _newposrate(expanded)],
                         axis=1)
    expanded = pd.concat([expanded,
                          _sevenDayAvg(expanded['% New Positive']),
                          _sevenDayAvg(expanded['New Positive']),
                          _sevenDayPRate(expanded[['New Tests','New Positive']])],
                          axis = 1)
    expanded['New Positive per 100k'] = expanded['New Positive'] * 100000 / pop
    cols = ['DayOfWeek','Phase',
            'New Tests', 'New Positive','New Negative',
            'New Positive per 100k', '% New Positive',
            '7 Day Avg New Positive','7 Day Avg % New Positive',
            'Positive Test Rate 7 Day Window',
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
    def find_region(idx):
        fips = idx[2]
        for k in regions:
            if fips in regions[k]:
                return 'IL-'+ k
        if fips != 0:
            return pop.loc[fips]['State']
        else:
            return idx[1]
    nonzeros = usf_cases.index.map(find_region).to_series(index=usf_cases.index)
    nonzeros = nonzeros.rename('Recovery Region')
    return nonzeros


def _newpos(totcases):
    daily = totcases.groupby(by=['stateFIPS','countyFIPS']).diff().fillna(0).astype(int)
    return daily.rename('New Positive')

def _newneg(totcases):
    daily = totcases.groupby(by=['stateFIPS','countyFIPS']).diff().fillna(0).astype(int)
    return daily.rename('New Negative')

def _newdead(totdead):
    daily = totdead.groupby(by=['stateFIPS','countyFIPS']).diff().fillna(0).astype(int)
    return daily.rename('New Deaths')

## Intended use is on previously selected subset of USFacts dataset.

def expandUSFData(usf_cases,pop):    
    reorg = pd.concat([usf_cases,
                       #_phase(usf_cases),                       
                       #_dayofweek(usf_cases),
                       #_ilregions(usf_cases, pop),
                       _newpos(usf_cases['Total Positive']),
                       _newdead(usf_cases['Total Deaths'])],
                      axis=1)    
    reorg = pd.concat([reorg,                       
                       _per100k(reorg['New Positive'], pop),
                       _per100k(reorg['Total Positive'], pop),
                       _per100k(reorg['New Deaths'], pop),
                       _per100k(reorg['Total Deaths'], pop)],
                      axis=1)
    reorg = pd.concat([reorg,
                       _sevenDayAvg(reorg['New Positive']),
                       _sevenDayAvg(reorg['New Positive per 100k'])],
                      axis=1)    
    return reorg
    
#%%

def _mc7day(col):
    name = '7 Day Avg ' + col.name
    return col.rolling(7).mean().fillna(0).rename(name)

def _total(col):
    name = 'Total ' + col.name
    return col.cumsum().rename(name)


def expandMCData(mc_cases):
    everyone = (mc_cases['Student']+mc_cases['Employee']).rename('Everyone')
    mc_cases = pd.concat([mc_cases,everyone],axis=1)
    mc_cases = pd.concat([mc_cases,
                          _mc7day(mc_cases['Student']),
                          _mc7day(mc_cases['Employee']),
                          _mc7day(mc_cases['Everyone']),
                          _total(mc_cases['Student']),
                          _total(mc_cases['Employee']),
                          _total(mc_cases['Everyone'])
                          ],
                         axis=1)
    return mc_cases

    
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

