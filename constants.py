#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Global Constants

@author: Hrishikesh Terdalkar
"""

###############################################################################
# Task Categories

TASK_SENTENCE_BOUNDARY = "sentence_boundary"
TASK_WORD_ORDER = "word_order"
TASK_TOKEN_TEXT_ANNOTATION = "token_text_annotation"
TASK_TOKEN_CLASSIFICATION = "token_classification"
TASK_TOKEN_GRAPH_EDGE_LABEL = "token_graph_edge_label"
TASK_TOKEN_GRAPH_NO_EDGE_LABEL = "token_graph_no_edge_label"
TASK_SENTENCE_CLASSIFICATION = "sentence_classification"
TASK_SENTENCE_GRAPH_EDGE_LABEL = "sentence_graph_edge_label"

TASK_CATEGORY_LIST = [
    TASK_SENTENCE_BOUNDARY,
    TASK_WORD_ORDER,
    TASK_TOKEN_TEXT_ANNOTATION,
    TASK_TOKEN_CLASSIFICATION,
    TASK_TOKEN_GRAPH_EDGE_LABEL,
    TASK_TOKEN_GRAPH_NO_EDGE_LABEL,
    TASK_SENTENCE_CLASSIFICATION,
    TASK_SENTENCE_GRAPH_EDGE_LABEL
]

###############################################################################

TASK_TEMPLATES = {
    category: "task_{category}.html"
    for category in TASK_CATEGORY_LIST
}

RESULT_TEMPLATES = {
    category: "result_{category}.html"
    for category in TASK_CATEGORY_LIST
}
