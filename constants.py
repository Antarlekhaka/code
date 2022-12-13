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
TASK_TOKEN_GRAPH = "token_graph"
TASK_TOKEN_CONNECTION = "token_connection"
TASK_SENTENCE_CLASSIFICATION = "sentence_classification"
TASK_SENTENCE_GRAPH = "sentence_graph"

TASK_CATEGORY_LIST = [
    TASK_SENTENCE_BOUNDARY,
    TASK_WORD_ORDER,
    TASK_TOKEN_TEXT_ANNOTATION,
    TASK_TOKEN_CLASSIFICATION,
    TASK_TOKEN_GRAPH,
    TASK_TOKEN_CONNECTION,
    TASK_SENTENCE_CLASSIFICATION,
    TASK_SENTENCE_GRAPH
]

###############################################################################

TASK_TEMPLATES = {
    category: f"task_{category}.html"
    for category in TASK_CATEGORY_LIST
}

RESULT_TEMPLATES = {
    category: f"result_{category}.html"
    for category in TASK_CATEGORY_LIST
}

###############################################################################

TASK_DETAILS = {
    TASK_SENTENCE_BOUNDARY: {
        "name": "sentence_boundary",
        "title": "Sentence Boundary Detection",
        "short": "Boundary",
        "help": "Mark the sentence boundary using the boundary marker."
    },
    TASK_WORD_ORDER: {
        "name": "word_order",
        "title": "Canonical Word Order",
        "short": "Word Order",
        "help": (
            "Arrange the words in the correct order. Optionally, "
            "add new tokens or exclude existing tokens from the sentence."
        )
    },
    TASK_TOKEN_TEXT_ANNOTATION: {
        "name": "token_text_annotation",
        "title": "Token Text Annotation",
        "short": "TextAnno",
        "help": "Enter text annotations associated with the tokens."
    },
    TASK_TOKEN_CLASSIFICATION: {
        "name": "token_classification",
        "title": "Token Classification",
        "short": "TokClf",
        "help": (
            "Classify tokens "
            "by selecting the correct category from the dropdown menu."
        )
    },
    TASK_TOKEN_GRAPH: {
        "name": "token_graph",
        "title": "Token Graph",
        "short": "TokGraph",
        "help": (
            "Create an edge-labelled graph on tokens "
            "in the form of triplets."
        )
    },
    TASK_TOKEN_CONNECTION: {
        "name": "token_connection",
        "title": "Token Connection",
        "short": "TokConn",
        "help": (
            "Mark the token connections. "
            "First click on the source token and then on the target token, "
            "followed by confirming the connection."
        )
    },
    TASK_SENTENCE_CLASSIFICATION: {
        "name": "sentence_classification",
        "title": "Sentence Classification",
        "short": "SentClass",
        "help": (
            "Classify sentences "
            "by selecting the correct category from the dropdown menu."
        )
    },
    TASK_SENTENCE_GRAPH: {
        "name": "sentence_graph",
        "title": "Sentence Graph",
        "short": "SentGraph",
        "help": (
            "Create an edge-labelled graph on sentences "
            "in the form of tripelts. "
            "Sentences can be connected through the "
            "constituent tokens or directly."
            "Direct connections are marked using "
            "the special tokens that appear at the start of the sentence."
        )
    }
}
