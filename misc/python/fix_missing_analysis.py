#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix Missing Token Analysis

Use most commonly found analysis for other tokens as a heuristic.

Created on Wed May 10 18:42:30 2023

@author: Hrishikesh Terdalkar
"""

import json
from functools import lru_cache
from collections import defaultdict, Counter

from sqlalchemy import or_, and_
from explore_database import Token, db

###############################################################################


@lru_cache()
def get_token(tid):
    return Token.query.get(tid)


def get_token_text(tid):
    token = get_token(tid)
    return (
        token.text
        if token.text not in [None, "_"]
        else (token.analysis["misc"].get("Unsandhied") or "#")
    )


# --------------------------------------------------------------------------- #


def get_heuristic_analysis(token_text: str = None, token_id: int = None):
    if not token_text and not token_id:
        return

    if not token_text:
        token_text = get_token_text(token_id)

    analysis_stats = defaultdict(Counter)
    misc_stats = defaultdict(Counter)

    similar_tokens = Token.query.filter(
        or_(
            Token.text == token_text,
            and_(
                Token.analysis["misc"]["Unsandhied"] == token_text,
                Token.analysis["misc"]["UnsandhiedReconstructed"] != True
            )
        )
    ).all()
    for tok in similar_tokens:
        if tok.analysis:
            for k, v in tok.analysis.items():
                if k == "misc":
                    is_reconstructed = v.get("UnsandhiedReconstructed")
                    unsandhied_keys = ["Unsandhied", "UnsandhiedReconstructed"]
                    for k1, v1 in v.items():
                        if is_reconstructed and k1 in unsandhied_keys:
                            continue
                        misc_stats[k1].update(
                            [json.dumps(v1, ensure_ascii=False)]
                        )
                else:
                    analysis_stats[k].update(
                        [json.dumps(v, ensure_ascii=False)]
                    )

    result_analysis = {}
    result_misc = {}
    for k, v in analysis_stats.items():
        _stat, _freq = v.most_common(1)[0]
        if _freq > 3:
            result_analysis[k] = json.loads(_stat)

    for k1, v1 in misc_stats.items():
        _stat, _freq = v1.most_common(1)[0]
        if _freq > 3:
            result_misc[k1] = json.loads(_stat)

    if result_misc:
        result_analysis["misc"] = result_misc

    return result_analysis, analysis_stats, misc_stats

###############################################################################
