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

ANVAYA_CASE_ORDER = ["Loc", "Nom", "Dat", "Abl", "Ins", "Acc"]
ANVAYA_XPOS_ORDER = ["CAD", "CX", "CNG", "V"]

###############################################################################


def get_anvaya(token_list: Dict[int, Dict]) -> List[int]:
    print(token_list)
    case_order = []
    xpos_order = []
    used = set()
    unused = set(token_list)
    for case in ANVAYA_CASE_ORDER:
        for token_id, token in token_list.items():
            if token["analysis"].get("feats", {}).get("Case") == case:
                case_order.append(token_id)
                unused.remove(token_id)
                used.add(token_id)

    for xpos in ANVAYA_XPOS_ORDER:
        for token_id, token in token_list.items():
            if token_id in used:
                continue
            if token["analysis"].get("xpos") == xpos:
                xpos_order.append(token_id)
                unused.remove(token_id)
                used.add(token_id)

    anvaya_order = []
    anvaya_order.extend(case_order)

    for token_id, token in token_list.items():
        if token_id in unused:
            anvaya_order.append(token_id)
            unused.remove(token_id)
            used.add(token_id)

    anvaya_order.extend(xpos_order)
    assert set(token_list) == set(anvaya_order)

    return case_order
