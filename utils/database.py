#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Utility Functions
"""

###############################################################################

import logging
from typing import Dict, List
from collections import defaultdict

from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.relationships import RelationshipProperty

from models_sqla import User, Role
from models_sqla import Corpus, Chapter, Verse, Line, Token
from models_sqla import (
    Task, Progress,
    Boundary,
    Anvaya,
    Entity,
    TokenGraph,
    Coreference,
    SentenceClassification,
    DiscourseGraph
)

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

def export_data(
    annotator_ids: List[int],
    chapter_ids: List[int],
    task_ids: List[int],
    output_format: str = "standard"
):
    """Export Data

    Parameters
    ----------
    annotator_ids : List[int]
        Annotator IDs
    chapter_ids : List[int]
        Chapter IDs
    task_ids : List[int]
        Task IDs
    output_format : str, optional
        Output Format, "standard" or "simple"
        The default is "standard".

    Returns
    -------
    _type_
        _description_
    """

    chapters = Chapter.query.filter(Chapter.id.in_(chapter_ids)).all()
    annotators = User.query.filter(User.id.in_(annotator_ids)).all()
    tasks = Task.query.filter(Task.id.in_(task_ids)).all()

    data = defaultdict(dict)

    for chapter in chapters:
        for annotator in annotators:
            line_query = Line.query.filter(
                Line.verse.has(Verse.chapter_id == chapter.id)
            )
            line_ids = [
                line.id for line in line_query.all()
            ]

            for task in tasks:
                print(
                    f"Fetching annotation for Task {task.id} ({task.name}) "
                    f"from Chapter {chapter.id} ({chapter.name}) "
                    f"for User {annotator.id} ({annotator.username})."
                )
                if task.name == "sentence_boundary":
                    pass
                if task.name == "anvaya":
                    pass
                if task.name == "named_entity":
                    pass
                if task.name == "token_graph":
                    pass
                if task.name == "coreference":
                    pass
                if task.name == "sentence_classification":
                    pass
                if task.name == "intersentence_connection":
                    pass

    return data


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


###############################################################################


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

    # TODO: Consider rewriting with a focus on Verse instead of Line
    # TODO: Remember to remove .limit(30)
    # NOTE: Line ID is important for tokens
    # Do we want to change the database structure to remove Line table
    # altogether and only keep only a line_id field in Verse table?

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
                    if (
                        token.annotator_id is None or
                        token.annotator_id in annotator_ids
                    )
                    # NOTE: now tokens also have annotator_id,
                    # so, may be directly fetch with annotator_id or null
                    # (instead of doing this in Python)
                    # (null is needed for tokens from original corpus)
                    # Could also consider keeping original tokens in 'tokens'
                    # and adding a '_tokens' for custom tokens
                ]],
                'boundary': {},
                'sentences': {},
                'anvaya': {},
                'entity': [],
                'relation': [],
                'coreference': [],
                'sentence_classification': [],
                'intersentence_connection': [],
                'progress': [
                    {
                        "task_id": p.task_id,
                        "task_short": p.task.short,
                        "verse_id": p.verse_id,
                        "annotator_id": p.annotator_id,
                        "updated_at": p.updated_at
                    }
                    for p in Progress.query.filter(
                        Progress.verse_id == verse_id,
                        Progress.annotator_id.in_(annotator_ids),
                    ).all()
                ]
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
                if (
                    token.annotator_id is None or
                    token.annotator_id in annotator_ids
                )
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

    # ----------------------------------------------------------------------- #
    # boundary specific data - BEGIN
    for boundary in boundary_query.all():
        verse_id = boundary.verse_id
        data[verse_id]['boundary'][boundary.id] = {
            'id': boundary.id,
            'token_id': boundary.token_id,
            'verse_id': boundary.verse_id,
            'annotator_id': boundary.annotator_id,
            'annotator': boundary.annotator.username,
        }
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
        # TODO: consider if we should provide predicted anvaya separately
        #       instead of in the same field

        # ------------------------------------------------------------------- #

        entity_query = Entity.query.filter(
            Entity.boundary_id == boundary.id,
            Entity.annotator_id.in_(annotator_ids)
        )

        data[verse_id]['entity'].extend([
            {
                'id': entity.id,
                'boundary_id': entity.boundary_id,
                'token_id': entity.token_id,
                'label_id': entity.label_id,
                'annotator_id': entity.annotator_id,
                'is_deleted': entity.is_deleted
            }
            for entity in entity_query.all()
        ])

        # ------------------------------------------------------------------- #

        token_graph_query = TokenGraph.query.filter(
            TokenGraph.boundary_id == boundary.id,
            TokenGraph.annotator_id.in_(annotator_ids)
        )

        data[verse_id]['relation'].extend([
            {
                'id': relation.id,
                'boundary_id': relation.boundary_id,
                'src_id': relation.src_id,
                'label_id': relation.label_id,
                'dst_id': relation.dst_id,
                'annotator_id': relation.annotator_id,
                'is_deleted': relation.is_deleted
            }
            for relation in token_graph_query.all()
        ])

        # ------------------------------------------------------------------- #

        coreference_query = Coreference.query.filter(
            Coreference.boundary_id == boundary.id,
            Coreference.annotator_id.in_(annotator_ids)
        )

        data[verse_id]['coreference'].extend([
            {
                'id': coreference.id,
                'boundary_id': coreference.boundary_id,
                'src_id': coreference.src_id,
                'dst_id': coreference.dst_id,
                'annotator_id': coreference.annotator_id,
                'is_deleted': coreference.is_deleted
            }
            for coreference in coreference_query.all()
        ])

        # ------------------------------------------------------------------- #

        sentence_classification_query = SentenceClassification.query.filter(
            SentenceClassification.boundary_id == boundary.id,
            SentenceClassification.annotator_id.in_(annotator_ids)
        )

        data[verse_id]['sentence_classification'].extend([
            {
                'id': sentclf.id,
                'boundary_id': sentclf.boundary_id,
                'label_id': sentclf.label_id,
                'annotator_id': sentclf.annotator_id,
                'is_deleted': sentclf.is_deleted
            }
            for sentclf in sentence_classification_query.all()
        ])

        # ------------------------------------------------------------------- #

        # NOTE: We show connections that at the src_boundary_id
        intersentence_connection_query = DiscourseGraph.query.filter(
            DiscourseGraph.src_boundary_id == boundary.id,
            DiscourseGraph.annotator_id.in_(annotator_ids)
        )

        data[verse_id]['intersentence_connection'].extend([
            {
                'id': isc.id,
                'src_boundary_id': isc.src_boundary_id,
                'src_token_id': isc.src_token_id,
                'dst_boundary_id': isc.dst_boundary_id,
                'dst_token_id': isc.dst_token_id,
                'label_id': isc.label_id,
                'relation_type': isc.relation_type,
                'annotator_id': isc.annotator_id,
                'is_deleted': isc.is_deleted
            }
            for isc in intersentence_connection_query.all()
        ])

        # ------------------------------------------------------------------- #

    # boundary specific data - END
    # ----------------------------------------------------------------------- #
    return data


def get_sentences(
    verse_id: int, annotator_id: int
) -> Dict[int, Dict[int, Token]]:
    """Get sentences (a list of tokens) that end on the specific line

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

    # TODO: Consider only verses from this chapter
    # TODO: If too many tokens, emit an error

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
