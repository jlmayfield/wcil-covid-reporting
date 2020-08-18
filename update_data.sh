#!/bin/bash

# get the latest datasets from usafacts.org
wget -N https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_confirmed_usafacts.csv
wget -N https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_deaths_usafacts.csv
wget -N https://usafactsstatic.blob.core.windows.net/public/data/covid-19/covid_county_population_usafacts.csv
# pull my spreadsheets on Warren County Data
wget "https://docs.google.com/spreadsheets/d/1KR9c7TJBioHAMScGKByp2rPARCrV0n-hdDjkW7vpgU8/export?format=csv&gid=1716403665" -O "WCHD_Reports.csv"
wget "https://docs.google.com/spreadsheets/d/1KR9c7TJBioHAMScGKByp2rPARCrV0n-hdDjkW7vpgU8/export?format=csv&gid=1514869071" -O "WCHD_Demographics.csv"
