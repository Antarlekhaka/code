#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collection of Heuristics

Created on Tue Jun 07 07:24:30 2022

@author: Hrishikesh Terdalkar
"""

###############################################################################

from typing import Dict, List

###############################################################################

ANVAYA_CASE_ORDER = ['Nom', 'Loc', 'Dat', 'Abl', 'Ins', 'Acc']
ANVAYA_XPOS_ORDER = ['NC', r'.*', 'V']

###############################################################################


def anvaya(token_list: List[Dict]) -> List[int]:
    return list(token_list)
