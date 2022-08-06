/* ********************************** */
// Task Related Functions, Events etc.
/* ********************************** */
// Note: Variables in capital are declared in the HTML template.

function refresh_row_data(unique_id, _callback) {
    const verse_data_url = SAMPLE_VERSE_DATA_URL.replace('0', unique_id);
    $.get(verse_data_url, function (data) {
        $corpus_table.bootstrapTable('updateByUniqueId', {
            id: unique_id,
            row: data[unique_id],
            replace: true
        });
        if (_callback) {
            _callback(unique_id);
        }
    }, 'json');
    console.log(`Verse data updated for ID: ${unique_id}`);
}

// Tab Change
$('a[data-toggle="tab"]').on('shown.bs.tab', function (event) {
    const active_tab = event.target;
    const previous_tab = event.relatedTarget;
    console.log(active_tab);
});

$refresh_verse_buttons.click(function() {
    const verse_id = $verse_id_containers.html();
    refresh_row_data(verse_id);
});

/* ********************************** BEGIN Task 1 ********************************** */
// Task 1: Sentence Boundary

// Setup-1
// TODO: move here

// Skip-1
$task_1_skip.click(function () {
    $task_1_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');
    // Task 1 Skip Actions
    // ...
    $task_2_tab.click();
    // $task_2_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
});

// Submit-1
$task_1_submit.click(function () {
    $task_1_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');

    // Identify Boundary Token IDs
    var marker_positions = $task_1_input.data('marker_positions');
    var submitted_tokens = $task_1_input.val().split(/\s+/);
    var line_break_tokens = [];

    var current_idx = -2;
    for (var i=0; i < submitted_tokens.length; ++i) {
        if (submitted_tokens[i] === "##") {
            line_break_tokens.push(marker_positions[current_idx]);
        } else {
            current_idx += 1;
        }
    }

    $.post(API_URL, {
        action: "update_sentence_boundary",
        verse_id: $verse_id_containers.html(),
        boundaries: line_break_tokens.join(","),
    },
    function (response) {
        $.notify({
            message: response.message
        }, {
            type: response.style
        });

        if (response.changes) {
            const verse_id = $verse_id_containers.html();

            /*
            var boundary_objects = [];
            $.each(line_break_tokens, function(index, _token_id) {
                boundary_objects.push({
                    'token_id': _token_id,
                    'verse_id': verse_id,
                    'annotator': CURRENT_USERNAME,
                });
            });
            var current_row = $corpus_table.bootstrapTable('getRowByUniqueId', verse_id);
            current_row.marked = true;
            current_row.boundary = boundary_objects;

            $corpus_table.bootstrapTable('updateByUniqueId', {
                verse_id: current_row.verse_id,
                row: current_row
            });
            */

            // update local table
            // next task is anvaya, therefore,

            refresh_row_data(verse_id, setup_anvaya);

            // move to the next task
            $task_2_tab.click();

            // don't need this because there's no $task_2_input;
            // $task_2_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
        }
    },
    'json');
});

/* *********************************** END Task 1 *********************************** */

/* ********************************** BEGIN Task 2 ********************************** */
// Task 2: Anvaya

// Setup-2
function setup_sortable() {
    $('.connected-sortable').sortable({
        opacity: 0.75,
        revert: true,
        cursor: "move",
        tolerance: "pointer",
        placeholder: 'btn btn-secondary py-3 px-5 mb-1 mr-1',
        connectWith: ".sortable"
    }).on("sortremove", function(e, ui) {
        var toggle_id = ui.item[0].id.replace("button", "toggle");
        $(`#${toggle_id}`).prop("disabled", false);
    });
    $('.sortable').sortable({
        opacity: 0.75,
        revert: true,
        cursor: "move",
        tolerance: "pointer",
        placeholder: 'btn btn-secondary py-3 px-5 mb-1 mr-1',
    }).on("sortstop sortreceive", function(e, ui) {
        // ui.item contains the current dragged element.
        // Triggered when the user stopped sorting and the DOM position has changed.
        var anvaya_order = [];
        $(this).children().each(function (){
            anvaya_order.push(this.id);
        });
        $(this).data("anvaya", anvaya_order);
        console.log("Saved Order: " + anvaya_order);
    });
}

