// Globals

$(document).ready(function () {
    // TODO: Set-up placeholders for other tasks as well
    const task_2_placeholder_content = $task_2_sample_anvaya_container.html();
    $task_2_anvaya_container.html(task_2_placeholder_content);

    const $task_6_placeholder = $task_6_sample_sentence_classification_input.clone();
    $task_6_placeholder.removeAttr("id");
    $task_6_placeholder.find(".sentence-label").selectpicker();
    $task_6_placeholder.appendTo($task_6_sentence_classification_input_container);

    // Split Columns
    var splitobj = Split(["#corpus-column","#annotation-column"], {
        elementStyle: function (dimension, size, gutterSize) {
            $(window).trigger('resize');
            return {
                'flex-basis': `calc(${size}% - ${gutterSize}px)`
            };
        },
        gutterStyle: function (dimension, gutterSize) {
            return {
                'flex-basis':  `${gutterSize}px`
            };
        },
        sizes: [49, 51],
        minSize: 300,
        gutterSize: 10,
        cursor: 'col-resize'
    });
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

    storage.setItem("current_verse_id", parseInt(verse_id));
    storage.setItem("next_verse_id", parseInt(verse_id) + 1);

    storage.setItem("current_index", parseInt(index));
    storage.setItem("next_index", parseInt(index) + 1);

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

// Click / Double-Click Cell
// 'click-cell.bs.table' / 'dbl-click-cell.bs.table'
$corpus_table.on('dbl-click-cell.bs.table', function (event, field, value, row, $element) {

});
