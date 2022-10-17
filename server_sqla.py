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
__copyright__ = "Copyright (C) 2020-2021 Hrishikesh Terdalkar"
__version__ = "1.0"

###############################################################################

import os
import re
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

from models_sqla import (db, user_datastore,
                         CustomLoginForm, CustomRegisterForm,
                         Corpus, Chapter, Verse, Line, Token,
                         Task, Progress, Anvaya, Boundary,
                         EntityLabel, Entity,
                         RelationLabel, TokenGraph,
                         Coreference,
                         SentenceLabel, SentenceClassification,
                         DiscourseLabel, DiscourseGraph)
from settings import app

from utils.reverseproxied import ReverseProxied
from utils.database import export_data, get_verse_data, get_chapter_data
from utils.conllu import DigitalCorpusSanskrit

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
# DCS CoNLL-U Utility

DCS = DigitalCorpusSanskrit()

###############################################################################
# Database Utlity Functions


def update_progress(verse_id: int, annotator_id: int, task_id: int):
    """Update Progress

    Parameters
    ----------
    verse_id : int
        Verse ID
    annotator_id : int
        Annotator ID
    task_id : int
        Task ID
    """
    progress_query = Progress.query.filter(
        Progress.verse_id == verse_id,
        Progress.annotator_id == annotator_id,
        Progress.task_id == task_id
    )
    progress = progress_query.one_or_none()
    if progress is None:
        progress = Progress()
        progress.verse_id = verse_id
        progress.annotator_id = annotator_id
        progress.task_id = task_id

    # TODO: Is there a better way than manually triggering this?
    progress.updated_at = datetime.datetime.utcnow()

    db.session.add(progress)
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
    if not Task.query.first():
        task_data_file = os.path.join(app.tables_dir, "task.json")
        with open(task_data_file, encoding="utf-8") as f:
            tasks_data = json.load(f)

        for idx, task in enumerate(tasks_data, start=1):
            t = Task()
            t.id = task["id"]
            t.name = task["name"]
            t.title = task["title"]
            t.short = task["short"]
            t.help = task["help"]
            t.order = idx
            objects.append(t)

        webapp.logger.info(f"Loaded {idx} tasks.")

    # Labels
    label_models = [EntityLabel, RelationLabel, SentenceLabel, DiscourseLabel]
    for label_model in label_models:
        if not label_model.query.first():
            table_name = label_model.__tablename__
            table_data_file = os.path.join(
                app.tables_dir, f"{table_name}.json"
            )
            with open(table_data_file, encoding="utf-8") as f:
                table_data = json.load(f)

            for idx, label in enumerate(table_data, start=1):
                lm = label_model()
                lm.label = label["label"]
                lm.description = label["description"]
                objects.append(lm)

            webapp.logger.info(f"Loaded {idx} {table_name}s.")

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
def inject_global_constants():
    theme_files = glob.glob(
        os.path.join(app.dir, 'static', 'themes', 'css', 'bootstrap.*.min.css')
    )
    theme_js_files = glob.glob(
        os.path.join(app.dir, 'static', 'themes', 'js', 'bootstrap.*.min.js')
    )
    themes = ['default'] + sorted([os.path.basename(theme).split('.')[1]
                                   for theme in theme_files])
    themes_js = sorted([os.path.basename(theme).split('.')[1]
                        for theme in theme_js_files])

    CONSTANTS = {
        'entity_labels': EntityLabel.query.filter(
            EntityLabel.is_deleted == False  # noqa # '== False' is required
        ).with_entities(
            EntityLabel.id, EntityLabel.label, EntityLabel.description
        ).order_by(EntityLabel.label).all(),
        # 'entity_labels': [
        #     ("CHAR", "Character"),
        #     ("ORG", "Organization"),
        #     ("LOC", "Location"),
        #     ("GPE", "Geo-Political Entity"),
        #     ("TIME", "Time"),
        #     ("NUM", "Numeric"),
        #     ("CURR", "Currency"),
        # ]
        'relation_labels': RelationLabel.query.filter(
            RelationLabel.is_deleted == False  # noqa # '== False' is required
        ).with_entities(
            RelationLabel.id, RelationLabel.label, RelationLabel.description
        ).order_by(RelationLabel.label).all(),
        # 'task_labels': Label.query.filter(
        #     ActionLabel.is_deleted == False  # noqa # '== False' is required
        # ).with_entities(
        #     Label.id, Label.task_id, Label.label, Label.description
        # ).order_by(Label.task_id, Label.label).all(),
        'tasks': [
            {
                "id": task.id,
                "name": task.name,
                "title": task.title,
                "short": task.short,
                "help": task.help,
                "order": task.order
            }
            for task in Task.query.filter(
                Task.is_deleted == False  # noqa # '== False' is required
            ).order_by(Task.order).all()
        ],
        'sentence_labels': SentenceLabel.query.filter(
            SentenceLabel.is_deleted == False  # noqa # '== False' is required
        ).with_entities(
            SentenceLabel.id, SentenceLabel.label, SentenceLabel.description
        ).order_by(SentenceLabel.label).all(),
        'discourse_labels': DiscourseLabel.query.filter(
            DiscourseLabel.is_deleted == False  # noqa # '== False' is required
        ).with_entities(
            DiscourseLabel.id, DiscourseLabel.label, DiscourseLabel.description
        ).order_by(DiscourseLabel.label).all(),
        'admin_labels': [
            {
                "name": "entity",
                "title": "Entity",
                "is_active": True,
                "object_name": "entity_labels"
            },
            {
                "name": "relation",
                "title": "Relation",
                "is_active": False,
                "object_name": "relation_labels"
            },
            {
                "name": "sentence",
                "title": "Sentence",
                "is_active": False,
                "object_name": "sentence_labels"
            },
            {
                "name": "discourse",
                "title": "Discourse",
                "is_active": False,
                "object_name": "discourse_labels"
            },
        ]
    }
    return {
        'title': app.title,
        'now': datetime.datetime.utcnow(),
        'constants': CONSTANTS,
        'themes': themes,
        'themes_js': themes_js,
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

    data['users'] = [
        {
            "id": user.id,
            "username": user.username
        }
        for user in user_query.all()
    ]
    data['annotators'] = [
        {
            "id": user.id,
            "username": user.username
        }
        for user in user_query.all()
        if annotator_role in user.roles
    ]
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
def show_export():
    data = {}
    data['title'] = 'Export'
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
    data['tasks'] = [
        {
            "id": task.id,
            "name": task.name,
            "title": task.title,
            "short": task.short,
            "help": task.help,
            "order": task.order
        }
        for task in Task.query.filter(
            Task.is_deleted == False  # noqa # '== False' is required
        ).order_by(Task.order).all()
    ]

    if request.method == "POST":
        annotator_id = current_user.id
        chapter_ids = request.form.getlist('chapter_id')
        annotation_data = export_data(
            annotator_ids=[annotator_id],
            chapter_ids=chapter_ids,
            task_ids=[],
            output_format="simple"
        )
        annotation_result = {
            k[0]: v
            for k, v in annotation_data["visual"].items()
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

    role_actions = {
        "admin": [],
        "annotator": [
            "update_sentence_boundary",
            "add_token",
            "update_anvaya",
            "update_named_entity",
            "update_token_graph",
            "update_coreference",
            "update_sentence_classification",
            "update_intersentence_connection",
        ],
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

    task_actions = []
    next_task = {}
    task_query = Task.query.filter(
        Task.is_deleted == False  # noqa # '== False' is required
    ).order_by(Task.order)

    _first_task = None
    _task = None

    for task in task_query.all():
        task_actions.append(f"update_{task.name}")
        if _first_task is None:
            _task = task.name
            _first_task = _task
        else:
            next_task[_task] = task.name
            _task = task.name

    next_task[_task] = _first_task

    if action in task_actions:
        api_response["first_task"] = _first_task

    # ----------------------------------------------------------------------- #

    api_response["success"] = True
    api_response["message"] = "Under construction."
    api_response["style"] = "warning"

    # ----------------------------------------------------------------------- #

    if action == "update_sentence_boundary":
        task_name = action.replace("update_", "")
        task_id = Task.query.filter(Task.name == task_name).first().id

        verse_id = int(request.form["verse_id"])
        annotator_id = current_user.id
        boundary_tokens = [
            int(b.strip())
            for b in request.form["boundaries"].split(",")
            if b.strip()
        ]

        perform_update = False
        objects_to_update = []
        # If there's any change between existing tokens and marked tokens,
        # delete  all existing boundary tokens from this verse
        # Anvaya also gets deleted as (CASCADE)
        # Entity also gets deleted as (CASCADE)
        # TokenGraph also gets deleted as (CASCADE)
        # Coreference also gets deleted as (CASCADE)
        # SentenceClassification also gets deleted as (CASCADE)
        # DiscourseGraph also gets deleted as (CASCADE)

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

            if next_boundary:
                anvaya_of_next_boundary_query = Anvaya.query.filter(
                    Anvaya.boundary_id == next_boundary.id,
                    Anvaya.annotator_id == annotator_id
                )
                anvaya_of_next_boundary_query.delete(synchronize_session=False)

            # add new boundary markers
            for boundary_token in boundary_tokens:
                boundary = Boundary()
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

            update_progress(
                verse_id=verse_id,
                annotator_id=annotator_id,
                task_id=task_id
            )
            api_response["success"] = True
            api_response["next_task"] = next_task[task_name]
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
        verse_id = int(request.form["verse_id"])
        annotator_id = current_user.id
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

    if action == "update_anvaya":
        task_name = action.replace("update_", "")
        task_id = Task.query.filter(Task.name == task_name).first().id

        verse_id = int(request.form["verse_id"])
        annotator_id = current_user.id
        anvaya = json.loads(request.form["anvaya"])

        anvaya_order = {}
        boundary_ids = []

        for dom_boundary_id, dom_token_ids in anvaya.items():
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
            anvaya_order[boundary_id] = _order

        objects_to_update = []

        existing_anvaya_query = Anvaya.query.filter(
            Anvaya.boundary_id.in_(boundary_ids),
            Anvaya.annotator_id == annotator_id
        )
        existing_anvaya_query.delete(synchronize_session=False)

        for boundary_id, token_ids in anvaya_order.items():
            for order_id, token_id in enumerate(token_ids, start=1):
                anvaya = Anvaya()
                anvaya.boundary_id = boundary_id
                anvaya.token_id = token_id
                anvaya.order = order_id
                anvaya.annotator_id = annotator_id
                objects_to_update.append(anvaya)

        try:
            if objects_to_update:
                db.session.bulk_save_objects(objects_to_update)
                db.session.commit()
                api_response["message"] = "Successfully updated!"
                api_response["style"] = "success"
            else:
                api_response["message"] = "No changes were submitted."
                api_response["style"] = "warning"

            update_progress(
                verse_id=verse_id,
                annotator_id=annotator_id,
                task_id=task_id
            )
            api_response["success"] = True
            api_response["next_task"] = next_task[task_name]
        except Exception as e:
            webapp.logger.exception(e)
            webapp.logger.info(request.form)
            api_response["success"] = False
            api_response["message"] = "Something went wrong!"
            api_response["style"] = "danger"

        api_response["data"] = None
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == "update_named_entity":
        task_name = action.replace("update_", "")
        task_id = Task.query.filter(Task.name == task_name).first().id

        verse_id = int(request.form["verse_id"])
        annotator_id = current_user.id
        entity_data = json.loads(request.form["entity_data"])

        objects_to_update = []
        try:
            entity_data = {
                int(k.split('-')[-1]): {
                    "boundary_id": int(v["boundary_id"]),
                    "label_id": int(v["label_id"])
                }
                for k, v in entity_data.items()
                if re.match(r'entity-selector-([0-9]+)$', k)
            }
        except Exception:
            api_response["success"] = False
            api_response["message"] = "Invalid data."
            api_response["style"] = "danger"
            return jsonify(api_response)

        existing_entities = Entity.query.filter(
            Entity.boundary.has(Boundary.verse_id == verse_id),
            Entity.annotator_id == annotator_id,
        ).all()
        existing_entity_token_ids = [
            entity.token_id
            for entity in existing_entities
        ]
        for entity in existing_entities:
            if entity.token_id not in entity_data:
                # entity exists but was not submitted (i.e. removed)
                # TODO: This triggers on the deleted entities always
                # Perhaps we need to add a check
                # That should avoid "Successfully updated" message even when
                # there are no updates
                entity.is_deleted = True
                objects_to_update.append(entity)
            else:
                # entity exists and is submitted (i.e. retained)
                # check if there are any changes to the entity
                token_id = entity.token_id
                if any([
                    entity.label_id != entity_data[token_id]["label_id"],
                    entity.boundary_id != entity_data[token_id]["boundary_id"],
                    entity.is_deleted is True
                ]):
                    entity.label_id = entity_data[token_id]["label_id"]
                    entity.boundary_id = entity_data[token_id]["boundary_id"]
                    entity.is_deleted = False
                    objects_to_update.append(entity)

        for token_id, _entity_data in entity_data.items():
            if token_id in existing_entity_token_ids:
                # submitted entity already exists
                # "else" part of the previous condition block handles this
                # so we can skip here
                continue

            # submitted entity doesn't exist, create
            entity = Entity()
            entity.boundary_id = _entity_data["boundary_id"]
            entity.token_id = token_id
            entity.label_id = _entity_data["label_id"]
            entity.annotator_id = annotator_id
            entity.is_deleted = False
            objects_to_update.append(entity)

        try:
            if objects_to_update:
                db.session.bulk_save_objects(objects_to_update)
                db.session.commit()
                api_response["message"] = "Successfully updated!"
                api_response["style"] = "success"
            else:
                api_response["message"] = "No changes were submitted."
                api_response["style"] = "warning"

            update_progress(
                verse_id=verse_id,
                annotator_id=annotator_id,
                task_id=task_id
            )
            api_response["success"] = True
            api_response["next_task"] = next_task[task_name]
        except Exception as e:
            webapp.logger.exception(e)
            webapp.logger.info(request.form)
            api_response["success"] = False
            api_response["message"] = "Something went wrong!"
            api_response["style"] = "danger"

        api_response["data"] = None
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == "update_token_graph":
        task_name = action.replace("update_", "")
        task_id = Task.query.filter(Task.name == task_name).first().id

        verse_id = int(request.form["verse_id"])
        annotator_id = current_user.id
        graph_data = json.loads(request.form.get("graph_data", "[]"))

        objects_to_update = []
        try:
            # validate graph_data: List[Dict]
            # keys: boundary_id, src_id, label_id, dst_id
            # values: strings? cast int()
            graph_data = {
                (
                    int(rel["src_id"]),
                    int(rel["label_id"]),
                    int(rel["dst_id"])
                ): {
                    k: int(v)
                    for k, v in rel.items()
                }
                for rel in graph_data
            }
        except Exception:
            api_response["success"] = False
            api_response["message"] = "Invalid data."
            api_response["style"] = "danger"
            return jsonify(api_response)

        existing_relations_query = TokenGraph.query.filter(
            TokenGraph.boundary.has(Boundary.verse_id == verse_id),
            TokenGraph.annotator_id == annotator_id,
        )

        existing_relations = existing_relations_query.all()
        existing_relation_tuples = [
            (relation.src_id, relation.label_id, relation.dst_id)
            for relation in existing_relations_query.all()
        ]

        for relation in existing_relations:
            rel_tuple = (relation.src_id, relation.label_id, relation.dst_id)
            if rel_tuple not in graph_data:
                # relation exists but was not submitted (i.e. removed)
                relation.is_deleted = True
                objects_to_update.append(relation)
            else:
                # relation exists and is submitted (i.e. retained)
                # check if there are any changes to the relation
                if any([
                    relation.boundary_id != graph_data[rel_tuple]["boundary_id"],
                    relation.is_deleted is True
                ]):
                    relation.boundary_id = graph_data[rel_tuple]["boundary_id"]
                    relation.is_deleted = False
                    objects_to_update.append(relation)

        for rel_tuple, _relation_data in graph_data.items():
            if rel_tuple in existing_relation_tuples:
                # submitted relation already exists
                # "else" part of the previous condition block handles this
                # so we can skip here
                continue

            # submitted relation doesn't exist, create
            relation = TokenGraph()
            relation.boundary_id = _relation_data["boundary_id"]
            relation.src_id = _relation_data["src_id"]
            relation.label_id = _relation_data["label_id"]
            relation.dst_id = _relation_data["dst_id"]
            relation.annotator_id = annotator_id
            relation.is_deleted = False
            objects_to_update.append(relation)

        try:
            if objects_to_update:
                db.session.bulk_save_objects(objects_to_update)
                db.session.commit()
                api_response["message"] = "Successfully updated!"
                api_response["style"] = "success"
            else:
                api_response["message"] = "No changes were submitted."
                api_response["style"] = "warning"

            update_progress(
                verse_id=verse_id,
                annotator_id=annotator_id,
                task_id=task_id
            )
            api_response["success"] = True
            api_response["next_task"] = next_task[task_name]
        except Exception as e:
            webapp.logger.exception(e)
            webapp.logger.info(request.form)
            api_response["success"] = False
            api_response["message"] = "Something went wrong!"
            api_response["style"] = "danger"

        api_response["data"] = None
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == "update_coreference":
        task_name = action.replace("update_", "")
        task_id = Task.query.filter(Task.name == task_name).first().id

        verse_id = int(request.form["verse_id"])
        annotator_id = current_user.id
        coref_data = json.loads(
            request.form.get("coreference_data", "[]")
        )
        context_data = json.loads(
            request.form.get("context_data", "[]")
        )

        objects_to_update = []
        try:
            # validate coreference_data: List[Dict]
            # keys: boundary_id, src_id, dst_id
            # values: strings? cast int()
            coref_data = {
                (
                    int(coref["src_id"]),
                    int(coref["dst_id"])
                ): {
                    k: int(v)
                    for k, v in coref.items()
                }
                for coref in coref_data
            }
            context_data = [int(boundary_id) for boundary_id in context_data]
        except Exception:
            api_response["success"] = False
            api_response["message"] = "Invalid data."
            api_response["style"] = "danger"
            return jsonify(api_response)

        existing_corefs_query = Coreference.query.filter(
            Coreference.boundary_id.in_(context_data),
            Coreference.annotator_id == annotator_id,
        )

        existing_corefs = existing_corefs_query.all()
        existing_coref_tuples = [
            (coref.src_id, coref.dst_id)
            for coref in existing_corefs
        ]

        for coref in existing_corefs:
            coref_tuple = (coref.src_id, coref.dst_id)
            if coref_tuple not in coref_data:
                # coref exists but was not submitted (i.e. removed)
                coref.is_deleted = True
                objects_to_update.append(coref)
            else:
                # TODO: do we really need to check boundary_id?
                # when would it be different when src_id and dst_id are same?
                # only if we change convention?

                # coref exists and is submitted (i.e. retained)
                # check if there are any changes to the coref
                if any([
                    coref.boundary_id != coref_data[coref_tuple]["boundary_id"],
                    coref.is_deleted is True
                ]):
                    coref.boundary_id = coref_data[coref_tuple]["boundary_id"]
                    coref.is_deleted = False
                    objects_to_update.append(coref)

        for coref_tuple, _coref_data in coref_data.items():
            if coref_tuple in existing_coref_tuples:
                # submitted coref already exists
                # "else" part of the previous condition block handles this
                # so we can skip here
                continue

            # submitted coref doesn't exist, create
            coref = Coreference()
            coref.boundary_id = _coref_data["boundary_id"]
            coref.src_id = _coref_data["src_id"]
            coref.dst_id = _coref_data["dst_id"]
            coref.annotator_id = annotator_id
            coref.is_deleted = False
            objects_to_update.append(coref)

        try:
            if objects_to_update:
                db.session.bulk_save_objects(objects_to_update)
                db.session.commit()
                api_response["message"] = "Successfully updated!"
                api_response["style"] = "success"
            else:
                api_response["message"] = "No changes were submitted."
                api_response["style"] = "warning"

            update_progress(
                verse_id=verse_id,
                annotator_id=annotator_id,
                task_id=task_id
            )
            api_response["success"] = True
            api_response["next_task"] = next_task[task_name]
        except Exception as e:
            webapp.logger.exception(e)
            webapp.logger.info(request.form)
            api_response["success"] = False
            api_response["message"] = "Something went wrong!"
            api_response["style"] = "danger"

        api_response["data"] = None
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == "update_sentence_classification":
        task_name = action.replace("update_", "")
        task_id = Task.query.filter(Task.name == task_name).first().id

        verse_id = int(request.form["verse_id"])
        annotator_id = current_user.id
        classification_data = json.loads(
            request.form.get("classification_data", "[]")
        )
        objects_to_update = []
        try:
            # validate classification_data: List[Dict]
            # keys: boundary_id, label_id
            # values: strings? cast int()
            classification_data = {
                int(sentclf["boundary_id"]): int(sentclf["label_id"])
                for sentclf in classification_data
            }
        except Exception:
            api_response["success"] = False
            api_response["message"] = "Invalid data."
            api_response["style"] = "danger"
            return jsonify(api_response)

        existing_classification_query = SentenceClassification.query.filter(
            SentenceClassification.boundary.has(Boundary.verse_id == verse_id),
            SentenceClassification.annotator_id == annotator_id,
        )

        existing_classification = existing_classification_query.all()
        existing_boundaries = {
            sentclf.boundary_id: sentclf.label_id
            for sentclf in existing_classification_query.all()
        }

        for sentclf in existing_classification:
            if sentclf.boundary_id not in classification_data:
                # sentclf exists but was not submitted (i.e. removed)
                sentclf.is_deleted = True
                objects_to_update.append(sentclf)
            else:
                # sentclf exists and is submitted (i.e. retained)
                # check if there are any changes to the sentclf
                if any([
                    sentclf.label_id != classification_data[sentclf.boundary_id],
                    sentclf.is_deleted is True
                ]):
                    sentclf.label_id = classification_data[sentclf.boundary_id]
                    sentclf.is_deleted = False
                    objects_to_update.append(sentclf)

        for _boundary_id, _label_id in classification_data.items():
            if _boundary_id in existing_boundaries:
                # submitted sentclf already exists
                # "else" part of the previous condition block handles this
                # so we can skip here
                continue

            # submitted sentclf doesn't exist, create
            sentclf = SentenceClassification()
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

            update_progress(
                verse_id=verse_id,
                annotator_id=annotator_id,
                task_id=task_id
            )
            api_response["success"] = True
            api_response["next_task"] = next_task[task_name]
        except Exception as e:
            webapp.logger.exception(e)
            webapp.logger.info(request.form)
            api_response["success"] = False
            api_response["message"] = "Something went wrong!"
            api_response["style"] = "danger"

        api_response["data"] = None

        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == "update_intersentence_connection":
        task_name = action.replace("update_", "")
        task_id = Task.query.filter(Task.name == task_name).first().id

        verse_id = int(request.form["verse_id"])
        annotator_id = current_user.id
        intersentence_connection_data = json.loads(
            request.form.get("intersentence_connection_data", "[]")
        )
        context_data = json.loads(
            request.form.get("context_data", "[]")
        )
        objects_to_update = []
        try:
            # validate intersentence_connection_data: List[Dict]
            # keys:
            # src_boundary_id, src_token_id,
            # dst_boundary_id, dst_token_id
            # label_id, relation_type (0, 1, 2, 3)
            # values: strings? cast int()
            intersentence_connection_data = {
                (
                    int(isc["src_boundary_id"]),
                    int(isc["src_token_id"]),
                    int(isc["dst_boundary_id"]),
                    int(isc["dst_token_id"]),
                    int(isc["relation_type"])
                ): {
                    k: int(v)
                    for k, v in isc.items()
                }
                for isc in intersentence_connection_data
            }
            context_data = [int(boundary_id) for boundary_id in context_data]
        except Exception:
            api_response["success"] = False
            api_response["message"] = "Invalid data."
            api_response["style"] = "danger"
            return jsonify(api_response)

        # TODO: Re-examine if the conditions are proper
        existing_iscs_query = DiscourseGraph.query.filter(
            DiscourseGraph.src_boundary_id.in_(context_data),
            DiscourseGraph.dst_boundary_id.in_(context_data),
            DiscourseGraph.annotator_id == annotator_id,
        )

        existing_iscs = existing_iscs_query.all()
        existing_isc_tuples = [
            (
                isc.src_boundary_id,
                isc.src_token_id,
                isc.dst_boundary_id,
                isc.dst_token_id,
                isc.relation_type
            )
            for isc in existing_iscs
        ]

        for isc in existing_iscs:
            isc_tuple = (
                isc.src_boundary_id,
                isc.src_token_id,
                isc.dst_boundary_id,
                isc.dst_token_id,
                isc.relation_type
            )
            if isc_tuple not in intersentence_connection_data:
                # isc exists but was not submitted (i.e. removed)
                isc.is_deleted = True
                objects_to_update.append(isc)
            else:
                # TODO: Re-examine conditions in any()
                # i.e. conditions to decide whether isc should be updated

                # isc exists and is submitted (i.e. retained)
                # check if there are any changes to the isc
                if any([
                    isc.label_id != intersentence_connection_data[isc_tuple]["label_id"],
                    isc.is_deleted is True
                ]):
                    isc.label_id = intersentence_connection_data[isc_tuple]["label_id"]
                    isc.is_deleted = False
                    objects_to_update.append(isc)

        for isc_tuple, _isc_data in intersentence_connection_data.items():
            if isc_tuple in existing_isc_tuples:
                # submitted isc already exists
                # "else" part of the previous condition block handles this
                # so we can skip here
                continue

            # submitted isc doesn't exist, create
            isc = DiscourseGraph()
            isc.src_boundary_id = _isc_data["src_boundary_id"]
            isc.src_token_id = _isc_data["src_token_id"]
            isc.dst_boundary_id = _isc_data["dst_boundary_id"]
            isc.dst_token_id = _isc_data["dst_token_id"]
            isc.label_id = _isc_data["label_id"]
            isc.relation_type = _isc_data["relation_type"]
            isc.annotator_id = annotator_id
            isc.is_deleted = False
            objects_to_update.append(isc)

        try:
            if objects_to_update:
                db.session.bulk_save_objects(objects_to_update)
                db.session.commit()
                api_response["message"] = "Successfully updated!"
                api_response["style"] = "success"
            else:
                api_response["message"] = "No changes were submitted."
                api_response["style"] = "warning"

            update_progress(
                verse_id=verse_id,
                annotator_id=annotator_id,
                task_id=task_id
            )
            api_response["success"] = True
            api_response["next_task"] = next_task[task_name]
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
def action():
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

            # Add/Remove Labels

            # - Named Entity Type
            'entity_type_add', 'entity_type_remove',

            # - Token Graph Relation Type
            'relation_type_add', 'relation_type_remove',

            # - Sentence Type
            'sentence_type_add', 'sentence_type_remove',

            # - Discourse Relation Type
            'discourse_type_add', 'discourse_type_remove',

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
    # Ontology

    if action in [
        'entity_type_add', 'entity_type_remove',
        'relation_type_add', 'relation_type_remove',
        'sentence_type_add', 'sentence_type_remove',
        'discourse_type_add', 'discourse_type_remove',
    ]:
        action_parts = action.split('_')

        object_name = action_parts[0]
        target_action = action_parts[-1]

        object_label = request.form[f'{object_name}_label_text']
        object_label_desc = request.form.get(f'{object_name}_label_desc')

        MODELS = {
            'entity': (EntityLabel, Entity, 'label_id'),
            'relation': (RelationLabel, TokenGraph, 'label_id'),
            'sentence': (SentenceLabel, SentenceClassification, 'label_id'),
            'discourse': (DiscourseLabel, DiscourseGraph, 'label_id'),
        }
        (
            _object_model, _annotation, _annotation_attribute
        ) = MODELS[object_name]
        _object_label = _object_model.query.filter(
            _object_model.label == object_label
        ).first()

        if target_action == 'add':
            message = f"Added {object_name.title()} label '{object_label}'."
            if _object_label is None:
                _object_label = _object_model()
                _object_label.label = object_label
                _object_label.description = object_label_desc
                _object_label.is_deleted = False
                status = True
                db.session.add(_object_label)
            else:
                if _object_label.is_deleted:
                    _object_label.is_deleted = False
                    status = True
                    db.session.add(_object_label)
                else:
                    message = f"{object_name.title()} label '{object_label}' already exists."

        if target_action == 'remove':
            message = f"{object_name.title()} label '{object_label}' does not exist."
            if _object_label is not None and not _object_label.is_deleted:
                objects_with_given_label = _annotation.query.filter(
                    getattr(
                        _annotation, _annotation_attribute
                    ) == _object_label.id,
                    _annotation.is_deleted == False  # noqa
                ).all()
                if objects_with_given_label:
                    message = f"{object_name.title()} label '{object_label}' is being used in annotations."
                else:
                    _object_label.is_deleted = True
                    db.session.add(_object_label)
                    status = True
                    message = f"Removed {object_name} label '{object_label}'."

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
            # [[[], [], [], ...], [[], [], [], ...], ...]
            # data: list of verses
            # verse: list of lines
            # line: dict (id, verse_id, text, tokens)
            # should have metadata, text, line_id, chapter_verse_id

            # tokens: list of dict
            # token: dict 10 CoNLL-U mandatory fields
            # in particular,
            # "id", "form", "lemma", "upos", "xpos", "feats", "misc"
            # function should take file and produce such output

            try:
                verses = DCS.read_conllu_data(chapter_file.read().decode())
            except Exception as e:
                webapp.logger.exception(e)
                flash("Invalid file format.")
                return redirect(request.referrer)

            # --------------------------------------------------------------- #
            # Insert Data
            try:
                chapter = Chapter()
                chapter.corpus_id = corpus.id
                chapter.name = chapter_name
                chapter.description = chapter_description

                for _verse in verses:
                    verse = Verse()
                    verse.chapter = chapter
                    for _line in _verse:
                        line = Line()
                        if _line.get('id'):
                            line.id = _line.get('id')
                        line.verse = verse
                        line.text = _line.get('text', '')

                        for _idx, _token in enumerate(
                            _line["tokens"], start=1
                        ):
                            inner_id = _token["id"]
                            inner_id = (
                                "".join(map(str, inner_id))
                                if isinstance(inner_id, (list, tuple))
                                else str(inner_id)
                            )
                            del _token["id"]

                            token = Token()
                            token.inner_id = inner_id
                            token.order = _idx * 10
                            token.line = line
                            token.text = _token["form"]
                            token.lemma = _token["lemma"]
                            token.analysis = _token
                            token.display = {
                                "Word": _token["form"],
                                "Lemma": _token["lemma"],
                                "UPOS": _token["upos"],
                                "XPOS": _token["xpos"],
                                "Features": "<br>".join(
                                    f"{k}={v}"
                                    for k, v in _token["feats"].items()
                                ),
                                "Misc": "<br>".join(
                                    f"{k}={v}"
                                    for k, v in _token["misc"].items()
                                )
                            }
                            db.session.add(token)

            except Exception as e:
                webapp.logger.exception(e)
                flash("An error occurred while inserting data.", "danger")
            else:
                db.session.commit()
                flash(
                    f"Chapter '{chapter_name}' added successfully.",
                    "success"
                )
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
    import socket

    host = 'localhost'

    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)

    port = '5000'

    webapp.run(host=host, port=port, debug=True)
