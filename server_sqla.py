#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Annotation Server

Deployment
----------

1. Using Flask-Run

```
$ export FLASK_APP="server:webapp"
$ flask run
```

2. Using gunicorn

```
$ gunicorn -b host:port server:webapp
```

3. Direct (dev only)

```
$ python server.py
```
"""

__author__ = "Hrishikesh Terdalkar"
__copyright__ = "Copyright (C) 2022-2023 Hrishikesh Terdalkar"
__version__ = "1.0"

###############################################################################

import os
import re
import csv
import glob
import json
import logging
import datetime

import git
import requests
from flask import (Flask, render_template, redirect, jsonify, url_for,
                   request, flash, session, Response, abort)
from flask_security import (Security, auth_required, permissions_required,
                            hash_password, current_user, user_registered,
                            user_authenticated)
from flask_security.utils import uia_email_mapper
# from sqlalchemy import or_, and_

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from flask_babelex import Babel
from flask_wtf import CSRFProtect
from flask_mail import Mail
from flask_migrate import Migrate

# from indic_transliteration.sanscript import transliterate

from constants import (
    # Task Category Names
    TASK_SENTENCE_BOUNDARY,
    TASK_WORD_ORDER,
    TASK_TOKEN_TEXT_ANNOTATION,
    TASK_TOKEN_CLASSIFICATION,
    TASK_TOKEN_GRAPH,
    TASK_TOKEN_CONNECTION,
    TASK_SENTENCE_CLASSIFICATION,
    TASK_SENTENCE_GRAPH,

    TASK_DEFAULT_INFORMATION,
    TASK_UPDATE_ACTIONS,
    TASK_ANNOTATION_TEMPLATES, TASK_EXPORT_TEMPLATES
)

from models_sqla import (db, user_datastore,
                         CustomLoginForm, CustomRegisterForm,
                         Corpus, Chapter, Verse, Line, Token,
                         Task, SubmitLog, WordOrder, Boundary,
                         TokenTextAnnotation, TokenLabel, TokenClassification,
                         TokenRelationLabel, TokenGraph,
                         TokenConnection,
                         SentenceLabel, SentenceClassification,
                         SentenceRelationLabel, SentenceGraph)
from settings import app

from utils.reverseproxied import ReverseProxied
from utils.database import export_data, get_verse_data, get_chapter_data
from utils.database import add_chapter
from utils.export import simple_format, standard_format
from utils.conllu import CoNLLUParser

###############################################################################

logging.basicConfig(format='[%(asctime)s] %(name)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO,
                    handlers=[logging.FileHandler(app.log_file),
                              logging.StreamHandler()])

###############################################################################
# UIA Mapper


def uia_username_mapper(identity):
    pattern = r'^(?!_$)(?![0-9_.])(?!.*[_.]{2})[a-zA-Z0-9_.]+(?<![.])$'
    return identity if re.match(pattern, identity) else None


###############################################################################
# Flask Application

webapp = Flask(app.name, static_folder='static')
webapp.config['DEBUG'] = app.debug
webapp.wsgi_app = ReverseProxied(webapp.wsgi_app)
webapp.url_map.strict_slashes = False


webapp.config['SECRET_KEY'] = app.secret_key
webapp.config['SECURITY_PASSWORD_SALT'] = app.security_password_salt
webapp.config['JSON_AS_ASCII'] = False
webapp.config['JSON_SORT_KEYS'] = False

# SQLAlchemy Config
webapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
webapp.config['SQLALCHEMY_DATABASE_URI'] = app.sqla['database_uri']
webapp.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
}

# CSRF Token Expiry
webapp.config['WTF_CSRF_TIME_LIMIT'] = None

###############################################################################
# Flask-Security-Too Configuration

webapp.config['SECURITY_REGISTERABLE'] = True
webapp.config['SECURITY_SEND_REGISTER_EMAIL'] = app.smtp_enabled
webapp.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = [
    {'email': {'mapper': uia_email_mapper}},
    {'username': {'mapper': uia_username_mapper}}
]

webapp.config['SECURITY_RECOVERABLE'] = app.smtp_enabled
webapp.config['SECURITY_CHANGEABLE'] = True
webapp.config['SECURITY_TRACKABLE'] = True
# NOTE: SECURITY_USERNAME_ still buggy in Flask-Security-Too
# Exercise caution before enabling the following two options
# webapp.config['SECURITY_USERNAME_ENABLE'] = True
# webapp.config['SECURITY_USERNAME_REQUIRED'] = True
webapp.config['SECURITY_POST_LOGIN_VIEW'] = 'show_home'
webapp.config['SECURITY_POST_LOGOUT_VIEW'] = 'show_home'

###############################################################################
# Mail Configuration

if app.smtp_enabled:
    webapp.config['MAIL_SERVER'] = app.smtp['server']
    webapp.config['MAIL_USERNAME'] = app.smtp['username']
    webapp.config['MAIL_DEFAULT_SENDER'] = (app.smtp['name'],
                                            app.smtp['username'])
    webapp.config['MAIL_PASSWORD'] = app.smtp['password']
    webapp.config['MAIL_USE_SSL'] = app.smtp['use_ssl']
    webapp.config['MAIL_USE_TLS'] = app.smtp['use_tls']
    webapp.config['MAIL_PORT'] = app.smtp['port']
    webapp.config['MAIL_DEBUG'] = True

###############################################################################
# Initialize standard Flask extensions

db.init_app(webapp)

csrf = CSRFProtect(webapp)
security = Security(webapp, user_datastore,
                    login_form=CustomLoginForm,
                    register_form=CustomRegisterForm)
mail = Mail(webapp)
migrate = Migrate(webapp, db)
babel = Babel(webapp)

limiter = Limiter(
    webapp,
    key_func=get_remote_address,
    default_limits=["1800 per hour"]
)

###############################################################################
# CoNLL-U Utility

CONLLU_CONFIG = app.config["conllu"]
CONLLU_PARSER = CoNLLUParser(
    input_scheme=CONLLU_CONFIG["input_scheme"],
    store_scheme=CONLLU_CONFIG["store_scheme"],
    input_fields=CONLLU_CONFIG["input_fields"],
    relevant_fields=CONLLU_CONFIG["relevant_fields"],
    transliterate_metadata_keys=CONLLU_CONFIG["transliterate_metadata_keys"],
    transliterate_token_keys=CONLLU_CONFIG["transliterate_token_keys"]
)

###############################################################################
# Database Utility Functions


def record_submit(verse_id: int, annotator_id: int, task_id: int):
    """Record Submit

    Parameters
    ----------
    verse_id : int
        Verse ID
    annotator_id : int
        Annotator ID
    task_id : int
        Task ID
    """
    submit_log = SubmitLog()
    submit_log.verse_id = verse_id
    submit_log.annotator_id = annotator_id
    submit_log.task_id = task_id
    db.session.add(submit_log)
    db.session.commit()


###############################################################################
# Hooks


@webapp.before_first_request
def init_database():
    """Initiate database and create admin user"""
    db.create_all()
    role_definitions = sorted(app.role_definitions,
                              key=lambda x: x['level'],
                              reverse=True)
    for role_definition in role_definitions:
        name = role_definition['name']
        description = role_definition['description']
        permissions = role_definition['permissions']
        level = role_definition['level']
        user_datastore.find_or_create_role(
            name=name,
            description=description,
            level=level,
            permissions=permissions
        )

    if not user_datastore.find_user(username=app.admin['username']):
        user_datastore.create_user(
            username=app.admin['username'],
            email=app.admin['email'],
            password=hash_password(app.admin['password']),
            roles=['owner', 'admin', 'curator',
                   'annotator', 'member']
        )

    # ----------------------------------------------------------------------- #
    # Populate various tables if empty

    objects = []

    # Task
    required_tasks = [TASK_SENTENCE_BOUNDARY, TASK_WORD_ORDER]
    if not Task.query.first():
        for task_idx, task_category in enumerate(required_tasks, start=1):
            task_information = TASK_DEFAULT_INFORMATION[task_category]

            t = Task()
            t.id = task_idx
            t.category = task_category
            t.title = task_information["title"]
            t.short = task_information["short"]
            t.help = task_information["help"]
            t.order = task_idx
            t.is_deleted = True
            objects.append(t)

        webapp.logger.info(f"Loaded {task_idx} tasks.")

    # Save
    if objects:
        db.session.bulk_save_objects(objects)

    # ----------------------------------------------------------------------- #

    db.session.commit()

# --------------------------------------------------------------------------- #


@user_registered.connect_via(webapp)
def assign_default_roles(sender, user, **extra):
    """Assign member role to users after successful registration"""
    user_datastore.add_role_to_user(user, 'member')
    db.session.commit()


@user_authenticated.connect_via(webapp)
def _after_authentication_hook(sender, user, **extra):
    pass

###############################################################################
# Global Context


@webapp.context_processor
def inject_global_context():
    theme_css_files = glob.glob(
        os.path.join(app.dir, 'static', 'themes', 'css', 'bootstrap.*.min.css')
    )
    theme_js_files = glob.glob(
        os.path.join(app.dir, 'static', 'themes', 'js', 'bootstrap.*.min.js')
    )
    THEMES = {
        "with_css": ['default'] + sorted([
            os.path.basename(theme).split('.')[1]
            for theme in theme_css_files
        ]),
        "with_js": sorted([
            os.path.basename(theme).split('.')[1]
            for theme in theme_js_files
        ])
    }

    # NOTE: do we really need to have these in global context?
    # since they are not required on "every" page
    # move them to individual routes?
    # alternatively, can we add a check here which route is loading,
    # and export variables based on that?
    all_tasks = {
        task.id: {
            "id": task.id,
            "category": task.category,
            "title": task.title,
            "short": task.short,
            "help": task.help,
            "order": task.order,
            "is_deleted": task.is_deleted
        }
        for task in Task.query.order_by(Task.order).all()
    }
    active_tasks = {
        task_id: task for
        task_id, task in all_tasks.items()
        if not task["is_deleted"]
    }
    active_task_ids = list(active_tasks)
    if active_task_ids:
        first_task = active_task_ids[0]
        next_task = dict(
            zip(
                active_task_ids,
                active_task_ids[1:] + [active_task_ids[0]]
            )
        )
    else:
        first_task = None
        next_task = {}

    TASKS = {
        'tasks': all_tasks,
        'active_ids': active_task_ids,
        'active_tasks': active_tasks,
        'first_task': first_task,
        'next_task': next_task,

        # task default information
        'default': TASK_DEFAULT_INFORMATION,

        # task categories
        'task_sentence_boundary': TASK_SENTENCE_BOUNDARY,
        'task_word_order': TASK_WORD_ORDER,
        'task_token_text_annotation': TASK_TOKEN_TEXT_ANNOTATION,
        'task_token_classification': TASK_TOKEN_CLASSIFICATION,
        'task_token_graph': TASK_TOKEN_GRAPH,
        'task_token_connection': TASK_TOKEN_CONNECTION,
        'task_sentence_classification': TASK_SENTENCE_CLASSIFICATION,
        'task_sentence_graph': TASK_SENTENCE_GRAPH,

        # update actions
        'update_actions': TASK_UPDATE_ACTIONS,
    }

    LABELS = {
        # 'task_labels': Label.query.filter(
        #     ActionLabel.is_deleted == False  # noqa # '== False' is required
        # ).with_entities(
        #     Label.id, Label.task_id, Label.label, Label.description
        # ).order_by(Label.task_id, Label.label).all(),
        'token_labels': TokenLabel.query.filter(
            TokenLabel.is_deleted == False  # noqa # '== False' is required
        ).with_entities(
            TokenLabel.id,
            TokenLabel.task_id,
            TokenLabel.label,
            TokenLabel.description
        ).order_by(TokenLabel.label).all(),
        'token_relation_labels': TokenRelationLabel.query.filter(
            TokenRelationLabel.is_deleted == False  # noqa # '== False' is required
        ).with_entities(
            TokenRelationLabel.id,
            TokenRelationLabel.task_id,
            TokenRelationLabel.label,
            TokenRelationLabel.description
        ).order_by(TokenRelationLabel.label).all(),
        'sentence_labels': SentenceLabel.query.filter(
            SentenceLabel.is_deleted == False  # noqa # '== False' is required
        ).with_entities(
            SentenceLabel.id,
            SentenceLabel.task_id,
            SentenceLabel.label,
            SentenceLabel.description
        ).order_by(SentenceLabel.label).all(),
        'sentence_relation_labels': SentenceRelationLabel.query.filter(
            SentenceRelationLabel.is_deleted == False  # noqa # '== False' is required
        ).with_entities(
            SentenceRelationLabel.id,
            SentenceRelationLabel.task_id,
            SentenceRelationLabel.label,
            SentenceRelationLabel.description
        ).order_by(SentenceRelationLabel.label).all(),
        'admin_labels': []
    }

    for task in Task.query.all():
        _name = None
        if task.category == TASK_TOKEN_CLASSIFICATION:
            _name = "token"
            _object_name = "token_labels"
        if task.category == TASK_TOKEN_GRAPH:
            _name = "token_relation"
            _object_name = "token_relation_labels"
        if task.category == TASK_SENTENCE_CLASSIFICATION:
            _name = "sentence"
            _object_name = "sentence_labels"
        if task.category == TASK_SENTENCE_GRAPH:
            _name = "sentence_relation"
            _object_name = "sentence_relation_labels"

        if _name is not None:
            LABELS["admin_labels"].append({
                "task_id": task.id,
                "name": _name,
                "title": task.title,
                "object_name": _object_name
            })

    return {
        'title': app.title,
        'now': datetime.datetime.utcnow(),
        'context_tasks': TASKS,
        'context_labels': LABELS,
        'context_themes': THEMES,
        'config': app.config
    }

###############################################################################
# Views


@webapp.route("/admin")
@auth_required()
@permissions_required('view_acp')
def show_admin():
    data = {}
    data['title'] = 'Admin'

    user_level = max([role.level for role in current_user.roles])
    annotator_role = user_datastore.find_role('annotator')

    user_model = user_datastore.user_model
    role_model = user_datastore.role_model
    user_query = user_model.query
    role_query = role_model.query

    data['users'] = []
    data['annotators'] = []

    for user in user_query.all():
        user_object = {
            "id": user.id,
            "username": user.username,
            "email": user.email
        }
        data['users'].append(user_object)
        if annotator_role in user.roles:
            data['annotators'].append(user_object)

    data['roles'] = [
        role.name
        for role in role_query.order_by(role_model.level).all()
        if role.level < user_level
    ]

    data['corpus_list'] = [
        {
            'id': corpus.id,
            'name': corpus.name,
            'chapters': [
                {
                    'id': chapter.id,
                    'name': chapter.name
                }
                for chapter in corpus.chapters.all()
            ]
        }
        for corpus in Corpus.query.all()
    ]
    data['pa'] = app.pa_enabled

    admin_result = session.get('admin_result', None)
    if admin_result:
        data['result'] = admin_result
        del session['admin_result']
    return render_template('admin.html', data=data)


@webapp.route("/export", methods=["GET", "POST"])
@auth_required()
@permissions_required('annotate')
def show_export():
    data = {}
    data['title'] = 'Export'

    if current_user.has_role("curator"):
        user_model = user_datastore.user_model
        user_query = user_model.query
        data['users'] = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
            for user in user_query.all()
        ]
    data['corpus_list'] = [
        {
            'id': corpus.id,
            'name': corpus.name,
            'chapters': [
                {
                    'id': chapter.id,
                    'name': chapter.name
                }
                for chapter in corpus.chapters.all()
            ]
        }
        for corpus in Corpus.query.all()
    ]

    if request.method == "POST":
        annotator_id = None
        if current_user.has_role("curator"):
            annotator_id = request.form.get('annotator_id', '').strip()

        if not annotator_id:
            annotator_id = current_user.id

        chapter_ids = request.form.getlist('chapter_id')

        annotation_data = export_data(
            annotator_ids=[int(annotator_id)],
            chapter_ids=[int(chapter_id) for chapter_id in chapter_ids],
            task_ids=[]
        )
        simple_data = simple_format(annotation_data)
        annotation_result = {
            k[0]: v
            for k, v in simple_data.items()
        }
        data['form'] = {
            'annotator_id': annotator_id,
            'chapter_ids': chapter_ids
        }
        data["result"] = annotation_result

    return render_template('export.html', data=data)


@webapp.route("/settings")
@auth_required()
@permissions_required('view_ucp')
def show_settings():
    data = {}
    data['title'] = 'Settings'
    return render_template('settings.html', data=data)


@webapp.route("/corpus")
@webapp.route("/corpus/<string:chapter_id>")
@auth_required()
@permissions_required('view_corpus')
def show_corpus(chapter_id=None):
    if chapter_id is None:
        flash("Please select a corpus to view.")
        return redirect(url_for('show_home'))

    data = {}
    data['title'] = 'Corpus'
    data['chapter_id'] = chapter_id
    return render_template('corpus.html', data=data)


@webapp.route("/terms")
def show_terms():
    data = {'title': 'Terms of Use'}
    return render_template('terms.html', data=data)


@webapp.route("/contact")
def show_contact():
    data = {'title': 'Contact Us'}
    contacts = []
    replacement = {'@': 'at', '.': 'dot'}
    for _contact in app.contacts:
        contact = _contact.copy()
        email = (
            _contact['email'].replace('.', ' . ').replace('@', ' @ ').split()
        )
        contact['email'] = []

        for email_part in email:
            contact['email'].append({
                'text': replacement.get(email_part, email_part),
                'is_text': replacement.get(email_part) is None
            })
        contacts.append(contact)
    data['contacts'] = contacts
    return render_template('contact.html', data=data)


@webapp.route("/about")
def show_about():
    data = {
        'title': 'About',
        'about': app.about
    }
    return render_template('about.html', data=data)


@webapp.route("/<page>")
def show_custom_page(page):
    if page in app.custom_pages:
        page_data = app.custom_pages[page]
        data = {
            'title': page_data['title'],
            'card_header': page_data['card_header'],
            'card_body': page_data['card_body']
        }
        return render_template('pages.html', data=data)
    else:
        abort(404)


@webapp.route("/")
@auth_required()
def show_home():
    data = {}
    data['title'] = 'Home'
    data['corpus_list'] = [
        {'id': corpus.id, 'name': corpus.name, 'chapters': [
            {'id': chapter.id, 'name': chapter.name}
            for chapter in corpus.chapters.all()
        ]}
        for corpus in Corpus.query.all()
    ]

    return render_template('home.html', data=data)

###############################################################################
# Action Endpoints


@webapp.route("/api/search/analysis/<string:token_text>")
@auth_required()
def api_search_token(token_text: str):
    search_query = Token.query.filter(
        Token.text == token_text
    ).group_by(Token.analysis)
    analyses = [
        token.analysis for token in search_query
    ]
    return jsonify({
        'text': token_text,
        'matches': analyses
    })


# --------------------------------------------------------------------------- #


@webapp.route("/api", methods=["POST"])
@auth_required()
def api():
    api_response = {}
    api_response['success'] = False
    try:
        action = request.form['action']
    except KeyError:
        api_response['message'] = "Insufficient parameters in request."
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #
    # Action Authorization

    task_update_actions = list(TASK_UPDATE_ACTIONS.values())
    annotator_actions = task_update_actions + ["add_token"]

    role_actions = {
        "admin": [],
        "annotator": annotator_actions,
        "curator": [],
        "querier": []
    }
    valid_actions = [
        action for actions in role_actions.values() for action in actions
    ]

    if action not in valid_actions:
        api_response["message"] = f"Invalid action. ({action})"
        return jsonify(api_response)

    for role, actions in role_actions.items():
        if action in actions and not current_user.has_role(role):
            api_response["message"] = "Insufficient permissions."
            return jsonify(api_response)

    # ----------------------------------------------------------------------- #
    # Populate next_task

    task_query = Task.query.filter(
        Task.is_deleted == False  # noqa # '== False' is required
    ).order_by(Task.order)
    active_task_ids = [task.id for task in task_query.all()]

    if active_task_ids:
        first_task = active_task_ids[0]
        next_task = dict(
            zip(
                active_task_ids,
                active_task_ids[1:] + [active_task_ids[0]]
            )
        )
    else:
        first_task = None
        next_task = {}

    if action in task_update_actions:
        api_response["first_task"] = first_task

    # ----------------------------------------------------------------------- #

    api_response["success"] = True
    api_response["message"] = "Under construction."
    api_response["style"] = "warning"

    # ----------------------------------------------------------------------- #

    if action == TASK_UPDATE_ACTIONS[TASK_SENTENCE_BOUNDARY]:
        annotator_id = current_user.id
        task_id = int(request.form["task_id"])
        verse_id = int(request.form["verse_id"])
        boundary_tokens = [
            int(b.strip())
            for b in request.form["boundaries"].split(",")
            if b.strip()
        ]

        perform_update = False
        objects_to_update = []
        # If there's any change between existing tokens and marked tokens,
        # delete  all existing boundary tokens from this verse
        # WordOrder also gets deleted as (CASCADE)
        # TokenClassification also gets deleted as (CASCADE)
        # TokenGraph also gets deleted as (CASCADE)
        # TokenConnection also gets deleted as (CASCADE)
        # SentenceClassification also gets deleted as (CASCADE)
        # SentenceGraph also gets deleted as (CASCADE)

        # NOTE: A sentence boundary task should always be "present"
        # (even if inactive), since very other task is tied to boundary_id
        # NOTE: We do not check with task_id because, only single sentence
        # boundary task is supported
        # TODO: Perhaps remove `task_id` column from Boundary table altogether
        existing_boundary_query = Boundary.query.filter(
            Boundary.verse_id == verse_id,
            Boundary.annotator_id == annotator_id
        )

        existing_boundary_tokens = [
            _boundary.token_id
            for _boundary in existing_boundary_query.all()
        ]
        if set(existing_boundary_tokens) != set(boundary_tokens):
            perform_update = True

            # delete existing boundary markers from current verse
            # NOTE: this *could* be improved to only delete the changed one
            # but every change in boundary marker affects the boundary AFTER it
            # as well, (and only that), and while adding multiple boundary
            # markers, this can get complicated, so, delete all
            existing_boundary_query.delete(synchronize_session=False)

            # delete the first boundary marker after the current verse
            next_boundary = Boundary.query.filter(
                Boundary.verse_id > verse_id,
                Boundary.annotator_id == annotator_id,
            ).order_by(Boundary.token_id).first()
            print(next_boundary)

            # NOTE: We do not check with task_id because, currently, only
            # single word order task is supported (as there needs to be a
            # link between this and boundary task)
            # NOTE: If for some reason we need multiple word order tasks,
            # all of them would require to be deleted anyway as the boundary
            # gets changed, so we might never need to check with task_id here
            if next_boundary:
                word_order_of_next_boundary_query = WordOrder.query.filter(
                    WordOrder.boundary_id == next_boundary.id,
                    WordOrder.annotator_id == annotator_id
                )
                word_order_of_next_boundary_query.delete(
                    synchronize_session=False
                )

            # add new boundary markers
            for boundary_token in boundary_tokens:
                boundary = Boundary()
                boundary.task_id = task_id
                boundary.verse_id = verse_id
                boundary.token_id = boundary_token
                boundary.annotator_id = annotator_id
                objects_to_update.append(boundary)

        try:
            if perform_update:
                if objects_to_update:
                    db.session.bulk_save_objects(objects_to_update)
                db.session.commit()
                api_response["message"] = "Successfully updated!"
                api_response["style"] = "success"
                api_response["changes"] = True
            else:
                api_response["message"] = "No changes were submitted."
                api_response["style"] = "warning"

            record_submit(
                verse_id=verse_id,
                annotator_id=annotator_id,
                task_id=task_id
            )
            api_response["success"] = True
            api_response["next_task"] = next_task[task_id]
        except Exception as e:
            webapp.logger.exception(e)
            webapp.logger.info(request.form)
            api_response["success"] = False
            api_response["message"] = "Something went wrong!"
            api_response["style"] = "danger"

        api_response["data"] = None
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == "add_token":
        annotator_id = current_user.id
        verse_id = int(request.form["verse_id"])
        token_data = json.loads(request.form["token_data"])

        # NOTE: associate added tokens with the first line of the verse
        _line = Line.query.filter(Line.verse_id == verse_id).first()
        _line_id = _line.id

        lowest_order = Token.query.filter(
            Token.line_id == _line_id
        ).order_by(Token.order).first().order

        token = Token()
        token.line_id = _line_id
        token.inner_id = "custom"  # NOTE: not unique
        token.order = min(lowest_order, 0) - 1
        token.text = token_data['text']
        token.lemma = token_data['lemma']
        token.analysis = token_data['analysis']
        token.annotator_id = annotator_id

        try:
            db.session.add(token)
            db.session.commit()
            api_response["message"] = (
                f"Token '{token_data['text']}' ({token_data['lemma']}) added!"
            )
            api_response["style"] = "success"
            api_response["success"] = True
        except Exception as e:
            webapp.logger.exception(e)
            api_response["success"] = False
            api_response["message"] = "Something went wrong!"
            api_response["style"] = "danger"

        api_response["data"] = None
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == TASK_UPDATE_ACTIONS[TASK_WORD_ORDER]:
        annotator_id = current_user.id
        task_id = int(request.form["task_id"])
        verse_id = int(request.form["verse_id"])
        word_order = json.loads(request.form["word_order"])

        word_order_order = {}
        boundary_ids = []

        for dom_boundary_id, dom_token_ids in word_order.items():
            m1 = re.match(r'boundary-([0-9]+)$', dom_boundary_id)
            if not m1:
                api_response["message"] = "Invalid boundary ID."
                api_response["style"] = "danger"
                api_response["success"] = False
                break
            boundary_id = int(m1.group(1))
            boundary_ids.append(boundary_id)

            _order = []
            for dom_token_id in dom_token_ids:
                m2 = re.match(r'token-button-([0-9]+)$', dom_token_id)
                if m2:
                    _order.append(int(m2.group(1)))
            word_order_order[boundary_id] = _order

        objects_to_update = []

        existing_word_order_query = WordOrder.query.filter(
            WordOrder.task_id == task_id,
            WordOrder.boundary_id.in_(boundary_ids),
            WordOrder.annotator_id == annotator_id
        )
        existing_word_order_query.delete(synchronize_session=False)

        for boundary_id, token_ids in word_order_order.items():
            for order_id, token_id in enumerate(token_ids, start=1):
                _word_order = WordOrder()
                _word_order.task_id = task_id
                _word_order.boundary_id = boundary_id
                _word_order.token_id = token_id
                _word_order.order = order_id
                _word_order.annotator_id = annotator_id
                objects_to_update.append(_word_order)

        try:
            if objects_to_update:
                db.session.bulk_save_objects(objects_to_update)
                db.session.commit()
                api_response["message"] = "Successfully updated!"
                api_response["style"] = "success"
            else:
                api_response["message"] = "No changes were submitted."
                api_response["style"] = "warning"

            record_submit(
                verse_id=verse_id,
                annotator_id=annotator_id,
                task_id=task_id
            )
            api_response["success"] = True
            api_response["next_task"] = next_task[task_id]
        except Exception as e:
            webapp.logger.exception(e)
            webapp.logger.info(request.form)
            api_response["success"] = False
            api_response["message"] = "Something went wrong!"
            api_response["style"] = "danger"

        api_response["data"] = None
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == TASK_UPDATE_ACTIONS[TASK_TOKEN_TEXT_ANNOTATION]:
        annotator_id = current_user.id
        task_id = int(request.form["task_id"])
        verse_id = int(request.form["verse_id"])
        text_annotation_data = json.loads(request.form["text_annotation_data"])

        objects_to_update = []
        try:
            text_annotation_data = {
                int(k.split('-')[-1]): {
                    "boundary_id": int(v["boundary_id"]),
                    "text_annotation": v["text_annotation"]
                }
                for k, v in text_annotation_data.items()
                if re.match(r'token-text-annotation-input-[0-9]+-([0-9]+)$', k)
            }
        except Exception:
            api_response["success"] = False
            api_response["message"] = "Invalid data."
            api_response["style"] = "danger"
            return jsonify(api_response)

        existing_text_annotations = TokenTextAnnotation.query.filter(
            TokenTextAnnotation.task_id == task_id,
            TokenTextAnnotation.boundary.has(Boundary.verse_id == verse_id),
            TokenTextAnnotation.annotator_id == annotator_id,
        ).all()
        existing_text_annotation_token_ids = [
            text_annotation.token_id
            for text_annotation in existing_text_annotations
        ]
        for text_annotation in existing_text_annotations:
            if text_annotation.token_id not in text_annotation_data:
                # text_annotation exists but was not submitted (i.e. removed)
                # TODO: This triggers on the deleted entities always
                # Perhaps we need to add a check
                # That should avoid "Successfully updated" message even when
                # there are no updates
                text_annotation.is_deleted = True
                objects_to_update.append(text_annotation)
            else:
                # text_annotation exists and is submitted (i.e. retained)
                # check if there are any changes to the text_annotation
                token_id = text_annotation.token_id
                if any([
                    text_annotation.text != text_annotation_data[token_id]["text_annotation"],
                    text_annotation.boundary_id != text_annotation_data[token_id]["boundary_id"],
                    text_annotation.is_deleted is True
                ]):
                    text_annotation.text = text_annotation_data[token_id]["text_annotation"]
                    text_annotation.boundary_id = text_annotation_data[token_id]["boundary_id"]
                    text_annotation.is_deleted = False
                    objects_to_update.append(text_annotation)

        for token_id, _text_annotation_data in text_annotation_data.items():
            if token_id in existing_text_annotation_token_ids:
                # submitted text_annotation already exists
                # "else" part of the previous condition block handles this
                # so we can skip here
                continue

            # submitted text_annotation doesn't exist, create
            text_annotation = TokenTextAnnotation()
            text_annotation.task_id = task_id
            text_annotation.boundary_id = _text_annotation_data["boundary_id"]
            text_annotation.token_id = token_id
            text_annotation.text = _text_annotation_data["text_annotation"]
            text_annotation.annotator_id = annotator_id
            text_annotation.is_deleted = False
            objects_to_update.append(text_annotation)

        try:
            if objects_to_update:
                db.session.bulk_save_objects(objects_to_update)
                db.session.commit()
                api_response["message"] = "Successfully updated!"
                api_response["style"] = "success"
            else:
                api_response["message"] = "No changes were submitted."
                api_response["style"] = "warning"

            record_submit(
                verse_id=verse_id,
                annotator_id=annotator_id,
                task_id=task_id
            )
            api_response["success"] = True
            api_response["next_task"] = next_task[task_id]
        except Exception as e:
            webapp.logger.exception(e)
            webapp.logger.info(request.form)
            api_response["success"] = False
            api_response["message"] = "Something went wrong!"
            api_response["style"] = "danger"

        api_response["data"] = None
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == TASK_UPDATE_ACTIONS[TASK_TOKEN_CLASSIFICATION]:
        annotator_id = current_user.id
        task_id = int(request.form["task_id"])
        verse_id = int(request.form["verse_id"])
        token_classification_data = json.loads(
            request.form["token_classification_data"]
        )

        objects_to_update = []
        try:
            token_classification_data = {
                int(k.split('-')[-1]): {
                    "boundary_id": int(v["boundary_id"]),
                    "label_id": int(v["label_id"])
                }
                for k, v in token_classification_data.items()
                if re.match(r'token-class-selector-[0-9]+-([0-9]+)$', k)
            }
        except Exception:
            api_response["success"] = False
            api_response["message"] = "Invalid data."
            api_response["style"] = "danger"
            return jsonify(api_response)

        existing_token_classification = TokenClassification.query.filter(
            TokenClassification.task_id == task_id,
            TokenClassification.boundary.has(Boundary.verse_id == verse_id),
            TokenClassification.annotator_id == annotator_id,
        ).all()
        existing_token_classification_token_ids = [
            tokclf.token_id
            for tokclf in existing_token_classification
        ]
        for tokclf in existing_token_classification:
            if tokclf.token_id not in token_classification_data:
                # tokclf exists but was not submitted (i.e. removed)
                # TODO: This triggers on the deleted entities always
                # Perhaps we need to add a check
                # That should avoid "Successfully updated" message even when
                # there are no updates
                tokclf.is_deleted = True
                objects_to_update.append(tokclf)
            else:
                # tokclf exists and is submitted (i.e. retained)
                # check if there are any changes to the tokclf
                token_id = tokclf.token_id
                if any([
                    tokclf.label_id != token_classification_data[token_id]["label_id"],
                    tokclf.boundary_id != token_classification_data[token_id]["boundary_id"],
                    tokclf.is_deleted is True
                ]):
                    tokclf.label_id = token_classification_data[token_id]["label_id"]
                    tokclf.boundary_id = token_classification_data[token_id]["boundary_id"]
                    tokclf.is_deleted = False
                    objects_to_update.append(tokclf)

        for token_id, _tokclf_data in token_classification_data.items():
            if token_id in existing_token_classification_token_ids:
                # submitted tokclf already exists
                # "else" part of the previous condition block handles this
                # so we can skip here
                continue

            # submitted tokclf doesn't exist, create
            tokclf = TokenClassification()
            tokclf.task_id = task_id
            tokclf.boundary_id = _tokclf_data["boundary_id"]
            tokclf.token_id = token_id
            tokclf.label_id = _tokclf_data["label_id"]
            tokclf.annotator_id = annotator_id
            tokclf.is_deleted = False
            objects_to_update.append(tokclf)

        try:
            if objects_to_update:
                db.session.bulk_save_objects(objects_to_update)
                db.session.commit()
                api_response["message"] = "Successfully updated!"
                api_response["style"] = "success"
            else:
                api_response["message"] = "No changes were submitted."
                api_response["style"] = "warning"

            record_submit(
                verse_id=verse_id,
                annotator_id=annotator_id,
                task_id=task_id
            )
            api_response["success"] = True
            api_response["next_task"] = next_task[task_id]
        except Exception as e:
            webapp.logger.exception(e)
            webapp.logger.info(request.form)
            api_response["success"] = False
            api_response["message"] = "Something went wrong!"
            api_response["style"] = "danger"

        api_response["data"] = None
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == TASK_UPDATE_ACTIONS[TASK_TOKEN_GRAPH]:
        annotator_id = current_user.id
        task_id = int(request.form["task_id"])
        verse_id = int(request.form["verse_id"])
        token_graph_data = json.loads(
            request.form.get("token_graph_data", "[]")
        )

        objects_to_update = []
        try:
            # validate token_graph_data: List[Dict]
            # keys: boundary_id, src_id, label_id, dst_id
            # values: strings? cast int()
            token_graph_data = {
                (
                    int(tokrel["src_id"]),
                    int(tokrel["label_id"]),
                    int(tokrel["dst_id"])
                ): {
                    k: int(v)
                    for k, v in tokrel.items()
                }
                for tokrel in token_graph_data
            }
        except Exception:
            api_response["success"] = False
            api_response["message"] = "Invalid data."
            api_response["style"] = "danger"
            return jsonify(api_response)

        existing_tokrels_query = TokenGraph.query.filter(
            TokenGraph.task_id == task_id,
            TokenGraph.boundary.has(Boundary.verse_id == verse_id),
            TokenGraph.annotator_id == annotator_id,
        )

        existing_tokrels = existing_tokrels_query.all()
        existing_tokrel_tuples = [
            (tokrel.src_id, tokrel.label_id, tokrel.dst_id)
            for tokrel in existing_tokrels
        ]

        for tokrel in existing_tokrels:
            tokrel_tuple = (tokrel.src_id, tokrel.label_id, tokrel.dst_id)
            if tokrel_tuple not in token_graph_data:
                # tokrel exists but was not submitted (i.e. removed)
                tokrel.is_deleted = True
                objects_to_update.append(tokrel)
            else:
                # tokrel exists and is submitted (i.e. retained)
                # check if there are any changes to the tokrel
                if any([
                    tokrel.boundary_id != token_graph_data[tokrel_tuple]["boundary_id"],
                    tokrel.is_deleted is True
                ]):
                    tokrel.boundary_id = token_graph_data[tokrel_tuple]["boundary_id"]
                    tokrel.is_deleted = False
                    objects_to_update.append(tokrel)

        for tokrel_tuple, _tokrel_data in token_graph_data.items():
            if tokrel_tuple in existing_tokrel_tuples:
                # submitted tokrel already exists
                # "else" part of the previous condition block handles this
                # so we can skip here
                continue

            # submitted tokrel doesn't exist, create
            tokrel = TokenGraph()
            tokrel.task_id = task_id
            tokrel.boundary_id = _tokrel_data["boundary_id"]
            tokrel.src_id = _tokrel_data["src_id"]
            tokrel.label_id = _tokrel_data["label_id"]
            tokrel.dst_id = _tokrel_data["dst_id"]
            tokrel.annotator_id = annotator_id
            tokrel.is_deleted = False
            objects_to_update.append(tokrel)

        try:
            if objects_to_update:
                db.session.bulk_save_objects(objects_to_update)
                db.session.commit()
                api_response["message"] = "Successfully updated!"
                api_response["style"] = "success"
            else:
                api_response["message"] = "No changes were submitted."
                api_response["style"] = "warning"

            record_submit(
                verse_id=verse_id,
                annotator_id=annotator_id,
                task_id=task_id
            )
            api_response["success"] = True
            api_response["next_task"] = next_task[task_id]
        except Exception as e:
            webapp.logger.exception(e)
            webapp.logger.info(request.form)
            api_response["success"] = False
            api_response["message"] = "Something went wrong!"
            api_response["style"] = "danger"

        api_response["data"] = None
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == TASK_UPDATE_ACTIONS[TASK_TOKEN_CONNECTION]:
        annotator_id = current_user.id
        task_id = int(request.form["task_id"])
        verse_id = int(request.form["verse_id"])
        token_connection_data = json.loads(
            request.form.get("token_connection_data", "[]")
        )
        context_data = json.loads(
            request.form.get("context_data", "[]")
        )

        objects_to_update = []
        try:
            # validate token_connection_data: List[Dict]
            # keys: boundary_id, src_id, dst_id
            # values: strings? cast int()
            token_connection_data = {
                (
                    int(tokcon["src_id"]),
                    int(tokcon["dst_id"])
                ): {
                    k: int(v)
                    for k, v in tokcon.items()
                }
                for tokcon in token_connection_data
            }
            context_data = [int(boundary_id) for boundary_id in context_data]
        except Exception:
            api_response["success"] = False
            api_response["message"] = "Invalid data."
            api_response["style"] = "danger"
            return jsonify(api_response)

        existing_tokcons_query = TokenConnection.query.filter(
            TokenConnection.task_id == task_id,
            TokenConnection.boundary_id.in_(context_data),
            TokenConnection.annotator_id == annotator_id,
        )

        existing_tokcons = existing_tokcons_query.all()
        existing_tokcon_tuples = [
            (tokcon.src_id, tokcon.dst_id)
            for tokcon in existing_tokcons
        ]

        for tokcon in existing_tokcons:
            tokcon_tuple = (tokcon.src_id, tokcon.dst_id)
            if tokcon_tuple not in token_connection_data:
                # tokcon exists but was not submitted (i.e. removed)
                tokcon.is_deleted = True
                objects_to_update.append(tokcon)
            else:
                # TODO: do we really need to check boundary_id?
                # when would it be different when src_id and dst_id are same?
                # only if we change convention?

                # tokcon exists and is submitted (i.e. retained)
                # check if there are any changes to the tokcon
                if any([
                    tokcon.boundary_id != token_connection_data[tokcon_tuple]["boundary_id"],
                    tokcon.is_deleted is True
                ]):
                    tokcon.boundary_id = token_connection_data[tokcon_tuple]["boundary_id"]
                    tokcon.is_deleted = False
                    objects_to_update.append(tokcon)

        for tokcon_tuple, _tokcon_data in token_connection_data.items():
            if tokcon_tuple in existing_tokcon_tuples:
                # submitted tokcon already exists
                # "else" part of the previous condition block handles this
                # so we can skip here
                continue

            # submitted tokcon doesn't exist, create
            tokcon = TokenConnection()
            tokcon.task_id = task_id
            tokcon.boundary_id = _tokcon_data["boundary_id"]
            tokcon.src_id = _tokcon_data["src_id"]
            tokcon.dst_id = _tokcon_data["dst_id"]
            tokcon.annotator_id = annotator_id
            tokcon.is_deleted = False
            objects_to_update.append(tokcon)

        try:
            if objects_to_update:
                db.session.bulk_save_objects(objects_to_update)
                db.session.commit()
                api_response["message"] = "Successfully updated!"
                api_response["style"] = "success"
            else:
                api_response["message"] = "No changes were submitted."
                api_response["style"] = "warning"

            record_submit(
                verse_id=verse_id,
                annotator_id=annotator_id,
                task_id=task_id
            )
            api_response["success"] = True
            api_response["next_task"] = next_task[task_id]
        except Exception as e:
            webapp.logger.exception(e)
            webapp.logger.info(request.form)
            api_response["success"] = False
            api_response["message"] = "Something went wrong!"
            api_response["style"] = "danger"

        api_response["data"] = None
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == TASK_UPDATE_ACTIONS[TASK_SENTENCE_CLASSIFICATION]:
        annotator_id = current_user.id
        task_id = int(request.form["task_id"])
        verse_id = int(request.form["verse_id"])
        sentence_classification_data = json.loads(
            request.form.get("sentence_classification_data", "[]")
        )
        objects_to_update = []
        try:
            # validate sentence_classification_data: List[Dict]
            # keys: boundary_id, label_id
            # values: strings? cast int()
            sentence_classification_data = {
                int(sentclf["boundary_id"]): int(sentclf["label_id"])
                for sentclf in sentence_classification_data
            }
        except Exception:
            api_response["success"] = False
            api_response["message"] = "Invalid data."
            api_response["style"] = "danger"
            return jsonify(api_response)

        existing_sentence_classification = SentenceClassification.query.filter(
            SentenceClassification.task_id == task_id,
            SentenceClassification.boundary.has(Boundary.verse_id == verse_id),
            SentenceClassification.annotator_id == annotator_id,
        ).all()
        existing_boundaries = {
            sentclf.boundary_id: sentclf.label_id
            for sentclf in existing_sentence_classification
        }

        for sentclf in existing_sentence_classification:
            if sentclf.boundary_id not in sentence_classification_data:
                # sentclf exists but was not submitted (i.e. removed)
                sentclf.is_deleted = True
                objects_to_update.append(sentclf)
            else:
                # sentclf exists and is submitted (i.e. retained)
                # check if there are any changes to the sentclf
                if any([
                    sentclf.label_id != sentence_classification_data[sentclf.boundary_id],
                    sentclf.is_deleted is True
                ]):
                    sentclf.label_id = sentence_classification_data[sentclf.boundary_id]
                    sentclf.is_deleted = False
                    objects_to_update.append(sentclf)

        for _boundary_id, _label_id in sentence_classification_data.items():
            if _boundary_id in existing_boundaries:
                # submitted sentclf already exists
                # "else" part of the previous condition block handles this
                # so we can skip here
                continue

            # submitted sentclf doesn't exist, create
            sentclf = SentenceClassification()
            sentclf.task_id = task_id
            sentclf.boundary_id = _boundary_id
            sentclf.label_id = _label_id
            sentclf.annotator_id = annotator_id
            sentclf.is_deleted = False
            objects_to_update.append(sentclf)

        try:
            if objects_to_update:
                db.session.bulk_save_objects(objects_to_update)
                db.session.commit()
                api_response["message"] = "Successfully updated!"
                api_response["style"] = "success"
            else:
                api_response["message"] = "No changes were submitted."
                api_response["style"] = "warning"

            record_submit(
                verse_id=verse_id,
                annotator_id=annotator_id,
                task_id=task_id
            )
            api_response["success"] = True
            api_response["next_task"] = next_task[task_id]
        except Exception as e:
            webapp.logger.exception(e)
            webapp.logger.info(request.form)
            api_response["success"] = False
            api_response["message"] = "Something went wrong!"
            api_response["style"] = "danger"

        api_response["data"] = None

        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == TASK_UPDATE_ACTIONS[TASK_SENTENCE_GRAPH]:
        annotator_id = current_user.id
        task_id = int(request.form["task_id"])
        verse_id = int(request.form["verse_id"])
        sentence_graph_data = json.loads(
            request.form.get("sentence_graph_data", "[]")
        )
        context_data = json.loads(
            request.form.get("context_data", "[]")
        )

        objects_to_update = []
        try:
            # validate sentence_graph_data: List[Dict]
            # keys:
            # src_boundary_id, src_token_id,
            # dst_boundary_id, dst_token_id
            # label_id, relation_type (0, 1, 2, 3)
            # values: strings? cast int()
            sentence_graph_data = {
                (
                    int(sentrel["src_boundary_id"]),
                    int(sentrel["src_token_id"]),
                    int(sentrel["dst_boundary_id"]),
                    int(sentrel["dst_token_id"]),
                    int(sentrel["relation_type"])
                ): {
                    k: int(v)
                    for k, v in sentrel.items()
                }
                for sentrel in sentence_graph_data
            }
            context_data = [int(boundary_id) for boundary_id in context_data]
        except Exception:
            api_response["success"] = False
            api_response["message"] = "Invalid data."
            api_response["style"] = "danger"
            return jsonify(api_response)

        # TODO: Re-examine if the conditions are proper
        existing_sentrels_query = SentenceGraph.query.filter(
            SentenceGraph.task_id == task_id,
            SentenceGraph.src_boundary_id.in_(context_data),
            SentenceGraph.dst_boundary_id.in_(context_data),
            SentenceGraph.annotator_id == annotator_id,
        )

        existing_sentrels = existing_sentrels_query.all()
        existing_sentrel_tuples = [
            (
                sentrel.src_boundary_id,
                sentrel.src_token_id,
                sentrel.dst_boundary_id,
                sentrel.dst_token_id,
                sentrel.relation_type
            )
            for sentrel in existing_sentrels
        ]

        for sentrel in existing_sentrels:
            sentrel_tuple = (
                sentrel.src_boundary_id,
                sentrel.src_token_id,
                sentrel.dst_boundary_id,
                sentrel.dst_token_id,
                sentrel.relation_type
            )
            if sentrel_tuple not in sentence_graph_data:
                # sentrel exists but was not submitted (i.e. removed)
                sentrel.is_deleted = True
                objects_to_update.append(sentrel)
            else:
                # TODO: Re-examine conditions in any()
                # i.e. conditions to decide whether sentrel should be updated

                # sentrel exists and is submitted (i.e. retained)
                # check if there are any changes to the sentrel
                if any([
                    sentrel.label_id != sentence_graph_data[sentrel_tuple]["label_id"],
                    sentrel.is_deleted is True
                ]):
                    sentrel.label_id = sentence_graph_data[sentrel_tuple]["label_id"]
                    sentrel.is_deleted = False
                    objects_to_update.append(sentrel)

        for sentrel_tuple, _sentrel_data in sentence_graph_data.items():
            if sentrel_tuple in existing_sentrel_tuples:
                # submitted sentrel already exists
                # "else" part of the previous condition block handles this
                # so we can skip here
                continue

            # submitted sentrel doesn't exist, create
            sentrel = SentenceGraph()
            sentrel.task_id = task_id
            sentrel.src_boundary_id = _sentrel_data["src_boundary_id"]
            sentrel.src_token_id = _sentrel_data["src_token_id"]
            sentrel.dst_boundary_id = _sentrel_data["dst_boundary_id"]
            sentrel.dst_token_id = _sentrel_data["dst_token_id"]
            sentrel.label_id = _sentrel_data["label_id"]
            sentrel.relation_type = _sentrel_data["relation_type"]
            sentrel.annotator_id = annotator_id
            sentrel.is_deleted = False
            objects_to_update.append(sentrel)

        try:
            if objects_to_update:
                db.session.bulk_save_objects(objects_to_update)
                db.session.commit()
                api_response["message"] = "Successfully updated!"
                api_response["style"] = "success"
            else:
                api_response["message"] = "No changes were submitted."
                api_response["style"] = "warning"

            record_submit(
                verse_id=verse_id,
                annotator_id=annotator_id,
                task_id=task_id
            )
            api_response["success"] = True
            api_response["next_task"] = next_task[task_id]
        except Exception as e:
            webapp.logger.exception(e)
            webapp.logger.info(request.form)
            api_response["success"] = False
            api_response["message"] = "Something went wrong!"
            api_response["style"] = "danger"

        api_response["data"] = None
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == "custom_action":
        api_response["data"] = None
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    return jsonify(api_response)


# --------------------------------------------------------------------------- #


@webapp.route("/api/chapter/<int:chapter_id>")
@auth_required()
def api_chapter(chapter_id):
    chapter = Chapter.query.get(chapter_id)
    if chapter is None:
        return jsonify({
            'title': 'Invalid Chapter ID',
            'data': []
        })

    data = get_chapter_data(chapter_id, current_user)

    response = {
        'title': f"{chapter.corpus.name} - {chapter.name}",
        'data': list(data.values())
    }
    return jsonify(response)

# --------------------------------------------------------------------------- #


@webapp.route("/api/verse/<int:verse_id>")
@auth_required()
def api_verse(verse_id):
    verse = Verse.query.get(verse_id)
    if verse is None:
        return jsonify({})

    annotator_ids = []
    if current_user.has_permission('annotate'):
        annotator_ids = [current_user.id]

    data = get_verse_data([verse_id], annotator_ids=annotator_ids)
    return jsonify(data)

# --------------------------------------------------------------------------- #

###############################################################################


@webapp.route("/action", methods=["POST"])
@auth_required()
def perform_action():
    status = False
    try:
        action = request.form['action']
    except KeyError:
        flash("Insufficient paremeters in request.")
        return redirect(request.referrer)

    # ----------------------------------------------------------------------- #
    # Admin Actions

    role_actions = {
        'owner': [
            'application_info', 'application_update', 'application_reload'
        ],
        'admin': [
            'user_role_add', 'user_role_remove',

            # Task Order/Status Update
            'task_update',
            'task_collection_update',

            # Add/Remove/Upload Labels

            # - Token Label
            'token_label_add',
            'token_label_remove',
            'token_label_upload',

            # - Token Graph Relation Label
            'token_relation_label_add',
            'token_relation_label_remove',
            'token_relation_label_upload',

            # - Sentence Label
            'sentence_label_add',
            'sentence_label_remove',
            'sentence_label_upload',

            # - Sentence Graph Relation Label
            'sentence_relation_label_add',
            'sentence_relation_label_remove',
            'sentence_relation_label_upload',

            # Data
            'corpus_add', 'chapter_add',

            # Export
            'annotation_download',
        ],
        'curator': [],
        'annotator': ['show_user_annotation'],
        'member': ['update_settings']
    }
    valid_actions = [
        action for actions in role_actions.values() for action in actions
    ]

    if action not in valid_actions:
        flash(f"Invalid action. ({action})")
        return redirect(request.referrer)

    for role, actions in role_actions.items():
        if action in actions and not current_user.has_role(role):
            flash("You are not authorized to perform that action.", "danger")
            return redirect(request.referrer)

    # ----------------------------------------------------------------------- #
    # Show Application Information

    if action in [
        'application_info', 'application_update', 'application_reload'
    ] and not app.pa_enabled:
        flash("PythonAnywhere configuration incomplete or missing.")
        return redirect(request.referrer)

    if action == 'application_info':
        info_url = app.pa_api_url + app.pa_api_actions['info']
        response = requests.get(info_url, headers=app.pa_headers)
        if response.status_code == 200:
            pretty_info = json.dumps(
                json.loads(response.content.decode()),
                indent=2
            )
            session['admin_result'] = pretty_info
        else:
            print(response.content.decode())
            flash("Something went wrong.")
        return redirect(request.referrer)

    # Perform git-pull
    if action == 'application_update':
        try:
            repo = git.cmd.Git(app.dir)
            result = repo.pull()
        except Exception as e:
            result = f'Error\n{e}'
        session['admin_result'] = result

        if result == 'Already up-to-date.':
            flash("Already up-to-date.")
        elif 'Updating' in result and 'changed,' in result:
            flash("Application code has been updated.", "success")
        else:
            flash("Something went wrong.")
        return redirect(request.referrer)

    # API App Reload
    if action == 'application_reload':
        reload_url = app.pa_api_url + app.api_actions['reload']
        response = requests.post(reload_url, headers=app.pa_headers)
        if response.status_code == 200:
            flash("Application has been reloaded.", "success")
            return Response("Success")
        else:
            print(response.content.decode())
            flash("Something went wrong.")
            return Response("Failure")

    # ----------------------------------------------------------------------- #
    # Manage User Role

    if action in ['user_role_add', 'user_role_remove']:
        target_user = request.form['target_user']
        target_role = request.form['target_role']
        target_action = action.split('_')[-1]

        _user = user_datastore.find_user(username=target_user)
        _role = user_datastore.find_role(target_role)

        user_level = max([role.level for role in current_user.roles])
        target_level = max([role.level for role in _user.roles])

        valid_update = True
        if _user == current_user:
            if _role.level == user_level:
                flash("You cannot modify your highest role.")
                valid_update = False
        else:
            if user_level <= target_level:
                flash(f"You cannot modify '{target_user}'.", "danger")
                valid_update = False

        if valid_update:
            if target_action == 'add':
                status = user_datastore.add_role_to_user(_user, _role)
                message = "Added role '{}' to user '{}'."
            if target_action == 'remove':
                status = user_datastore.remove_role_from_user(_user, _role)
                message = "Removed role '{}' from user '{}'."

            if status:
                db.session.commit()
                flash(message.format(target_role, target_user), "info")
            else:
                flash("No changes were made.")

        return redirect(request.referrer)

    # ----------------------------------------------------------------------- #
    # Task Update

    if action == 'task_update':
        task_id = request.form["task_id"]
        task_category = request.form["task_category"]
        task_title = request.form["task_title"]
        task_short = request.form["task_short"]
        task_help = request.form["task_help"]

        if task_id == "auto":
            task_count = Task.query.count()
            task = Task()
            task.category = task_category
            task.title = task_title
            task.short = task_short
            task.help = task_help
            task.order = task_count + 1
            message = f"New task added. (Category: '{task_category}')"
        else:
            task = Task.query.get(task_id)
            if task is None:
                message = f"Invalid task ID: {task_id}"
            else:
                task.title = task_title
                task.short = task_short
                task.help = task_help
                message = f"Task {task_id} updated."

        if task is not None:
            db.session.add(task)
            db.session.commit()
            flash(message, "success")
        else:
            flash(message)
        return redirect(request.referrer)

    if action == 'task_collection_update':
        tasks = Task.query.all()
        for task in tasks:
            task_active = request.form.get(f"task-{task.id}-status") == "on"
            task.is_deleted = not task_active
            task_order = request.form.get(f"task-{task.id}-order")
            if task_order:
                task.order = int(task_order)
        db.session.bulk_save_objects(tasks)
        db.session.commit()
        flash("Tasks updated!", "success")
        return redirect(request.referrer)

    # ----------------------------------------------------------------------- #
    # Ontology

    if action in [
            # - Token Label
            'token_label_add',
            'token_label_remove',
            'token_label_upload',

            # - Token Graph Relation Label
            'token_relation_label_add',
            'token_relation_label_remove',
            'token_relation_label_upload',

            # - Sentence Label
            'sentence_label_add',
            'sentence_label_remove',
            'sentence_label_upload',

            # - Sentence Graph Relation Label
            'sentence_relation_label_add',
            'sentence_relation_label_remove',
            'sentence_relation_label_upload',
    ]:
        action_parts = action.split('_label_')

        object_name = action_parts[0]
        target_action = action_parts[-1]

        MODELS = {
            'token': (TokenLabel, TokenClassification, 'label_id'),
            'token_relation': (TokenRelationLabel, TokenGraph, 'label_id'),
            'sentence': (SentenceLabel, SentenceClassification, 'label_id'),
            'sentence_relation': (
                SentenceRelationLabel, SentenceGraph, 'label_id'
            ),
        }
        _model, _annotation_model, _attribute = MODELS[object_name]
        _model_name = _model.__name__

        if target_action == 'add':
            _label_task_id = request.form[f'{object_name}_label_task_id']
            _label_text = request.form[f'{object_name}_label_text']
            _label_description = request.form[f'{object_name}_label_desc']

            _instance = _model.query.filter(
                _model.label == _label_text,
                _model.task_id == _label_task_id
            ).first()

            message = f"Added {_model_name} '{_label_text}'."
            if _instance is None:
                _instance = _model()
                _instance.task_id = _label_task_id
                _instance.label = _label_text
                _instance.description = _label_description
                _instance.is_deleted = False
                status = True
                db.session.add(_instance)
            else:
                if _instance.is_deleted:
                    _instance.is_deleted = False
                    status = True
                    db.session.add(_instance)
                else:
                    message = f"{_model_name} '{_label_text}' already exists."

        if target_action == 'remove':
            _label_text = request.form[f'{object_name}_label_text']
            message = f"{_model_name} '{_label_text}' does not exists."
            if _instance is not None and not _instance.is_deleted:
                objects_with_given_label = _annotation_model.query.filter(
                    getattr(_annotation_model, _attribute) == _instance.id,
                    _annotation_model.is_deleted == False  # noqa
                ).all()
                if objects_with_given_label:
                    f"{_model_name} '{_label_text}' is used in annotation."
                else:
                    _instance.is_deleted = True
                    db.session.add(_instance)
                    status = True
                    message = f"Removed {_model_name} '{_label_text}'."

        if target_action == 'upload':
            # Labels
            # NOTE: Refer to `data/tables/README.md` for format of JSON and CSV
            _label_task_id = int(request.form[f'{object_name}_label_task_id'])
            _label_file = request.files['label_file']
            _upload_format = request.files['upload_format']

            _existing_labels = {
                (_instance.task_id, _instance.label): _instance
                for _instance in _model.query.all()
            }

            if _upload_format == "json":
                with open(_label_file, encoding="utf-8") as f:
                    table_data = json.load(f)
            elif _upload_format == "csv":
                with open(_label_file, encoding="utf-8") as f:
                    table_data = list(csv.DictReader(f))

            _add_count = 0
            _undelete_count = 0
            _ignore_count = 0
            objects_to_update = []
            for idx, label in enumerate(table_data, start=1):
                _label_identifier = (_label_task_id, label["label"])
                if _label_identifier in _existing_labels:
                    _instance = _existing_labels[_label_identifier]
                    if _instance.is_deleted:
                        _instance.is_deleted = False
                        _undelete_count += 1
                        objects_to_update.append(_instance)
                    else:
                        _ignore_count += 1
                else:
                    _instance = _model()
                    _instance.task_id = _label_task_id
                    _instance.label = label["label"]
                    _instance.description = label["description"]
                    _add_count += 1
                    objects_to_update.append(_instance)

                if objects_to_update:
                    db.session.bulk_save_objects(objects_to_update)
                    status = True
                    _total = _add_count + _undelete_count
                    message = (
                        f"Added {_total} {_model_name}s. "
                        f"({_add_count} + {_undelete_count})"
                    )
                else:
                    message = f"No new {_model_name}s were added."

        if status:
            db.session.commit()
            flash(message, "info")
        else:
            flash(message)
        return redirect(request.referrer)

    # ----------------------------------------------------------------------- #
    # Corpus Add

    if action in ['corpus_add']:
        corpus_name = request.form['corpus_name']
        corpus_description = request.form['corpus_description']
        try:
            corpus = Corpus()
            corpus.name = corpus_name
            corpus.description = corpus_description
            db.session.add(corpus)
            db.session.commit()
            flash((f"Created corpus '{corpus_name}' successfully."
                   f" (ID: {corpus.id})"), "success")
        except Exception:
            flash("Something went wrong during corpus creation.")
        return redirect(request.referrer)

    if action in ['chapter_add']:
        if 'chapter_file' not in request.files:
            flash("No file part found.")
            return redirect(request.referrer)

        corpus_id = request.form['corpus_id']
        chapter_name = request.form['chapter_name']
        chapter_description = request.form['chapter_description']
        chapter_file = request.files['chapter_file']
        chapter_filename = chapter_file.filename

        if chapter_filename == '':
            flash("No file selected.")
            return redirect(request.referrer)

        # Validity
        allowed_extensions = {'conllu', 'txt'}
        file_extension = chapter_filename.rsplit('.', 1)[1].lower()
        is_valid_filename = (file_extension in allowed_extensions)

        if chapter_file and is_valid_filename:
            corpus_query = Corpus.query.filter(Corpus.id == corpus_id)
            corpus = corpus_query.first()
            if corpus is None:
                flash("No corpus selected.")
                return redirect(request.referrer)

            # NOTE: "processing" which should give data as
            # [[{}, {}, {}, ...], [{}, {}, {}, ...], ...]
            # data: list of verses
            # verse: list of lines
            # line: dict (id, verse_id, text, tokens)
            # should have metadata, text, sent_id, sent_counter

            # tokens: list of dict
            # token: dict 10 CoNLL-U mandatory fields
            # in particular,
            # "id", "form", "lemma", "upos", "xpos", "feats", "misc"
            # function should take file and produce such output
            # `CORPUS.read_conllu_data` formats it in this format

            try:
                chapter_data = CONLLU_PARSER.read_conllu_data(
                    chapter_file.read().decode()
                )
            except Exception as e:
                webapp.logger.exception(e)
                flash("Invalid file format.")
                return redirect(request.referrer)

            # --------------------------------------------------------------- #
            # Insert Data

            result = add_chapter(
                corpus_id=corpus.id,
                chapter_name=chapter_name,
                chapter_description=chapter_description,
                chapter_data=chapter_data
            )
            flash(result["message"], result["style"])

            # --------------------------------------------------------------- #
        else:
            flash("Invalid file or file extension.")

        return redirect(request.referrer)

    if action == 'annotation_download':
        flash("Work in progress")
        print(request.form)
        return redirect(request.referrer)


    # ----------------------------------------------------------------------- #
    # Update Settings

    if action == 'update_settings':
        display_name = request.form['display_name']
        theme = request.form['theme']

        settings = {
            'display_name': display_name,
            'theme': theme
        }
        current_user.settings = settings
        db.session.commit()
        return redirect(request.referrer)

    # ----------------------------------------------------------------------- #
    # Annotator Actions

    # ----------------------------------------------------------------------- #
    # Action Template

    if action == 'custom_action':
        # action code
        status = True  # action_result
        if status:
            flash("Action completed successfully.", "success")

    # ----------------------------------------------------------------------- #

    if not status:
        flash("Action failed.", "danger")

    return redirect(request.referrer)

###############################################################################


if __name__ == '__main__':
    import argparse
    import socket

    hostname = socket.gethostname()
    default_host = socket.gethostbyname(hostname)
    default_port = '5000'

    parser = argparse.ArgumentParser(description="Antarlekhaka Server")
    parser.add_argument("-H", "--host", help="Hostname", default=default_host)
    parser.add_argument("-P", "--port", help="Port", default=default_port)
    args = vars(parser.parse_args())

    host = args["host"]
    port = args["port"]

    webapp.run(host=host, port=port, debug=True)
