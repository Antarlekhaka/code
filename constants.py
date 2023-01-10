#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Global Constants

@author: Hrishikesh Terdalkar
"""
###############################################################################
# Roles

ROLE_OWNER = "owner"
ROLE_ADMIN = "admin"
ROLE_CURATOR = "curator"
ROLE_ANNOTATOR = "annotator"
ROLE_MEMBER = "member"
ROLE_GUEST = "guest"

# --------------------------------------------------------------------------- #
# Permissions

PERMISSION_VIEW_UCP = "view_ucp"
PERMISSION_VIEW_CORPUS = "view_corpus"
PERMISSION_ANNOTATE = "annotate"
PERMISSION_CURATE = "curate"
PERMISSION_VIEW_ACP = "view_acp"

# --------------------------------------------------------------------------- #
# Role Definitions

ROLE_DEFINITIONS = [
    {
        "name": ROLE_GUEST,
        "level": 1,
        "description": "Guest",
        "permissions": []
    },
    {
        "name": ROLE_MEMBER,
        "level": 5,
        "description": "Member",
        "permissions": [PERMISSION_VIEW_UCP, PERMISSION_VIEW_CORPUS]
    },
    {
        "name": ROLE_ANNOTATOR,
        "level": 50,
        "description": "Annotator",
        "permissions": [PERMISSION_ANNOTATE],
    },
    {
        "name": ROLE_CURATOR,
        "level": 75,
        "description": "Curator",
        "permissions": [PERMISSION_ANNOTATE, PERMISSION_CURATE]
    },
    {
        "name": ROLE_ADMIN,
        "level": 100,
        "description": "Administrator",
        "permissions": [PERMISSION_VIEW_ACP]
    },
    {
        "name": ROLE_OWNER,
        "level": 1000,
        "description": "Owner",
        "permissions": [PERMISSION_VIEW_ACP]
    },
]

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

TASK_TEMPLATE_PREFIX = "task"
RESULT_TEMPLATE_PREFIX = "result"
TASK_UPDATE_ACTION_PREFIX = "update"

TASK_ANNOTATION_TEMPLATES = {
    category: f"{TASK_TEMPLATE_PREFIX}_{category}.html"
    for category in TASK_CATEGORY_LIST
}

TASK_EXPORT_TEMPLATES = {
    category: f"{RESULT_TEMPLATE_PREFIX}_{category}.html"
    for category in TASK_CATEGORY_LIST
}

TASK_UPDATE_ACTIONS = {
    category: f"{TASK_UPDATE_ACTION_PREFIX}_{category}"
    for category in TASK_CATEGORY_LIST
}

###############################################################################

TASK_DEFAULT_INFORMATION = {
    TASK_SENTENCE_BOUNDARY: {
        "category": "sentence_boundary",
        "title": "Sentence Boundary Detection",
        "short": "Boundary",
        "help": "Mark the sentence boundary using the boundary marker."
    },
    TASK_WORD_ORDER: {
        "category": "word_order",
        "title": "Word Order",
        "short": "Word Order",
        "help": (
            "Arrange the words in the correct order. Optionally, "
            "add new tokens or exclude existing tokens from the sentence."
        )
    },
    TASK_TOKEN_TEXT_ANNOTATION: {
        "category": "token_text_annotation",
        "title": "Token Text Annotation",
        "short": "TextAnno",
        "help": "Enter text annotations associated with the tokens."
    },
    TASK_TOKEN_CLASSIFICATION: {
        "category": "token_classification",
        "title": "Token Classification",
        "short": "TokClf",
        "help": (
            "Classify tokens "
            "by selecting the correct category from the dropdown menu."
        )
    },
    TASK_TOKEN_GRAPH: {
        "category": "token_graph",
        "title": "Token Graph",
        "short": "TokGraph",
        "help": (
            "Create an edge-labelled graph on tokens "
            "in the form of triplets."
        )
    },
    TASK_TOKEN_CONNECTION: {
        "category": "token_connection",
        "title": "Token Connection",
        "short": "TokConn",
        "help": (
            "Mark the token connections. "
            "First click on the source token and then on the target token, "
            "followed by confirming the connection."
        )
    },
    TASK_SENTENCE_CLASSIFICATION: {
        "category": "sentence_classification",
        "title": "Sentence Classification",
        "short": "SentClass",
        "help": (
            "Classify sentences "
            "by selecting the correct category from the dropdown menu."
        )
    },
    TASK_SENTENCE_GRAPH: {
        "category": "sentence_graph",
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