function setup_anvaya(verse_id) {
    const row = $corpus_table.bootstrapTable('getRowByUniqueId', verse_id);

    $task_2_anvaya_container.html("");
    const $extra = $("<div>", {
        id: `extra-${verse_id}`,
        class: "border px-1 pt-1 m-1 rounded connected-sortable",
        style: "background-color: #eeeeff; border-color: #aaaaff !important;"
    });
    $task_2_anvaya_container.append($extra);
    const extra_tokens = row.sentences['extra'];

    var used_extra_tokens = [];
    for (const [boundary_id, sentence_tokens] of Object.entries(row.sentences)) {
        if (boundary_id == "extra") {
            continue;
        }
        console.log(boundary_id);
        console.log(sentence_tokens);
        for (const token_id of row.anvaya[boundary_id]) {
            if (extra_tokens.hasOwnProperty(token_id)) {
                used_extra_tokens.push(token_id);
            }
        }
    }
    for (const [boundary_id, sentence_tokens] of Object.entries(row.sentences)) {
        console.log(row);
        var token_order;
        if (boundary_id != "extra") {
            token_order = row.anvaya[boundary_id];
            // ensure in server_sqla.py that row.anvaya isn't empty
            // either it is annotated anvaya, or it's obtained via heuristic
        } else {
            // order doesn't really matter, just need extra tokens
            token_order = Object.keys(sentence_tokens);
        }
        console.log("Token Order: " + token_order);

        const $sentence = $("<div>", {
            id: `boundary-${boundary_id}`,
            class: "sortable border px-1 pt-1 m-1 rounded",
            style: "background-color: #eeffee; border-color: #aaffaa !important;"
        });
        const $unused = $("<div>", {
            id: `unused-${boundary_id}`,
            class: "border px-1 pt-1 m-1 rounded",
            style: "background-color: #ffeeee; border-color: #ffaaaa !important;"
        });
        if (boundary_id != "extra") {
            $task_2_anvaya_container.append($sentence);
            $task_2_anvaya_container.append($unused);
        }

        for (const token_id of token_order) {
            var token;
            if (sentence_tokens.hasOwnProperty(token_id)) {
                token = sentence_tokens[token_id];
            } else if (extra_tokens.hasOwnProperty(token_id)) {
                token = extra_tokens[token_id];
            } else {
                console.log("Something weird happened. Token is neither part of sentence, nor extra.");
            }
            var token_class = "btn btn-light";
            var token_text = token.text;

            if (token.text === "_") {
                token_class = "btn btn-warning";
                token_text = token.analysis.unsandhied;
            }
            const $token_button = $("<div>", {
                id: `token-button-${token.id}`,
                role: "group",
                class: "btn-group mr-1 mb-1 border border-secondary rounded",
            });

            if (boundary_id == "extra") {
                if (!used_extra_tokens.includes(token.id)) {
                    $extra.append($token_button);
                }
            } else {
                $sentence.append($token_button);
            }
            const $token = $("<span>", {
                id: `token-${token.id}`,
                class: token_class,
                title: `ID: ${token.id}\nText:${token.text}\nLemma: ${token.lemma}\nPadapāṭha: ${token.analysis.unsandhied}`,
                html: token_text
            });
            $token_button.append($token);

            if (token.annotator_id == null) {
                const $token_toggle = $("<button>", {
                    id: `token-toggle-${token.id}`,
                    name: "token-toggle",
                    class: "btn btn-secondary exclude-token",
                    html: '<i class="fa fa-times"></i>',
                    on: {
                        click: function() {
                            if ($(this).hasClass("exclude-token")) {
                                $(this).removeClass("exclude-token");
                                $(this).removeClass("btn-secondary");
                                $(this).addClass("btn-info");
                                $(this).html('<i class="fa fa-plus"></i>');
                                $(`#unused-${boundary_id}`).append($(this).parent());
                            } else {
                                $(this).removeClass("btn-info");
                                $(this).addClass("btn-secondary");
                                $(this).addClass("exclude-token");
                                $(this).html('<i class="fa fa-times"></i>');
                                $(`#boundary-${boundary_id}`).append($(this).parent());
                            }
                            $(".sortable").trigger("sortstop");
                        }
                    }
                });
                $token_button.append($token_toggle);
            } else  {
                const $token_toggle = $("<button>", {
                    id: `token-toggle-${token.id}`,
                    name: "token-toggle",
                    class: "btn btn-secondary include-token",
                    html: '<i class="fa fa-times"></i>',
                    disabled: true,
                    on: {
                        click: function() {
                            $(`#extra-${verse_id}`).append($(this).parent());
                            $(this).prop("disabled", true);
                            $(".sortable").trigger("sortstop");
                        }
                    }
                });
                $token_button.append($token_toggle);

                const $token_remove = $("<button>", {
                    id: `token-remove-${token.id}`,
                    name: "token-remove",
                    class: "btn btn-danger",
                    html: '<i class="fas fa-trash-alt"></i>',
                    on: {
                        click: function() {
                            // remove token
                            $.notify({
                                message: "Token Removal Message. (not-performed)"
                            }, {
                                type: "warning"
                            });
                        }
                    }
                });
                $token_button.append($token_remove);
            }
        };
    }
    setup_sortable();
}

