#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  9 08:49:09 2020

@author: jlmayfield
"""

import pandas as pd
import numpy as np

def prepwchd(raw_wchd):
    """
    Rebuild raw data with same index as usafacts data: (date,state,county)
    
    Parameters
    ----------
    raw_wchd : dataFrame
        WCHD as read from google sheets.

    Returns
    -------
    DataFrame
        Same data as the raw data set but the index is now hierarchical 
        to match the usafacts data

    """
    raw_wchd['countyFIPS'] = 17187
    raw_wchd['stateFIPS'] = 17
    return raw_wchd.reset_index().set_index(['date','stateFIPS','countyFIPS'])

def prepusafacts(raw_usafacts):
    """
    raw total casese data read from usafacts csv files into hierarchical index
    of (date,state,county).

    Parameters
    ----------
    raw_usafacts : DataFrame
        raw usafacts data

    Returns
    -------
    reorg : DataFrame
        The data is now a single column data frame (total cases) with
        a multi-index: (date,countyFIPS,stateFIPS). Names were dropped 
        but can be recovered through the population dataframe as needed
    """
    reorg = raw_usafacts.drop(['County Name','State'],
                              axis=1).reset_index().set_index(['countyFIPS','stateFIPS'])
    reorg = reorg.stack().rename('Total Cases').to_frame()
    reorg.index.names = ['countyFIPS','stateFIPS','date']
    reorg = reorg.reorder_levels(['date','stateFIPS','countyFIPS'])
    return reorg


def usafactsprep(casedata):
    dates = np.array(casedata.columns[3:].map(pd.to_datetime))
    states = casedata['State'].unique()
    cfips = np.array(casedata.index)
    midx = pd.MultiIndex.from_product([dates,cfips,states],
                                      names=['date','countyFIPS','State'])

def datefix(casedata):
    """))
    Rewrite date strings to pandas standard and reorganize columns to be in
    chronological order.

    Parameters
    ----------
    casedata : DataFrame
        Raw dataframe from file input. Assumes first three columns are city,
        state, and fips data and Date-based case data begins in column 4.
    Returns
    -------
    DataFrame
        Case data with date-based columns in pandas standard formated and sorted.

    """
    dates = casedata.columns[3:]
    fixed = { d : str(pd.to_datetime(d).date()) for d in dates}
    dstr = casedata.rename(columns=fixed)
    sorted_dates = sorted(fixed.values())    
    return dstr[list(casedata.columns[0:3]) + sorted_dates]

def prune_data(casedata,pad=6):
    """
    Remove all dates up until the first reported case in the given data set and
    leaves pad number of zero case days proceeding that date. It is assumed
    that at least pad number of days exist prior to the first recorded case.
    Parameters
    ----------
    casedata : DataFrame
        County level case data

    Returns
    -------
    DataFrame
        Copy of case data but with all dates prior to the first known case 
        removed. 

    """
    has_cases = (casedata.iloc[:,3:] != 0).any(axis=0)
    first = casedata.columns.get_loc(has_cases.idxmax())
    if first - pad < 3:
        needed = abs((first-pad)-3) #missing days for pad
        first_date = pd.to_datetime(casedata.columns[3]) #as datetime
        missing = [str((first_date - pd.Timedelta(n,unit='D')).date())
                   for n in range(needed,0,-1)] # missing dates 
        dates = pd.DataFrame(index=casedata.index,
                             columns=missing).fillna(0) # pad dates
        return pd.concat([casedata.iloc[:,0:3],dates,casedata.iloc[:,3:]],axis=1)
    else:
        days = list(casedata.iloc[:,first-pad:].columns)
        keepers = list(casedata.columns[0:3])+days    
        return casedata[keepers]