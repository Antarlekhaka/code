const $corpus_table = $("#corpus_viewer");

const $verse_id_containers = $(".verse-id-container");
const $refresh_verse_buttons = $(".refresh-verse");
const $task_submit_buttons = $(".task-submit-button");
const $task_tabs = $(".task-tab");

const $tabs = {};
for (const [task_id, task] of Object.entries(TASK_ACTIVE_TASKS)) {
    $tabs[task_id] = $(`#task-${task_id}-tab`);
}

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
const $snapshot_graph_button = $("#snapshot-graph-button");
const $graph = $("#graph");

/* ******************* */

/* Load Context */
// Load more context rows for token connection and sentence graph tasks

const $load_context_buttons = $(".load-context-button");

/* ******************* */

// Globals
const storage = window.localStorage;
