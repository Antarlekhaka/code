#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Utility Functions
"""

###############################################################################

import logging
from typing import Dict, List
from collections import defaultdict
import uuid

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


def get_unique_id():
    return uuid.uuid4()


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

    data = {
        "chapter": {},
        "annotation": {},
        "visual": {}
    }

    node_ids = {}

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
            task_data = defaultdict(dict)

            # --------------------------------------------------------------- #

            boundary_query = Boundary.query.filter(
                Boundary.verse_id.in_(verse_ids),
                Boundary.annotator_id == annotator.id
            ).order_by(Boundary.token_id)

            annotation_data["sentence_boundary"] = {
                boundary.id: {
                    "token_id": boundary.token_id,
                    "verse_id": boundary.verse_id,
                }
                for boundary in boundary_query.all()
            }
            boundary_ids = list(annotation_data["sentence_boundary"])

            # --------------------------------------------------------------- #

            anvaya_query = Anvaya.query.filter(
                Anvaya.boundary_id.in_(boundary_ids),
                Anvaya.annotator_id == annotator.id
            ).join(Boundary).order_by(Boundary.token_id, Anvaya.order)
            annotation_data["anvaya"] = [
                {
                    "verse_id": anvaya.boundary.verse_id,
                    "boundary_id": anvaya.boundary_id,
                    "token_id": anvaya.token_id
                }
                for anvaya in anvaya_query.all()
            ]

            # --------------------------------------------------------------- #

            entity_query = Entity.query.filter(
                Entity.boundary_id.in_(boundary_ids),
                Entity.annotator_id == annotator.id,
                Entity.is_deleted == False  # noqa
            ).order_by(Entity.token_id)
            annotation_data["named_entity"] = [
                {
                    "verse_id": entity.boundary.verse_id,
                    "boundary_id": entity.boundary_id,
                    "token_id": entity.token_id,
                    "label_id": entity.label_id,
                    "label_label": entity.label.label,
                    "label_description": entity.label.description,
                }
                for entity in entity_query.all()
            ]

        # ------------------------------------------------------------------- #

            token_graph_query = TokenGraph.query.filter(
                TokenGraph.boundary_id.in_(boundary_ids),
                TokenGraph.annotator_id == annotator.id,
                TokenGraph.is_deleted == False  # noqa
            ).order_by(TokenGraph.src_id, TokenGraph.dst_id)

            annotation_data["token_graph"] = [
                {
                    "verse_id": relation.boundary.verse_id,
                    "boundary_id": relation.boundary_id,
                    "src_id": relation.src_id,
                    "label_id": relation.label_id,
                    "label_label": relation.label.label,
                    "label_description": relation.label.description,
                    "dst_id": relation.dst_id,
                }
                for relation in token_graph_query.all()
            ]

            # --------------------------------------------------------------- #

            coreference_query = Coreference.query.filter(
                Coreference.boundary_id.in_(boundary_ids),
                Coreference.annotator_id == annotator.id,
                Coreference.is_deleted == False  # noqa
            ).order_by(Coreference.src_id)

            annotation_data["coreference"] = [
                {
                    "verse_id": coreference.boundary.verse_id,
                    "boundary_id": coreference.boundary_id,
                    "src_id": coreference.src_id,
                    "dst_id": coreference.dst_id,
                }
                for coreference in coreference_query.all()
            ]

            # --------------------------------------------------------------- #

            sentence_classification_query = SentenceClassification.query.filter(
                SentenceClassification.boundary_id.in_(boundary_ids),
                SentenceClassification.annotator_id == annotator.id,
                SentenceClassification.is_deleted == False  # noqa
            ).join(Boundary).order_by(Boundary.token_id)

            annotation_data["sentence_classification"] = [
                {
                    "verse_id": sentclf.boundary.verse_id,
                    "boundary_id": sentclf.boundary_id,
                    "label_id": sentclf.label_id,
                    "label_label": sentclf.label.label,
                }
                for sentclf in sentence_classification_query.all()
            ]

            # --------------------------------------------------------------- #

            # NOTE: We show connections that at the src_boundary_id
            intersentence_connection_query = DiscourseGraph.query.filter(
                DiscourseGraph.src_boundary_id.in_(boundary_ids),
                DiscourseGraph.annotator_id == annotator.id,
                DiscourseGraph.is_deleted == False  # noqa
            ).order_by(DiscourseGraph.src_token_id)

            annotation_data["intersentence_connection"] = [
                {
                    "src_verse_id": isc.src_boundary.verse_id,
                    "src_boundary_id": isc.src_boundary_id,
                    "src_token_id": isc.src_token_id,
                    "dst_verse_id": isc.dst_boundary.verse_id,
                    "dst_boundary_id": isc.dst_boundary_id,
                    "dst_token_id": isc.dst_token_id,
                    "label_id": isc.label_id,
                    "label_label": isc.label.label,
                    "relation_type": isc.relation_type,
                }
                for isc in intersentence_connection_query.all()
            ]

            # --------------------------------------------------------------- #

            data["annotation"][annotation_id] = annotation_data

        # ------------------------------------------------------------------- #
        # Visual
        # ------------------------------------------------------------------- #

        for annotation_id, annotation_data in data["annotation"].items():

            # --------------------------------------------------------------- #

            boundary_tokens = [
                boundary["token_id"]
                for boundary in annotation_data["sentence_boundary"].values()
            ]
            next_boundary = boundary_tokens[0] if boundary_tokens else None

            display_text = []
            for verse_id, verse_tokens in chapter_data["verse_tokens"].items():
                for line_tokens in verse_tokens:
                    line_text = []
                    for token_id in line_tokens:
                        token = chapter_data["tokens"][token_id]

                        if token["text"] and token["text"] not in ["_"]:
                            if token["annotator_id"] is None:
                                line_text.append(token["text"])

                            if next_boundary and next_boundary == token_id:
                                line_text.append("##")
                                boundary_tokens.pop(0)
                                next_boundary = (
                                    boundary_tokens[0]
                                    if boundary_tokens
                                    else None
                                )

                    display_text.append(line_text)
                display_text[-1].extend(["//", str(verse_id)])
                display_text.append([])

            task_data["sentence_boundary"] = "\n".join(
                " ".join(line_text)
                for line_text in display_text
            )

            # --------------------------------------------------------------- #

            preference = ["misc.Unsandhied", "form", "lemma"]
            display_text = []

            sentences = {}
            current_boundary_id = None
            sentence_tokens = []

            for anvaya in annotation_data["anvaya"]:
                if current_boundary_id is None:
                    current_boundary_id = anvaya["boundary_id"]

                if current_boundary_id != anvaya["boundary_id"]:
                    sentence_text = " ".join(sentence_tokens)
                    sentences[current_boundary_id] = sentence_text
                    display_text.append(
                        f"{anvaya['verse_id']}:\t{sentence_text}"
                    )

                    current_boundary_id = anvaya["boundary_id"]
                    sentence_tokens = []

                token_id = anvaya["token_id"]
                token = chapter_data["tokens"][token_id]
                for key in preference:
                    if "." in key:
                        k1, k2 = key.split(".", 1)
                        token_text = token["analysis"].get(k1, {}).get(k2)
                    else:
                        token_text = token["analysis"].get(key)
                    if token_text and token_text not in ["_"]:
                        sentence_tokens.append(token_text)
                        break
            else:
                sentence_text = " ".join(sentence_tokens)
                sentences[current_boundary_id] = sentence_text
                display_text.append(
                    f"{anvaya['verse_id']}:\t{sentence_text}"
                )

            task_data["anvaya"] = "\n\n".join(
                sentence_text
                for sentence_text in display_text
            )

            # --------------------------------------------------------------- #

            preference = ["lemma", "misc.Unsandhied", "form"]
            display_text = [
                ["Verse", "Token", "Label", "Description"],
                ["=====", "=====", "=====", "==========="]
            ]

            for entity in annotation_data["named_entity"]:
                entity_token_id = entity["token_id"]
                entity_token = chapter_data["tokens"][entity_token_id]
                for key in preference:
                    if "." in key:
                        k1, k2 = key.split(".", 1)
                        token_text = entity_token["analysis"].get(
                            k1, {}
                        ).get(k2)
                    else:
                        token_text = entity_token["analysis"].get(key)

                    if token_text and token_text not in ["_"]:
                        break

                display_text.append([
                    str(entity["verse_id"]),
                    token_text,
                    entity["label_label"],
                    entity["label_description"]
                ])

            task_data["named_entity"] = "\n".join(
                "\t".join(entity_row)
                for entity_row in display_text
            )

            # --------------------------------------------------------------- #

            preference = ["lemma", "misc.Unsandhied", "form"]

            token_graph_data = {
                "nodes": [],
                "edges": []
            }

            for relation in annotation_data["token_graph"]:
                from_id = None
                to_id = None

                for token_id in [relation["src_id"], relation["dst_id"]]:
                    token = chapter_data["tokens"][token_id]
                    for key in preference:
                        if "." in key:
                            k1, k2 = key.split(".", 1)
                            token_text = token["analysis"].get(k1, {}).get(k2)
                        else:
                            token_text = token["analysis"].get(key)

                        if token_text and token_text not in ["_"]:
                            break
                    if token_text not in node_ids:
                        node_ids[token_text] = get_unique_id()

                        token_graph_data["nodes"].append({
                            "id": node_ids[token_text],
                            "label": token_text,
                            "value": 3,
                            "group": None
                        })

                    if token_id == relation["src_id"]:
                        from_id = node_ids[token_text]
                    if token_id == relation["dst_id"]:
                        to_id = node_ids[token_text]

                token_graph_data["edges"].append({
                    "from": from_id,
                    "to": to_id,
                    "label": relation["label_label"],
                    "title": relation["label_description"],
                    "arrows": {
                        "to": {
                            "enabled": True
                        }
                    },
                    "value": 3,
                })

            task_data["token_graph"] = token_graph_data

            # --------------------------------------------------------------- #

            preference = ["lemma", "misc.Unsandhied", "form"]

            clusters = defaultdict(list)

            for coref in annotation_data["coreference"]:
                src_text = None
                dst_text = None

                for token_id in [coref["src_id"], coref["dst_id"]]:
                    token = chapter_data["tokens"][token_id]
                    for key in preference:
                        if "." in key:
                            k1, k2 = key.split(".", 1)
                            token_text = token["analysis"].get(k1, {}).get(k2)
                        else:
                            token_text = token["analysis"].get(key)

                        if token_text and token_text not in ["_"]:
                            break

                    if token_id == coref["src_id"]:
                        src_text = token_text
                    if token_id == coref["dst_id"]:
                        dst_text = token_text

            # TODO: form clusters (how?) id-based? or text-based?

            task_data["coreference"] = str(annotation_data["coreference"])

            # --------------------------------------------------------------- #

            display_text = [
                ["Verse", "Sentence", "Label", "Description"],
                ["=====", "========", "=====", "==========="]
            ]

            task_data["sentence_classification"] = str(
                annotation_data["sentence_classification"]
            )

            # --------------------------------------------------------------- #

            task_data["intersentence_connection"] = str(
                annotation_data["intersentence_connection"]
            )

            # --------------------------------------------------------------- #

            data["visual"][annotation_id] = task_data

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

    if user.has_permission("annotate"):
        annotator_ids = [user.id]

    if user.has_permission("curate") or user.has_role("admin"):
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
                "boundary": {},
                "sentences": {},
                "anvaya": {},
                "entity": [],
                "relation": [],
                "coreference": [],
                "sentence_classification": [],
                "intersentence_connection": [],
                "progress": [
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
        data[verse_id]["boundary"][boundary.id] = {
            "id": boundary.id,
            "token_id": boundary.token_id,
            "verse_id": boundary.verse_id,
            "annotator_id": boundary.annotator_id,
            "annotator": boundary.annotator.username,
        }
        data[verse_id]["sentences"] = get_sentences(
            verse_id, boundary.annotator_id
        )
        anvaya_query = Anvaya.query.filter(
            Anvaya.boundary_id == boundary.id,
            Anvaya.annotator_id.in_(annotator_ids)
        ).order_by(Anvaya.order)
        sentence_anvaya = [
            a.token_id for a in anvaya_query.all()
        ]
        # if anvaya doesn"t exist, apply heuristic
        if not sentence_anvaya:
            sentence_anvaya = get_anvaya(
                data[verse_id]["sentences"][boundary.id]
            )

        data[verse_id]["anvaya"][boundary.id] = sentence_anvaya
        # TODO: consider if we should provide predicted anvaya separately
        #       instead of in the same field

        # ------------------------------------------------------------------- #

        entity_query = Entity.query.filter(
            Entity.boundary_id == boundary.id,
            Entity.annotator_id.in_(annotator_ids)
        )

        data[verse_id]["entity"].extend([
            {
                "id": entity.id,
                "boundary_id": entity.boundary_id,
                "token_id": entity.token_id,
                "label_id": entity.label_id,
                "annotator_id": entity.annotator_id,
                "is_deleted": entity.is_deleted
            }
            for entity in entity_query.all()
        ])

        # ------------------------------------------------------------------- #

        token_graph_query = TokenGraph.query.filter(
            TokenGraph.boundary_id == boundary.id,
            TokenGraph.annotator_id.in_(annotator_ids)
        )

        data[verse_id]["relation"].extend([
            {
                "id": relation.id,
                "boundary_id": relation.boundary_id,
                "src_id": relation.src_id,
                "label_id": relation.label_id,
                "dst_id": relation.dst_id,
                "annotator_id": relation.annotator_id,
                "is_deleted": relation.is_deleted
            }
            for relation in token_graph_query.all()
        ])

        # ------------------------------------------------------------------- #

        coreference_query = Coreference.query.filter(
            Coreference.boundary_id == boundary.id,
            Coreference.annotator_id.in_(annotator_ids)
        )

        data[verse_id]["coreference"].extend([
            {
                "id": coreference.id,
                "boundary_id": coreference.boundary_id,
                "src_id": coreference.src_id,
                "dst_id": coreference.dst_id,
                "annotator_id": coreference.annotator_id,
                "is_deleted": coreference.is_deleted
            }
            for coreference in coreference_query.all()
        ])

        # ------------------------------------------------------------------- #

        sentence_classification_query = SentenceClassification.query.filter(
            SentenceClassification.boundary_id == boundary.id,
            SentenceClassification.annotator_id.in_(annotator_ids)
        )

        data[verse_id]["sentence_classification"].extend([
            {
                "id": sentclf.id,
                "boundary_id": sentclf.boundary_id,
                "label_id": sentclf.label_id,
                "annotator_id": sentclf.annotator_id,
                "is_deleted": sentclf.is_deleted
            }
            for sentclf in sentence_classification_query.all()
        ])

        # ------------------------------------------------------------------- #

        # NOTE: We show connections that at the src_boundary_id
        intersentence_connection_query = DiscourseGraph.query.filter(
            DiscourseGraph.src_boundary_id == boundary.id,
            DiscourseGraph.annotator_id.in_(annotator_ids)
        )

        data[verse_id]["intersentence_connection"].extend([
            {
                "id": isc.id,
                "src_boundary_id": isc.src_boundary_id,
                "src_token_id": isc.src_token_id,
                "dst_boundary_id": isc.dst_boundary_id,
                "dst_token_id": isc.dst_token_id,
                "label_id": isc.label_id,
                "relation_type": isc.relation_type,
                "annotator_id": isc.annotator_id,
                "is_deleted": isc.is_deleted
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
    sentences["extra"] = {
        token.id: {
            "id": token.id,
            "text": token.text,
            "lemma": token.lemma,
            "analysis": token.analysis,
            "annotator_id": token.annotator_id
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
                "id": token.id,
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
