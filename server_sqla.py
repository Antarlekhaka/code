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
from sqlalchemy import or_, and_

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from flask_babelex import Babel
from flask_wtf import CSRFProtect
from flask_mail import Mail
from flask_migrate import Migrate

from indic_transliteration.sanscript import transliterate

from models_sqla import (db, user_datastore,
                         CustomLoginForm, CustomRegisterForm,
                         Corpus, Chapter, Verse, Line, Token,
                         Lexicon,
                         Anvaya, Boundary,
                         ActionLabel, ActorLabel, Action)
from settings import app
from utils.reverseproxied import ReverseProxied
from utils.database import get_line_data, get_chapter_data
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


def get_lexicon(lemma: str) -> int:
    lexicon = Lexicon.query.filter(Lexicon.lemma == lemma).one_or_none()
    if lexicon:
        return lexicon.id


def create_lexicon(lemma: str) -> int:
    transliterations = [
        f"##{transliterate(lemma, 'devanagari', scheme)}"
        if not lemma.startswith(app.config['unnamed_prefix']) else ''
        for scheme in app.config['schemes']
    ]
    transliteration = ''.join(transliterations)
    lexicon = Lexicon()
    lexicon.lemma = lemma
    if transliteration:
        lexicon.transliteration = transliteration
    db.session.add(lexicon)
    db.session.flush()
    return lexicon.id


def get_or_create_lexicon(lemma: str) -> int:
    return get_lexicon(lemma) or create_lexicon(lemma)

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
    db.session.commit()


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
        'action_labels': ActionLabel.query.filter(
            ActionLabel.is_deleted == False  # noqa # '== False' is required
        ).with_entities(
            ActionLabel.id, ActionLabel.label, ActionLabel.description
        ).order_by(ActionLabel.label).all(),
        'actor_labels': ActorLabel.query.filter(
            ActorLabel.is_deleted == False  # noqa # '== False' is required
        ).with_entities(
            ActorLabel.id, ActorLabel.label, ActorLabel.description
        ).all()
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

    data['users'] = [user.username for user in user_query.all()]
    data['annotators'] = [user.username for user in user_query.all()
                          if annotator_role in user.roles]
    data['roles'] = [
        role.name
        for role in role_query.order_by(role_model.level).all()
        if role.level < user_level
    ]

    data['corpus_list'] = [
        {'id': corpus.id, 'name': corpus.name, 'chapters': [
            {'id': chapter.id, 'name': chapter.name}
            for chapter in corpus.chapters.all()
        ]}
        for corpus in Corpus.query.all()
    ]

    admin_result = session.get('admin_result', None)
    if admin_result:
        data['result'] = admin_result
        del session['admin_result']
    return render_template('admin.html', data=data)


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
            "update_multiword_type",
            "update_anvaya",
            "update_action_graph",
            "update_coreference"
        ],
        "curator": [],
        "querier": []
    }
    valid_actions = [
        action for actions in role_actions.values() for action in actions
    ]

    if action not in valid_actions:
        api_response["message"] = "Invalid action."
        return jsonify(api_response)

    for role, actions in role_actions.items():
        if action in actions and not current_user.has_role(role):
            api_response["message"] = "Insufficient permissions."
            return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    api_response["success"] = True
    api_response["message"] = "Under construction."
    api_response["style"] = "warning"

    # ----------------------------------------------------------------------- #

    if action == "update_sentence_boundary":
        verse_id = request.form["verse_id"]
        annotator_id = current_user.id
        boundary_tokens = [
            int(b.strip())
            for b in request.form["boundaries"].split(",")
            if b.strip()
        ]

        objects_to_update = []
        # IDs of objects that'll be deleted
        # We must also delete anvaya for these
        object_ids_delete = []

        existing_boundary_query = Boundary.query.filter(
            Boundary.verse_id == verse_id,
            Boundary.annotator_id == annotator_id
        )
        existing_boundary_tokens = {}
        for _boundary in existing_boundary_query.all():
            existing_boundary_tokens[_boundary.token_id] = _boundary
            if _boundary.token_id not in boundary_tokens:
                if not _boundary.is_deleted:
                    _boundary.is_deleted = True
                    objects_to_update.append(_boundary)
                    object_ids_delete.append(_boundary.id)

        Anvaya.query.filter(
            Anvaya.boundary_id.in_(object_ids_delete)
        ).update({
            Anvaya.is_deleted: True
        })

        for boundary_token in boundary_tokens:
            if boundary_token not in existing_boundary_tokens:
                boundary = Boundary()
                boundary.verse_id = verse_id
                boundary.token_id = boundary_token
                boundary.annotator_id = annotator_id
                objects_to_update.append(boundary)
            else:
                boundary = existing_boundary_tokens[boundary_token]
                if boundary.is_deleted:
                    boundary.is_deleted = False
                    objects_to_update.append(boundary)

        try:
            if objects_to_update:
                db.session.bulk_save_objects(objects_to_update)
                db.session.commit()
                api_response["message"] = "Successfully updated!"
                api_response["style"] = "success"
            else:
                api_response["message"] = "No changes were submitted."
                api_response["style"] = "warning"
            api_response["success"] = True
        except Exception as e:
            print(e)
            print(request.form)
            api_response["success"] = False
            api_response["message"] = "Something went wrong!"
            api_response["style"] = "danger"

        api_response["data"] = None
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == "update_multiword_type":
        api_response["data"] = None
        api_response["message"] = "update_multiword_type"
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == "update_anvaya":
        verse_id = request.form["verse_id"]
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
                m2 = re.match(r'token-([0-9]+)$', dom_token_id)
                if m2:
                    _order.append(int(m2.group(1)))
            anvaya_order[boundary_id] = _order

        objects_to_update = []
        existing_anvaya_query = Anvaya.query.filter(
            Anvaya.boundary_id.in_(boundary_ids),
            Anvaya.annotator_id == annotator_id
        )
        existing_sentences = {}
        for _anvaya in existing_anvaya_query.all():
            existing_sentences[_anvaya.boundary_id] = _anvaya
            if _anvaya.is_deleted:
                _anvaya.is_deleted = False
                _anvaya.anvaya_order = anvaya_order[_anvaya.boundary_id]
                objects_to_update.append(_anvaya)

        for boundary_id in boundary_ids:
            if boundary_id not in existing_sentences:
                anvaya = Anvaya()
                anvaya.boundary_id = boundary_id
                anvaya.anvaya_order = anvaya_order[boundary_id]
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
            api_response["success"] = True
        except Exception as e:
            print(e)
            print(request.form)
            api_response["success"] = False
            api_response["message"] = "Something went wrong!"
            api_response["style"] = "danger"

        api_response["data"] = None
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == "update_action_graph":
        api_response["data"] = None
        api_response["message"] = "update_action_graph"
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == "update_coreference":
        api_response["data"] = None
        api_response["message"] = "update_coreference"
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    if action == "custom_action":
        api_response["data"] = None
        return jsonify(api_response)

    # ----------------------------------------------------------------------- #

    return jsonify(api_response)


