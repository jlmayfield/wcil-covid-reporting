#!/bin/bash

DATESTRING='date +%Y-%m-%d'
OUTFILE='schoolReport.md'

cat 01-school-report.md > $OUTFILE
echo '<p>updated on $DATESTRING </p>'  >> $OUTFILE
cat WC-School-Daily.txt >> $OUTFILE
cat 03-explanations.md  >> $OUTFILE
