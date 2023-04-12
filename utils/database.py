#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Utility Functions

Note: Functions are usable only in an application context.

@author: Hrishikesh Terdalkar
"""

###############################################################################

import logging
from typing import Dict, List
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
from utils.heuristic import get_word_order

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
                if (
                    token.annotator_id is None or
                    token.annotator_id in annotator_ids
                )
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
                    if (
                        token.annotator_id is None or
                        token.annotator_id in annotator_ids
                    )
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
                        SubmitLog.task_id
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
                if (
                    token.annotator_id is None or
                    token.annotator_id in annotator_ids
                )
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
        sentence_word_order = [
            a.token_id for a in word_order_query.all()
        ]
        # if word_order doesn't exist, apply heuristic
        if not sentence_word_order:
            if word_order_task_active:
                sentence_word_order = get_word_order(
                    data[verse_id]["sentences"][boundary.id]
                )
            else:
                sentence_word_order = list(
                    data[verse_id]["sentences"][boundary.id]
                )

        data[verse_id][TASK_WORD_ORDER][boundary.id] = sentence_word_order
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
