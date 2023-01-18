// Storage
const storage = window.localStorage;

// Storage Keys
const KEY_DATA_COLLAPSIBLE_SHOW = "data_collapsible_show";
const KEY_ONTOLOGY_TAB_ACTIVE = "ontology_tab_active";

// Parent Elements
const DATA_COLLAPSIBLE_PARENT_ID = "manage_data";
const DATA_COLLAPSIBLE_DEFAULT_SHOW_ID = "corpus_container";
const ONTOLOGY_TAB_PARENT_ID = "labels-tab";

/* ********************************* Main ********************************* */

$(document).ready(function () {
    // Render CustomFile input element
    bsCustomFileInput.init();

    // Display active elements
    const data_collapsible_show_id  = storage.getItem(KEY_DATA_COLLAPSIBLE_SHOW);
    if (!data_collapsible_show_id) {
        data_collapsible_show_id = DATA_COLLAPSIBLE_DEFAULT_SHOW_ID;
    };
    $(`#${data_collapsible_show_id}`).collapse('show');

    const ontology_tab_active_id = storage.getItem(KEY_ONTOLOGY_TAB_ACTIVE);
    if (ontology_tab_active_id) {
        $(`#${ontology_tab_active_id}`).tab('show');
    };
});

/* ******************************** Events ******************************** */

$(`#${DATA_COLLAPSIBLE_PARENT_ID} .collapse`).on('shown.bs.collapse', function (event) {
    const target_element = event.target;
    const target_id = target_element.id;
    storage.setItem(KEY_DATA_COLLAPSIBLE_SHOW, target_id);
});

$(`#${ONTOLOGY_TAB_PARENT_ID} .ontology-tab`).on('shown.bs.tab', function (event) {
    const target_element = event.target;
    const target_id = target_element.id;
    storage.setItem(KEY_ONTOLOGY_TAB_ACTIVE, target_id);
});

/* **************************** Task Management **************************** */

// Elements
const $task_modal = $("#task-modal");
const $task_form = $("#task-update-form");
const $task_modal_action = $("#task-modal-action");
const $task_modal_submit_button = $("#task-modal-submit");

const $input_task_id = $("#task-modal-input-task-id");
const $span_task_id = $("#task-modal-span-task-id");
const $input_task_category = $("#task-modal-select-task-category");
const $span_task_category = $("#task-modal-span-task-category");
const $input_task_title = $("#task-modal-input-task-title");
const $input_task_short = $("#task-modal-input-task-short");
const $input_task_help = $("#task-modal-textarea-task-help");

// Events
$task_modal.on("show.bs.modal", function (event) {
    const $modal = $(this);
    // button that triggered the modal
    const $trigger_button = $(event.relatedTarget);
    // extract info from data-* attributes
    const action = $trigger_button.data("action");
    var modal_title = null;
    if (action == "add") {
        $modal.find(".modal-title").text("Add Task");

        $input_task_id.val("auto");
        $span_task_id.html("auto");

        $span_task_category.addClass("d-none");
        $span_task_category.html("");
        $input_task_category.prop("required", true);
        $input_task_category.selectpicker("show");
        $input_task_category.val("");
        $input_task_category.selectpicker("refresh");

        $input_task_title.val("");
        $input_task_short.val("");
        $input_task_help.val("");
    }
    if (action == "edit") {
        $modal.find(".modal-title").text("Edit Task");

        const task_id = $trigger_button.data("task-id");
        const the_task = TASK_TASKS[task_id];

        $input_task_id.val(task_id);
        $span_task_id.html(task_id);

        $input_task_category.selectpicker("hide");
        $input_task_category.prop("required", false);
        $span_task_category.removeClass("d-none");
        $span_task_category.html(TASK_DEFAULT[the_task.category].title);

        $input_task_title.val(the_task.title);
        $input_task_short.val(the_task.short);
        $input_task_help.val(the_task.help);
    }
});

$input_task_category.on("changed.bs.select", function (event, clicked_index, is_selected, previous_value) {
    const chosen_category = $input_task_category.selectpicker("val");
    const default_information = TASK_DEFAULT[chosen_category];
    $input_task_title.val(default_information.title);
    $input_task_short.val(default_information.short);
    $input_task_help.val(default_information.help);
});

$task_modal_submit_button.on("click", function (event) {
    if ($task_form[0].checkValidity()) {
        $task_form.submit();
    } else {
        $task_form[0].reportValidity();
    }
});
