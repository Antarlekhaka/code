#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export Data

@author: Hrishikesh Terdalkar
"""

###############################################################################

import uuid
from typing import List
from collections import defaultdict

import networkx as nx

from constants import (
    TASK_SENTENCE_BOUNDARY,
    TASK_WORD_ORDER,
    TASK_TOKEN_TEXT_ANNOTATION,
    TASK_TOKEN_CLASSIFICATION,
    TASK_TOKEN_GRAPH,
    TASK_TOKEN_CONNECTION,
    TASK_SENTENCE_CLASSIFICATION,
    TASK_SENTENCE_GRAPH
)

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
# Format Data
# --------------------------------------------------------------------------- #


def format_data(data, **kwargs):
    simple_data = {}
    standard_data = {}

    token_text_preference_map = kwargs.get("token_text_preference", {})
    default_token_text_preference = ["lemma", "form"]

    # for chapter_id, chapter_data in data["chapter"].items():
    #     print(chapter_id)
    #     print(chapter_data.keys())
    #     print(chapter_data["tokens"].keys())

    for annotation_id, annotation_data in data["annotation"].items():
        chapter_id, annotator_id = annotation_id
        chapter_data = data["chapter"][chapter_id]

        task_data_simple = defaultdict(lambda: defaultdict(dict))
        task_data_standard = defaultdict(lambda: defaultdict(dict))

        # ------------------------------------------------------------------- #
        # NOTE: Assumption is that there's only one SentenceBoundary task
        # TODO: Obtain Task ID of SentenceBoundary Task
        # Don't want to add database calls from this module, so perhaps
        # export task_id from `export_data` function itself
        # (as with the other tasks)
        task_id = 1

        boundary_tokens = [
            boundary["token_id"]
            for boundary in annotation_data[TASK_SENTENCE_BOUNDARY].values()
        ]
        next_boundary = boundary_tokens[0] if boundary_tokens else None

        text_simple = []
        text_standard = []
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

                text_simple.append(line_text)
            text_simple[-1].extend(["//", str(verse_id)])
            text_simple.append([])

        task_data_simple[TASK_SENTENCE_BOUNDARY][task_id] = "\n".join(
            " ".join(line_text)
            for line_text in text_simple
        )
        task_data_standard[TASK_SENTENCE_BOUNDARY][task_id] = None

        # ------------------------------------------------------------------- #
        # NOTE: Assumption is that there's only one WordOrder task
        # TODO: Obtain Task ID of WordOrder Task
        # Don't want to add database calls from this module, so perhaps
        # export task_id from `export_data` function itself
        # (as with the other tasks)
        task_id = 2

        preference = token_text_preference_map.get(
            TASK_WORD_ORDER, default_token_text_preference
        )

        SENTENCE_TEXT = {}
        text_simple = [
            ["#", "Verse", "Word Order"],
            ["-", "-----", "----------"]
        ]
        text_standard = []

        sent_idx = 0
        current_boundary_id = None
        current_verse_id = None
        sentence_token_texts = []

        for word_order in annotation_data[TASK_WORD_ORDER]:
            if current_boundary_id is None:
                current_boundary_id = word_order["boundary_id"]
                current_verse_id = word_order["verse_id"]

            if current_boundary_id != word_order["boundary_id"]:
                sent_idx += 1
                sentence_text = " ".join(sentence_token_texts)
                SENTENCE_TEXT[current_boundary_id] = sentence_text
                text_simple.append(
                    [str(sent_idx), str(current_verse_id), sentence_text]
                )

                current_boundary_id = word_order["boundary_id"]
                current_verse_id = word_order["verse_id"]
                sentence_token_texts = []

            token_id = word_order["token_id"]
            token = chapter_data["tokens"][token_id]
            token_text = get_token_text(token, preference)
            sentence_token_texts.append(token_text)
        else:
            sent_idx += 1
            sentence_text = " ".join(sentence_token_texts)
            SENTENCE_TEXT[current_boundary_id] = sentence_text
            text_simple.append(
                [str(sent_idx), str(current_verse_id), sentence_text]
            )

        task_data_simple[TASK_WORD_ORDER][task_id] = "\n".join(
            "\t".join(sentence_row)
            for sentence_row in text_simple
        )
        task_data_standard[TASK_WORD_ORDER][task_id] = None

        # ------------------------------------------------------------------- #

        preference = token_text_preference_map.get(
            TASK_TOKEN_TEXT_ANNOTATION, default_token_text_preference
        )
        text_simple_header = [
            ["Verse", "Token", "Annotation"],
            ["-----", "-----", "----------"]
        ]
        text_simple = defaultdict(list)
        text_standard = defaultdict(list)

        for text_annotation in annotation_data[TASK_TOKEN_TEXT_ANNOTATION]:
            task_id = text_annotation["task_id"]
            if task_id not in text_simple:
                text_simple[task_id].extend(text_simple_header)

            text_annotation_token_id = text_annotation["token_id"]
            text_annotation_token = chapter_data["tokens"][text_annotation_token_id]
            token_text = get_token_text(text_annotation_token, preference)

            text_simple[task_id].append([
                str(text_annotation["verse_id"]),
                token_text,
                text_annotation["text"]
            ])

        for task_id in text_simple:
            task_data_simple[TASK_TOKEN_TEXT_ANNOTATION][task_id] = "\n".join(
                "\t".join(text_annotation_row)
                for text_annotation_row in text_simple[task_id]
            )
            task_data_standard[TASK_TOKEN_TEXT_ANNOTATION][task_id] = None

        # ------------------------------------------------------------------- #

        preference = token_text_preference_map.get(
            TASK_TOKEN_CLASSIFICATION, default_token_text_preference
        )
        text_simple_header = [
            ["Verse", "Token", "Label", "Description"],
            ["-----", "-----", "-----", "-----------"]
        ]
        text_simple = defaultdict(list)
        text_standard = defaultdict(list)

        for tokclf in annotation_data[TASK_TOKEN_CLASSIFICATION]:
            task_id = tokclf["task_id"]
            if task_id not in text_simple:
                text_simple[task_id].extend(text_simple_header)

            tokclf_token_id = tokclf["token_id"]
            tokclf_token = chapter_data["tokens"][tokclf_token_id]
            token_text = get_token_text(tokclf_token, preference)

            text_simple[task_id].append([
                str(tokclf["verse_id"]),
                token_text,
                tokclf["label_label"],
                tokclf["label_description"]
            ])

        for task_id in text_simple:
            task_data_simple[TASK_TOKEN_CLASSIFICATION][task_id] = "\n".join(
                "\t".join(tokclf_row)
                for tokclf_row in text_simple[task_id]
            )
            task_data_standard[TASK_TOKEN_CLASSIFICATION][task_id] = None

        # ------------------------------------------------------------------- #

        preference = token_text_preference_map.get(
            TASK_TOKEN_GRAPH, default_token_text_preference
        )

        token_graph_data_simple = {}
        token_graph_node_ids = {}
        token_graph_data_standard = {}

        for tokrel in annotation_data[TASK_TOKEN_GRAPH]:
            task_id = tokrel["task_id"]
            if task_id not in token_graph_data_simple:
                token_graph_data_simple[task_id] = {
                    "nodes": [],
                    "edges": []
                }
                token_graph_node_ids[task_id] = {}

            from_id = None
            to_id = None

            for token_id in [tokrel["src_id"], tokrel["dst_id"]]:
                token = chapter_data["tokens"][token_id]
                token_text = get_token_text(token, preference)

                if token_text not in token_graph_node_ids[task_id]:
                    token_graph_node_ids[task_id][token_text] = get_unique_id()

                    token_graph_data_simple[task_id]["nodes"].append({
                        "id": token_graph_node_ids[task_id][token_text],
                        "label": token_text,
                        "value": 3,
                        "group": None
                    })

                if token_id == tokrel["src_id"]:
                    from_id = token_graph_node_ids[task_id][token_text]
                if token_id == tokrel["dst_id"]:
                    to_id = token_graph_node_ids[task_id][token_text]

            token_graph_data_simple[task_id]["edges"].append({
                "from": from_id,
                "to": to_id,
                "label": tokrel["label_description"],
                "title": tokrel["label_label"],
                "arrows": {
                    "to": {
                        "enabled": True
                    }
                },
                "value": 3,
            })

        task_data_simple[TASK_TOKEN_GRAPH] = token_graph_data_simple
        task_data_standard[TASK_TOKEN_GRAPH] = token_graph_data_standard

        # ------------------------------------------------------------------- #

        preference = token_text_preference_map.get(
            TASK_TOKEN_CONNECTION, default_token_text_preference
        )

        token_connection_graph = {}
        for tokcon in annotation_data[TASK_TOKEN_CONNECTION]:
            task_id = tokcon["task_id"]
            if task_id not in token_connection_graph:
                token_connection_graph[task_id] = nx.DiGraph()

            token_connection_graph[task_id].add_edge(
                tokcon["src_id"], tokcon["dst_id"]
            )

        text_simple = defaultdict(list)
        text_standard = defaultdict(list)

        for task_id in token_connection_graph:
            clusters = nx.weakly_connected_components(
                token_connection_graph[task_id]
            )
            for cluster_idx, cluster in enumerate(clusters):
                cluster_text = []
                for token_id in cluster:
                    token = chapter_data["tokens"][token_id]
                    token_text = get_token_text(token, preference)
                    cluster_text.append(
                        "/".join([
                            token_text,
                            f"verse-{token['verse_id']}",
                            f"line-{token['line_id']}",
                            f"token-{token['inner_id']}"
                        ])
                    )

                text_simple[task_id].append(cluster_text)

            task_data_simple[TASK_TOKEN_CONNECTION][task_id] = "\n".join(
                ", ".join(cluster_text)
                for cluster_text in text_simple[task_id]
            )
            task_data_standard[TASK_TOKEN_CONNECTION][task_id] = None

        # ------------------------------------------------------------------- #

        text_simple_header = [
            ["#", "Verse", "Sentence", "Label", "Description"],
            ["-", "-----", "--------", "-----", "-----------"]
        ]
        text_simple = defaultdict(list)
        text_standard = defaultdict(list)
        snclf_idx = {}

        for snclf in annotation_data[TASK_SENTENCE_CLASSIFICATION]:
            task_id = snclf["task_id"]
            if task_id not in text_simple:
                text_simple[task_id].extend(text_simple_header)
                snclf_idx[task_id] = 0

            snclf_idx[task_id] += 1
            text_simple[task_id].append([
                str(snclf_idx[task_id]),
                str(snclf["verse_id"]),
                SENTENCE_TEXT[snclf["boundary_id"]],
                snclf["label_label"],
                snclf["label_description"]
            ])

        for task_id in text_simple:
            task_data_simple[TASK_SENTENCE_CLASSIFICATION][task_id] = "\n".join(
                "\t".join(sentence_row)
                for sentence_row in text_simple[task_id]
            )
            task_data_standard[TASK_SENTENCE_CLASSIFICATION][task_id] = None

        # ------------------------------------------------------------------- #

        preference = token_text_preference_map.get(
            TASK_SENTENCE_GRAPH, default_token_text_preference
        )

        sentence_graph_data_simple = {}
        sentence_graph_node_ids = {}
        sentence_graph_data_standard = {}

        for sentrel in annotation_data[TASK_SENTENCE_GRAPH]:
            task_id = sentrel["task_id"]
            if task_id not in sentence_graph_data_simple:
                sentence_graph_data_simple[task_id] = {
                    "nodes": [],
                    "edges": []
                }
                sentence_graph_node_ids[task_id] = {}

            from_id = None
            to_id = None

            src_token = chapter_data["tokens"][sentrel["src_token_id"]]
            dst_token = chapter_data["tokens"][sentrel["dst_token_id"]]
            relation_type = sentrel["relation_type"]

            src_title = SENTENCE_TEXT[sentrel["src_boundary_id"]]
            dst_title = SENTENCE_TEXT[sentrel["dst_boundary_id"]]

            if relation_type in [2, 3]:
                src_token_text = f"S-{sentrel['src_boundary_id']}"
                src_group = 1
            else:
                src_token_text = get_token_text(src_token, preference)
                src_group = 0

            if relation_type in [1, 3]:
                dst_token_text = f"S-{sentrel['dst_boundary_id']}"
                dst_group = 1
            else:
                dst_token_text = get_token_text(dst_token, preference)
                dst_group = 0

            if src_token_text not in sentence_graph_node_ids[task_id]:
                sentence_graph_node_ids[task_id][src_token_text] = get_unique_id()

                sentence_graph_data_simple[task_id]["nodes"].append({
                    "id": sentence_graph_node_ids[task_id][src_token_text],
                    "label": src_token_text,
                    "title": src_title,
                    "value": 3,
                    "group": src_group
                })

            if dst_token_text not in sentence_graph_node_ids[task_id]:
                sentence_graph_node_ids[task_id][dst_token_text] = get_unique_id()

                sentence_graph_data_simple[task_id]["nodes"].append({
                    "id": sentence_graph_node_ids[task_id][dst_token_text],
                    "label": dst_token_text,
                    "title": dst_title,
                    "value": 3,
                    "group": dst_group
                })

            sentence_graph_data_simple[task_id]["edges"].append({
                "from": sentence_graph_node_ids[task_id][src_token_text],
                "to": sentence_graph_node_ids[task_id][dst_token_text],
                "label": sentrel["label_label"],
                "title": sentrel["label_description"],
                "arrows": {
                    "to": {
                        "enabled": True
                    }
                },
                "value": 3,
            })

        task_data_simple[TASK_SENTENCE_GRAPH] = sentence_graph_data_simple
        task_data_standard[TASK_SENTENCE_CLASSIFICATION] = sentence_graph_data_standard

        # ------------------------------------------------------------------- #

        simple_data[annotation_id] = task_data_simple
        standard_data[annotation_id] = task_data_standard

    return simple_data, standard_data


###############################################################################