@webapp.route("/api/corpus/<int:chapter_id>")
@auth_required()
def api_corpus(chapter_id):
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

            # Action
            'action_type_add', 'action_type_remove',
            'actor_type_add', 'actor_type_remove',

            # Data
            'corpus_add', 'chapter_add',
        ],
        'curator': [],
        'annotator': [],
        'member': ['update_settings']
    }
    valid_actions = [
        action for actions in role_actions.values() for action in actions
    ]

    if action not in valid_actions:
        flash("Invalid action.")
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
        'action_type_add', 'action_type_remove',
        'actor_type_add', 'actor_type_remove',
    ]:
        action_parts = action.split('_')

        object_name = action_parts[0]
        target_action = action_parts[-1]

        object_label = request.form[f'{object_name}_label']
        object_label_desc = request.form.get(f'{object_name}_label_description')

        MODELS = {
            'action': (ActionLabel, Action, 'label_id'),
            'actor': (ActorLabel, Action, 'actor_label_id')
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
            message = f"{object_name.title()} label '{object_label}' does not exists."
            if _object_label is not None and not _object_label.is_deleted:
                objects_with_given_label = _annotation.query.filter(
                    getattr(_annotation, _annotation_attribute) == _object_label.id,
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

            try:
                data = DCS.parse_conllu(chapter_file.read().decode())
            except Exception:
                flash("Invalid file format.")
                return redirect(request.referrer)

            chapter_lines = []

            for line in data:
                unit = {
                    "id": line.metadata["line_id"],
                    "verse": line.metadata['chapter_verse_id'],
                    "text": line.metadata["text"],
                    "tokens": [
                        {
                            "ID": token.get("id") or "",
                            "Word": token.get("form") or "",
                            "Padapāṭha": token.get("unsandhied") or "",
                            "Lemma": token.get("lemma") or "",
                            "UPOS": token.get("upos") or "",
                            "XPOS": token.get("xpos") or "",
                            "Features": "<br>".join(
                                f"{k}={v}"
                                for k, v in (token.get("feats") or {}).items()
                            )
                        }
                        for token in line
                    ]
                }
                chapter_lines.append(unit)

            # Group verses
            verses = []
            last_verse_id = None
            for _line in chapter_lines:
                line_verse_id = _line.get('verse')
                if line_verse_id is None or line_verse_id != last_verse_id:
                    last_verse_id = line_verse_id
                    verses.append([])
                verses[-1].append(_line)

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

                        for _idx, _token in enumerate(_line["tokens"]):
                            token = Token()
                            token.order = _idx
                            token.line = line
                            token.analysis = _token
                            db.session.add(token)

            except Exception as e:
                logging.exception(e)
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
    host = 'localhost'
    port = '5000'

    webapp.run(host=host, port=port, debug=True)
