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
    reorg = raw_wchd.reset_index().set_index(['date','stateFIPS','countyFIPS'])
    reorg.sort_index(inplace=True)
    return reorg
    

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
    reorg.columns= pd.to_datetime(reorg.columns)
    reorg = reorg.stack().rename('Total Positive').to_frame()
    reorg.index.names = ['countyFIPS','stateFIPS','date']
    reorg = reorg.reorder_levels(['date','stateFIPS','countyFIPS'])
    reorg.sort_index(inplace=True)
    return reorg

