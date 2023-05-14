#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluate Word Order Heuristic

Created on Thu Apr 27 02:25:00 2023

@author: Hrishikesh Terdalkar
"""

###############################################################################

import os
import sys
import math
import json
import pickle
from functools import lru_cache
from collections import defaultdict

import pandas as pd
from scipy.stats import kendalltau
from nltk.translate.bleu_score import (
    corpus_bleu, sentence_bleu, SmoothingFunction
)
from tqdm import tqdm

from explore_database import Token, Boundary, WordOrder
from utils.database import get_sentences
from utils.heuristic import (
    get_word_order_base, get_word_order_random, get_word_order_heuristic
)

###############################################################################

heuristics = {
    "base": get_word_order_base,
    "random": get_word_order_random,
    "heuristic": get_word_order_heuristic
}

if len(sys.argv) > 1 and sys.argv[1] in heuristics:
    heuristic_method = sys.argv[1]
else:
    heuristic_method = "heuristic"

get_word_order = heuristics.get(heuristic_method)

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

# NOTE: unique word order per annotator per boundary
word_order_query = WordOrder.query.group_by(
    WordOrder.annotator_id,
    WordOrder.boundary_id
)

available_word_orders = [
    (wo.annotator_id, wo.boundary_id, wo.boundary.verse_id)
    for wo in word_order_query
]

dataset_path = "sentences_with_word_order.pkl"
if os.path.isfile(dataset_path):
    with open(dataset_path, "rb") as f:
        sentences_with_word_order = pickle.load(f)
else:
    # NOTE: get_sentences is going to be called multiple times for verses
    # that have more boundaries in them. fix?

    sentences_with_word_order = {
        (annotator_id, verse_id): get_sentences(verse_id, annotator_id)
        for annotator_id, boundary_id, verse_id in tqdm(available_word_orders)
    }
    with open(dataset_path, "wb") as f:
        pickle.dump(sentences_with_word_order, f)

# --------------------------------------------------------------------------- #

annotated_word_order = {
    (annotator_id, boundary_id, verse_id): [
        wo.token_id
        for wo in WordOrder.query.filter(
            WordOrder.annotator_id == annotator_id,
            WordOrder.boundary_id == boundary_id
        ).order_by(WordOrder.order).all()
    ]
    for annotator_id, boundary_id, verse_id in available_word_orders
}

# --------------------------------------------------------------------------- #

annotated_sentences = [
    [
        tuple(
            [*abv, tid, get_token_text(tid), get_token(tid).analysis['upos']]
        )
        for tid in awo
    ]
    for abv, awo in annotated_word_order.items()
]
with open("annotated_sentences.json", "w") as f:
    json.dump(annotated_sentences, f)

# pos-tagged corpus
corpus = [
    [tuple(tok[-2:]) for tok in sent]
    for sent in annotated_sentences
    if len(sent) > 1
]

# --------------------------------------------------------------------------- #

heuristic_word_order = {}
for annotator_verse, verse_sentences in sentences_with_word_order.items():
    annotator_id, verse_id = annotator_verse
    extra_tokens = verse_sentences['extra']
    for boundary_id, tokens in verse_sentences.items():
        if boundary_id == 'extra':
            continue
        tokens.update(extra_tokens)

        aid_bid = (annotator_id, boundary_id)
        if aid_bid not in heuristic_word_order:
            heuristic_word_order[aid_bid] = get_word_order(tokens)
        else:
            print(f"Oops! {aid_bid} already present!")

# --------------------------------------------------------------------------- #


def kendall_tau(x, y, alpha=0):
    """
    Weighted Kendall Tau

    Weight of every concordant or discordant pair is e^-(alpha * index_diff)
    When alpha = 0, returns regular Kendall Tau
    alpha = 0
    => weight(x, y) = 1 for all x, y
    => n_c == w_c and n_d == w_d
    => w_tau == tau
    """
    n = len(x)
    n_c, n_d = 0, 0
    w_c, w_d = 0, 0

    def weight(i, j):
        return math.exp(-alpha * abs(i-j))

    for i in range(n):
        for j in range(i+1, n):
            if (x[i] < x[j] and y[i] < y[j]) or (x[i] > x[j] and y[i] > y[j]):
                n_c += 1
                w_c += weight(i, j)
            elif (x[i] < x[j] and y[i] > y[j]) or (x[i] > x[j] and y[i] < y[j]):
                n_d += 1
                w_d += weight(i, j)

    if w_c + w_d:
        w_tau = (w_c - w_d) / (w_c + w_d)
    else:
        w_tau = 0

    return w_tau, w_c, w_d


# --------------------------------------------------------------------------- #
# Evaluation

evaluation_data = []
evaluation_data_headers = [
    # 'annotator_id', 'boundary_id', 'verse_id',
    'aid', 'bid', 'vid',
    'verse_tokens', 'annotated_anvaya', 'heuristic_anvaya',
    'kendall_tau', 'bleu_4'
]


evaluation_metric = defaultdict(dict)
word_order_tokens = {}

a_sent_all = []
h_sent_all = []

N_C = 0
N_D = 0
W_C = 0
W_D = 0
perfect_match = []

for aid_bid_vid, awo in tqdm(annotated_word_order.items()):
    aid, bid, vid = aid_bid_vid
    aid_bid = (aid, bid)
    hwo = heuristic_word_order[aid_bid]
    hwo_used = [x for x in hwo if x in awo]

    if len(hwo_used) < 2:
        continue

    a_sent = [get_token_text(tid) for tid in awo]
    h_sent = [get_token_text(tid) for tid in hwo_used]
    v_sent = [get_token_text(tid) for tid in sorted(hwo_used)]

    if h_sent == a_sent:
        perfect_match.append(
            (aid, bid, vid, " ".join(v_sent), " ".join(h_sent))
        )

    word_order_tokens[aid_bid] = (v_sent, a_sent, h_sent)

    token_rank = defaultdict(list)
    for idx, word in enumerate(a_sent):
        token_rank[word].append(idx)

    a_rank = list(range(len(a_sent)))
    h_rank = [token_rank[w].pop(0) for w in h_sent]

    kendall_tau_score, n_c, n_d = kendall_tau(a_rank, h_rank)
    # weighted_kendall_tau_score, w_c, w_d = kendall_tau(a_rank, h_rank, weight=1)

    scipy_kendall_tau, _p = kendalltau(a_rank, h_rank)
    try:
        assert round(kendall_tau_score, 4) == round(scipy_kendall_tau, 4)
    except AssertionError:
        print(kendall_tau_score, scipy_kendall_tau)

    N_C += n_c
    N_D += n_d
    # W_C += w_c
    # W_D += w_d

    # print([a_sent], h_sent)
    sentence_bleu_4_score = sentence_bleu(
        [a_sent], h_sent, smoothing_function=SmoothingFunction().method3
    )
    # print([a_sent], h_sent, sentence_bleu_4_score)
    a_sent_all.append([a_sent])
    h_sent_all.append(h_sent)

    evaluation_metric["kendall_tau"][aid_bid] = kendall_tau_score
    # evaluation_metric["weighted_kendall_tau"][aid_bid] = weighted_kendall_tau_score
    evaluation_metric["bleu_4"][aid_bid] = sentence_bleu_4_score

    evaluation_data.append(
        [aid, bid, vid] +
        [' '.join(sent) for sent in [v_sent, a_sent, h_sent]] +
        [
            round(kendall_tau_score, 4),
            # round(weighted_kendall_tau_score, 4),
            round(sentence_bleu_4_score, 4)
        ]
    )

# --------------------------------------------------------------------------- #

evaluation_sentence = defaultdict(dict)
macro_average = defaultdict(float)
micro_average = {}

for metric, sentence_scores in evaluation_metric.items():
    denominator = 0
    for aid_bid, sentence_score in sentence_scores.items():
        evaluation_sentence[aid_bid][metric] = sentence_score

        if isinstance(sentence_score, tuple):
            _score, _p = sentence_score
        else:
            _score = sentence_score
        if not math.isnan(_score):
            macro_average[metric] += _score
            denominator += 1
    macro_average[metric] /= denominator


# micro_average["weighted_kendall_tau"] = (W_C - W_D) / (W_C + W_D)
micro_average["kendall_tau"] = (N_C - N_D) / (N_C + N_D)
micro_average["bleu_4"] = corpus_bleu(a_sent_all, h_sent_all)

# --------------------------------------------------------------------------- #

evaluation_dataframe = pd.DataFrame(
    evaluation_data, columns=evaluation_data_headers
)
evaluation_dataframe.to_csv("evaluation_data_anvaya.csv", index=False)
perfect_match_dataframe = pd.DataFrame(
    perfect_match, columns=["aid", "bid", "vid", "verse", "heuristic"]
)
perfect_match_dataframe.to_csv("evaluation_data_perfect_match.csv")

# --------------------------------------------------------------------------- #

evaluation_results = [heuristic_method]
for k in ["kendall_tau", "bleu_4"]:
    evaluation_results.extend([
        round(macro_average[k], 4),
        round(micro_average[k], 4)
    ])
evaluation_results.append(round(len(perfect_match)/len(evaluation_data), 4))

print(evaluation_results)
results_file = "evaluation_results.csv"
with open(results_file, "a+") as f:
    f.write(",".join(map(str, evaluation_results)))
    f.write("\n")


###############################################################################
