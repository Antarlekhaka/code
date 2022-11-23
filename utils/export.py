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
    token_graph_node_ids = {}
    discourse_graph_node_ids = {}
    simple_data = {}

    for chpater_id, chapter_data in data["chapter"].items():

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
            display_text = [
                ["", "Verse", "Anvaya"],
                ["", "-----", "------"]
            ]

            sent_idx = 0
            current_boundary_id = None
            current_verse_id = None
            sentence_tokens = []

            for anvaya in annotation_data["anvaya"]:
                if current_boundary_id is None:
                    current_boundary_id = anvaya["boundary_id"]
                    current_verse_id = anvaya["verse_id"]

                if current_boundary_id != anvaya["boundary_id"]:
                    sent_idx += 1
                    sentence_text = " ".join(sentence_tokens)
                    sentences[current_boundary_id] = sentence_text
                    display_text.append(
                        [str(sent_idx), str(current_verse_id), sentence_text]
                    )

                    current_boundary_id = anvaya["boundary_id"]
                    current_verse_id = anvaya["verse_id"]
                    sentence_tokens = []

                token_id = anvaya["token_id"]
                token = chapter_data["tokens"][token_id]
                token_text = get_token_text(token, preference)
                sentence_tokens.append(token_text)
            else:
                sent_idx += 1
                sentence_text = " ".join(sentence_tokens)
                sentences[current_boundary_id] = sentence_text
                display_text.append(
                    [str(sent_idx), str(current_verse_id), sentence_text]
                )

            task_data["anvaya"] = "\n".join(
                "\t".join(sentence_row)
                for sentence_row in display_text
            )

            # --------------------------------------------------------------- #

            preference = ["lemma", "misc.Unsandhied", "form"]

            display_text = [
                ["Verse", "Token", "Annotation"],
                ["-----", "-----", "----------"]
            ]

            for text_annotation in annotation_data["token_text_annotation"]:
                text_annotation_token_id = text_annotation["token_id"]
                text_annotation_token = chapter_data["tokens"][text_annotation_token_id]
                token_text = get_token_text(text_annotation_token, preference)

                display_text.append([
                    str(text_annotation["verse_id"]),
                    token_text,
                    text_annotation["text"]
                ])

            task_data["token_text_annotation"] = "\n".join(
                "\t".join(text_annotation_row)
                for text_annotation_row in display_text
            )

            # --------------------------------------------------------------- #

            preference = ["lemma", "misc.Unsandhied", "form"]

            display_text = [
                ["Verse", "Token", "Label", "Description"],
                ["-----", "-----", "-----", "-----------"]
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

                    if token_text not in token_graph_node_ids:
                        token_graph_node_ids[token_text] = get_unique_id()

                        token_graph_data["nodes"].append({
                            "id": token_graph_node_ids[token_text],
                            "label": token_text,
                            "value": 3,
                            "group": None
                        })

                    if token_id == relation["src_id"]:
                        from_id = token_graph_node_ids[token_text]
                    if token_id == relation["dst_id"]:
                        to_id = token_graph_node_ids[token_text]

                token_graph_data["edges"].append({
                    "from": from_id,
                    "to": to_id,
                    "label": relation["label_description"],
                    "title": relation["label_label"],
                    "arrows": {
                        "to": {
                            "enabled": True
                        }
                    },
                    "value": 3,
                })

            task_data["token_graph"] = token_graph_data

            # --------------------------------------------------------------- #

            preference = ["misc.Unsandhied", "form", "lemma"]

            coreference_graph = nx.DiGraph()
            coreference_graph.add_edges_from([
                (coref["src_id"], coref["dst_id"])
                for coref in annotation_data["coreference"]
            ])

            display_text = []

            clusters = nx.weakly_connected_components(coreference_graph)
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

                display_text.append(cluster_text)

            task_data["coreference"] = "\n".join(
                ", ".join(cluster_text)
                for cluster_text in display_text
            )

            # --------------------------------------------------------------- #

            display_text = [
                ["", "Verse", "Sentence", "Label", "Description"],
                ["", "-----", "--------", "-----", "-----------"]
            ]

            for snclf_idx, snclf in enumerate(
                annotation_data["sentence_classification"], 1
            ):
                display_text.append([
                    str(snclf_idx),
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

            preference = ["lemma", "misc.Unsandhied", "form"]

            discourse_graph_data = {
                "nodes": [],
                "edges": []
            }

            for relation in annotation_data["intersentence_connection"]:
                from_id = None
                to_id = None

                src_token = chapter_data["tokens"][relation["src_token_id"]]
                dst_token = chapter_data["tokens"][relation["dst_token_id"]]
                relation_type = relation["relation_type"]

                src_title = sentences[relation["src_boundary_id"]]
                dst_title = sentences[relation["dst_boundary_id"]]

                if relation_type in [2, 3]:
                    src_token_text = f"S-{relation['src_boundary_id']}"
                    src_group = 1
                else:
                    src_token_text = get_token_text(src_token, preference)
                    src_group = 0

                if relation_type in [1, 3]:
                    dst_token_text = f"S-{relation['dst_boundary_id']}"
                    dst_group = 1
                else:
                    dst_token_text = get_token_text(dst_token, preference)
                    dst_group = 0

                if src_token_text not in discourse_graph_node_ids:
                    discourse_graph_node_ids[src_token_text] = get_unique_id()

                    discourse_graph_data["nodes"].append({
                        "id": discourse_graph_node_ids[src_token_text],
                        "label": src_token_text,
                        "title": src_title,
                        "value": 3,
                        "group": src_group
                    })

                if dst_token_text not in discourse_graph_node_ids:
                    discourse_graph_node_ids[dst_token_text] = get_unique_id()

                    discourse_graph_data["nodes"].append({
                        "id": discourse_graph_node_ids[dst_token_text],
                        "label": dst_token_text,
                        "title": dst_title,
                        "value": 3,
                        "group": dst_group
                    })

                discourse_graph_data["edges"].append({
                    "from": discourse_graph_node_ids[src_token_text],
                    "to": discourse_graph_node_ids[dst_token_text],
                    "label": relation["label_label"],
                    "title": relation["label_description"],
                    "arrows": {
                        "to": {
                            "enabled": True
                        }
                    },
                    "value": 3,
                })

            print(discourse_graph_data)
            task_data["intersentence_connection"] = discourse_graph_data

            # --------------------------------------------------------------- #

            simple_data[annotation_id] = task_data

    return simple_data


###############################################################################
# Standard Format
# --------------------------------------------------------------------------- #


def standard_format(data):
    pass


###############################################################################
