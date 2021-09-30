#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""


@author: jlmayfield
"""


from cvdataprep import IDPHDataCollector,loadusafacts
import pandas as pd

#%%
if __name__ == '__main__':
    print("\nPulling Updated Totals from IDPH\n")
    #IDPHDataCollector.writeTotals()
    IDPHDataCollector.updateDemos()
    counties = IDPHDataCollector.getCountyData()
    nopop = counties[-2:].set_index('County')
    counties = counties[:-2].set_index('County')
    populations, _, _ = loadusafacts()
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
    minset = ['Peoria','Henry','Mercer',
              'Rock Island','McDonough',
              'Hancock','Knox','Fulton','Stark','Schuyler',
              'Warren','Henderson']
    #Scrape all IL counties for totals
    IDPHDataCollector.writeTotalsAll(minset)
    # Gets all the county data. Only changes if population counts are 
    #  updated
    IDPHDataCollector.writeCountyData(minset)
    #IDPHDataCollector.writeTotalsAll(nopop.index)
    #IDPHDataCollector.writeCountyData(nopop.index)
    
