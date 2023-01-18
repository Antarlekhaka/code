#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLAlchemy Models

Created on Sun Mar 07 13:08:36 2021

@author: Hrishikesh Terdalkar
"""

###############################################################################

import sqlite3
from datetime import datetime as dt
from sqlalchemy import (Boolean, DateTime, Column, Integer, String, Text,
                        ForeignKey, JSON, Enum, Index, event)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.engine import Engine

from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin, SQLAlchemyUserDatastore
from flask_security.forms import LoginForm, RegisterForm, StringField, Required

# --------------------------------------------------------------------------- #

from constants import TASK_CATEGORY_LIST

###############################################################################
# Foreign Key Support for SQLite3


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if type(dbapi_connection) is sqlite3.Connection:
        # play well with other database backends
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


###############################################################################
# Create database connection object

db = SQLAlchemy()

###############################################################################
# Corpus Database Models


class Corpus(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    scheme = Column(
        Enum('devanagari', 'velthuis', 'iast', 'itrans', 'slp1', 'hk', 'wx'),
        default='devanagari', nullable=False
    )
    description = Column(String(255), nullable=False)


class Chapter(db.Model):
    id = Column(Integer, primary_key=True)
    corpus_id = Column(Integer, ForeignKey('corpus.id', ondelete='CASCADE'),
                       nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(255), nullable=False)

    corpus = relationship(
        'Corpus',
        backref=backref('chapters', cascade='all,delete-orphan', lazy='dynamic')
    )


class Verse(db.Model):
    id = Column(Integer, primary_key=True)
    chapter_id = Column(Integer, ForeignKey('chapter.id', ondelete='CASCADE'),
                        nullable=False, index=True)

    chapter = relationship(
        'Chapter',
        backref=backref('verses', cascade='all,delete-orphan', lazy='dynamic')
    )


class Line(db.Model):
    id = Column(Integer, primary_key=True)
    verse_id = Column(Integer, ForeignKey('verse.id', ondelete='CASCADE'),
                      nullable=False, index=True)
    text = Column(Text, nullable=False)

    verse = relationship(
        'Verse',
        backref=backref('lines', cascade='all,delete-orphan', lazy='dynamic')
    )


class Token(db.Model):
    id = Column(Integer, primary_key=True)
    line_id = Column(Integer, ForeignKey('line.id', ondelete='CASCADE'),
                     nullable=False, index=True)
    inner_id = Column(String(255), nullable=False)
    order = Column(Integer, nullable=False)
    text = Column(String(255), nullable=False)
    lemma = Column(String(255), nullable=False)
    analysis = Column(JSON, nullable=False)
    display = Column(JSON, nullable=True)

    annotator_id = Column(Integer, ForeignKey('user.id'), nullable=True)

    line = relationship(
        'Line',
        backref=backref('tokens', cascade='all,delete-orphan', lazy='dynamic')
    )
    annotator = relationship(
        'User', backref=backref('tokens', lazy='dynamic')
    )
    # removed index because all custom added tokens get same order-id
    # __table_args__ = (
    #     Index('token_line_id_order', 'line_id', 'order', unique=True),
    # )


###############################################################################
# User Database Models


DEFAULT_SETTING = {
    'display_name': '',
    'theme': 'united',
}


class Role(db.Model, RoleMixin):
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    description = Column(String(255))
    level = Column(Integer)
    permissions = Column(String(255))


class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True)
    email = Column(String(255), unique=True)
    password = Column(String(255))
    active = Column(Boolean, default=True)
    fs_uniquifier = Column(String(255), unique=True)
    confirmed_at = Column(DateTime)
    settings = Column(JSON, default=DEFAULT_SETTING)
    last_login_at = Column(DateTime)
    current_login_at = Column(DateTime)
    last_login_ip = Column(String(255))
    current_login_ip = Column(String(255))
    login_count = Column(Integer)
    roles = relationship('Role', secondary='roles_users',
                         backref=backref('users', lazy='dynamic'))


class RolesUsers(db.Model):
    __tablename__ = 'roles_users'
    id = Column(Integer, primary_key=True)
    user_id = Column('user_id', Integer, ForeignKey('user.id'))
    role_id = Column('role_id', Integer, ForeignKey('role.id'))

###############################################################################
# Task Specific Models


class Task(db.Model):
    id = Column(Integer, primary_key=True)
    category = Column(Enum(*TASK_CATEGORY_LIST), nullable=False)
    # name = Column(String(255), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    short = Column(String(255), nullable=False)
    help = Column(String(255), nullable=False)
    order = Column(Integer, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)


class SubmitLog(db.Model):
    id = Column(Integer, primary_key=True)
    verse_id = Column(Integer, ForeignKey('verse.id', ondelete='CASCADE'),
                      nullable=False, index=True)
    annotator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    task_id = Column(Integer, ForeignKey('task.id'), nullable=False)
    updated_at = Column(DateTime, default=dt.utcnow, onupdate=dt.utcnow)

    verse = relationship(
        'Verse',
        backref=backref(
            'submits', cascade='all,delete-orphan', lazy='dynamic'
        )
    )
    annotator = relationship(
        'User', backref=backref('submits', lazy='dynamic')
    )
    task = relationship(
        'Task',
        backref=backref('submits', cascade='all,delete-orphan', lazy='dynamic')
    )


# --------------------------------------------------------------------------- #


class Boundary(db.Model):
    id = Column(Integer, primary_key=True)
    # ----------------------------------------------------------------------- #
    task_id = Column(Integer, ForeignKey('task.id', ondelete='CASCADE'),
                     nullable=False, index=True)
    verse_id = Column(Integer, ForeignKey('verse.id', ondelete='CASCADE'),
                      nullable=False, index=True)
    token_id = Column(Integer, ForeignKey('token.id'), nullable=False)
    # ----------------------------------------------------------------------- #
    annotator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    updated_at = Column(DateTime, default=dt.utcnow, onupdate=dt.utcnow)

    task = relationship(
        'Task',
        backref=backref(
            'boundaries', cascade='all,delete-orphan', lazy='dynamic'
        )
    )
    verse = relationship(
        'Verse',
        backref=backref(
            'boundaries', cascade='all,delete-orphan', lazy='dynamic'
        )
    )
    token = relationship(
        'Token', backref=backref('boundaries', lazy='dynamic')
    )
    annotator = relationship(
        'User', backref=backref('boundaries', lazy='dynamic')
    )
    __table_args__ = (
         Index('boundary_token_id_annotator_id',
               'token_id', 'annotator_id', unique=True),
    )


class WordOrder(db.Model):
    id = Column(Integer, primary_key=True)
    # ----------------------------------------------------------------------- #
    task_id = Column(Integer, ForeignKey('task.id', ondelete='CASCADE'),
                     nullable=False, index=True)
    boundary_id = Column(
        Integer, ForeignKey('boundary.id', ondelete='CASCADE'), nullable=False
    )
    token_id = Column(Integer, ForeignKey('token.id'), nullable=False)
    order = Column(Integer, nullable=False)
    # ----------------------------------------------------------------------- #
    annotator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    updated_at = Column(DateTime, default=dt.utcnow, onupdate=dt.utcnow)

    task = relationship(
        'Task',
        backref=backref(
            'word_order', cascade='all,delete-orphan', lazy='dynamic'
        )
    )
    boundary = relationship(
        'Boundary',
        backref=backref(
            'word_order', cascade='all,delete-orphan', lazy='dynamic'
        )
    )
    token = relationship(
        'Token', backref=backref('word_order', lazy='dynamic')
    )
    annotator = relationship(
        'User',
        backref=backref('word_order', lazy='dynamic')
    )
    __table_args__ = (
         Index('word_order_boundary_id_annotator_id_token_id',
               'boundary_id', 'annotator_id', 'token_id', unique=True),
    )


class TokenTextAnnotation(db.Model):
    id = Column(Integer, primary_key=True)
    # ----------------------------------------------------------------------- #
    task_id = Column(Integer, ForeignKey('task.id', ondelete='CASCADE'),
                     nullable=False, index=True)
    boundary_id = Column(
        Integer, ForeignKey('boundary.id', ondelete='CASCADE'), nullable=False
    )
    token_id = Column(Integer, ForeignKey('token.id'), nullable=False)
    text = Column(String(255), nullable=False)
    # ----------------------------------------------------------------------- #
    annotator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=dt.utcnow, onupdate=dt.utcnow)

    task = relationship(
        'Task',
        backref=backref(
            'annotations', cascade='all,delete-orphan', lazy='dynamic'
        )
    )
    boundary = relationship(
        'Boundary',
        backref=backref(
            'annotations', cascade='all,delete-orphan', lazy='dynamic'
        )
    )
    token = relationship(
        'Token', backref=backref('annotations', lazy='dynamic')
    )
    annotator = relationship(
        'User', backref=backref('annotations', lazy='dynamic')
    )
    __table_args__ = (
         Index('token_text_annotation_task_id_annotator_id_token_id',
               'task_id', 'annotator_id', 'token_id', unique=True),
    )


class TokenClassification(db.Model):
    id = Column(Integer, primary_key=True)
    # ----------------------------------------------------------------------- #
    task_id = Column(Integer, ForeignKey('task.id', ondelete='CASCADE'),
                     nullable=False, index=True)
    boundary_id = Column(
        Integer, ForeignKey('boundary.id', ondelete='CASCADE'), nullable=False
    )
    token_id = Column(Integer, ForeignKey('token.id'), nullable=False)
    label_id = Column(Integer, ForeignKey('token_label.id'), nullable=False)
    # ----------------------------------------------------------------------- #
    annotator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=dt.utcnow, onupdate=dt.utcnow)

    task = relationship(
        'Task',
        backref=backref('tokclf', cascade='all,delete-orphan', lazy='dynamic')
    )
    boundary = relationship(
        'Boundary',
        backref=backref('tokclf', cascade='all,delete-orphan', lazy='dynamic')
    )
    token = relationship('Token', backref=backref('tokclf', lazy='dynamic'))
    label = relationship(
        'TokenLabel',
        backref=backref('tokclf', lazy='dynamic')
    )
    annotator = relationship(
        'User', backref=backref('tokclf', lazy='dynamic')
    )
    __table_args__ = (
         Index('token_classification_task_id_annotator_id_token_id',
               'task_id', 'annotator_id', 'token_id', unique=True),
    )


class TokenGraph(db.Model):
    id = Column(Integer, primary_key=True)
    # ----------------------------------------------------------------------- #
    task_id = Column(Integer, ForeignKey('task.id', ondelete='CASCADE'),
                     nullable=False, index=True)
    boundary_id = Column(
        Integer, ForeignKey('boundary.id', ondelete='CASCADE'), nullable=False
    )
    src_id = Column(Integer, ForeignKey('token.id'), nullable=False)
    label_id = Column(
        Integer, ForeignKey('token_relation_label.id'), nullable=False
    )
    dst_id = Column(Integer, ForeignKey('token.id'), nullable=False)
    # ----------------------------------------------------------------------- #
    annotator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=dt.utcnow, onupdate=dt.utcnow)

    task = relationship(
        'Task',
        backref=backref(
            'token_graphs', cascade='all,delete-orphan', lazy='dynamic'
        )
    )
    src_token = relationship('Token', foreign_keys=[src_id])
    dst_token = relationship('Token', foreign_keys=[dst_id])
    label = relationship(
        'TokenRelationLabel', backref=backref('token_graphs', lazy='dynamic')
    )
    boundary = relationship(
        'Boundary',
        backref=backref(
            'token_graphs', cascade='all,delete-orphan', lazy='dynamic'
        )
    )
    annotator = relationship(
        'User', backref=backref('token_graphs', lazy='dynamic')
    )

    __table_args__ = (
         Index('token_graph_task_id_annotator_id_src_id_dst_id',
               'task_id', 'annotator_id', 'src_id', 'dst_id', unique=True),
    )
    # the above will not allow multiple edges between same two token ids
    # if that is to be allowed, we would need something like the below
    # (which is pretty much same as not having a unique index)

    # __table_args__ = (
    #      Index('token_graph_annotator_id_src_id_label_id_dst_id',
    #            'annotator_id', 'src_id', 'label_id', 'dst_id', unique=True),
    # )


class TokenConnection(db.Model):
    id = Column(Integer, primary_key=True)
    # ----------------------------------------------------------------------- #
    task_id = Column(Integer, ForeignKey('task.id', ondelete='CASCADE'),
                     nullable=False, index=True)
    boundary_id = Column(
        Integer, ForeignKey('boundary.id', ondelete='CASCADE'), nullable=False
    )
    src_id = Column(Integer, ForeignKey('token.id'), nullable=False)
    dst_id = Column(Integer, ForeignKey('token.id'), nullable=False)
    # ----------------------------------------------------------------------- #
    annotator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=dt.utcnow, onupdate=dt.utcnow)

    task = relationship(
        'Task',
        backref=backref(
            'token_connections', cascade='all,delete-orphan', lazy='dynamic'
        )
    )
    src_token = relationship('Token', foreign_keys=[src_id])
    dst_token = relationship('Token', foreign_keys=[dst_id])
    boundary = relationship(
        'Boundary',
        backref=backref(
            'token_connections', cascade='all,delete-orphan', lazy='dynamic'
        )
    )
    annotator = relationship(
        'User', backref=backref('token_connections', lazy='dynamic')
    )

    __table_args__ = (
         Index('token_connection_task_id_annotator_id_src_id_dst_id',
               'task_id', 'annotator_id', 'src_id', 'dst_id', unique=True),
    )


class SentenceClassification(db.Model):
    id = Column(Integer, primary_key=True)
    # ----------------------------------------------------------------------- #
    task_id = Column(Integer, ForeignKey('task.id', ondelete='CASCADE'),
                     nullable=False, index=True)
    boundary_id = Column(
        Integer, ForeignKey('boundary.id', ondelete='CASCADE'), nullable=False
    )
    label_id = Column(Integer, ForeignKey('sentence_label.id'), nullable=False)
    # ----------------------------------------------------------------------- #
    annotator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=dt.utcnow, onupdate=dt.utcnow)

    task = relationship(
        'Task',
        backref=backref('sentclf', cascade='all,delete-orphan', lazy='dynamic')
    )
    label = relationship(
        'SentenceLabel', backref=backref('sentclf', lazy='dynamic')
    )
    boundary = relationship(
        'Boundary',
        backref=backref('sentclf', cascade='all,delete-orphan', lazy='dynamic')
    )
    annotator = relationship(
        'User', backref=backref('sentclf', lazy='dynamic')
    )

    __table_args__ = (
         Index('sentence_classification_task_id_annotator_id_boundary_id',
               'task_id', 'annotator_id', 'boundary_id', unique=True),
    )


class SentenceGraph(db.Model):
    id = Column(Integer, primary_key=True)
    # ----------------------------------------------------------------------- #
    task_id = Column(Integer, ForeignKey('task.id', ondelete='CASCADE'),
                     nullable=False, index=True)
    src_boundary_id = Column(
        Integer, ForeignKey('boundary.id', ondelete='CASCADE'), nullable=False
    )
    dst_boundary_id = Column(
        Integer, ForeignKey('boundary.id', ondelete='CASCADE'), nullable=False
    )
    src_token_id = Column(Integer, ForeignKey('token.id'), nullable=False)
    dst_token_id = Column(Integer, ForeignKey('token.id'), nullable=False)
    label_id = Column(
        Integer, ForeignKey('sentence_relation_label.id'), nullable=False
    )
    relation_type = Column(Integer, nullable=False)
    # type == 0: token-token connection
    # type == 1: token-sentence connection
    # type == 2: sentence-token connection
    # type == 3: sentence-sentence connection
    # ----------------------------------------------------------------------- #
    annotator_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    updated_at = Column(DateTime, default=dt.utcnow, onupdate=dt.utcnow)

    task = relationship(
        'Task',
        backref=backref(
            'sentence_graphs', cascade='all,delete-orphan', lazy='dynamic'
        )
    )
    label = relationship(
        'SentenceRelationLabel',
        backref=backref('sentence_graphs', lazy='dynamic')
    )
    src_boundary = relationship(
        'Boundary',
        backref=backref(
            'sentence_graphs_src', cascade='all,delete-orphan', lazy='dynamic'
        ),
        foreign_keys=[src_boundary_id]
    )
    dst_boundary = relationship(
        'Boundary',
        backref=backref(
            'sentence_graphs_dst', cascade='all,delete-orphan', lazy='dynamic'
        ),
        foreign_keys=[dst_boundary_id]
    )
    annotator = relationship(
        'User', backref=backref('sentence_graphs', lazy='dynamic')
    )

    __table_args__ = (
         Index(
            ('sentence_graph_task_id_annotator_id_'
             'src_boundary_id_dst_boundary_id_'
             'src_token_id_dst_token_id_relation_type'),
            'task_id', 'annotator_id',
            'src_boundary_id', 'dst_boundary_id',
            'src_token_id', 'dst_token_id', 'relation_type',
            unique=True),
    )


###############################################################################
# Label Models


class TokenLabel(db.Model):
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('task.id'), nullable=False)
    label = Column(String(255), nullable=False)
    description = Column(String(255))
    is_deleted = Column(Boolean, default=False, nullable=False)
    task = relationship(
        'Task',
        backref=backref(
            'token_labels',
            cascade='all,delete-orphan', lazy='dynamic'
        )
    )


class TokenRelationLabel(db.Model):
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('task.id'), nullable=False)
    label = Column(String(255), nullable=False)
    description = Column(String(255))
    is_deleted = Column(Boolean, default=False, nullable=False)
    task = relationship(
        'Task',
        backref=backref(
            'token_relation_labels',
            cascade='all,delete-orphan', lazy='dynamic'
        )
    )


class SentenceLabel(db.Model):
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('task.id'), nullable=False)
    label = Column(String(255), nullable=False)
    description = Column(String(255))
    is_deleted = Column(Boolean, default=False, nullable=False)
    task = relationship(
        'Task',
        backref=backref(
            'sentence_labels',
            cascade='all,delete-orphan', lazy='dynamic'
        )
    )


class SentenceRelationLabel(db.Model):
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('task.id'), nullable=False)
    label = Column(String(255), nullable=False)
    description = Column(String(255))
    is_deleted = Column(Boolean, default=False, nullable=False)
    task = relationship(
        'Task',
        backref=backref(
            'sentence_relation_labels',
            cascade='all,delete-orphan', lazy='dynamic'
        )
    )


###############################################################################
# NOTE:
# * we can add a generic Task table and a generic Label table later
# * task can later be replaced by task_id
# Task "type" can be generic

# class TaskLabel(db.Model):
#     id = Column(Integer, primary_key=True)
#     task_id = Column(Integer, ForeignKey('task.id'), nullable=False)
#     label = Column(String(255), nullable=False)
#     description = Column(String(255))
#     is_deleted = Column(Boolean, default=False, nullable=False)

#     task = relationship(
#         'Task',
#         backref=backref('labels', cascade='all,delete-orphan', lazy='dynamic')
#     )


###############################################################################
# Setup Flask-Security

user_datastore = SQLAlchemyUserDatastore(db, User, Role)

###############################################################################


class CustomRegisterForm(RegisterForm):
    username = StringField('Username', [Required()])

    def validate(self):
        if user_datastore.find_user(username=self.username.data):
            self.username.errors = ["Username already taken"]
            return False

        if not super(CustomRegisterForm, self).validate():
            return False

        return True


class CustomLoginForm(LoginForm):
    email = StringField('Username or Email', [Required()])

###############################################################################
