#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collection of Heuristics

@author: Hrishikesh Terdalkar
"""

###############################################################################

from typing import Dict, List

###############################################################################
# NOTE: token_list contains dictionary of (token_id, token_details)
# token_details objects are dictionaries produced by parsing CoNLL-U data
# Specific structure could be assumed for these dictionaries as per input data


def get_sentence_boundary(token_list: Dict[int, Dict]) -> int:
    """Heuristic to identify sentence boundary"""
    if token_list:
        return list(token_list)[-1]


def get_word_order(token_list: Dict[int, Dict]) -> List[int]:
    """Heuristic to get word order"""

    CASE_ORDER = ["Loc", "Nom", "Dat", "Abl", "Ins", "Acc"]
    XPOS_ORDER = ["CAD", "CX", "CNG", "V"]

    case_order = []
    xpos_order = []
    used = set()
    unused = set(token_list)
    for case in CASE_ORDER:
        for token_id, token in token_list.items():
            if not isinstance(token["analysis"], dict):
                continue

            if token["analysis"].get("feats", {}).get("Case") == case:
                case_order.append(token_id)
                unused.remove(token_id)
                used.add(token_id)

    for xpos in XPOS_ORDER:
        for token_id, token in token_list.items():
            if token_id in used:
                continue
            if token["analysis"].get("xpos") == xpos:
                xpos_order.append(token_id)
                unused.remove(token_id)
                used.add(token_id)

    word_order = []
    word_order.extend(case_order)

    for token_id, token in token_list.items():
        if token_id in unused:
            word_order.append(token_id)
            unused.remove(token_id)
            used.add(token_id)

    word_order.extend(xpos_order)
    assert set(token_list) == set(word_order)

    return word_order


def get_lemma(text: str) -> str:
    """Heuristic to identify lemma"""
    return text
