// Globals

$(document).ready(function () {
    const task_2_placeholder_content = $task_2_sample_anvaya_container.html();
    $task_2_anvaya_container.html(task_2_placeholder_content);

    const $task_6_placeholder = $task_6_sample_sentence_classification_input.clone();
    $task_6_placeholder.removeAttr("id");
    $task_6_placeholder.find(".sentence-label").selectpicker();
    $task_6_placeholder.appendTo($task_6_sentence_classification_input_container);
});

// Exapand Row on Select
$corpus_table.on('check.bs.table', function (e, row, $element) {
    $corpus_table.bootstrapTable('collapseAllRows');
    $corpus_table.bootstrapTable('expandRow', $element.data('index'));
});

// Row Expand
$corpus_table.on('expand-row.bs.table', function (e, index, row, $detail) {
    const verse_id = row.verse_id;

    $verse_id_containers.html(verse_id);
    $add_token_modal_button.prop('disabled', false);
    $refresh_verse_buttons.prop('disabled', false);

    storage.setItem("next", parseInt(verse_id) + 1);

    // // Setup All Tasks
    // for (const task_id of ["1", "2", "3", "4", "5", "6", "7", "8"]) {
    //     setup_task(task_id, verse_id);
    // }

    // Do we need to initiate all the tasks ?
    // Since we do them on tab change individually anyway.
    // Instead, just find the active tab and setup that one.
    // Alternatively, force focus on Task-1
    const $active_tab = $('a[aria-selected="true"]');
    const active_task_id = $active_tab.attr('id').replace(/task-([0-9]+)-tab/, "$1");
    setup_task(active_task_id, verse_id);

});


// Tab Change
$('a[data-toggle="pill"]').on('shown.bs.tab', function (event) {
    const verse_id = $verse_id_containers.html();
    if (verse_id == "None") {
        $.notify({
            message: "Please select a verse first."
        }, {
            type: "warning"
        })
        return;
    }

    const active_tab = event.target;
    const task_id = active_tab.id.replace(/task-([0-9]+)-tab/, "$1");

    setup_task(task_id, verse_id);
});

// Page Change
$corpus_table.on('page-change.bs.table', function (e, number, size) {
    $verse_id_containers.html("None");
    $add_token_modal_button.prop('disabled', true);
    $refresh_verse_buttons.prop('disabled', true);
    $("textarea").prop('disabled', true).removeClass('text-info').addClass('text-muted');

    $task_1_input_before.val("");
    $task_1_input_after.val("");
    $task_1_input.val("");
});

