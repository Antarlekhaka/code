const $corpus_table = $("#corpus_viewer");

const $verse_id_containers = $(".verse-id-container");
const $refresh_verse_buttons = $(".refresh-verse");

const $tabs = {
    "sentence_boundary": $("#task-1-tab"),
    "word_order": $("#task-2-tab"),
    "token_classification": $("#task-3-tab"),
    "token_graph": $("#task-4-tab"),
    "token_connection": $("#task-5-tab"),
    "sentence_classification": $("#task-6-tab"),
    "sentence_graph": $("#task-7-tab"),
    "token_text_annotation": $("#task-8-tab"),
}

const $task_1_submit = $("#task-1-submit");
const $task_2_submit = $("#task-2-submit");
const $task_3_submit = $("#task-3-submit");
const $task_4_submit = $("#task-4-submit");
const $task_5_submit = $("#task-5-submit");
const $task_6_submit = $("#task-6-submit");
const $task_7_submit = $("#task-7-submit");
const $task_8_submit = $("#task-8-submit");

// Task-1
const $task_1_input = $("#task-1-input");
const $task_1_input_before = $("#task-1-input-before");
const $task_1_input_after = $("#task-1-input-after")

// Task-2
const $task_2_word_order_container = $("#word-order-container");
const $task_2_sample_word_order_container = $("#sample-word-order-container");

/* *** Add Token *** */

const $add_token_modal = $("#add-token-modal");
const $add_token_form = $("#add-token-form");
const $add_token_button = $("#add-token");
const $add_token_modal_button = $("#add-token-modal-button");

const $add_token_input_text = $("#add-token-input-text");
const $add_token_input_lemma = $("#add-token-input-lemma");

const $add_token_input_analysis_upos = $("#add-token-input-analysis-upos");
const $add_token_input_analysis_xpos = $("#add-token-input-analysis-upos");

const $add_token_analysis_items = $(".add-token-analysis-item");
const $add_token_feature_items = $(".add-token-feature-item");

const add_token_analysis_label_selector = ".add-token-analysis-label";
const add_token_analysis_input_selector = ".add-token-analysis-input";
const add_token_feature_label_selector = ".add-token-feature-label";
const add_token_feature_input_selector = ".add-token-feature-input";

/* ***************** */

// Task-8
const $task_8_form = $("#token-text-annotation-form");
const $task_8_token_text_annotation_table = $("#token-text-annotation-table");
const $task_8_token_non_annotation_table = $("#token-non-annotation-table");
const task_8_sample_token_text_annotation_text = $("#sample-token-text-annotation-text");

// Task-3
const $task_3_form = $("#token-classification-form");
const $task_3_token_classification_table = $("#token-classification-table");
const $task_3_token_null_class_table = $("#token-null-class-table");
const task_3_sample_token_type = $("#sample-token-type");

// Task-4
const $task_4_form = $("#token-graph-form");

/* *** Graph Modal *** */

const $show_graph_modal_buttons = $(".show-graph-modal-button");
const $show_graph_modal = $("#show-graph-modal");
const $show_graph_modal_label = $("#show-graph-modal-label")
const $snapshot_graph_button = $('#snapshot-graph-button');
const $graph = $("#graph");

/* ******************* */

const $task_4_token_graph_container = $("#token-graph-container");
const $task_4_token_graph_input_container = $("#token-graph-input-container");

const $task_4_sample_token_graph_input_container = $("#sample-token-graph-input-container");
const $task_4_sample_token_graph_input = $("#sample-token-graph-input");
const $task_4_sample_source_entity = $("#sample-source-entity");
const $task_4_sample_target_entity = $("#sample-target-entity");
const $task_4_sample_relation_label = $("#sample-relation-label");

// Task-5
const $task_5_token_connection_context_container = $("#tokcon-context-container");

const $task_5_token_connection_intermediate_row_container = $("#tokcon-intermediate-row-container");
const $task_5_token_connection_source_container = $("#tokcon-source-token-container");
const $task_5_token_connection_target_container = $("#tokcon-target-token-container");
const $task_5_token_connection_nnection_reset_button = $("#tokcon-reset-button");
const $task_5_token_connection_confirm_button = $("#tokcon-confirm-button");

const $task_5_token_connection_annotation_container = $("#tokcon-annotation-container");

// Task-6
const $task_6_form = $("#sentence-classification-form");

const $task_6_sentence_classification_container = $("#sentence-classification-container");
const $task_6_sentence_classification_input_container = $("#sentence-classification-input-container");

const $task_6_sample_sentence_classification_input_container = $("#sample-sentence-classification-input-container");
const $task_6_sample_sentence_classification_input = $("#sample-sentence-classification-input");

// Task-7
const $task_7_form = $("#sentence-graph-form");
const $task_7_sentence_graph_context_container = $("#sentence-graph-context-container");

const $task_7_sentence_graph_intermediate_row_container = $("#sentence-graph-intermediate-row-container");
const $task_7_sentence_graph_source_container = $("#sentence-graph-source-token-container");
const $task_7_sentence_graph_relation_selector = $("#sentence-graph-relation-selector");
const $task_7_sentence_graph_target_container = $("#sentence-graph-target-token-container");
const $task_7_sentence_graph_reset_button = $("#sentence-graph-reset-button");
const $task_7_sentence_graph_confirm_button = $("#sentence-graph-confirm-button");

const $task_7_sentence_graph_annotation_container = $("#sentence-graph-annotation-container");

const $show_graph_button_sentence_graph = $("#show-graph-sentence-graph");

// Globals
var storage = window.localStorage;
