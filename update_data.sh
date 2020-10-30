#!/bin/bash

# get the latest datasets from usafacts.org
wget -N https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_confirmed_usafacts.csv
wget -N https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_deaths_usafacts.csv
wget -N https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_county_population_usafacts.csv
# pull my spreadsheets on Warren County Data
wget "https://docs.google.com/spreadsheets/d/1KR9c7TJBioHAMScGKByp2rPARCrV0n-hdDjkW7vpgU8/export?format=csv&gid=891318752" -O "WCHD_Reports.csv"
wget "https://docs.google.com/spreadsheets/d/1KR9c7TJBioHAMScGKByp2rPARCrV0n-hdDjkW7vpgU8/export?format=csv&gid=1514869071" -O "WCHD_Case_Demographics.csv"
wget "https://docs.google.com/spreadsheets/d/1KR9c7TJBioHAMScGKByp2rPARCrV0n-hdDjkW7vpgU8/export?format=csv&gid=2139817650" -O "WCHD_Death_Demographics.csv"
wget "https://docs.google.com/spreadsheets/d/1KR9c7TJBioHAMScGKByp2rPARCrV0n-hdDjkW7vpgU8/export?format=csv&gid=1651303281" -O "ILDPH_Reports.csv"
wget "https://docs.google.com/spreadsheets/d/1KR9c7TJBioHAMScGKByp2rPARCrV0n-hdDjkW7vpgU8/export?format=csv&gid=1945656910" -O "MC_Reports.csv"
