// Globals

$(document).ready(function () {
});

$corpus_table.on('check.bs.table', function (e, row, $element) {
    $corpus_table.bootstrapTable('collapseAllRows');
    $corpus_table.bootstrapTable('expandRow', $element.data('index'));
});

$corpus_table.on('expand-row.bs.table', function (e, index, row, $detail) {
    $line_id_containers.html(row.line_id);
    storage.setItem("next", parseInt(row.line_id) + 1);

    const data = $corpus_table.bootstrapTable('getData');
    const start_index = (index > 2) ? (index - 2) : 0;
    const end_index = (index < data.length - 2) ? (index + 2) : data.length - 1;
    const context = data.slice(start_index, end_index + 1);

    // console.log(data);

    var task_1_text_before = [];
    var task_1_text_after = [];

    var task_1_text = [];
    var task_2_text = [];
    var task_3_text = [];
    var task_4_text = [];
    var task_5_text = [];

    $.each(context, function(index, line){
        if (line.line_id < row.line_id) {
            task_1_text_before.push(`${line.line_id} ${line.line}`);
        }
        if (line.line_id == row.line_id) {
            task_1_text.push(`${line.line_id} ${line.line}`);
        }
        if (line.line_id > row.line_id) {
            task_1_text_after.push(`${line.line_id} ${line.line}`);
        }
    });
    $.each(row.tokens, function(index, token) {
        // console.log(token);
        if (token.id instanceof Array) {
            var next_token = row.tokens[index + 1];
            var token_type = "sandhi";
            if (next_token.analysis.Features.indexOf("Cpd") > -1) {
                var token_type = "samAsa";
            }

            task_2_text.push(`${token.line_id}\t${token.id.join("")}\t${token.analysis.Word}\t${token_type}`);
        }
    });


    $task_1_input_before.html(task_1_text_before.join("\n"));
    $task_1_input_after.html(task_1_text_after.join("\n"));

    $task_1_input.html(task_1_text.join("\n"));
    $task_2_input.html(task_2_text.join("\n"));
    $task_3_input.html(task_3_text.join("\n"));
    $task_4_input.html(task_4_text.join("\n"));
    $task_5_input.html(task_5_text.join("\n"));

    $task_1_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
});

$corpus_table.on('page-change.bs.table', function (e, number, size) {
    $line_id_containers.html("None");

    $("textarea").prop('disabled', true).removeClass('text-info').addClass('text-muted');
    $task_1_input_before.html("");
    $task_1_input_after.html("");
    $task_1_input.html("");
    $task_2_input.html("");
    $task_3_input.html("");
    $task_4_input.html("");
    $task_5_input.html("");
});

/* ********************  Skip ******************** */

$task_1_skip.click(function () {
    $task_1_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');
    // Task 1 Skip Actions
    // ...
    $task_2_tab.click();
    $task_2_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
});
$task_2_skip.click(function () {
    $task_2_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');
    // Task 2 Actions
    // ...
    $task_3_tab.click();
    $task_3_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
});
$task_3_skip.click(function () {
    $task_3_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');
    // Task 3 Skip Actions
    // ...
    $task_4_tab.click();
    $task_4_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
});
$task_4_skip.click(function () {
    $task_4_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');
    // Task 4 Skip Actions
    // ...
    $task_5_tab.click();
    $task_5_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
});
$task_5_skip.click(function() {
    $task_5_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');
    // Task 5 Skip Actions
    // ...
    $task_1_tab.click();
    $corpus_table.bootstrapTable('collapseAllRows');
    $corpus_table.bootstrapTable('uncheckAll');
    $corpus_table.bootstrapTable('expandRowByUniqueId', storage.getItem("next"));
});


/* ********************  Submit ******************** */

$task_1_submit.click(function () {
    $task_1_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');
    // Task 1 Actions
    // ...
    $task_2_tab.click();
    $task_2_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
});
$task_2_submit.click(function () {
    $task_2_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');
    // Task 2 Actions
    // ...
    $task_3_tab.click();
    $task_3_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
});
$task_3_submit.click(function () {
    $task_3_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');
    // Task 3 Actions
    // ...
    $task_4_tab.click();
    $task_4_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
});
$task_4_submit.click(function () {
    $task_4_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');
    // Task 4 Actions
    // ...
    $task_5_tab.click();
    $task_5_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
});
$task_5_submit.click(function() {
    $task_5_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');
    // Task 5 Actions
    // ...
    $task_1_tab.click();
    $corpus_table.bootstrapTable('collapseAllRows');
    $corpus_table.bootstrapTable('uncheckAll');
    $corpus_table.bootstrapTable('expandRowByUniqueId', storage.getItem("next"));
});