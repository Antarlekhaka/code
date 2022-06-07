#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Utility Functions
"""

###############################################################################

import logging
from typing import Dict, List

from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.relationships import RelationshipProperty

from models_sqla import User, Role
from models_sqla import Corpus, Chapter, Verse, Line, Token
from models_sqla import Anvaya, Boundary

###############################################################################

LOGGER = logging.getLogger(__name__)

###############################################################################


def search_model(
    model,
    offset: int = 0,
    limit: int = 30,
    **property_arguments
):
    """Search generic SQLAlchemy models"""
    conditions = []
    for property_name, property_value in property_arguments.items():
        if hasattr(model, property_name):
            attribute = getattr(model, property_name)
            if isinstance(attribute.property, ColumnProperty):
                if attribute.type.python_type is str:
                    conditions.append(attribute.ilike(property_value))
                else:
                    conditions.append(attribute == property_value)
            elif isinstance(attribute.property, RelationshipProperty):
                LOGGER.info(f"'{property_name}' is a 'RelationshipProperty'.")

    return model.query.filter(*conditions).offset(offset).limit(limit)


###############################################################################


def get_chapter_data(chapter_id: int, user: User, all: bool = False) -> dict:
    """Get Chapter Data

    Fetch line data for the lines belonging to the specified chapter.
    Calls `get_line_data()`.

    Parameters
    ----------
    chapter_id : int
        Chapter ID
    user : User
        User object for the user associated with the request
        If the user has `annotate` permissions, annotations will be fetched
    all : bool
        If True, and the user has `curate` permission or `admin` role,
        annotations by all the users will be fetched.
        The default is False

    Returns
    -------
    dict
        Line data, keyed by line IDs
    """
    chapter = Chapter.query.get(chapter_id)

    verse_ids = [
        verse.id
        for verse in chapter.verses
    ]
    annotator_ids = []

    if user.has_permission('annotate'):
        annotator_ids = [user.id]

    if user.has_permission('curate') or user.has_role('admin'):
        annotator_ids = None if all else [user.id]

    return get_verse_data(verse_ids, annotator_ids=annotator_ids)


def get_line_data(
    line_ids: List[int],
    annotator_ids: List[int] = None,
) -> dict:
    """Get Line Data

    Fetch content, linguistic information and annotations

    Parameters
    ----------
    line_ids : List[int]
        List of line IDs
    annotator_ids : List[int], optional
        List of user IDs of annotators
        If None, annotations by all the users will be fetched.
        The default is None.

    Returns
    -------
    dict
        Line data, keyed by line IDs
    """
    line_object_query = Line.query.filter(Line.id.in_(line_ids))
    data = {
        line.id: {
            'line_id': line.id,
            'verse_id': line.verse_id,
            'line': line.text,
            'analysis': [
                token.analysis
                for token in line.tokens.all()
            ],
            'tokens': [
                {
                    'id': token.id,
                    'relative_id': token.analysis['ID'],
                    'line_id': token.line_id,
                    'order': token.order,
                    'analysis': token.analysis
                }
                for token in line.tokens.all()
            ],
            'boundary': [],
            'sentences': {},
            'anvaya': {},
            'entity': [],
            'relation': [],
            'action': [],
            'marked': False,
        }
        for line in line_object_query.limit(30)
    }

    if annotator_ids is None:
        boundary_query = Boundary.query.filter(
            Boundary.line_id.in_(line_ids)
        )
    else:
        boundary_query = Boundary.query.filter(
            Boundary.line_id.in_(line_ids),
            Boundary.annotator_id.in_(annotator_ids)
        )

    for boundary in boundary_query.all():
        data[boundary.line_id]['boundary'].append(
            {
                'id': boundary.id,
                'token_id': boundary.token_id,
                'line_id': boundary.line_id,
                'annotator': boundary.annotator.username,
                'is_deleted': boundary.is_deleted
            }
        )
        data[boundary.line_id]['sentences'] = get_sentences(
            boundary.line_id,
            boundary.annotator_id
        )

    return data


def get_verse_data(
    verse_ids: List[int],
    annotator_ids: List[int] = None,
) -> dict:
    """Get Verse Data

    Fetch content, linguistic information and annotations

    Parameters
    ----------
    verse_ids : List[int]
        List of verse IDs
    annotator_ids : List[int], optional
        List of user IDs of annotators
        If None, annotations by all the users will be fetched.
        The default is None.

    Returns
    -------
    dict
        Line data, keyed by line IDs
    """
    line_object_query = Line.query.filter(Line.verse_id.in_(verse_ids))
    data = {}

    for line in line_object_query.limit(30):
        verse_id = line.verse_id
        if not data.get(verse_id):
            data[verse_id] = {
                'verse_id': verse_id,
                'text': [line.text],
                'analysis': [[
                    token.analysis
                    for token in line.tokens.all()
                ]],
                'tokens': [[
                    {
                        'id': token.id,
                        'relative_id': token.analysis['ID'],
                        'verse_id': verse_id,
                        'line_id': token.line_id,
                        'order': token.order,
                        'analysis': token.analysis
                    }
                    for token in line.tokens.all()
                ]],
                'boundary': [],
                'sentences': {},
                'anvaya': {},
                'entity': [],
                'relation': [],
                'action': [],
                'marked': False,
            }
        else:
            data[verse_id]['text'].append(line.text)
            data[verse_id]['analysis'].append([
                token.analysis
                for token in line.tokens.all()
            ])
            data[verse_id]['tokens'].append([
                {
                    'id': token.id,
                    'relative_id': token.analysis['ID'],
                    'verse_id': verse_id,
                    'line_id': token.line_id,
                    'order': token.order,
                    'analysis': token.analysis
                }
                for token in line.tokens.all()
            ])

    if annotator_ids is None:
        boundary_query = Boundary.query.filter(
            Boundary.verse_id.in_(verse_ids)
        )
    else:
        boundary_query = Boundary.query.filter(
            Boundary.verse_id.in_(verse_ids),
            Boundary.annotator_id.in_(annotator_ids)
        )

    for boundary in boundary_query.all():
        verse_id = boundary.verse_id
        data[verse_id]['boundary'].append(
            {
                'id': boundary.id,
                'token_id': boundary.token_id,
                'verse_id': boundary.verse_id,
                'annotator': boundary.annotator.username,
                'is_deleted': boundary.is_deleted
            }
        )
        data[verse_id]['sentences'] = get_sentences(
            verse_id, boundary.annotator_id
        )
        anvaya = Anvaya.query.filter(
            Anvaya.boundary_id == boundary.id,
            Anvaya.is_deleted == False  # noqa
        ).first()
        if anvaya:
            data[verse_id]['anvaya'][boundary.id] = anvaya.anvaya_order

    return data


def get_sentences(
    verse_id: int, annotator_id: int
) -> Dict[int, Dict[int, Token]]:
    """Get sentences (as a list of tokens) that end on the specific line

    Parameters
    ----------
    verse_id : int
        Verse ID
    annotator_id : int
        Annotator ID

    Returns
    -------
    Dict[int, Dict[int, Token]]
        Dictionary
        * `Boundary.id`s (also corresponding to sentences) as keys
        * Dictionary of (token_id, tokens) in the sentences as values
    """
    sentences = {}

    # boundaries present in the current line
    boundaries = Boundary.query.filter(
        Boundary.verse_id == verse_id,
        Boundary.annotator_id == annotator_id,
        Boundary.is_deleted == False  # noqa # '== False' is required
    ).order_by(Boundary.token_id).all()

    if not boundaries:
        return sentences

    # previous boundary, which serves as the starting point
    # of the first boundary in the current line
    previous_boundary = Boundary.query.filter(
        Boundary.verse_id < verse_id,
        Boundary.annotator_id == annotator_id,
        Boundary.is_deleted == False  # noqa # '== False' is required
    ).order_by(Boundary.token_id.desc()).first()

    previous_boundary_token_id = (
        previous_boundary.token_id if previous_boundary else -1
    )

    for boundary in boundaries:
        tokens = Token.query.filter(
            Token.id > previous_boundary_token_id,
            Token.id <= boundary.token_id
        ).order_by(Token.id).all()
        sentences[boundary.id] = {
            token.id: {
                'id': token.id,
                'sentence_id': boundary.id,
                'boundary_id': boundary.id,
                'analysis': token.analysis,
            }
            for token in tokens
        }
        previous_boundary_token_id = boundary.token_id

    return sentences
