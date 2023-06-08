#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Utility Functions

Note: Functions are usable only in an application context.

@author: Hrishikesh Terdalkar
"""

###############################################################################

import logging
from typing import Dict, List, Any
from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.relationships import RelationshipProperty

from models_sqla import db, User, Role
from models_sqla import Corpus, Chapter, Verse, Line, Token
from models_sqla import (
    Task,
    Boundary,
    WordOrder,
    TokenTextAnnotation,
    TokenClassification,
    TokenGraph,
    TokenConnection,
    SentenceClassification,
    SentenceGraph,
    TokenRelationLabel,
    SubmitLog
)
from constants import (
    AUTO_ANNOTATION_USER_ID,

    ROLE_ADMIN,
    PERMISSION_CURATE,
    PERMISSION_ANNOTATE,

    TASK_SENTENCE_BOUNDARY,
    TASK_WORD_ORDER,
    TASK_TOKEN_TEXT_ANNOTATION,
    TASK_TOKEN_CLASSIFICATION,
    TASK_TOKEN_GRAPH,
    TASK_TOKEN_CONNECTION,
    TASK_SENTENCE_CLASSIFICATION,
    TASK_SENTENCE_GRAPH
)
from utils.heuristic import get_word_order, get_token_graph

###############################################################################

LOGGER = logging.getLogger(__name__)

###############################################################################

# NOTE: Format Verse Data (`chapter_data`)
# [[{}, {}, {}, ...], [{}, {}, {}, ...], ...]
# data: list of verses
# verse: list of lines
# line: dict (id, verse_id, text, tokens)
# tokens: list of dict
# token: dict 10 CoNLL-U mandatory fields
# in particular,
# "id", "form", "lemma", "upos", "xpos", "feats", "misc"
# `CONLLU_PARSER.read_conllu_data` formats it in this format


def add_chapter(
    corpus_id: int,
    chapter_name: str,
    chapter_description: str,
    chapter_data: List[List[Dict]]
):
    """Add Chapter Data

    Parameters
    ----------
    corpus_id : int
        Corpus ID
    chapter_name : str
        Chapter Name
    chapter_description : str
        Chapter Description
    chapter_data : List[List[Dict]]
        Chapter data as formatted by `CONLLU_PARSER.read_conllu_data()`
    """

    result = {
        "message": None,
        "style": None
    }

    # Assume `chapter_name` to be unique
    # In order to avoid the need to delete entire database when re-running
    # the `bulk_add_chapter` function
    # (otherwise there is unique `line_id` constraint violation)
    if Chapter.query.filter(
        Chapter.name == chapter_name
    ).first():
        result["message"] = f"Chapter '{chapter_name}' already exists."
        result["style"] = "warning"
        return result

    try:
        chapter = Chapter()
        chapter.corpus_id = corpus_id
        chapter.name = chapter_name
        chapter.description = chapter_description

        for _verse in chapter_data:
            verse = Verse()
            verse.chapter = chapter
            for _line in _verse:
                line = Line()
                if _line.get('id'):
                    line.id = _line.get('id')
                line.verse = verse
                line.text = _line.get('text', '')

                is_subtoken = False
                end_id = None
                for _idx, _token in enumerate(
                    _line["tokens"], start=1
                ):
                    _token_id = _token["id"]
                    inner_id = (
                        "".join(map(str, _token_id))
                        if isinstance(_token_id, (list, tuple))
                        else str(_token_id)
                    )
                    del _token["id"]

                    token = Token()
                    token.inner_id = inner_id
                    token.order = _idx * 10
                    token.line = line
                    token.text = _token["form"]
                    if is_subtoken:
                        token.text = "_"
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

                    if str(_token_id) == str(end_id):
                        is_subtoken = False
                        end_id = None

                    if isinstance(_token_id, (list, tuple)):
                        is_subtoken = True
                        end_id = _token_id[-1]

            # NOTE: SentenceBoundary task is auto created at the start
            # * Auto-boundary: Insert verse boundary as sentence boundary
            # * Use AUTO_ANNOTATOR_USER_ID as `annotator_id`
            # * Auto-boundary is used if the SentenceBoundary is not active
            task = Task.query.filter(
                Task.category == TASK_SENTENCE_BOUNDARY
            ).first()
            boundary = Boundary()
            boundary.task = task
            boundary.token = token
            boundary.verse = verse
            boundary.annotator_id = AUTO_ANNOTATION_USER_ID
            db.session.add(boundary)

    except Exception as e:
        result["message"] = "An error occurred while inserting data."
        result["style"] = "danger"
        LOGGER.exception(e)
    else:
        db.session.commit()
        result["message"] = f"Chapter '{chapter_name}' added successfully."
        result["style"] = "success"

    return result


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
    task_ids: List[int]
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

    Returns
    -------
    _type_
        _description_
    """

    chapters = Chapter.query.filter(Chapter.id.in_(chapter_ids)).all()
    annotators = User.query.filter(User.id.in_(annotator_ids)).all()

    data = {
        "chapter": {},
        "annotation": {},
    }

    # ----------------------------------------------------------------------- #

    for chapter in chapters:
        chapter_data = {
            "tokens": {},
            "verse_tokens": defaultdict(list),
        }

        # ------------------------------------------------------------------- #

        line_query = Line.query.filter(
            Line.verse.has(Verse.chapter_id == chapter.id)
        )
        for line in line_query.all():
            verse_id = line.verse_id
            line_tokens = {
                token.id: {
                    "id": token.id,
                    "inner_id": token.inner_id,
                    "verse_id": verse_id,
                    "line_id": token.line_id,
                    "order": token.order,
                    "text": token.text,
                    "lemma": token.lemma,
                    "analysis": token.analysis,
                    "annotator_id": token.annotator_id
                }
                for token in line.tokens.all()
                # if (
                #     token.annotator_id is None or
                #     token.annotator_id in annotator_ids
                # )
            }
            chapter_data["tokens"].update(line_tokens)
            chapter_data["verse_tokens"][verse_id].append(list(line_tokens))

        # ------------------------------------------------------------------- #

        data["chapter"][chapter.id] = chapter_data

        # ------------------------------------------------------------------- #

        verse_ids = [verse.id for verse in chapter.verses]
        for annotator in annotators:
            annotation_id = (chapter.id, annotator.id)
            annotation_data = defaultdict(dict)

            # --------------------------------------------------------------- #

            boundary_query = Boundary.query.filter(
                Boundary.verse_id.in_(verse_ids),
                Boundary.annotator_id == annotator.id
            ).order_by(Boundary.token_id)

            annotation_data[TASK_SENTENCE_BOUNDARY] = {
                boundary.id: {
                    "task_id": boundary.task_id,
                    "token_id": boundary.token_id,
                    "verse_id": boundary.verse_id,
                }
                for boundary in boundary_query.all()
            }
            boundary_ids = list(annotation_data[TASK_SENTENCE_BOUNDARY])

            # --------------------------------------------------------------- #

            word_order_query = WordOrder.query.filter(
                WordOrder.boundary_id.in_(boundary_ids),
                WordOrder.annotator_id == annotator.id
            ).join(Boundary).order_by(
                WordOrder.task_id, Boundary.token_id, WordOrder.order
            )

            # TODO: avoid .boundary.verse_id call ?
            # fetch from task_data[TASK_SENTENCE_BOUNDARY] ?
            annotation_data[TASK_WORD_ORDER] = [
                {
                    "task_id": word_order.task_id,
                    "verse_id": word_order.boundary.verse_id,
                    "boundary_id": word_order.boundary_id,
                    "token_id": word_order.token_id
                }
                for word_order in word_order_query.all()
            ]

            # --------------------------------------------------------------- #

            text_annotation_query = TokenTextAnnotation.query.filter(
                TokenTextAnnotation.boundary_id.in_(boundary_ids),
                TokenTextAnnotation.annotator_id == annotator.id,
                TokenTextAnnotation.is_deleted == False  # noqa
            ).order_by(TokenTextAnnotation.token_id)

            # TODO: avoid .boundary.verse_id call ?
            # fetch from task_data[TASK_SENTENCE_BOUNDARY] ?
            annotation_data[TASK_TOKEN_TEXT_ANNOTATION] = [
                {
                    "task_id": text_annotation.task_id,
                    "verse_id": text_annotation.boundary.verse_id,
                    "boundary_id": text_annotation.boundary_id,
                    "token_id": text_annotation.token_id,
                    "text": text_annotation.text
                }
                for text_annotation in text_annotation_query.all()
            ]

            # --------------------------------------------------------------- #

            token_classification_query = TokenClassification.query.filter(
                TokenClassification.boundary_id.in_(boundary_ids),
                TokenClassification.annotator_id == annotator.id,
                TokenClassification.is_deleted == False  # noqa
            ).order_by(TokenClassification.token_id)

            # TODO: avoid .boundary.verse_id call ?
            # fetch from task_data[TASK_SENTENCE_BOUNDARY] ?
            annotation_data[TASK_TOKEN_CLASSIFICATION] = [
                {
                    "task_id": tokclf.task_id,
                    "verse_id": tokclf.boundary.verse_id,
                    "boundary_id": tokclf.boundary_id,
                    "token_id": tokclf.token_id,
                    "label_id": tokclf.label_id,
                    "label_label": tokclf.label.label,
                    "label_description": tokclf.label.description,
                }
                for tokclf in token_classification_query.all()
            ]

            # --------------------------------------------------------------- #

            token_graph_query = TokenGraph.query.filter(
                TokenGraph.boundary_id.in_(boundary_ids),
                TokenGraph.annotator_id == annotator.id,
                TokenGraph.is_deleted == False  # noqa
            ).order_by(TokenGraph.src_id, TokenGraph.dst_id)

            # TODO: avoid .boundary.verse_id call ?
            # fetch from task_data[TASK_SENTENCE_BOUNDARY] ?
            annotation_data[TASK_TOKEN_GRAPH] = [
                {
                    "task_id": tokrel.task_id,
                    "verse_id": tokrel.boundary.verse_id,
                    "boundary_id": tokrel.boundary_id,
                    "src_id": tokrel.src_id,
                    "label_id": tokrel.label_id,
                    "label_label": tokrel.label.label,
                    "label_description": tokrel.label.description,
                    "dst_id": tokrel.dst_id,
                }
                for tokrel in token_graph_query.all()
            ]

            # --------------------------------------------------------------- #

            token_connection_query = TokenConnection.query.filter(
                TokenConnection.boundary_id.in_(boundary_ids),
                TokenConnection.annotator_id == annotator.id,
                TokenConnection.is_deleted == False  # noqa
            ).order_by(TokenConnection.src_id)

            # TODO: avoid .boundary.verse_id call ?
            # fetch from task_data[TASK_SENTENCE_BOUNDARY] ?
            annotation_data[TASK_TOKEN_CONNECTION] = [
                {
                    "task_id": token_connection.task_id,
                    "verse_id": token_connection.boundary.verse_id,
                    "boundary_id": token_connection.boundary_id,
                    "src_id": token_connection.src_id,
                    "dst_id": token_connection.dst_id,
                }
                for token_connection in token_connection_query.all()
            ]

            # --------------------------------------------------------------- #

            sentence_classification_query = SentenceClassification.query.filter(
                SentenceClassification.boundary_id.in_(boundary_ids),
                SentenceClassification.annotator_id == annotator.id,
                SentenceClassification.is_deleted == False  # noqa
            ).join(Boundary).order_by(Boundary.token_id)

            # TODO: avoid .boundary.verse_id call ?
            # fetch from task_data[TASK_SENTENCE_BOUNDARY] ?
            annotation_data[TASK_SENTENCE_CLASSIFICATION] = [
                {
                    "task_id": sentclf.task_id,
                    "verse_id": sentclf.boundary.verse_id,
                    "boundary_id": sentclf.boundary_id,
                    "label_id": sentclf.label_id,
                    "label_label": sentclf.label.label,
                    "label_description": sentclf.label.description,
                }
                for sentclf in sentence_classification_query.all()
            ]

            # --------------------------------------------------------------- #

            # NOTE: We show connections that at the src_boundary_id
            sentence_graph_query = SentenceGraph.query.filter(
                SentenceGraph.src_boundary_id.in_(boundary_ids),
                SentenceGraph.annotator_id == annotator.id,
                SentenceGraph.is_deleted == False  # noqa
            ).order_by(SentenceGraph.src_token_id)

            # TODO: avoid .src_boundary.verse_id call ?
            # TODO: avoid .dst_boundary.verse_id call ?
            # fetch from task_data[TASK_SENTENCE_BOUNDARY] ?
            # any guarantee that .dst_boundary. will be present?

            annotation_data[TASK_SENTENCE_GRAPH] = [
                {
                    "task_id": sentrel.task_id,
                    "src_verse_id": sentrel.src_boundary.verse_id,
                    "src_boundary_id": sentrel.src_boundary_id,
                    "src_token_id": sentrel.src_token_id,
                    "dst_verse_id": sentrel.dst_boundary.verse_id,
                    "dst_boundary_id": sentrel.dst_boundary_id,
                    "dst_token_id": sentrel.dst_token_id,
                    "label_id": sentrel.label_id,
                    "label_label": sentrel.label.label,
                    "label_description": sentrel.label.description,
                    "relation_type": sentrel.relation_type,
                }
                for sentrel in sentence_graph_query.all()
            ]

            # --------------------------------------------------------------- #

            data["annotation"][annotation_id] = annotation_data

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
        If the user has `PERMISSION_ANNOTATE` permissions,
        annotations will be fetched
    all : bool
        If True, and the user has `PERMISSION_CURATE` permission
        or `ROLE_ADMIN` role, annotations by all the users will be fetched.
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

    if user.has_permission(PERMISSION_ANNOTATE):
        annotator_ids = [user.id]

    if user.has_permission(PERMISSION_CURATE) or user.has_role(ROLE_ADMIN):
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
        Verse data, keyed by verse IDs
    """
    annotator_ids = annotator_ids or []
    line_object_query = Line.query.filter(Line.verse_id.in_(verse_ids))

    sentence_boundary_task_active = Task.query.filter(
        Task.category == TASK_SENTENCE_BOUNDARY,
        Task.is_deleted == False  # noqa
    ).one_or_none()
    word_order_task_active = Task.query.filter(
        Task.category == TASK_WORD_ORDER,
        Task.is_deleted == False  # noqa
    ).one_or_none()

    data = {}

    # TODO: Consider rewriting with a focus on Verse instead of Line
    # NOTE: Line ID is important for tokens
    # Do we want to change the database structure to remove Line table
    # altogether and only keep only a line_id field in Verse table?

    for line in line_object_query:
        verse_id = line.verse_id
        if not data.get(verse_id):
            data[verse_id] = {
                "verse_id": verse_id,
                "text": [line.text],
                "display": [[
                    token.display
                    for token in line.tokens.all()
                    if not token.annotator_id
                    # tokens that do not have annotator_id are original
                ]],
                "tokens": [[
                    {
                        "id": token.id,
                        "inner_id": token.inner_id,
                        "verse_id": verse_id,
                        "line_id": token.line_id,
                        "order": token.order,
                        "text": token.text,
                        "lemma": token.lemma,
                        "analysis": token.analysis,
                        # "display": token.display,
                        "annotator_id": token.annotator_id
                    }
                    for token in line.tokens.all()
                    # if (
                    #     token.annotator_id is None or
                    #     token.annotator_id in annotator_ids
                    # )
                    # NOTE: now tokens also have annotator_id,
                    # so, may be directly fetch with annotator_id or null
                    # (instead of doing this in Python)
                    # (null is needed for tokens from original corpus)
                    # Could also consider keeping original tokens in "tokens"
                    # and adding a "_tokens" for custom tokens
                ]],
                TASK_SENTENCE_BOUNDARY: {},
                "sentences": {},
                TASK_WORD_ORDER: {},
                TASK_TOKEN_TEXT_ANNOTATION: [],
                TASK_TOKEN_CLASSIFICATION: [],
                TASK_TOKEN_GRAPH: [],
                TASK_TOKEN_CONNECTION: [],
                TASK_SENTENCE_CLASSIFICATION: [],
                TASK_SENTENCE_GRAPH: [],
                "heuristics": {
                    TASK_WORD_ORDER: {},
                    TASK_TOKEN_TEXT_ANNOTATION: [],
                    TASK_TOKEN_CLASSIFICATION: [],
                    TASK_TOKEN_GRAPH: [],
                    TASK_TOKEN_CONNECTION: [],
                    TASK_SENTENCE_CLASSIFICATION: [],
                    TASK_SENTENCE_GRAPH: []
                },
                "progress": [
                    {
                        "task_id": p.task_id,
                        "task_short": p.task.short,
                        "verse_id": p.verse_id,
                        "annotator_id": p.annotator_id,
                        "updated_at": latest_update_time
                    }

                    for p, latest_update_time in db.session.query(
                        SubmitLog,
                        func.max(SubmitLog.updated_at)
                    ).filter(
                        SubmitLog.verse_id == verse_id,
                        SubmitLog.annotator_id.in_(annotator_ids),
                        Task.is_deleted == False  # noqa
                    ).group_by(
                        SubmitLog.task_id,
                        SubmitLog.annotator_id
                    ).join(
                        Task
                    ).order_by(Task.order).all()
                ]
            }
        else:
            data[verse_id]["text"].append(line.text)
            data[verse_id]["display"].append([
                token.display
                for token in line.tokens.all()
                if not token.annotator_id
                # tokens that do not have annotator_id are original
            ])
            data[verse_id]["tokens"].append([
                {
                    "id": token.id,
                    "inner_id": token.inner_id,
                    "verse_id": verse_id,
                    "line_id": token.line_id,
                    "order": token.order,
                    "text": token.text,
                    "lemma": token.lemma,
                    "analysis": token.analysis,
                    # "display": token.display,
                    "annotator_id": token.annotator_id
                }
                for token in line.tokens.all()
                # if (
                #     token.annotator_id is None or
                #     token.annotator_id in annotator_ids
                # )
            ])

    if sentence_boundary_task_active:
        boundary_query = Boundary.query.filter(
            Boundary.verse_id.in_(verse_ids),
            Boundary.annotator_id.in_(annotator_ids)
        ).order_by(Boundary.token_id)
    else:
        boundary_query = Boundary.query.filter(
            Boundary.verse_id.in_(verse_ids),
            Boundary.annotator_id == AUTO_ANNOTATION_USER_ID
        ).order_by(Boundary.token_id)

    # ----------------------------------------------------------------------- #
    # boundary specific data - BEGIN
    for boundary in boundary_query.all():
        verse_id = boundary.verse_id
        data[verse_id][TASK_SENTENCE_BOUNDARY][boundary.id] = {
            "id": boundary.id,
            "task_id": boundary.task_id,
            "token_id": boundary.token_id,
            "verse_id": boundary.verse_id,
            "annotator_id": boundary.annotator_id,
            "annotator": boundary.annotator.username,
        }
        if sentence_boundary_task_active:
            data[verse_id]["sentences"] = get_sentences(
                verse_id, boundary.annotator_id
            )
        else:
            data[verse_id]["sentences"] = get_sentences(
                verse_id, AUTO_ANNOTATION_USER_ID
            )

        # NOTE: Currently there is no support for multiple word order tasks.
        # Further, since the word order is used in other tasks to display
        # tokens, it is straightforward how such support would work, as it
        # would require a choice of word order task to display order
        word_order_query = WordOrder.query.filter(
            WordOrder.boundary_id == boundary.id,
            WordOrder.annotator_id.in_(annotator_ids)
        ).order_by(WordOrder.order)
        annotated_word_order = [
            a.token_id for a in word_order_query.all()
        ]
        verse_word_order = list(
            data[verse_id]["sentences"][boundary.id]
        )
        # if word_order doesn't exist, apply heuristic
        if not annotated_word_order:
            display_word_order = verse_word_order
            if word_order_task_active:
                heuristic_word_order = get_word_order(
                    data[verse_id]["sentences"][boundary.id]
                )
            else:
                heuristic_word_order = verse_word_order
            data[verse_id]["heuristics"][TASK_WORD_ORDER][boundary.id] = (
                heuristic_word_order
            )
        else:
            display_word_order = annotated_word_order
        data[verse_id][TASK_WORD_ORDER][boundary.id] = display_word_order
        # TODO: consider if we should provide predicted word_order separately
        #       instead of in the same field

        # ------------------------------------------------------------------- #

        text_annotation_query = TokenTextAnnotation.query.filter(
            TokenTextAnnotation.boundary_id == boundary.id,
            TokenTextAnnotation.annotator_id.in_(annotator_ids)
        )

        data[verse_id][TASK_TOKEN_TEXT_ANNOTATION].extend([
            {
                "id": text_annotation.id,
                "task_id": text_annotation.task_id,
                "boundary_id": text_annotation.boundary_id,
                "token_id": text_annotation.token_id,
                "text": text_annotation.text,
                "annotator_id": text_annotation.annotator_id,
                "is_deleted": text_annotation.is_deleted
            }
            for text_annotation in text_annotation_query.all()
        ])

        # ------------------------------------------------------------------- #

        token_classification_query = TokenClassification.query.filter(
            TokenClassification.boundary_id == boundary.id,
            TokenClassification.annotator_id.in_(annotator_ids)
        )

        data[verse_id][TASK_TOKEN_CLASSIFICATION].extend([
            {
                "id": tokclf.id,
                "task_id": tokclf.task_id,
                "boundary_id": tokclf.boundary_id,
                "token_id": tokclf.token_id,
                "label_id": tokclf.label_id,
                "annotator_id": tokclf.annotator_id,
                "is_deleted": tokclf.is_deleted
            }
            for tokclf in token_classification_query.all()
        ])

        # ------------------------------------------------------------------- #

        token_graph_query = TokenGraph.query.filter(
            TokenGraph.boundary_id == boundary.id,
            TokenGraph.annotator_id.in_(annotator_ids)
        )

        data[verse_id][TASK_TOKEN_GRAPH].extend([
            {
                "id": tokrel.id,
                "task_id": tokrel.task_id,
                "boundary_id": tokrel.boundary_id,
                "src_id": tokrel.src_id,
                "label_id": tokrel.label_id,
                "dst_id": tokrel.dst_id,
                "annotator_id": tokrel.annotator_id,
                "is_deleted": tokrel.is_deleted
            }
            for tokrel in token_graph_query.all()
        ])

        # NOTE: Do we pass task_id to get_token_graph()
        # * Would need to pass task_id all TOKEN_GRAPH category tasks,
        #   so would need an outer loop.
        #   e.g. for task_id in [valid_token_graph_tasks]:
        # Other alternative could be to have separate heuristic functions for
        # every token graph task, but managing that might be harder!

        sentence_tokens = data[verse_id]["sentences"][boundary.id]
        used_tokens = {
            _token_id: sentence_tokens[_token_id]
            for _token_id in data[verse_id][TASK_WORD_ORDER][boundary.id]
            if _token_id in sentence_tokens
        }

        # TODO: Need better heuristic management.
        # One option is to connect TASK_ID to heuristic functions
        # This mapping needs to be dynamic though? Since the task_ids would be
        # decided based on the order in which tasks are added.

        # The following assumes a single TOKEN_GRAPH task, else the dictionary
        # might not work well since there might be common labels across tasks
        # and their ID will get overwritten

        # Further, this relation map can be generated outside the verse loop,
        # so that it's calculated only once per function call instead of once
        # per boundary

        token_relation_label_query = TokenRelationLabel.query.filter(
            TokenRelationLabel.is_deleted == False  # noqa
        )
        token_relation_map = {
            token_relation_label.label: token_relation_label.id
            for token_relation_label in token_relation_label_query.all()
        }

        data[verse_id]["heuristics"][TASK_TOKEN_GRAPH].extend(
            get_token_graph(used_tokens, boundary.id, token_relation_map)
        )

        # ------------------------------------------------------------------- #

        token_connection_query = TokenConnection.query.filter(
            TokenConnection.boundary_id == boundary.id,
            TokenConnection.annotator_id.in_(annotator_ids)
        )

        data[verse_id][TASK_TOKEN_CONNECTION].extend([
            {
                "id": token_connection.id,
                "task_id": token_connection.task_id,
                "boundary_id": token_connection.boundary_id,
                "verse_id": token_connection.boundary.verse_id,
                "src_id": token_connection.src_id,
                "dst_id": token_connection.dst_id,
                "annotator_id": token_connection.annotator_id,
                "is_deleted": token_connection.is_deleted
            }
            for token_connection in token_connection_query.all()
        ])

        # ------------------------------------------------------------------- #

        sentence_classification_query = SentenceClassification.query.filter(
            SentenceClassification.boundary_id == boundary.id,
            SentenceClassification.annotator_id.in_(annotator_ids)
        )

        data[verse_id][TASK_SENTENCE_CLASSIFICATION].extend([
            {
                "id": sentclf.id,
                "task_id": sentclf.task_id,
                "boundary_id": sentclf.boundary_id,
                "label_id": sentclf.label_id,
                "annotator_id": sentclf.annotator_id,
                "is_deleted": sentclf.is_deleted
            }
            for sentclf in sentence_classification_query.all()
        ])

        # ------------------------------------------------------------------- #

        # NOTE: We show connections that at the src_boundary_id
        sentence_graph_query = SentenceGraph.query.filter(
            SentenceGraph.src_boundary_id == boundary.id,
            SentenceGraph.annotator_id.in_(annotator_ids)
        )

        data[verse_id][TASK_SENTENCE_GRAPH].extend([
            {
                "id": sentrel.id,
                "task_id": sentrel.task_id,
                "src_boundary_id": sentrel.src_boundary_id,
                "src_verse_id": sentrel.src_boundary.verse_id,
                "src_token_id": sentrel.src_token_id,
                "dst_boundary_id": sentrel.dst_boundary_id,
                "dst_verse_id": sentrel.dst_boundary.verse_id,
                "dst_token_id": sentrel.dst_token_id,
                "label_id": sentrel.label_id,
                "relation_type": sentrel.relation_type,
                "annotator_id": sentrel.annotator_id,
                "is_deleted": sentrel.is_deleted
            }
            for sentrel in sentence_graph_query.all()
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

    # get first token from the chapter the verse_id belongs to
    verse = Verse.query.get(verse_id)

    chapter_id = verse.chapter_id
    chapter_first_verse = Verse.query.filter(
        Verse.chapter_id == chapter_id
    ).order_by(Verse.id).first()
    chapter_first_line = Line.query.filter(
        Line.verse_id == chapter_first_verse.id
    ).order_by(Line.id).first()
    chapter_first_token = Token.query.filter(
        Token.line_id == chapter_first_line.id
    ).order_by(Token.id).first()

    verse_first_token = Token.query.filter(
        Token.line.has(Line.verse_id == verse_id)
    ).order_by(Token.id).first()

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
        previous_boundary.token_id
        if (
            previous_boundary is not None and
            previous_boundary.verse_id >= chapter_first_verse.id
        )
        else chapter_first_token.id - 1
    )
    # ----------------------------------------------------------------------- #

    extra_tokens = Token.query.filter(
        Token.line.has(Line.verse_id == verse_id),
        Token.annotator_id != None  # noqa
    ).all()
    sentences["extra"] = {
        token.id: {
            "id": token.id,
            "inner_id": token.inner_id,
            "line_id": token.line_id,
            "verse_id": verse_id,
            "text": token.text,
            "lemma": token.lemma,
            "analysis": token.analysis,
            "annotator_id": token.annotator_id
        }
        for token in extra_tokens
    }

    # ----------------------------------------------------------------------- #
    # TODO: If too many tokens, emit error? / consider first token of verse?

    for boundary in boundaries:
        tokens = Token.query.filter(
            Token.id > previous_boundary_token_id,
            Token.id <= boundary.token_id
        ).order_by(Token.id).all()

        sentences[boundary.id] = {
            token.id: {
                "id": token.id,
                "inner_id": token.inner_id,
                "sentence_id": boundary.id,
                "boundary_id": boundary.id,
                "order": token.order,
                "text": token.text,
                "lemma": token.lemma,
                "analysis": token.analysis,
                "annotator_id": token.annotator_id
            }
            for token in tokens
        }
        previous_boundary_token_id = boundary.token_id

    return sentences


###############################################################################
# Progress

def get_annotation_progress(annotator_ids: List[int] = None) -> Any:
    fetch_all_users = annotator_ids is None
    # ----------------------------------------------------------------------- #
    # progress query
    # one entry per user per verse
    progress_query = SubmitLog.query.with_entities(
        SubmitLog.annotator_id,
        Verse.chapter_id,
        SubmitLog.verse_id,
        func.group_concat(SubmitLog.task_id.distinct()).label("task_list"),
        # NOTE: task_count isn't really required if there's another processing
        # phase. (`task_count = len(task_list.split(","))`)
        # processing is currently done on the JS side,
        # making task_count further unnecessary
        func.count(SubmitLog.task_id.distinct()).label("task_count"),
        func.min(SubmitLog.updated_at).label("first_update_at"),
        func.max(SubmitLog.updated_at).label("last_update_at"),
    ).filter(
        True if fetch_all_users else SubmitLog.annotator_id.in_(annotator_ids),
        Task.is_deleted == False  # noqa
    ).join(
        Task, Verse
    ).group_by(
        SubmitLog.annotator_id, SubmitLog.verse_id
    ).order_by(
        SubmitLog.annotator_id, SubmitLog.verse_id, SubmitLog.task_id,
    )
    # ----------------------------------------------------------------------- #
    # progress record
    progress_record = defaultdict(lambda: defaultdict(list))
    for row in progress_query.all():
        (
            annotator_id, chapter_id, verse_id,
            task_list, task_count,
            first_update_at, last_update_at
        ) = row
        progress_record[annotator_id][chapter_id].append(
            {
                "verse_id": verse_id,
                "task_list": task_list,
                "task_count": task_count,
                "first_update_at": first_update_at,
                "last_update_at": last_update_at
            }
        )
    # ----------------------------------------------------------------------- #
    # task detail
    task_detail = {
        task.id: {
            "title": task.title,
            "short": task.short,
            "category": task.category,
        }
        for task in Task.query.all()
    }
    # ----------------------------------------------------------------------- #
    # user detail
    user_detail = {
        user.id: {
            "email": user.email,
            "username": user.username,
        }
        for user in User.query.filter(
            True if fetch_all_users else User.id.in_(annotator_ids),
        ).all()
    }
    # ----------------------------------------------------------------------- #
    # chapter detail
    chapter_detail = {
        chapter_id: {
            "chapter_id": chapter_id,
            "chapter_name": chapter_name,
            "book_name": chapter_name.split()[0],
            "verse_count": verse_count
        }
        for chapter_id, chapter_name, verse_count in Verse.query.with_entities(
            Verse.chapter_id,
            Chapter.name,
            func.count(Chapter.id).label("verse_count")
        ).join(Chapter).group_by(Verse.chapter_id).all()
    }
    # ----------------------------------------------------------------------- #

    return {
        "progress": progress_record,
        "task": task_detail,
        "chapter": chapter_detail,
        "user": user_detail,
    }


###############################################################################
# Clone Annotations


def clone_user_annotations(
    source_user_ids: List[int],
    target_user_id: int,
    task_ids: List[int] = None,
    chapter_ids: List[int] = None,
) -> Dict[str, Any]:
    """Clone annotations from one or more annotators to a target annotator

    Parameters
    ----------
    source_user_ids : List[int]
        ID of the annotator(s) whose annotations are to be copied
    target_user_id : int
        ID of the annotator to whom the annotations are to be copied

    Returns
    -------
    Dict[str, Any]
        Result of the copy operation
    """
    task_table_models = {
        TASK_SENTENCE_BOUNDARY: Boundary,
        TASK_WORD_ORDER: WordOrder,
        TASK_TOKEN_TEXT_ANNOTATION: TokenTextAnnotation,
        TASK_TOKEN_CLASSIFICATION: TokenClassification,
        TASK_TOKEN_GRAPH: TokenGraph,
        TASK_TOKEN_CONNECTION: TokenConnection,
        TASK_SENTENCE_CLASSIFICATION: SentenceClassification,
        TASK_SENTENCE_GRAPH: SentenceGraph
    }

    # NOTE: TASK_SENTENCE_BOUNDARY is always included in cloning,
    # even if `task_ids` do not contain a boundary task.
    # REASON: As all other annotation tasks refer to `boundary_id`,
    # not copying boundary task would imply we have to refer  to original
    # `boundary_id` and if any of the original annotation changes,
    # it'll CASCADE delete. Thus, not copying boundary could result in some
    # annotator's actions affecting someone else's annotations.

    # NOTE: Assumption is that there's only one SentenceBoundary task
    # TODO: Do we want to somehow obtain task id of SentenceBoundary task?
    # NOTE: The sorted() call is to ensure that we clone boundary task first
    task_id_sentence_boundary = 1
    if task_ids is not None and task_id_sentence_boundary not in task_ids:
        task_ids = sorted(
            set([task_id_sentence_boundary, *(map(int, task_ids))])
        )

    clone_tasks = {
        task.id: task.category
        for task in Task.query.filter(
            True if task_ids is None else Task.id.in_(task_ids),
            Task.is_deleted == False,  # noqa
        ).all()
    }

    # We maintain a `boundary_id_map`, a map of old boundary ids to the
    # new boundary ids (generating new ids requires us to `flush()`).
    boundary_id_map = {}

    # data corresponding to columns in `exclude_columns` is not copied
    # they are updated using various strategies
    exclude_columns = ['id', 'annotator_id', 'is_clone', 'cloned_from_id']
    # NOTE: boundary_columns do need to be copied at first so that we retain
    # a reference of what to replace it with
    boundary_columns = ['boundary_id', 'src_boundary_id', 'dst_boundary_id']
    # those belonging to `update_columns` are set to the fixed values
    update_columns = {
        'annotator_id': target_user_id,
        'is_clone': True
    }
    # `boundary_id_map` is used to update boundary_columns
    # `cloned_from_id` is set to `id` of original row

    # ----------------------------------------------------------------------- #
    # clone tasks

    result = {
        "status": True,
        "errors": [],
        "count": {}
    }

    for task_id, task_category in clone_tasks.items():
        task_key = (task_id, task_category)
        task_model = task_table_models[task_category]
        column_names = [
            column.name for column in task_model.__table__.columns
        ]
        if chapter_ids is not None:
            if task_category == TASK_SENTENCE_BOUNDARY:
                chapter_condition = task_model.verse.has(
                    Verse.chapter_id.in_(chapter_ids)
                )
            else:
                chapter_condition = task_model.boundary.has(
                    Boundary.verse.has(
                        Verse.chapter_id.in_(chapter_ids)
                    )
                )
        else:
            chapter_condition = True

        cloned_task_annotations = [
            task_model(
                **{
                    column_name: getattr(row, column_name)
                    for column_name in column_names
                    if column_name not in exclude_columns
                },
                **update_columns,
                cloned_from_id=row.id
            )
            for row in task_model.query.filter(
                task_model.annotator_id.in_(source_user_ids),
                task_model.task_id == task_id,
                task_model.is_deleted == False if hasattr(task_model, "is_deleted") else True,  # noqa
                chapter_condition,
            ).all()
        ]
        if task_category == TASK_SENTENCE_BOUNDARY:
            # NOTE: This MUST happen first before any other task.
            try:
                # NOTE: we need `return_defaults=True` in order to ensure that
                # `id` values get populated after flush() is called.
                db.session.bulk_save_objects(
                    cloned_task_annotations, return_defaults=True
                )
            except Exception as e:
                LOGGER.exception(e)
                db.session.rollback()
                result["status"] = False
                result["errors"].append(
                    f"Error in copying {task_key} annotations."
                )
                # abort if we fail in copying boundary annotations
                return result
            else:
                # after `flush()`, we have `id` columns populated
                # store `boundary_id_map`
                db.session.flush()
                result["count"][task_key] = len(cloned_task_annotations)

                for annotation_object in cloned_task_annotations:
                    old_boundary_id = annotation_object.cloned_from_id
                    new_boundary_id = annotation_object.id
                    boundary_id_map[old_boundary_id] = new_boundary_id
        else:
            for annotation_object in cloned_task_annotations:
                for column in boundary_columns:
                    if hasattr(annotation_object, column):
                        current_id = getattr(annotation_object, column)
                        replacement_id = boundary_id_map[current_id]
                        setattr(annotation_object, column, replacement_id)

            try:
                db.session.bulk_save_objects(cloned_task_annotations)
            except Exception as e:
                LOGGER.exception(e)
                db.session.rollback()
                result["status"] = False
                result["errors"].append(
                    f"Error in copying {task_key} annotations."
                )
                return result
            else:
                result["count"][task_key] = len(cloned_task_annotations)

    # we reach this point means there were no errors
    db.session.commit()
    return result


###############################################################################
