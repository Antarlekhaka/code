#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration

@author: Hrishikesh Terdalkar
"""

###############################################################################

import os
from utils.configuration import Configuration
from constants import (
    TASK_SENTENCE_BOUNDARY,
    TASK_WORD_ORDER,
    TASK_TOKEN_TEXT_ANNOTATION,
    TASK_TOKEN_CLASSIFICATION,
    TASK_TOKEN_GRAPH,
    TASK_TOKEN_CONNECTION,
    TASK_SENTENCE_CLASSIFICATION,
    TASK_SENTENCE_GRAPH
)

###############################################################################
# EDIT

DEBUG = False

APP_NAME = "Antarlekhaka, a Multiple-Task Annotation Framework"
APP_TITLE = "Antarlekhaka"

APP_DIR = os.path.dirname(os.path.realpath(__file__))
LOG_FILE = os.path.join(APP_DIR, "antarlekhaka.log")

# DB_DIR is used for specifying directory containing SQLite3 database

DB_DIR = "db"
DATA_DIR = "data"
TABLES_DIR = os.path.join(DATA_DIR, "tables")
CORPUS_DIR = os.path.join(DATA_DIR, "corpus")

# --------------------------------------------------------------------------- #

APPLICATION_CONFIG = {
    "row_detail_formatter": "generic",

    # # Heuristic Settings
    # "use_heuristic": {
    #     "sentence_boundary": True,
    #     "word_order": True,
    #     "token_classification": True
    # },

    # CoNLL-U Corpus Settings
    "conllu": {
        "input_scheme": "iast",
        "store_scheme": "devanagari",
        "input_fields": [
            "id",      # 01
            "form",    # 02 word form or punctuation symbol
            # if it contains multiple words, the annotation
            # follows the proposals for multi-word annotation
            # (URL: format.html#words-tokens-and-empty-nodes)
            "lemma",   # 03 lemma or stem
            "upos",    # 04 universal POS tags
            "xpos",    # 05 language specific POS tags
            "feats",   # 06 key-value
            "head",    # 07
            "deprel",  # 08
            "deps",    # 09
            "misc"     # 10 key-value
        ],
        "relevant_fields": {
            "id": "",
            "form": "",
            "lemma": "",
            "upos": "",
            "xpos": "",
            "feats": {},
            "misc": {}
        },
        "transliterate_metadata_keys": ["text"],
        "transliterate_token_keys": ["form", "lemma", "misc.Unsandhied"],
    },
    # Plaintext Corpus Settings
    "plaintext": {
        "input_scheme": "iast",
        "store_scheme": "devanagari",
    },
    # TODO: handle corpus specific things through config?
    # corpus agnostic treatment will require changes to JS too
    # e.g. assumptions about / usage of "unsandhied"
    "token_analysis_items": [
        {"id": "upos", "title": "UPOS"},
        {"id": "xpos", "title": "XPOS"}
    ],
    "token_feature_items": [
        {"id": "case", "title": "Case"},
        {"id": "formation", "title": "Formation"},
        {"id": "gender", "title": "Gender"},
        {"id": "mood", "title": "Mood"},
        {"id": "number", "title": "Number"},
        {"id": "person", "title": "Person"},
        {"id": "tense", "title": "Tense"},
        {"id": "verb-form", "title": "VerbForm"},
        {"id": "voice", "title": "Voice"}
    ],
    "token_misc_items": [],
    # Export
    "export": {
        "token_text_preference": {
            TASK_WORD_ORDER: ["misc.Unsandhied", "form", "lemma"],
            TASK_TOKEN_TEXT_ANNOTATION: ["lemma", "misc.Unsandhied", "form"],
            TASK_TOKEN_CLASSIFICATION: ["lemma", "misc.Unsandhied", "form"],
            TASK_TOKEN_GRAPH: ["lemma", "misc.Unsandhied", "form"],
            TASK_TOKEN_CONNECTION: ["misc.Unsandhied", "form", "lemma"],
            TASK_SENTENCE_GRAPH: ["lemma", "misc.Unsandhied", "form"],
        }
    },
}

# --------------------------------------------------------------------------- #

CONTACTS = [
    {
        "name": "Hrishikesh Terdalkar",
        "email": "hrishirt@cse.iitk.ac.in",
        "designation": "PhD Student",
        "affiliation": "CSE, IITK",
    }
]

# --------------------------------------------------------------------------- #
# HTML About

ABOUT = """
"Antarlekhaka" is a framework for annotation towards numerous classes of
linguistic tasks such as sentence boundary, word order, token text annotation,
token classification (e.g. named entity recognition), token graph (e.g. action
graph), token connection (e.g. co-reference resolution), sentence classification,
sentence graph (e.g discourse graph).
"""

# --------------------------------------------------------------------------- #
# Custom Pages
# * Page under the key "custom" will be served at "/custom"
# * "title" will be used in <head> tag within <title>
# * "card_header" and "card_body" will appear as page content within a card
# * CAUTION: Only safe HTML content should be added.

CUSTOM_PAGES = {
    "custom": {
        "title": "Custom Title",
        "card_header": "Custom Header",
        "card_body": """This is a cusotm page with HTML content."""
    }
}

# --------------------------------------------------------------------------- #
# Security

# Generate a nice key using secrets.token_urlsafe()
SECRET_KEY = os.environ.get("SECRET_KEY", "secret-key")

# Bcrypt is set as default SECURITY_PASSWORD_HASH, which requires a salt
# Generate a good salt using: secrets.SystemRandom().getrandbits(128)
SECURITY_PASSWORD_SALT = os.environ.get(
    "SECURITY_PASSWORD_SALT", "00000000000000000000000000000000000000"
)

# --------------------------------------------------------------------------- #
# First User

ADMIN_USER = os.environ.get("ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "admin")
ADMIN_MAIL = os.environ.get("ADMIN_MAIL", "admin@localhost")

# --------------------------------------------------------------------------- #
# Neo4j

NEO4J_SERVER = ""
NEO4J_USERNAME = ""
NEO4J_PASSWORD = ""

# --------------------------------------------------------------------------- #
# PythonAnywhere

PA_DOMAIN = os.environ.get("PA_DOMAIN", "")
PA_USERNAME = os.environ.get("PA_USERNAME", "")
PA_TOKEN = os.environ.get("PA_TOKEN", "")

# --------------------------------------------------------------------------- #
# SMTP Config

SMTP_ENABLED = False

SMTP_SENDER_NAME = os.environ.get("SMTP_SENDER_NAME", "Antarlekhaka Admin")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
SMTP_PORT = os.environ.get("SMTP_PORT", "587")
SMTP_USE_SSL = os.environ.get("SMTP_USE_SSL", "0")
SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "1")

# --------------------------------------------------------------------------- #
# MongoDB Config

MONGO_HOST = os.environ.get("MONGO_HOST", "")
MONGO_USER = os.environ.get("MONGO_USER", "")
MONGO_PASS = os.environ.get("MONGO_PASS", "")
MONGO_DATABASE = os.environ.get("MONGO_DATABASE", "")
MONGO_OPTIONS = os.environ.get("MONGO_OPTIONS", "?retryWrites=true&w=majority")

# --------------------------------------------------------------------------- #
# MySQL Config

MYSQL_USER = os.environ.get("MYSQL_USER", "")
MYSQL_PASS = os.environ.get("MYSQL_PASS", "")
MYSQL_HOST = os.environ.get("MYSQL_HOST", "")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "")

# --------------------------------------------------------------------------- #
# SQLite Config

SQLITE_DATABASE = os.environ.get("SQLITE_DATABASE", "main.db")

# --------------------------------------------------------------------------- #

USE_MONGO = False
USE_MYSQL = False
USE_SQLITE = True

###############################################################################
# DO NOT EDIT

app = Configuration()
app.name = APP_NAME
app.title = APP_TITLE
app.debug = DEBUG

# Config
app.config = APPLICATION_CONFIG
app.about = ABOUT
app.custom_pages = CUSTOM_PAGES

# Paths
app.dir = APP_DIR
app.db_dir = os.path.join(APP_DIR, DB_DIR)
app.data_dir = os.path.join(APP_DIR, DATA_DIR)
app.tables_dir = os.path.join(APP_DIR, TABLES_DIR)
app.corpus_dir = os.path.join(APP_DIR, CORPUS_DIR)

app.log_file = LOG_FILE

# Security

app.secret_key = SECRET_KEY
app.security_password_salt = SECURITY_PASSWORD_SALT

# Users

app.admin = {
    "username": ADMIN_USER,
    "email": ADMIN_MAIL,
    "password": ADMIN_PASS
}

app.contacts = CONTACTS

# Neo4j
app.neo4j = {
    "server": NEO4J_SERVER,
    "username": NEO4J_USERNAME,
    "password": NEO4J_PASSWORD
}

# PythonAnywhere
# https://help.pythonanywhere.com/pages/API

app.pa_enabled = bool(PA_DOMAIN and PA_USERNAME and PA_TOKEN)
app.pa_api_actions = {
    "info": f"/webapps/{PA_DOMAIN}/",
    "reload": f"/webapps/{PA_DOMAIN}/reload/",
}

app.pa_api_url = f"https://www.pythonanywhere.com/api/v0/user/{PA_USERNAME}/"
app.pa_headers = {
    "Authorization": f"Token {PA_TOKEN}"
}

# MongoDB

if USE_MONGO:
    app.mongo = {
        "host": (f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}/"
                 f"{MONGO_DATABASE}?retryWrites=true&w=majority"),
        "connect": False,
        "connectTimeoutMS": 30000,
        "socketTimeoutMS": None,
        "socketKeepAlive": True,
        "maxPoolsize": 1
    }

# SMTP

app.smtp_enabled = SMTP_ENABLED
app.smtp = {
    "name": SMTP_SENDER_NAME,
    "server": SMTP_SERVER,
    "username": SMTP_USER,
    "password": SMTP_PASS,
    "port": int(SMTP_PORT),
    "use_ssl": bool(int(SMTP_USE_SSL)),
    "use_tls": bool(int(SMTP_USE_TLS))
}


# MySQL

if USE_MYSQL:
    app.sqla = {
        "database_uri": (
            f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASS}"
            f"@{MYSQL_HOST}/{MYSQL_DATABASE}"
        )
    }

# SQLite

if USE_SQLITE:
    app.sqla = {
        "database_uri": (
            f"sqlite:///{os.path.join(app.db_dir, SQLITE_DATABASE)}"
        )
    }

###############################################################################
