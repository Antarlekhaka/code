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

from utils.heuristic import get_anvaya

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
    annotator_ids = annotator_ids or []
    line_object_query = Line.query.filter(Line.verse_id.in_(verse_ids))
    data = {}

    for line in line_object_query.limit(30):
        verse_id = line.verse_id
        if not data.get(verse_id):
            data[verse_id] = {
                'verse_id': verse_id,
                'text': [line.text],
                'display': [[
                    token.display
                    for token in line.tokens.all()
                    if not token.annotator_id
                    # tokens that do not have annotator_id are original
                ]],
                'tokens': [[
                    {
                        'id': token.id,
                        'inner_id': token.inner_id,
                        'verse_id': verse_id,
                        'line_id': token.line_id,
                        'order': token.order,
                        'text': token.text,
                        'lemma': token.lemma,
                        'analysis': token.analysis,
                        # 'display': token.display,
                        'annotator_id': token.annotator_id
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
            data[verse_id]['display'].append([
                token.display
                for token in line.tokens.all()
                if not token.annotator_id
                # tokens that do not have annotator_id are original
            ])
            data[verse_id]['tokens'].append([
                {
                    'id': token.id,
                    'inner_id': token.inner_id,
                    'verse_id': verse_id,
                    'line_id': token.line_id,
                    'order': token.order,
                    'text': token.text,
                    'lemma': token.lemma,
                    'analysis': token.analysis,
                    # 'display': token.display,
                    'annotator_id': token.annotator_id
                }
                for token in line.tokens.all()
            ])

    if annotator_ids is None:
        boundary_query = Boundary.query.filter(
            Boundary.verse_id.in_(verse_ids)
        ).order_by(Boundary.token_id)
    else:
        boundary_query = Boundary.query.filter(
            Boundary.verse_id.in_(verse_ids),
            Boundary.annotator_id.in_(annotator_ids)
        ).order_by(Boundary.token_id)

    for boundary in boundary_query.all():
        verse_id = boundary.verse_id
        data[verse_id]['boundary'].append(
            {
                'id': boundary.id,
                'token_id': boundary.token_id,
                'verse_id': boundary.verse_id,
                'annotator': boundary.annotator.username,
            }
        )
        data[verse_id]['sentences'] = get_sentences(
            verse_id, boundary.annotator_id
        )
        anvaya_query = Anvaya.query.filter(
            Anvaya.boundary_id == boundary.id,
            Anvaya.annotator_id.in_(annotator_ids)
        ).order_by(Anvaya.order)
        sentence_anvaya = [
            a.token_id for a in anvaya_query.all()
        ]
        # if anvaya doesn't exist, apply heuristic
        if not sentence_anvaya:
            sentence_anvaya = get_anvaya(
                data[verse_id]['sentences'][boundary.id]
            )

        data[verse_id]['anvaya'][boundary.id] = sentence_anvaya

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

    # boundaries present in the current verse
    boundaries = Boundary.query.filter(
        Boundary.verse_id == verse_id,
        Boundary.annotator_id == annotator_id,
    ).order_by(Boundary.token_id).all()

    if not boundaries:
        return sentences

    # previous boundary, which serves as the starting point
    # of the first boundary in the current line
    previous_boundary = Boundary.query.filter(
        Boundary.verse_id < verse_id,
        Boundary.annotator_id == annotator_id,
    ).order_by(Boundary.token_id.desc()).first()

    previous_boundary_token_id = (
        previous_boundary.token_id if previous_boundary else -1
    )
    # ----------------------------------------------------------------------- #
    extra_tokens = Token.query.filter(
        Token.line.has(Line.verse_id == verse_id),
        Token.annotator_id != None  # noqa
    ).all()
    sentences['extra'] = {
        token.id: {
            'id': token.id,
            'text': token.text,
            'lemma': token.lemma,
            'analysis': token.analysis,
            'annotator_id': token.annotator_id
        }
        for token in extra_tokens
    }
    # ----------------------------------------------------------------------- #
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
                'order': token.order,
                'text': token.text,
                'lemma': token.lemma,
                'analysis': token.analysis,
                'annotator_id': token.annotator_id
            }
            for token in tokens
        }
        previous_boundary_token_id = boundary.token_id

    return sentences
