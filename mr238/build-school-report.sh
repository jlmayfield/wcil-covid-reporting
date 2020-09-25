#!/bin/bash

DATESTRING=$(date "+%Y-%m-%d at %H:%M ")
OUTFILE='MR238Report.md'

cat 01-school-report.md > $OUTFILE
echo "<p><small>last updated $DATESTRING </small></p>"  >> $OUTFILE
cat MR238-Daily.txt >> $OUTFILE
cat 03-explanations.md  >> $OUTFILE