/* Task-2 Actions */

// Add Token
$add_token_button.click(function() {
    if (!$add_token_form[0].checkValidity()) {
        $add_token_form[0].reportValidity();
        return;
    }
    const verse_id = $verse_id_containers.html();
    const token_text = $("#add-token-text").val();
    const token_lemma = $("#add-token-lemma").val();
    const token_analysis = $("#add-token-analysis").val();
    const token_data = {
        text: token_text,
        lemma: token_lemma,
        analysis: token_analysis,
    }
    $add_token_modal.modal('hide');
    $.post(API_URL, {
        action: "add_token",
        verse_id: verse_id,
        token_data: JSON.stringify(token_data)
    },
    function (response) {
        $.notify({
            message: response.message
        }, {
            type: response.style
        });

        if (response.success) {
            refresh_row_data(verse_id, setup_anvaya);
        }
    });
});

// Skip-2
$task_2_skip.click(function () {
    // $task_2_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');
    // Task 2 Skip Actions
    // ...
    $task_3_tab.click();
    $task_3_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
});

// Submit-2
$task_2_submit.click(function () {
    // $task_2_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');
    // Task 2 Actions

    const verse_id = $verse_id_containers.html();
    var anvaya_data = {}
    $('.sortable').each(function(sentence_index, sentence_element) {
        const boundary_id = sentence_element.id;
        anvaya_data[boundary_id] = $(sentence_element).data("anvaya");
    });
    console.log(anvaya_data);

    $.post(API_URL, {
        action: "update_anvaya",
        verse_id: verse_id,
        anvaya: JSON.stringify(anvaya_data)
    },
    function (response) {
        $.notify({
            message: response.message
        }, {
            type: response.style
        });

        if (response.success) {
            refresh_row_data(verse_id, setup_named_entity);
            // is this required?
            // yes, if the entities are to be shown in anvaya order or so,
            // otherwise, there's no dependence on anvaya task, and ideally, shouldn't be
            // called conditionally

            $task_3_tab.click();
            // don't need this because there's no $task_3_input;
            // $task_3_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
        }
    });
});

/* *********************************** END Task 2 *********************************** */

/* ********************************** BEGIN Task 3 ********************************** */
// Task 3: Named Entity

// Setup-3
function setup_named_entity(verse_id) {
    const row = $corpus_table.bootstrapTable('getRowByUniqueId', verse_id);

    $task_3_entity_table.html("");
    $task_3_non_entity_table.html("");

    // TODO: ad-hoc code, update properly
    var existing_entities = [];
    var existing_labels = {};
    for (const entity of row.entity) {
        existing_entities.push(entity.token_id);
        existing_labels[entity.token_id] = entity.label_id;
    }
    console.log(existing_labels);

    for (const line_tokens  of row.tokens) {
        for (const token of line_tokens) {
            var is_entity = false;
            var entity_label_id = null;
            const $entity_row = $("<tr>", {});
            if (existing_entities.includes(token.id)) {
                $task_3_entity_table.append($entity_row);
                is_entity = true;
                entity_label_id = existing_labels[token.id];
            } else {
                $task_3_non_entity_table.append($entity_row);
            }

            var token_text = token.text;
            var token_class = "btn btn-light";

            if (token.text === "_") {
                token_class = "btn btn-warning";
                token_text = token.analysis.unsandhied;
            }

            const $entity_cell = $("<td>", {});
            $entity_row.append($entity_cell);

            var $entity = $("<span>", {
                id: `entity-${token.id}`,
                class: token_class,
                title: `ID: ${token.id}\nText:${token.text}\nLemma: ${token.lemma}\nPadapāṭha: ${token.analysis.unsandhied}`,
                html: token_text
            });
            $entity_cell.append($entity);

            const $entity_type_cell = $("<td>");
            $entity_row.append($entity_type_cell);

            const $entity_selector_element = task_3_sample_entity_type.clone();
            $entity_type_cell.append($entity_selector_element);

            const entity_selector_id = `entity-selector-${token.id}`;
            $entity_selector_element.attr("id", entity_selector_id);

            if (is_entity) {
                $entity_selector_element.selectpicker('val', entity_label_id);
            } else {
                $entity_selector_element.selectpicker('hide');
            }

            const $entity_toggle_cell = $("<td>", {
                class: "col-sm-1",
            });
            $entity_row.append($entity_toggle_cell);

            var entity_class = (is_entity) ? "btn btn-secondary" : "btn btn-info include-entity";
            var entity_html = (is_entity) ? '<i class="fa fa-plus"></i>' : '<i class="fa fa-times"></i>';

            const $entity_toggle = $("<span>", {
                id: `entity-toggle-${token.id}`,
                name: "entity-toggle",
                class: entity_class,
                html: entity_html,
                on: {
                    click: function() {
                        const select_selector = `#${entity_selector_id}`;

                        if ($(this).hasClass("include-entity")) {
                            $(this).removeClass("include-entity");
                            $(this).removeClass("btn-info");
                            $(this).addClass("btn-secondary");
                            $(this).html('<i class="fa fa-times"></i>');
                            $(select_selector).selectpicker('show');
                            $task_3_entity_table.append($(this).parents('tr'));
                        } else {
                            $(this).removeClass("btn-secondary");
                            $(this).addClass("btn-info");
                            $(this).addClass("include-entity");
                            $(this).html('<i class="fa fa-plus"></i>');
                            $(select_selector).selectpicker('hide');
                            $task_3_non_entity_table.append($(this).parents('tr'));
                        }
                    }
                }
            });
            $entity_toggle_cell.append($entity_toggle);
        }
    }
}

