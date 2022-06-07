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
            if (!boundary.is_deleted) {
                boundary_tokens.add(boundary.token_id);
            }
        });
        $.each(verse.tokens, function(verse_index, line_tokens) {
            verse_text.push("\t");
            $.each(line_tokens, function(token_index, token) {
                if (token.analysis.Word !== "_") {
                    var token_id = token.id;

                    if (token.relative_id instanceof Array) {
                        // if token id is of composite word,
                        // we want the marker to be after the last component
                        token_id += token.relative_id[2] - token.relative_id[0] + 1;
                    }
                    if (verse.verse_id == row.verse_id) {
                        display_token_last_components.push(token_id);
                    }
                    verse_text.push(token.analysis.Word);
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

    $task_3_anvaya_container.html("");
    for (const [boundary_id, sentence_tokens] of Object.entries(row.sentences)) {
        var $sentence = $("<div>", {
            id: `boundary-${boundary_id}`,
            class: "sortable border border-secondary px-1 pt-1 m-1 rounded"
        });
        $task_3_anvaya_container.append($sentence);

        const token_order = row.anvaya[boundary_id] || Object.keys(sentence_tokens);
        console.log("Token Order:");
        console.log(token_order);
        for (const token_id of token_order) {
            token = sentence_tokens[token_id];
            if (token.analysis.Word !== "_") {
                var $token = $("<span>", {
                    id: `token-${token.id}`,
                    class: "btn btn-light mr-1 mb-1",
                    title: `ID: ${token.id}`
                });
                $token.html(token.analysis.Word);
                $sentence.append($token);
            }
        };
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
    $verse_id_containers.html("None");

    $("textarea").prop('disabled', true).removeClass('text-info').addClass('text-muted');
    $task_1_input_before.val("");
    $task_1_input_after.val("");
    $task_1_input.val("");
    $task_2_input.val("");
    // $task_3_input.val("");
    $task_4_input.val("");
    $task_5_input.val("");
});
