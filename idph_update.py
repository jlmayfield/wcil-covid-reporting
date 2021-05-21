#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""


@author: jlmayfield
"""


from cvdataprep import IDPHDataCollector

if __name__ == '__main__':
    print("\nPulling Updated Totals from IDPH\n")
    IDPHDataCollector.writeTotals()
    IDPHDataCollector.updateDemos()
