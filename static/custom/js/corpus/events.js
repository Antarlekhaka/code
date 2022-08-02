// Globals

$(document).ready(function () {
});

$corpus_table.on('check.bs.table', function (e, row, $element) {
    $corpus_table.bootstrapTable('collapseAllRows');
    $corpus_table.bootstrapTable('expandRow', $element.data('index'));
});


$corpus_table.on('expand-row.bs.table', function (e, index, row, $detail) {
    $verse_id_containers.html(row.verse_id);
    storage.setItem("next", parseInt(row.verse_id) + 1);

    const data = $corpus_table.bootstrapTable('getData');

    // console.log(data);

    // Task 1
    var task_1_text = [];
    var task_1_text_before = [];
    var task_1_text_after = [];

    const start_index = (index > 1) ? (index - 1) : 0;
    const end_index = (index < data.length - 1) ? (index + 1) : data.length - 1;
    const context = data.slice(start_index, end_index + 1);

    var display_token_last_components = [];
    $.each(context, function(verse_index, verse){
        console.log("Verse Tokens:");
        console.log(verse.tokens);
        console.log("Verse Boundary:");
        console.log(verse.boundary);

        var verse_text = [`${verse.verse_id}`];
        var boundary_tokens = new Set();

        $.each(verse.boundary, function(boundary_index, boundary) {
            boundary_tokens.add(boundary.token_id);
        });
        $.each(verse.tokens, function(verse_index, line_tokens) {
            verse_text.push("\t");
            $.each(line_tokens, function(token_index, token) {
                if (token.text !== "_") {
                    var token_id = token.id;

                    if (token.relative_id instanceof Array) {
                        // if token id is of composite word,
                        // we want the marker to be after the last component
                        token_id += token.relative_id[2] - token.relative_id[0] + 1;
                    }
                    if (verse.verse_id == row.verse_id) {
                        display_token_last_components.push(token_id);
                    }
                    verse_text.push(token.text);
                }
                if (boundary_tokens.has(token.id)) {
                    verse_text.push("##");
                }
            });
            if (verse_index < verse.tokens.length - 1) {
                verse_text.push("\n");
            }
        });
        var actual_verse_text = verse_text.join(" ");
        if (verse.verse_id < row.verse_id) {
            task_1_text_before.push(actual_verse_text);
        }
        if (verse.verse_id == row.verse_id) {
            task_1_text.push(actual_verse_text);
        }
        if (verse.verse_id > row.verse_id) {
            task_1_text_after.push(actual_verse_text);
        }
    });
    $task_1_input.data('marker_positions', display_token_last_components);
    $task_1_input_before.val(task_1_text_before.join("\n"));
    $task_1_input_after.val(task_1_text_after.join("\n"));

    $task_1_input.val(task_1_text.join("\n"));

    // Task 2
    // NOTE: need to be called after Task 1 submit
    // TODO: also need to check row.anvaya if it's available (previously annotated)
    setup_anvaya(row.verse_id);

    // $task_2_input.val(task_2_text.join("\n"));

    // Task 3
    // var task_3_text = [];
    // $task_3_input.val(task_3_text.join("\n"));
    setup_named_entity(row.verse_id);

    // Task 4
    var task_4_text = [];
    $task_4_input.val(task_4_text.join("\n"));

    // Task 5
    // var task_5_text = [];
    // $task_5_input.val(task_5_text.join("\n"));

    // Enable + Focus on Task 1
    $task_1_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
});

$corpus_table.on('page-change.bs.table', function (e, number, size) {
    $verse_id_containers.html("None");

    $("textarea").prop('disabled', true).removeClass('text-info').addClass('text-muted');
    $task_1_input_before.val("");
    $task_1_input_after.val("");
    $task_1_input.val("");
    // $task_2_input.val("");
    // $task_3_input.val("");
    $task_4_input.val("");
    // $task_5_input.val("");
});

$task_2_add_token_button.click(function () {

});