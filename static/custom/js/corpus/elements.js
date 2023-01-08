const $corpus_table = $("#corpus_viewer");

const $verse_id_containers = $(".verse-id-container");
const $refresh_verse_buttons = $(".refresh-verse");
const $task_submit_buttons = $(".task-submit-button");
const $task_tabs = $(".task-tab");

const $tabs = {};
for (const [task_id, task] of Object.entries(TASK_ACTIVE_TASKS)) {
    $tabs[task_id] = $(`#task-${task_id}-tab`);
}

// const $task_1_submit = $("#task-1-submit");
// const $task_2_submit = $("#task-2-submit");
// const $task_3_submit = $("#task-3-submit");
// const $task_4_submit = $("#task-4-submit");
// const $task_5_submit = $("#task-5-submit");
// const $task_6_submit = $("#task-6-submit");
// const $task_7_submit = $("#task-7-submit");
// const $task_8_submit = $("#task-8-submit");

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

/* *** Graph Modal *** */
// Single modal is used to show token graph and sentence graph
// across all relevant tasks

const $show_graph_modal_buttons = $(".show-graph-modal-button");
const $show_graph_modal = $("#show-graph-modal");
const $show_graph_modal_label = $("#show-graph-modal-label")
const $snapshot_graph_button = $('#snapshot-graph-button');
const $graph = $("#graph");

/* ******************* */

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
