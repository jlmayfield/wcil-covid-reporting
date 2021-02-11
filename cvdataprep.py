#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  9 08:49:09 2020

@author: jlmayfield
"""

import pandas as pd
import numpy as np


#%%

def loadwchd(datadir='./'):  
    """
    Read in raw data from WCHD and prepare as DataFrames

    Parameters
    ----------
    datadir : str, optional
        Path to directory containing the CSV files. The default is './'.

    Returns
    -------
    reports_wchd : DataFrame
        Case data. New Positive, Total Negative, New Deaths, and R2 rate data
    demo_wchd : DataFrame
        Case Demographics per Day
    death_wchd : DataFrame
        Death Demographics per Day

    """
    reports_wchd = pd.read_csv(datadir+'WCHD_Reports.csv',
                         header=[0],index_col=0,
                         parse_dates=True).fillna(0)
    demo_wchd = pd.read_csv(datadir+'WCHD_Case_Demographics.csv',
                       skiprows=[2],
                       header=[0,1],index_col=0,
                       parse_dates=True).fillna(0).iloc[:,0:12]
    demo_wchd.columns.names = ['Sex','Age']
    death_wchd = pd.read_csv('WCHD_Death_Demographics.csv',
                       skiprows=[2],
                       header=[0,1],index_col=0,
                       parse_dates=True).fillna(0).iloc[:,0:12]
    death_wchd.columns.names = ['Sex','Age']    
    return (reports_wchd,demo_wchd,death_wchd)

def loadidphdaily(datadir='./'):  
    """
    Read in raw data from IDPH about WC and prepare as DataFrames

    Parameters
    ----------
    datadir : str, optional
        Path to directory containing the CSV files. The default is './'.

    Returns
    -------
    tots : DataFrame
      

    """
    tots = pd.read_csv(datadir+'IDPH_Daily.csv',
                         header=[0],index_col=0,
                         parse_dates=True).fillna(0)
    tots.loc[:,'New Vaccines'] = tots['New Vaccines'].astype(int)    
    return tots

def loadusafacts(datadir='./'):
    """
    Read in raw data from USAFacts.org. 

    Parameters
    ----------
    datadir : str, optional
        Path to directory containing the CSV files. The default is './'.

    Returns
    -------
    population : DataFrame
        County Data with Population
    cases : DataFrame
        Total Cases per day

    """    
    population = pd.read_csv(datadir+'covid_county_population_usafacts.csv',
                         dtype={'countyFIPS':np.int64,
                                'County Name':str, 'State':str,
                                'population':np.int64},
                         index_col = 'countyFIPS')
    cases = pd.read_csv(datadir+'covid_confirmed_usafacts.csv',
                         dtype={'countyFIPS':np.int64,'stateFIPS':np.int64,
                                'County Name':str, 'State':str,
                                'date': np.datetime64,
                                'Total Positive':np.int64},
                         index_col = 'countyFIPS')
    deaths = pd.read_csv(datadir+'covid_deaths_usafacts.csv',
                         dtype={'countyFIPS':np.int64,'stateFIPS':np.int64,
                                'County Name':str, 'State':str,
                                'date': np.datetime64,
                                'Total Deaths':np.int64},
                         index_col = 'countyFIPS')
    return (population,cases,deaths)

def loadmcreports(datadir='./'):
    cases = pd.read_csv(datadir+'MC_Reports.csv',
                        dtype={'Student':'Int64',
                               'Employee':'Int64'},
                        parse_dates=True,
                        na_values=(''),
                        index_col = 'date').fillna(0)
    fst = cases.index[0]
    lst = pd.to_datetime('today')
    cases = cases.reindex(pd.date_range(fst,lst),fill_value=0)
    return cases                        

#%%

def prepidphdaily(raw_idph):
    raw_idph.loc[:,'countyFIPS'] = 17187
    raw_idph.loc[:,'stateFIPS'] = 17
    reorg = raw_idph.reset_index().set_index(['date','stateFIPS','countyFIPS'])
    reorg.sort_index(inplace=True)
    return reorg
    

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
    raw_wchd.loc[:,'countyFIPS'] = 17187
    raw_wchd.loc[:,'stateFIPS'] = 17
    reorg = raw_wchd.reset_index().set_index(['date','stateFIPS','countyFIPS'])
    reorg.sort_index(inplace=True)
    return reorg
    

def prepusafacts(raw_usafacts,raw_usf_deaths):
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
    result = reorg
    reorg = raw_usf_deaths.drop(['County Name','State'],
                                axis=1).reset_index().set_index(['countyFIPS','stateFIPS'])
    reorg.columns= pd.to_datetime(reorg.columns)
    reorg = reorg.stack().rename('Total Deaths').to_frame()
    reorg.index.names = ['countyFIPS','stateFIPS','date']
    reorg = reorg.reorder_levels(['date','stateFIPS','countyFIPS'])
    reorg.sort_index(inplace=True)
    return pd.concat([result,reorg],axis=1)

