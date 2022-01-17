#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul  9 08:49:09 2020

@author: jlmayfield
"""

import itertools
import math
import pandas as pd
import numpy as np
import requests as rq
import time



#%%

# https://data.census.gov/cedsci/table?g=0500000US17187&tid=ACSST5Y2019.S0101&moe=true
class WCILCensus:
    wchdmap = {'0-10':['00-04','05-09'],'10-20':['10-14','15-19'],                    
               '20-40':['20-24','25-29','30-34','35-39'],
               '40-60':['40-44','45-49','50-54','55-59'],
               '60-80':['60-64','65-69','70-74','75-79'],
               '80-100':['80-84','85+']}
    idphmap = {'<20':['00-04', '05-09', '10-14', '15-19'],
               '20-29':['20-24', '25-29'],
               '30-39':['30-34','35-39'],
               '40-49':['40-44','45-49'],
               '50-59':['50-54','55-59'],
               '60-69':['60-64','65-69'],
               '70-79':['70-74','75-79'],
               '80+':['80-84','85+']}
    normmap = {'0-19':['00-04','05-09','10-14','15-19'],
               '20-39':['20-24','25-29','30-34','35-39'],
               '40-59':['40-44','45-49','50-54','55-59'],
               '60-79':['60-64','65-69','70-74','75-79'],
               '80+':['80-84','85+']} 
    census = pd.read_csv('WCIL_census_data.csv',
                         index_col=0)
    @staticmethod
    def _remap(gmap):
        idx = gmap.keys()
        f = pd.DataFrame(data=[WCILCensus.census.loc[gmap[g]]['Female'].sum() for g in gmap],
                         index=idx,columns=['Female'])
        m = pd.DataFrame(data=[WCILCensus.census.loc[gmap[g]]['Male'].sum() for g in gmap],
                         index=idx,columns=['Male'])        
        return pd.concat([f,m],axis=1)        
    @staticmethod
    def loadcensus():
        return WCILCensus.census
    @staticmethod
    def loadidphgroups():
        return WCILCensus._remap(WCILCensus.idphmap)
    @staticmethod 
    def loadwchdgroups():
        return WCILCensus._remap(WCILCensus.wchdmap)
    @staticmethod
    def loadnormgroups():
        return WCILCensus._remap(WCILCensus.normmap)  
        
        
        

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

def loadidphdaily(county='Warren',datadir='./IDPH_Totals/'):  
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
    tots = pd.read_csv(datadir+'IDPH_DAILY_'+county.upper()+'.csv',
                         header=[0],index_col=0,
                         parse_dates=True)#.fillna(0)
    #tots.loc[:,'New Shots'] = tots['New Shots'].astype(int)    
    return tots

def loadidphdemos(county='Warren', datadir='./'):
    age = pd.read_csv(datadir+'IDPH_AGEDEMO_'+county.upper()+'.csv',
                      index_col=[0,1],
                      parse_dates=True)
    race = pd.read_csv(datadir+'IDPH_RACEDEMO_'+county.upper()+'.csv',
                      index_col=[0,1],
                      parse_dates=True)
    gender = pd.read_csv(datadir+'IDPH_GENDERDEMO_'+county.upper()+'.csv',
                      index_col=[0,1],
                      parse_dates=True)
    return age,race,gender

def loadidphvacdemos(county='Warren', datadir='./'):
    age = pd.read_csv(datadir+'IDPH_VAX_AGEDEMO_'+county.upper()+'.csv',
                      index_col=[0,1],
                      parse_dates=True)
    race = pd.read_csv(datadir+'IDPH_VAX_RACEDEMO_'+county.upper()+'.csv',
                      index_col=[0,1],
                      parse_dates=True)
    gender = pd.read_csv(datadir+'IDPH_VAX_GENDERDEMO_'+county.upper()+'.csv',
                      index_col=[0,1],
                      parse_dates=True)
    return age,race,gender

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
                         dtype={'countyFIPS':np.int64,'StateFIPS':np.int64,
                                'County Name':str, 'State':str,
                                'date': np.datetime64,
                                'Total Positive':np.int64},
                         index_col = 'countyFIPS')
    deaths = pd.read_csv(datadir+'covid_deaths_usafacts.csv',
                         dtype={'countyFIPS':np.int64,'StateFIPS':np.int64,
                                'County Name':str, 'State':str,
                                'date': np.datetime64,
                                'Total Deaths':np.int64},
                         index_col = 'countyFIPS')
    return (population,
            cases.rename(columns={"StateFIPS":"stateFIPS"}),
            deaths.rename(columns={"StateFIPS":"stateFIPS"}))

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
    idx = raw_wchd.index
    fipss = pd.DataFrame(data=[[17187,17] for i in idx],
                         index=idx,columns=['countyFIPS','stateFIPS'])
    allofit = pd.concat([raw_wchd,fipss],axis=1)
    reorg = allofit.reset_index().set_index(['date','stateFIPS','countyFIPS'])
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

#%%


#https://idph.illinois.gov/DPHPublicInformation/Help
class IDPHDataCollector:
    apibase = 'https://idph.illinois.gov/DPHPublicInformation/'
    countyHistAPI = 'api/COVID/GetCountyHistorical?countyName='
    demo = 'api/COVID/GetCountyDemographicsOverTime?countyName='
    demo2 = 'api/COVID/GetCountyDemographics?countyName='
    vac = 'api/COVIDVaccine/getVaccineAdministration?CountyName='
    currvac = 'api/COVIDVaccine/getVaccineAdministrationCurrent?CountyName='
    vacdemo = '/api/covidvaccine/getVaccineAdministrationDemos?countyname='
    vacage = 'api/COVIDVaccine/getCOVIDVaccineAdministrationCountyAge?countyname='
    @staticmethod
    def getCountyTotals(county='Warren'):
        colmap = {'ReportDate':'date',
                  'CountyName':'county',
                  'TotalTested':'Total Tests',
                  'CumulativeCases':'Total Positive',
                  'Deaths':'Total Deaths',
                  }
        tots = rq.get(IDPHDataCollector.apibase+\
                      IDPHDataCollector.countyHistAPI+county)
        d = pd.DataFrame(tots.json()['values']).rename(columns=colmap)
        d['date'] = pd.to_datetime(d['date'])
        d = d.set_index('date')        
        # date 4/11 appears twice? 
        d= d[~d.index.duplicated(keep='first')]
        d.index.name = 'date'        
        return d
    @staticmethod
    def getCountyAgeHistory(county='Warren',numdays=7):
        age = rq.get(IDPHDataCollector.apibase+\
                     IDPHDataCollector.demo+\
                     county+'&DaysIncluded='+str(numdays))
        colmap = {'ReportDate':'date',
                  'tested':'Total Tests',
                  'count':'Total Positive',
                  #'deaths':'New Deaths',
                  'CaseCountChange':'New Positive',
                  'age_group':'Age Group'}
        e = pd.DataFrame(age.json()).rename(columns=colmap)
        e['date'] = pd.to_datetime(e['date'])
        e = e.set_index(['date','Age Group'])
        return e
    @staticmethod
    def getVacDemo(county='Warren'):
        while True:
            try:
                demo = rq.get(IDPHDataCollector.apibase+\
                              IDPHDataCollector.vacdemo+county)  
                age = rq.get(IDPHDataCollector.apibase+\
                             IDPHDataCollector.vacage+county)                
                break
            except:
                print('Error Scraping vax demos for '+ county + '. Retrying...')
                time.sleep(3)            
        if demo.ok and age.ok:
            demo = demo.json()
            age = age.json()
        else:
            return pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame([])
        race = demo['Race']
        gender = demo['Gender']
        dates = [e['Report_Date'] for es in [race,gender,age] for e in es]
        dates = set(dates)
        if not len(dates) == 1:
            print('Date Conflict in demographic reports')
            return pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame([])
        date = pd.to_datetime(dates.pop())
               
        if len(age) > 0:
            age_data = pd.DataFrame(age,
                                    index=pd.Series([date]*len(age),
                                                    name='date'))
            age_data['AgeGroup'] = age_data['AgeGroup'].str.strip()
            drops = ['CountyName','TotalAdministeredDisplay',
                     'AdministeredCountDisplay', 'PersonsFullyVaccinatedDisplay',
                     'BoosterDoseAdministeredDisplay', 'Report_Date']
            age_data = age_data.drop(drops,axis=1).reset_index().set_index(['date','AgeGroup'])
        else:
            age_data = pd.DataFrame([])
        if len(race) > 0:
            race_data = pd.DataFrame(race,
                                    index=pd.Series([date]*len(race),
                                                    name='date'))
            race_data['Race'] = race_data['Race'].str.strip()
            drops = ['CountyName','AdministeredCountDisplay',
                     'PersonsFullyVaccinatedDisplay',
                     'PersonsVaccinatedOneDoseDisplay',
                     'BoosterDoseAdministeredDisplay', 'Report_Date']
            race_data = race_data.drop(drops,axis=1).reset_index().set_index(['date','Race'])
        else:
            race_data = pd.DataFrame([])
        if len(gender) > 0:
            gender_data = pd.DataFrame(gender,
                                       index=pd.Series([date]*len(gender),
                                                    name='date'))
            gender_data['Gender'] = gender_data['Gender'].str.strip()
            drops = ['CountyName','GenderDisplay','AdministeredCountDisplay',
                     'PersonsFullyVaccinatedDisplay',
                     'PersonsVaccinatedOneDoseDisplay',
                     'BoosterDoseAdministeredDisplay', 'Report_Date']
            gender_data = gender_data.drop(drops,axis=1).reset_index().set_index(['date','Gender'])
        else:
            gender_data = pd.DataFrame([])
        return race_data,gender_data,age_data
    @staticmethod
    def getDailyDemo(day,county='Warren'):
        while True:
            try:
                demo = rq.get(IDPHDataCollector.apibase+\
                              IDPHDataCollector.demo2+county+\
                                  '&reportDate='+day)        
                break
            except:
                print('Error Scraping ' + str(day) +'. Retrying...')
                time.sleep(3)            
        if demo.ok:
            demo = demo.json()
        else:
            return pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame([]),pd.DataFrame([])
        # extract date for report. should be equiv to day...
        date = pd.to_datetime("{}-{}-{}".format(demo['lastUpdatedDate']['year'],
                                                demo['lastUpdatedDate']['month'],
                                                demo['lastUpdatedDate']['day']))
        # extract all the demographic totals        
        f = demo['county_demographics'][0]
        # county level information (total-totals, name, etc) This should be duplicate info
        county_data = pd.DataFrame(dict(itertools.islice(f.items(),3)),
                                   index=[date]).rename(columns={'confirmed_cases':'Total Positive',
                                                                 'total_tested':'Total Tests'})
        # for real just the demo data this time
        demo_data = f['demographics']
        # organize age,race, and gender
        age = demo_data['age']
        if len(age) > 0:
            age_data = pd.DataFrame(demo_data['age'],
                                index=pd.Series([date]*len(demo_data['age']),name='date'))
            age_data['age_group'] = age_data['age_group'].str.strip()
            age_data = age_data.drop('race',axis=1).reset_index().set_index(['date','age_group'])
            age_data = age_data.rename(columns={'count':'Total Positive',
                                                'tested':'Total Tested'})
        else:
            age_data = pd.DataFrame([])
        race = demo_data['race']
        if len(race) > 0:
            race_data = pd.DataFrame(demo_data['race'],
                                     index=pd.Series([date]*len(demo_data['race']),name='date'))
            race_data['description'] = race_data['description'].str.strip()
            race_data = race_data.rename(columns={'description':'race_group',
                                                  'count':'Total Positive',
                                                  'tested':'Total Tested'})
            race_data = race_data.drop('color',axis=1).reset_index().set_index(['date',
                                                                                'race_group'])                         
        else:
            race_data = pd.DataFrame([])
        gender = demo_data['gender']
        if len(gender) > 0:
            gender_data = pd.DataFrame(demo_data['gender'],
                                       index=pd.Series([date]*len(demo_data['gender']),name='date'))
            gender_data = gender_data.rename(columns={'description':'sex_group',
                                                      'count':'Total Positive',
                                                      'tested':'Total Tested'})
            gender_data = gender_data.drop('color',axis=1).reset_index().set_index(['date',
                                                                                    'sex_group'])
        else:
            gender_data = pd.DataFrame([])
        return county_data,age_data,race_data,gender_data
    @staticmethod
    def getDemoHistory(first,last,county='Warren'):        
        dates = pd.date_range(first,last)
        tot = len(dates)
        done = 0
        def log_progress(d):
            res = IDPHDataCollector.getDailyDemo(str(d.date()),county)
            nonlocal done
            nonlocal tot
            done = done + 1
            if done % max(1,int(math.ceil(tot * 0.05))) == 0:
                print('{:.1%} {}'.format(done/tot,d.date()))
            return res            
        hist = [ log_progress(d) for d in dates ]
        cnty = pd.concat([ t[0] for t in hist ])
        ages = pd.concat([ t[1] for t in hist ])
        races = pd.concat([ t[2] for t in hist ])
        genders = pd.concat([ t[3] for t in hist ])
        return cnty,ages,races,genders   
    @staticmethod
    def getVaccineHistory(county='Warren'):
        vacframe = rq.get(IDPHDataCollector.apibase+\
                          IDPHDataCollector.vac+\
                          county).json()
        vachist = pd.DataFrame(vacframe['VaccineAdministration'])
        vachist = vachist.rename(columns={'CountyName':'County',
                                          'AdministeredCount':'Total Shots',
                                          'AdministeredCountChange':'New Shots',
                                          'PersonsFullyVaccinated':"Total Vaccinated",
                                          'PersonsFullyVaccinatedChange':"New Vaccinated",
                                          'Report_Date':'date'
                                          })
        vachist['date'] = pd.to_datetime(vachist['date'])
        vachist = vachist.set_index('date')
        vachist = vachist.drop(['AdministeredCountRollAvg','AllocatedDoses',
                                'PctVaccinatedPopulation',
                                'LHDReportedInventory','CommunityReportedInventory',
                                'TotalReportedInventory','InventoryReportDate'],axis=1)
        cty = vachist[['County','Population','Latitude','Longitude']]
        vachist = vachist.drop(['County','Population','Latitude','Longitude'],axis=1)
        return cty,vachist
    @staticmethod 
    def flattenDemoReport(report):
        tocols = report.unstack()
        newcols = ['{} {}'.format(c[0],c[1]) for c in tocols.columns]
        tocols.columns = newcols
        return tocols
    @staticmethod
    def totals(county='Warren'):
        tots = IDPHDataCollector.getCountyTotals(county)
        _,vacs = IDPHDataCollector.getVaccineHistory(county)
        firstday = min(tots.index[0],vacs.index[0])
        lastday = max(tots.index[-1],vacs.index[-1])
        idx = pd.date_range(firstday,lastday)
        if not idx.difference(tots.index).empty:
            tots = tots.reindex(index=pd.date_range(firstday,tots.index[-1])).fillna(0)
        if not idx.difference(vacs.index).empty:
            #DuPage has duplicate entries that seem to just be one
            # lacking shot totals. So.. fix.?
            if vacs.index.duplicated().any():
                vacs = vacs.groupby(vacs.index).max()
            vacs = vacs.reindex(index=pd.date_range(firstday,vacs.index[-1])).fillna(0)        
        alltots = pd.concat([tots,vacs],axis=1)
        # empty rows are all zeros -- 3/23/20 is sus
        missing = alltots[ (alltots.T == 0).all() ]        
        if len(missing) > 0:
            prev_idx = missing.index - pd.to_timedelta(1,unit='D')
            prevs = alltots.loc[prev_idx]
            prevs.index = missing.index
            alltots.loc[missing.index] = prevs           
        return alltots
    def writeTotals(county='Warren'):
        tots = IDPHDataCollector.totals(county)
        tosheet = tots[['Total Positive','Total Tests','Total Deaths',
                        'New Shots','Total Vaccinated']]
        tosheet.to_csv('IDPH_DAILY_'+county.upper()+'.csv',
                       index_label='date')
    def getCountyData():
        vacframe = rq.get(IDPHDataCollector.apibase+\
                          IDPHDataCollector.currvac).json()                          
        vachist = pd.DataFrame(vacframe['VaccineAdministration'])
        vachist = vachist.rename(columns={'CountyName':'County'})        
        cty = vachist[['County','Population','Latitude','Longitude']]
        return cty  
    def getNonCountyData():
        vacframe = rq.get(IDPHDataCollector.apibase+\
                          IDPHDataCollector.currvac).json()                          
        vachist = pd.DataFrame(vacframe['VaccineAdministration'])
        vachist = vachist.rename(columns={'CountyName':'County',
                                          'PersonsFullyVaccinated':'Total Vaccinated'})
        vachist = vachist[vachist['County'].isin(['Unknown','Out Of State'])]
        cty = vachist[['County','Total Vaccinated']]
        return cty
    def writeCountyData(counties=['Warren']):
        datadir = 'IDPH_Totals/'
        tosheet = IDPHDataCollector.getCountyData()
        tosheet.to_csv(datadir+'IDPH_County_Info.csv')        
    def writeTotalsAll(counties=['Warren']):
        datadir = 'IDPH_Totals/'
        for county in counties:
            print("Scraping "+ county)
            while True:
                try:
                    tots = IDPHDataCollector.totals(county)
                    break
                except:
                    print('Error Scraping ' + county +'. Retrying...')
                    time.sleep(3)
            tosheet = tots[['Total Positive','Total Tests','Total Deaths',
                            'New Shots','Total Vaccinated']]
            tosheet.to_csv(datadir+'IDPH_DAILY_'+county.upper()+'.csv',
                           index_label='date')            
    def writeDemos(firstday,lastday,county='Warren'):
        county_data,age_data,race_data,gender_data = IDPHDataCollector.getDemoHistory(firstday, lastday, county)
        age_data.to_csv('IDPH_AGEDEMO_'+county.upper()+'.csv')
        race_data.to_csv('IDPH_RACEDEMO_'+county.upper()+'.csv')
        gender_data.to_csv('IDPH_GENDERDEMO_'+county.upper()+'.csv')
    def writeVacDemos(county='Warren'):
        race_data,gender_data,age_data = IDPHDataCollector.getVacDemo(county)
        age_data.to_csv('IDPH_VAX_AGEDEMO_'+county.upper()+'.csv')
        race_data.to_csv('IDPH_VAX_RACEDEMO_'+county.upper()+'.csv')
        gender_data.to_csv('IDPH_VAX_GENDERDEMO_'+county.upper()+'.csv')
    def updateDemos(county="Warren"):        
        agecurr = pd.read_csv('IDPH_AGEDEMO_'+county.upper()+'.csv',
                              index_col=[0,1])
        racecurr = pd.read_csv('IDPH_RACEDEMO_'+county.upper()+'.csv',
                              index_col=[0,1])
        gendercurr = pd.read_csv('IDPH_GENDERDEMO_'+county.upper()+'.csv',
                              index_col=[0,1])
        nextday_file = pd.to_datetime(agecurr.index.get_level_values('date')[-1])+pd.Timedelta(1,unit='D')
        today = pd.to_datetime(pd.to_datetime('today').date())
        if today - nextday_file > pd.Timedelta(0,unit='D'):
            print('Updating with '+str(nextday_file.date())+' until '+\
                  str(today.date()))
            ctynew,agenew,racenew,gendernew = IDPHDataCollector.getDemoHistory(nextday_file,
                                                                               today,county)
            agecurr = pd.concat([agecurr,agenew])
            racecurr = pd.concat([racecurr,racenew])
            gendercurr = pd.concat([gendercurr,gendernew])
            agecurr.to_csv('IDPH_AGEDEMO_'+county.upper()+'.csv')
            racecurr.to_csv('IDPH_RACEDEMO_'+county.upper()+'.csv')
            gendercurr.to_csv('IDPH_GENDERDEMO_'+county.upper()+'.csv')
    def updateVacDemos(county="Warren"):        
        agecurr = pd.read_csv('IDPH_VAX_AGEDEMO_'+county.upper()+'.csv',
                              index_col=[0,1])
        racecurr = pd.read_csv('IDPH_VAX_RACEDEMO_'+county.upper()+'.csv',
                              index_col=[0,1])
        gendercurr = pd.read_csv('IDPH_VAX_GENDERDEMO_'+county.upper()+'.csv',
                              index_col=[0,1])
        nextday_file = pd.to_datetime(agecurr.index.get_level_values('date')[-1])+pd.Timedelta(1,unit='D')
        today = pd.to_datetime(pd.to_datetime('today').date())
        if today - nextday_file > pd.Timedelta(0,unit='D'):
            print('Updating Vaccine Data. Expecting ' + str(nextday_file.date()) + ' or later.')
            racenew,gendernew,agenew = IDPHDataCollector.getVacDemo(county)
            if racenew.index[0][0] >= nextday_file:
                print('Updating with vaccine data dated ' + str(racenew.index[0][0].date()))
                agecurr = pd.concat([agecurr,agenew])
                racecurr = pd.concat([racecurr,racenew])
                gendercurr = pd.concat([gendercurr,gendernew])            
                agecurr.to_csv('IDPH_VAX_AGEDEMO_'+county.upper()+'.csv')
                racecurr.to_csv('IDPH_VAX_RACEDEMO_'+county.upper()+'.csv')
                gendercurr.to_csv('IDPH_VAX_GENDERDEMO_'+county.upper()+'.csv')
            else:
                print('No new vaccine data found.')
        
        

    