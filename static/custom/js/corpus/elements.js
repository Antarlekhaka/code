const $corpus_table = $("#corpus_viewer");

const $verse_id_containers = $(".verse-id-container");
const $refresh_verse_buttons = $(".refresh-verse");

const $tabs = {
    "sentence_boundary": $("#task-1-tab"),
    "anvaya": $("#task-2-tab"),
    "named_entity": $("#task-3-tab"),
    "token_graph": $("#task-4-tab"),
    "coreference": $("#task-5-tab"),
    "sentence_classification": $("#task-6-tab"),
    "intersentence_connection": $("#task-7-tab"),
}

const $task_1_submit = $("#task-1-submit");
const $task_2_submit = $("#task-2-submit");
const $task_3_submit = $("#task-3-submit");
const $task_4_submit = $("#task-4-submit");
const $task_5_submit = $("#task-5-submit");
const $task_6_submit = $("#task-6-submit");
const $task_7_submit = $("#task-7-submit");

// Task-1
const $task_1_input = $("#task-1-input");
const $task_1_input_before = $("#task-1-input-before");
const $task_1_input_after = $("#task-1-input-after")

// Task-2
const $task_2_anvaya_container = $("#anvaya-container");
const $task_2_sample_anvaya_container = $("#sample-anvaya-container");

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

// Task-3
const $task_3_form = $("#entity-form");
const $task_3_entity_table = $("#entity-table");
const $task_3_non_entity_table = $("#non-entity-table");
const task_3_sample_entity_type = $("#sample-entity-type");

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
const $task_5_coref_context_container = $("#coref-context-container");

const $task_5_coref_intermediate_row_container = $("#coref-intermediate-row-container");
const $task_5_coref_source_container = $("#coref-source-token-container");
const $task_5_coref_target_container = $("#coref-target-token-container");
const $task_5_coref_reset_button = $("#coref-reset-button");
const $task_5_coref_confirm_button = $("#coref-confirm-button");

const $task_5_coref_annotation_container = $("#coref-annotation-container");

// Task-6
const $task_6_form = $("#sentence-classification-form");

const $task_6_sentence_classification_container = $("#sentence-classification-container");
const $task_6_sentence_classification_input_container = $("#sentence-classification-input-container");

const $task_6_sample_sentence_classification_input_container = $("#sample-sentence-classification-input-container");
const $task_6_sample_sentence_classification_input = $("#sample-sentence-classification-input");

// Task-7
const $task_7_form = $("#intersentence-connection-form");
const $task_7_intersentence_connection_context_container = $("#intersentence-connection-context-container");

const $task_7_intersentence_connection_intermediate_row_container = $("#intersentence-connection-intermediate-row-container");
const $task_7_intersentence_connection_source_container = $("#intersentence-connection-source-token-container");
const $task_7_intersentence_connection_relation_selector = $("#intersentence-connection-relation-selector");
const $task_7_intersentence_connection_target_container = $("#intersentence-connection-target-token-container");
const $task_7_intersentence_connection_reset_button = $("#intersentence-connection-reset-button");
const $task_7_intersentence_connection_confirm_button = $("#intersentence-connection-confirm-button");

const $task_7_intersentence_connection_annotation_container = $("#intersentence-connection-annotation-container");

const $show_graph_button_intersentence_connection = $("#show-graph-intersentence-connection");

// Globals
var storage = window.localStorage;