/* Task-3 Actions */

// Skip-3
$task_3_skip.click(function () {
    // $task_3_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');
    // Task 3 Actions
    // ...
    $task_4_tab.click();
    $task_4_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
});

// Submit-3
$task_3_submit.click(function () {
    // $task_3_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');
    // Task 3 Actions

    if (!$task_3_form[0].checkValidity()) {
        $task_3_form[0].reportValidity();
        return;
    }
    const verse_id = $verse_id_containers.html();
    var named_entity_data = {}
    $task_3_entity_table.find("select").each(function(select_index, select_element) {
        const token_id = select_element.id;
        const entity_label = $(select_element).val();
        named_entity_data[token_id] = entity_label;
    });

    $.post(API_URL, {
        action: "update_named_entity",
        verse_id: verse_id,
        entity_data: JSON.stringify(named_entity_data)
    },
    function (response) {
        $.notify({
            message: response.message
        }, {
            type: response.style
        });

        if (response.success) {
            // ....
            $task_4_tab.click();
            $task_4_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
        }
    });
});

/* *********************************** END Task 3 *********************************** */

/* ********************************** BEGIN Task 4 ********************************** */
// Setup-4

/* Task-4 Actions */

// Skip-4
$task_4_skip.click(function () {
    $task_4_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');
    // Task 4 Skip Actions
    // ...
    $task_5_tab.click();
    $task_5_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
});

// Submit-4
$task_4_submit.click(function () {
    $task_4_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');

    $.post(API_URL, {
        action: "update_action_graph",
        verse_id: $verse_id_containers.html(),
    },
    function (response) {
        $.notify({
            message: response.message
        }, {
            type: response.style
        });

        if (response.success) {
            // ....
            $task_5_tab.click();
            $task_5_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
        }
    });
});

/* *********************************** END Task 4 *********************************** */

/* ********************************** BEGIN Task 5 ********************************** */
// Setup-5

/* Task-5 Actions */

// Skip-5
$task_5_skip.click(function() {
    $task_5_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');
    // Task 5 Skip Actions
    // ...
    $task_1_tab.click();
    $corpus_table.bootstrapTable('collapseAllRows');
    $corpus_table.bootstrapTable('uncheckAll');
    $corpus_table.bootstrapTable('expandRowByUniqueId', storage.getItem("next"));
});

// Submit-5
$task_5_submit.click(function() {
    $task_5_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');

    $.post(API_URL, {
        action: "update_coreference",
        verse_id: $verse_id_containers.html(),
    },
    function (response) {
        $.notify({
            message: response.message
        }, {
            type: response.style
        });

        if (response.success) {
            // ....
            $task_1_tab.click();
            $corpus_table.bootstrapTable('collapseAllRows');
            $corpus_table.bootstrapTable('uncheckAll');
            $corpus_table.bootstrapTable('expandRowByUniqueId', storage.getItem("next"));
        }
    });
});

/* *********************************** END Task 5 *********************************** */
