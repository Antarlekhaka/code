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

    var display_token_last_components = [];
    $.each(context, function(index, line){
        console.log(line.tokens);
        console.log(line.boundary);

        var line_text = [`${line.line_id}`];
        var boundary_tokens = new Set();

        $.each(line.boundary, function(index, boundary) {
            if (!boundary.is_deleted) {
                boundary_tokens.add(boundary.token_id);
            }
        });
        $.each(line.tokens, function(index, token) {
            if (token.analysis.Word !== "_") {
                var token_id = token.id;

                if (token.relative_id instanceof Array) {
                    // if token id is of composite word,
                    // we want the marker to be after the last component
                    token_id += token.relative_id[2] - token.relative_id[0] + 1;
                }
                if (line.line_id == row.line_id) {
                    display_token_last_components.push(token_id);
                }
                line_text.push(token.analysis.Word);
            }
            if (boundary_tokens.has(token.id)) {
                line_text.push("##");
            }
        });
        var actual_line_text = line_text.join(" ");

        if (line.line_id < row.line_id) {
            task_1_text_before.push(actual_line_text);
        }
        if (line.line_id == row.line_id) {
            task_1_text.push(actual_line_text);
        }
        if (line.line_id > row.line_id) {
            task_1_text_after.push(actual_line_text);
        }
    });
    $task_1_input.data('marker_positions', display_token_last_components);
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
    // NOTE: need to be called after Task 1 submit
    // TODO: also need to check row.anvaya if it's available (previously annotated)

    var task_3_text = [];
    $task_3_anvaya_container.html("");
    for (const [boundary_id, tokens] of Object.entries(row.sentences)) {
        // var task_3_token_words = ["#"];
        // var task_3_token_ids = ["#"];
        // var task_3_anvaya = ["# word\tid\torder"];

        var order = 0;
        $.each(tokens, function(idx, token) {
            if (token.analysis.Word !== "_") {
                order += 1;
                // task_3_token_words.push(token.analysis.Word);
                // task_3_token_ids.push(token.id);
                // task_3_anvaya.push(`${token.analysis.Word}\t${token.id}\t${order}`);

                var $token = $("<span>", {
                    id: `token-${token.id}`,
                    class: "btn btn-light mr-1 mb-1",
                    disabled: null
                });
                $token.html(token.analysis.Word);
                $task_3_anvaya_container.append($token);
                console.log("Trying to append");
            }
        });
        // task_3_text.push(task_3_token_words.join(" "));
        // task_3_text.push(task_3_token_ids.join(" "));
        // task_3_text = [...task_3_text, ...task_3_anvaya];
        // task_3_text.push("");
    }
    setup_sortable();

    // $task_3_input.val(task_3_text.join("\n"));

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
    // $task_3_input.val("");
    $task_4_input.val("");
    $task_5_input.val("");
});
