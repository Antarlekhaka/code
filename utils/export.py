#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export Data
"""

###############################################################################

import uuid
from typing import List
from collections import defaultdict

import networkx as nx

###############################################################################


def get_unique_id():
    return uuid.uuid4()


def get_token_text(token: dict, key_preference: List[str]):
    token_text = None

    for key in key_preference:
        if "." in key:
            k1, k2 = key.split(".", 1)
            token_text = token["analysis"].get(k1, {}).get(k2)
        else:
            token_text = token["analysis"].get(key)
        if token_text and token_text not in ["_"]:
            break

    return token_text

###############################################################################
# Simple Format
# --------------------------------------------------------------------------- #


def simple_format(data):
    node_ids = {}
    simple_data = {}

    for chpater_id, chapter_data in data["chapter"].items():

        # chapter_data = {
        #     "tokens": {},
        #     "verse_tokens": defaultdict(list),
        # }

        for annotation_id, annotation_data in data["annotation"].items():

            task_data = defaultdict(dict)

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

            sentences = {}
            display_text = []

            current_boundary_id = None
            current_verse_id = None
            sentence_tokens = []

            for anvaya in annotation_data["anvaya"]:
                if current_boundary_id is None:
                    current_boundary_id = anvaya["boundary_id"]
                    current_verse_id = anvaya["verse_id"]

                if current_boundary_id != anvaya["boundary_id"]:
                    sentence_text = " ".join(sentence_tokens)
                    sentences[current_boundary_id] = sentence_text
                    display_text.append(
                        f"{current_verse_id}:\t{sentence_text}"
                    )

                    current_boundary_id = anvaya["boundary_id"]
                    current_verse_id = anvaya["verse_id"]
                    sentence_tokens = []

                token_id = anvaya["token_id"]
                token = chapter_data["tokens"][token_id]
                token_text = get_token_text(token, preference)
                sentence_tokens.append(token_text)
            else:
                sentence_text = " ".join(sentence_tokens)
                sentences[current_boundary_id] = sentence_text
                display_text.append(f"{current_verse_id}:\t{sentence_text}")

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
                token_text = get_token_text(entity_token, preference)

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
                    token_text = get_token_text(token, preference)

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

            coreference_graph = nx.DiGraph()
            coreference_graph.add_edges_from([
                (coref["src_id"], coref["dst_id"])
                for coref in annotation_data["coreference"]
            ])

            display_text = []

            clusters = nx.weakly_connected_components(coreference_graph)
            for cluster in clusters:
                cluster_text = []
                for token_id in cluster:
                    token = chapter_data["tokens"][token_id]
                    token_text = get_token_text(token, preference)
                    cluster_text.append(
                        f"{token_text}/{token['verse_id']}/{token['order']}"
                    )

                display_text.append(cluster_text)

            task_data["coreference"] = "\n\n".join(
                ", ".join(cluster_text)
                for cluster_text in display_text
            )

            # --------------------------------------------------------------- #

            display_text = [
                ["Verse", "Sentence", "Label", "Description"],
                ["=====", "========", "=====", "==========="]
            ]

            for snclf in annotation_data["sentence_classification"]:
                display_text.append([
                    str(snclf["verse_id"]),
                    sentences[snclf["boundary_id"]],
                    snclf["label_label"],
                    snclf["label_description"]
                ])

            task_data["sentence_classification"] = "\n".join(
                "\t".join(sentence_row)
                for sentence_row in display_text
            )

            # --------------------------------------------------------------- #

            task_data["intersentence_connection"] = str(
                annotation_data["intersentence_connection"]
            )

            # --------------------------------------------------------------- #

            simple_data[annotation_id] = task_data

    return simple_data


###############################################################################
# Standard Format
# --------------------------------------------------------------------------- #


def standard_format(data):
    pass


###############################################################################
