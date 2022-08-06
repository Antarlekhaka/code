const $corpus_table = $("#corpus_viewer");

const $verse_id_containers = $(".verse-id-container");
const $refresh_verse_buttons = $(".refresh-verse");

const $task_1_tab = $("#task-1-tab");
const $task_2_tab = $("#task-2-tab");
const $task_3_tab = $("#task-3-tab");
const $task_4_tab = $("#task-4-tab");
const $task_5_tab = $("#task-5-tab");

const $task_1_input_before = $("#task-1-input-before");
const $task_1_input_after = $("#task-1-input-after")

const $task_2_anvaya_container = $("#anvaya-container");
const $add_token_modal = $('#add-token-modal');
const $add_token_form = $("#add-token-form");
const $add_token_button = $("#add-token");
const $add_token_modal_button = $("#add-token-modal-button");

const $task_3_form = $("#entity-form");
const $task_3_entity_table = $("#entity-table");
const $task_3_non_entity_table = $("#non-entity-table");
const task_3_sample_entity_type = $("#sample-entity-type");

const $task_1_input = $("#task-1-input");
const $task_2_input = $("#task-2-input");
const $task_3_input = $("#task-3-input");
const $task_4_input = $("#task-4-input");
const $task_5_input = $("#task-5-input");

const $task_1_skip = $("#task-1-skip");
const $task_2_skip = $("#task-2-skip");
const $task_3_skip = $("#task-3-skip");
const $task_4_skip = $("#task-4-skip");
const $task_5_skip = $("#task-5-skip");

const $task_1_submit = $("#task-1-submit");
const $task_2_submit = $("#task-2-submit");
const $task_3_submit = $("#task-3-submit");
const $task_4_submit = $("#task-4-submit");
const $task_5_submit = $("#task-5-submit");

/*
// Line Annotation
const $form_prepare_entity = $("#form_prepare_entity");
const $line_id_entity = $("#line_id_entity");
const $entity_root = $("#input_entity_root");
const $entity_type = $("#input_entity_type");

const $add_entity_button = $("#add_entity");

const $confirm_entity_button = $("#confirm_entity_list");
const $entity_list = $("#entity_list");

// Relation Annotation
const $form_prepare_relation = $("#form_prepare_relation");
const $line_id_relation = $("#line_id_relation");
const $relation_source = $("#input_relation_source");
const $relation_label = $("#input_relation_label");
const $relation_detail = $("#input_relation_detail");
const $relation_target = $("#input_relation_target");

const $add_relation_button = $("#add_relation")

const $confirm_relation_button = $("#confirm_relation_list");
const $relation_list = $("#relation_list");

// Action Annotation
const $form_prepare_action = $("#form_prepare_action");
const $line_id_action = $("#line_id_action");
const $action_label = $("#input_action_label");
const $action_actor_label = $("#input_action_actor_label");
const $action_actor = $("#input_action_actor");

const $add_action_button = $("#add_action")

const $confirm_action_button = $("#confirm_action_list");
const $action_list = $("#action_list");

const $datalist_root = $("#datalist_root");
const $datalist_source = $("#datalist_source");
const $datalist_target = $("#datalist_target");
const $datalist_detail = $("#datalist_detail");
*/

// Globals
var storage = window.localStorage;
