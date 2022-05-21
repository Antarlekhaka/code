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

    // console.log(data);

    // Task 1
    var task_1_text = [];
    var task_1_text_before = [];
    var task_1_text_after = [];

    const start_index = (index > 2) ? (index - 2) : 0;
    const end_index = (index < data.length - 2) ? (index + 2) : data.length - 1;
    const context = data.slice(start_index, end_index + 1);

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
    $task_1_input_before.val(task_1_text_before.join("\n"));
    $task_1_input_after.val(task_1_text_after.join("\n"));

    $task_1_input.val(task_1_text.join("\n"));

    // Task 2
    var task_2_text = [];


    $.each(row.tokens, function(index, token) {
        // console.log(token);
        if (token.relative_id instanceof Array) {
            var next_token = row.tokens[index + 1];
            var token_type = "sandhi";
            if (next_token.analysis.Features.indexOf("Cpd") > -1) {
                var token_type = "samAsa";
            }

            task_2_text.push(`${token.line_id}\t${token.relative_id.join("")}\t${token.analysis.Word}\t${token_type}`);
        }
    });

    $task_2_input.val(task_2_text.join("\n"));

    // Task 3

    var task_3_text = [];
    $task_3_input.val(task_3_text.join("\n"));

    // Task 4
    var task_4_text = [];
    $task_4_input.val(task_4_text.join("\n"));

    // Task 5
    var task_5_text = [];
    $task_5_input.val(task_5_text.join("\n"));

    // Enable + Focus on Task 1
    $task_1_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
});

$corpus_table.on('page-change.bs.table', function (e, number, size) {
    $line_id_containers.html("None");

    $("textarea").prop('disabled', true).removeClass('text-info').addClass('text-muted');
    $task_1_input_before.val("");
    $task_1_input_after.val("");
    $task_1_input.val("");
    $task_2_input.val("");
    $task_3_input.val("");
    $task_4_input.val("");
    $task_5_input.val("");
});
