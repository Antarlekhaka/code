#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Collection of Heuristics

@author: Hrishikesh Terdalkar
"""

###############################################################################

import random
from typing import Dict, List

###############################################################################
# NOTE: token_list contains dictionary of (token_id, token_details)
# token_details objects are dictionaries produced by parsing CoNLL-U data
# Specific structure could be assumed for these dictionaries as per input data


def get_sentence_boundary(token_list: Dict[int, Dict]) -> int:
    """Heuristic to identify sentence boundary"""
    if token_list:
        return list(token_list)[-1]


###############################################################################


def get_word_order(*args, **kwargs):
    # return get_word_order_base(*args, **kwargs)
    # return get_word_order_random(*args, **kwargs)
    return get_word_order_heuristic(*args, **kwargs)


def get_word_order_base(token_list: Dict[int, Dict]) -> List[int]:
    return list(token_list)


def get_word_order_random(token_list: Dict[int, Dict]) -> List[int]:
    token_ids = list(token_list)
    random.shuffle(token_ids)
    return token_ids


def get_word_order_heuristic(token_list: Dict[int, Dict]) -> List[int]:
    """Heuristic to get word order"""

    CASE_ORDER = ["Voc", "Loc", "Nom", "Dat", "Abl", "Ins", "Acc"]
    SAME_CASE_UPOS_ORDER = ["PRON", "ADJ", "NUM", "NOUN"]
    UPOS_START_ORDER = ["INTJ"]
    UPOS_END_ORDER = ["ADP", "ADV", "PART", "VERB"]

    upos_start_order = []
    upos_end_order = []
    case_order = []
    used = set()
    unused = set(token_list)

    for case in CASE_ORDER:
        _same_case = []
        for token_id, token in token_list.items():
            if not isinstance(token["analysis"], dict):
                continue

            if token["analysis"].get("feats", {}).get("Case") == case:
                _same_case.append(token_id)

        # for token_id in _same_case:
        #     token = token_list[token_id]
        #     if token["analysis"].get("upos") not in SAME_CASE_UPOS_ORDER:
        #         case_order.append(token_id)

        for upos in SAME_CASE_UPOS_ORDER:
            for token_id in _same_case:
                token = token_list[token_id]
                if token["analysis"].get("upos") == upos:
                    case_order.append(token_id)
                    unused.remove(token_id)
                    used.add(token_id)

    for upos in UPOS_START_ORDER + UPOS_END_ORDER:
        for token_id, token in token_list.items():
            if token_id in used:
                continue
            if token["analysis"].get("upos") == upos:
                if upos in UPOS_START_ORDER:
                    upos_start_order.append(token_id)
                else:
                    upos_end_order.append(token_id)
                unused.remove(token_id)
                used.add(token_id)

    word_order = []
    word_order.extend(upos_start_order)
    word_order.extend(case_order)

    for token_id, token in token_list.items():
        if token_id in unused:
            word_order.append(token_id)
            unused.remove(token_id)
            used.add(token_id)

    word_order.extend(upos_end_order)
    assert set(token_list) == set(word_order)

    return word_order

###############################################################################


def get_lemma(text: str) -> str:
    """Heuristic to identify lemma"""
    return text


###############################################################################


def get_token_graph(
    token_list: Dict[int, Dict],
    boundary_id: int,
    relation_map: Dict[str, int]
) -> List[int]:
    """Heuristic to get token graph"""
    from functools import reduce

    relations = []

    # ----------------------------------------------------------------------- #

    rules = [
        {
            "src_condition": [("upos", "==", "VERB"), ("feats.Voice", "!=", "Pass")],
            "dst_condition": [("feats.Case", "==", "Nom"), ("upos", "==", "NOUN")],
            "relation_label": ["KARTA"]
        },
        {
            "src_condition": [("upos", "==", "VERB"), ("feats.Voice", "==", "Pass")],
            "dst_condition": [("feats.Case", "==", "Ins"), ("upos", "==", "NOUN")],
            "relation_label": ["KARTA"]
        },
        {
            "src_condition": [("upos", "==", "VERB"), ("feats.Voice", "!=", "Pass")],
            "dst_condition": [("feats.Case", "==", "Acc"), ("upos", "==", "NOUN")],
            "relation_label": ["KARMA"]
        },
        {
            "src_condition": [("upos", "==", "VERB"), ("feats.Voice", "==", "Pass")],
            "dst_condition": [("feats.Case", "==", "Nom"), ("upos", "==", "NOUN")],
            "relation_label": ["KARMA"]
        },
        {
            "src_condition": [("upos", "==", "VERB")],
            "dst_condition": [("feats.Case", "==", "Dat"), ("upos", "==", "NOUN")],
            "relation_label": ["SAMPRADANA"]
        },
        {
            "src_condition": [("upos", "==", "VERB")],
            "dst_condition": [("feats.Case", "==", "Abl"), ("upos", "==", "NOUN")],
            "relation_label": ["APADANA"]
        },
        {
            "src_condition": [("upos", "==", "VERB")],
            "dst_condition": [("feats.Case", "==", "Loc"), ("upos", "==", "NOUN")],
            "relation_label": [""]
        }
    ]

    # ----------------------------------------------------------------------- #

    def check_rule(_rule, _src_token, _dst_token):
        tokens = {
            "src": _src_token,
            "dst": _dst_token
        }
        conditions = []
        for condition_type in ["src", "dst"]:
            _conditions = _rule[f"{condition_type}_condition"]
            _token = tokens[condition_type]
            for (_key, _operator, _value) in _conditions:
                key = reduce(
                    lambda d, k: d.get(k, {}),
                    _key.split("."),
                    _token["analysis"]
                )
                if _operator == "==":
                    conditions.append(key == _value)
                if _operator == "!=":
                    conditions.append(key != _value)
        return all(conditions)

    # ----------------------------------------------------------------------- #

    src_token_list = list(token_list.items())
    dst_token_list = list(token_list.items())

    token_proximity = {
        (src_id, dst_id): src_idx - dst_idx
        for src_idx, src_id in enumerate(token_list)
        for dst_idx, dst_id in enumerate(token_list)
        if src_id != dst_id
    }

    for dst_idx, (dst_id, dst_token) in enumerate(dst_token_list):
        for src_idx, (src_id, src_token) in enumerate(src_token_list):
            if src_id == dst_id:
                continue

            if (
                not isinstance(src_token["analysis"], dict) or
                not isinstance(dst_token["analysis"], dict)
            ):
                continue

            for rule in rules:
                if check_rule(rule, src_token, dst_token):
                    relation_id = None
                    if rule["relation_label"]:
                        relation_id = relation_map.get(rule["relation_label"][0])

                    relations.append({
                        "boundary_id": boundary_id,
                        "src_id": src_id,
                        "label_id": relation_id,
                        "dst_id": dst_id
                    })

    return relations

###############################################################################
