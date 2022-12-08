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

WORD_ORDER_CASE_ORDER = ["Loc", "Nom", "Dat", "Abl", "Ins", "Acc"]
WORD_ORDER_XPOS_ORDER = ["CAD", "CX", "CNG", "V"]

###############################################################################


def get_word_order(token_list: Dict[int, Dict]) -> List[int]:
    case_order = []
    xpos_order = []
    used = set()
    unused = set(token_list)
    for case in WORD_ORDER_CASE_ORDER:
        for token_id, token in token_list.items():
            if not isinstance(token["analysis"], dict):
                continue

            if token["analysis"].get("feats", {}).get("Case") == case:
                case_order.append(token_id)
                unused.remove(token_id)
                used.add(token_id)

    for xpos in WORD_ORDER_XPOS_ORDER:
        for token_id, token in token_list.items():
            if token_id in used:
                continue
            if token["analysis"].get("xpos") == xpos:
                xpos_order.append(token_id)
                unused.remove(token_id)
                used.add(token_id)

    word_order_order = []
    word_order_order.extend(case_order)

    for token_id, token in token_list.items():
        if token_id in unused:
            word_order_order.append(token_id)
            unused.remove(token_id)
            used.add(token_id)

    word_order_order.extend(xpos_order)
    assert set(token_list) == set(word_order_order)

    return word_order_order
