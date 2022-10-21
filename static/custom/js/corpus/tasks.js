/* ********************************** */
// Task Related Constants, Functions, Events etc.
/* ********************************** */
// Note: Constants/Variables in capital are declared in the HTML template.

// Constants

const default_token_class_common = "btn";
const default_token_class_normal = "btn-light";
const default_token_class_subtoken = "btn-warning";
const default_token_class_manual = "btn-secondary";
const default_token_class_multitoken = "btn-info";

const default_token_element = "<span />";
const default_token_data = {};

const sentence_token_graph_input_container_class = "sentence-token-graph-input-container";

// Generic Functions

function generate_token_button(options) {
    const token = options.token;
    const id_prefix = options.id_prefix;
    const onclick = options.onclick;
    const token_element = options.token_element || default_token_element;
    const token_class_common = options.token_class_common || default_token_class_common;
    const token_class_normal = options.token_class_normal || default_token_class_normal;
    const token_class_subtoken = options.token_class_subtoken || default_token_class_subtoken;
    const token_class_manual = options.token_class_manual || default_token_class_manual;
    const token_class_multitoken = options.token_class_multitoken || default_token_class_multitoken;

    const token_data = options.token_data || default_token_data;

    var token_class = token_class_normal;
    var token_text = token.text;

    // whenever unsandhied is available, use it?
    if (token.analysis.misc.Unsandhied && token.analysis.misc.Unsandhied != "_") {
        token_text = token.analysis.misc.Unsandhied;
    }

    if (!token.text || (token.text == "_")) {
        // subtoken (result of sandhi or samaasa split)
        token_class = token_class_subtoken;
        token_text = token.analysis.misc.Unsandhied;
        // setting token_text again is actually redundant
        // since we already use token.analysis.misc.Unsandhied whenever available
    }

    if (token.inner_id.includes("-")) {
        token_class = token_class_multitoken;
    }

    // can both text and unsandhied be null?
    // use lemma in such a case?
    if ((!token_text || (token_text == "_")) && (token.lemma && (token.lemma != "_"))) {
        token_text = token.lemma;
    }

    if (token.annotator_id != null) {
        // token added manually
        token_class = token_class_manual;
    }

    const $token = $(token_element, {
        class: [token_class_common, token_class].join(" "),
        title: [
            `ID: ${token.id}`,
            `Text: ${token.text}`,
            `Lemma: ${token.lemma}`,
            `Padapāṭha: ${token.analysis.misc.Unsandhied}`,
        ].join("\n"),
        html: token_text
    });
    if (token_element.includes("button")) {
        $token.attr("type", "button");
    }
    if (id_prefix) {
        $token.attr('id', `${id_prefix}-${token.id}`);
    }
    if (onclick) {
        $token.click(function() { onclick($(this)); });
    }
    for (const [key, value] of Object.entries(token_data)) {
        $token.data(key, value);
    };

    return $token;
}

function draw_graph(data) {
    const container = $graph[0];
    const options = {
        nodes: {
            shape: 'box',
            scaling: {
                min: 12,
                max: 24,
                label: {
                    min: 15,
                    max: 30,
                    drawThreshold: 12,
                    maxVisible: 30
                }
            },
            font: {
                size: 16,
                face: 'Noto Serif Devanagari'
            },
            margin: 8
        },
        edges: {
            width: 0.15,
            color: {
                inherit: 'both'
            },
            scaling: {
                min: 1,
                max: 5,
                label: {
                    min: 10,
                    max: 25,
                    drawThreshold: 5,
                    maxVisible: 20
                }
            },
            font: {
                size: 5,
                face: 'Noto Serif Devanagari',
            }
        },
        interaction: {
            tooltipDelay: 100,
            hideEdgesOnDrag: false,
            hideEdgesOnZoom: false
        },
        layout: {
            hierarchical: {
               enabled: true,
               sortMethod: 'directed',
               levelSeparation: 200,
               nodeSpacing: 150,
               treeSpacing: 250,
            },
        },
        physics: false
    };

    NETWORK = new vis.Network(container, data, options);

    // get a JSON object
    NETWORK.on("afterDrawing", function (ctx) {
        const data_url = ctx.canvas.toDataURL();
        $snapshot_graph_button.data("src", data_url);
    });
}

function refresh_row_data(unique_id, _callback) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);
    const verse_data_url = SAMPLE_VERSE_DATA_URL.replace('0', unique_id);
    $.get(verse_data_url, function (data) {
        $corpus_table.bootstrapTable('updateByUniqueId', {
            id: unique_id,
            row: data[unique_id],
            replace: true
        });
        $corpus_table.bootstrapTable('collapseRowByUniqueId', unique_id);
        $corpus_table.bootstrapTable('check', storage.getItem('current_index'));

        if (_callback) {
            _callback(unique_id);
        }
    }, 'json');
    console.log(`Verse data updated for ID: ${unique_id}`);
}

$refresh_verse_buttons.click(function() {
    const verse_id = $verse_id_containers.html();
    refresh_row_data(verse_id);
});


/* ****************************** Generic Task Setup ****************************** */

function setup_task(task_id, verse_id) {
    switch (task_id) {
        case "1":
            setup_sentence_boundary(verse_id);
            break;
        case "2":
            setup_anvaya(verse_id);
            break;
        case "3":
            setup_named_entity(verse_id);
            break;
        case "4":
            setup_token_graph(verse_id);
            break;
        case "5":
            setup_coreference(verse_id);
            break;
        case "6":
            setup_sentence_classification(verse_id);
            break;
        case "7":
            setup_intersentence_connection(verse_id);
            break;

        default:
            break;
    }
}

/* ********************************** BEGIN Task 1 ********************************** */
// Task 1: Sentence Boundary

// Setup-1
function setup_sentence_boundary(verse_id) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const row = $corpus_table.bootstrapTable('getRowByUniqueId', verse_id);
    const data = $corpus_table.bootstrapTable('getData');

    // find out current index
    const index = data.findIndex(function(r) {
        return r.verse_id == verse_id;
    });

    // console.log(row);
    // console.log(data);
    // console.log(index);

    // calculate slice
    const start_index = (index > 1) ? (index - 1) : 0;
    const end_index = (index < data.length - 1) ? (index + 1) : data.length - 1;
    const context = data.slice(start_index, end_index + 1);

    var task_1_text = [];
    var task_1_text_before = [];
    var task_1_text_after = [];

    var display_token_last_components = [];
    for (const verse_data of context) {
        // console.log("Verse Tokens:");
        // console.log(verse.tokens);
        // console.log("Verse Boundary:");
        // console.log(verse.boundary);

        var verse_text = [`${verse_data.verse_id}`];
        var boundary_tokens = new Set();

        for (const [boundary_id, boundary] of Object.entries(verse_data.boundary)) {
            boundary_tokens.add(boundary.token_id);
        };
        $.each(verse_data.tokens, function(verse_index, line_tokens) {
            verse_text.push("\t");
            $.each(line_tokens, function(token_index, token) {
                if (token.annotator_id != null) {
                    return;
                    // "return;" in each() == "continue;"
                    // "return false;" in each() == "break;"
                }
                if (token.text !== "_") {
                    var token_id = token.id;

                    if (token.relative_id instanceof Array) {
                        // if token id is of composite word,
                        // we want the marker to be after the last component
                        token_id += token.relative_id[2] - token.relative_id[0] + 1;
                    }
                    if (verse_data.verse_id == row.verse_id) {
                        display_token_last_components.push(token_id);
                    }
                    verse_text.push(token.text);
                }
                if (boundary_tokens.has(token.id)) {
                    verse_text.push("##");
                }
            });
            if (verse_index < verse_data.tokens.length - 1) {
                verse_text.push("\n");
            }
        });
        var actual_verse_text = verse_text.join(" ");
        if (verse_data.verse_id < row.verse_id) {
            task_1_text_before.push(actual_verse_text);
        }
        if (verse_data.verse_id == row.verse_id) {
            task_1_text.push(actual_verse_text);
        }
        if (verse_data.verse_id > row.verse_id) {
            task_1_text_after.push(actual_verse_text);
        }
    };
    $task_1_input.data('marker_positions', display_token_last_components);
    $task_1_input_before.val(task_1_text_before.join("\n"));
    $task_1_input_after.val(task_1_text_after.join("\n"));

    $task_1_input.val(task_1_text.join("\n"));

    // Enable + Focus Text Area
    $task_1_input.prop('disabled', false).removeClass('text-muted').addClass('text-info').focus();
}

// Submit-1
$task_1_submit.click(function () {
    const verse_id = $verse_id_containers.html();

    // Identify Boundary Token IDs
    const marker_positions = $task_1_input.data('marker_positions');
    const submitted_tokens = $task_1_input.val().split(/\s+/);
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
        action: TASK_1_SUBMIT_ACTION,
        verse_id: verse_id,
        boundaries: line_break_tokens.join(","),
    },
    function (response) {
        $.notify({
            message: response.message
        }, {
            type: response.style
        });

        if (response.success) {
            $task_1_input.prop('disabled', true).removeClass('text-info').addClass('text-muted');

            refresh_row_data(verse_id);
            const first_task = response.first_task;
            const next_task = response.next_task;
            $tabs[next_task].click();
            if (next_task == first_task) {
                $corpus_table.bootstrapTable('check', storage.getItem("next_index"));
            }
        }
    },
    'json');
});

/* *********************************** END Task 1 *********************************** */

/* ********************************** BEGIN Task 2 ********************************** */
// Task 2: Anvaya

// Setup-2
function setup_sortable() {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    $('.connected-sortable').sortable({
        opacity: 0.75,
        revert: true,
        cursor: "move",
        tolerance: "pointer",
        placeholder: 'btn btn-secondary py-3 px-5 mb-1 mr-1',
        connectWith: ".sortable"
    }).on("sortremove", function(e, ui) {
        const toggle_id = ui.item[0].id.replace("button", "toggle");
        $(`#${toggle_id}`).prop('disabled', false);
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
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const row = $corpus_table.bootstrapTable('getRowByUniqueId', verse_id);

    $task_2_anvaya_container.html("");
    const $extra = $("<div />", {
        id: `extra-${verse_id}`,
        class: "border px-1 pt-1 m-1 rounded connected-sortable",
        style: "background-color: #eeeeff; border-color: #aaaaff !important;"
    });
    $task_2_anvaya_container.append($extra);
    const extra_tokens = row.sentences['extra'];
    var all_tokens = {};

    var used_extra_tokens = [];
    for (const [boundary_id, sentence_tokens] of Object.entries(row.sentences)) {
        $.extend(all_tokens, sentence_tokens);
        if (boundary_id == "extra") {
            continue;
        }
        // console.log("Boundary ID: " + boundary_id);
        // console.log("Tokens:")
        // console.log(sentence_tokens);
        for (const token_id of row.anvaya[boundary_id]) {
            if (extra_tokens.hasOwnProperty(token_id)) {
                used_extra_tokens.push(token_id);
            }
        }
    }
    for (const [boundary_id, sentence_tokens] of Object.entries(row.sentences)) {
        var token_order = [];
        var unused_tokens = [];
        if (boundary_id !== "extra") {
            token_order = row.anvaya[boundary_id];
            for (const [_token_id_string, _token] of Object.entries(sentence_tokens)) {
                if (!token_order.includes(_token.id)) {
                    unused_tokens.push(_token.id);
                }
            }
            // ensure in server_sqla.py that row.anvaya isn't empty
            // either it is annotated anvaya, or it's obtained via heuristic
        } else {
            // order doesn't really matter, just need extra tokens
            token_order = Object.keys(sentence_tokens);
        }
        console.log("Token Order: " + token_order);

        const $sentence = $("<div />", {
            id: `boundary-${boundary_id}`,
            class: "sortable border px-1 pt-1 m-1 rounded",
            style: "background-color: #eeffee; border-color: #aaffaa !important;"
        });
        const $unused = $("<div />", {
            id: `unused-${boundary_id}`,
            class: "border px-1 pt-1 m-1 rounded",
            style: "background-color: #ffeeee; border-color: #ffaaaa !important;"
        });
        if (boundary_id != "extra") {
            $task_2_anvaya_container.append($sentence);
            $task_2_anvaya_container.append($unused);
        }

        for (const token_id of [...token_order, ...unused_tokens]) {
            // while sentence_tokens contains token_order + unused_tokens,
            // doing it this way, instead of going over sentence_tokens
            // is required to present tokens in the token_order
            var token;
            if (sentence_tokens.hasOwnProperty(token_id)) {
                token = sentence_tokens[token_id];
            } else if (extra_tokens.hasOwnProperty(token_id)) {
                token = extra_tokens[token_id];
            } else {
                console.log("Something weird happened. Token is neither part of sentence, nor extra.");
            }

            const is_token_used = (!unused_tokens.includes(token.id));
            const is_extra_unused = (!used_extra_tokens.includes(token.id));

            const $token_button = $("<div />", {
                id: `token-button-${token.id}`,
                role: "group",
                class: "btn-group mr-1 mb-1 border border-secondary rounded",
            });

            if (boundary_id == "extra") {
                if (is_extra_unused) {
                    $extra.append($token_button);
                }
            } else {
                if (is_token_used) {
                    $sentence.append($token_button);
                } else {
                    $unused.append($token_button);
                }
            }
            const $token = generate_token_button({
                token: token,
                id_prefix: "token"
            });
            $token_button.append($token);

            if (token.annotator_id == null) {
                if (is_token_used) {
                    var token_class = "btn btn-secondary exclude-token";
                    var token_html = '<i class="fa fa-times"></i>';
                } else {
                    var token_class = "btn btn-info";
                    var token_html = '<i class="fa fa-plus"></i>';
                }
                const $token_toggle = $("<button />", {
                    id: `token-toggle-${token.id}`,
                    name: "token-toggle",
                    class: token_class,
                    html: token_html,
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
            } else {
                const $token_toggle = $("<button />", {
                    id: `token-toggle-${token.id}`,
                    name: "token-toggle",
                    class: "btn btn-secondary include-token",
                    html: '<i class="fa fa-times"></i>',
                    disabled: is_extra_unused,
                    on: {
                        click: function() {
                            $(`#extra-${verse_id}`).append($(this).parent());
                            $(this).prop("disabled", true);
                            $(".sortable").trigger("sortstop");
                        }
                    }
                });
                $token_button.append($token_toggle);
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
    const token_text = $add_token_input_text.val();
    const token_lemma = $add_token_input_lemma.val();
    const token_analysis_upos = $add_token_input_analysis_upos.val();
    const token_analysis_xpos = $add_token_input_analysis_xpos.val();
    var token_features = {};

    $add_token_feature_items.each(function(_index, _element){
        const $element = $(_element);
        const label = $element.find(add_token_feature_label_selector).html().trim();
        const value = $element.find(add_token_feature_input_selector).val();
        if (value) {
            token_features[label] = value;
        }
    });
    const token_analysis = {
        form: token_text,
        lemma: token_lemma,
        upos: token_analysis_upos,
        xpos: token_analysis_xpos,
        feats: token_features,
        misc: {
            "Unsandhied": token_text
        } // Corpus Specific
    }
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
            refresh_row_data(verse_id);
        }
    });
});

// Submit-2
$task_2_submit.click(function () {
    // Task 2 Actions

    const verse_id = $verse_id_containers.html();
    var anvaya_data = {}
    $('.sortable').each(function(sentence_index, sentence_element) {
        const boundary_id = sentence_element.id;
        anvaya_data[boundary_id] = $(sentence_element).data("anvaya");
    });
    // console.log("Anvaya Data: ");
    // console.log(anvaya_data);

    $.post(API_URL, {
        action: TASK_2_SUBMIT_ACTION,
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
            refresh_row_data(verse_id);
            const first_task = response.first_task;
            const next_task = response.next_task;
            $tabs[next_task].click();
            if (next_task == first_task) {
                $corpus_table.bootstrapTable('check', storage.getItem("next_index"));
            }
        }
    });
});

/* *********************************** END Task 2 *********************************** */

/* ********************************** BEGIN Task 3 ********************************** */
// Task 3: Named Entity

// Setup-3
function setup_named_entity(verse_id) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const row = $corpus_table.bootstrapTable('getRowByUniqueId', verse_id);

    $task_3_entity_table.html("");
    $task_3_non_entity_table.html("");

    var all_tokens = {};
    var used_tokens = [];
    var boundary_tokens = {};

    for (const [boundary_id, sentence_tokens] of Object.entries(row.sentences)) {
        $.extend(all_tokens, sentence_tokens);
        if (boundary_id !== "extra") {
            [].push.apply(used_tokens, row.anvaya[boundary_id]);
            boundary_tokens[boundary_id] = row.anvaya[boundary_id];
        }
    }

    // record existing labels
    // existing_entities array could be avoided perhaps
    // in that case, .includes() can be replaced with .hasOwnProperty() check
    var existing_entities = [];
    var existing_labels = {};
    for (const entity of row.entity) {
        if (entity.is_deleted) {
            continue;
        }
        existing_entities.push(entity.token_id);
        existing_labels[entity.token_id] = entity.label_id;
    }

    for (const [boundary_id, used_token_ids] of Object.entries(boundary_tokens)) {
        for (const token_id of used_token_ids) {
            const token = all_tokens[token_id];
            var is_entity = false;
            var entity_label_id = null;
            const $entity_row = $("<tr />", {});
            if (existing_entities.includes(token.id)) {
                $task_3_entity_table.append($entity_row);
                is_entity = true;
                entity_label_id = existing_labels[token.id];
            } else {
                $task_3_non_entity_table.append($entity_row);
            }

            const $entity_cell = $("<td />", {});
            $entity_row.append($entity_cell);

            const $entity = generate_token_button({
                token: token,
                id_prefix: "entity"
            });
            $entity_cell.append($entity);

            const $entity_type_cell = $("<td />");
            $entity_row.append($entity_type_cell);

            const $entity_selector_element = task_3_sample_entity_type.clone();
            $entity_selector_element.data("boundary-id", boundary_id);
            $entity_type_cell.append($entity_selector_element);

            const entity_selector_id = `entity-selector-${token.id}`;
            $entity_selector_element.attr("id", entity_selector_id);

            if (is_entity) {
                $entity_selector_element.selectpicker('val', entity_label_id);
            } else {
                $entity_selector_element.selectpicker('hide');
            }

            const $entity_toggle_cell = $("<td />", {
                class: "col-sm-1",
            });
            $entity_row.append($entity_toggle_cell);

            const entity_class = (is_entity) ? "btn btn-secondary" : "btn btn-info include-entity";
            const entity_html = (is_entity) ? '<i class="fa fa-times"></i>' : '<i class="fa fa-plus"></i>';

            const $entity_toggle = $("<span />", {
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

// Submit-3
$task_3_submit.click(function () {
    // Task 3 Actions

    if (!$task_3_form[0].checkValidity()) {
        $task_3_form[0].reportValidity();
        return;
    }
    const verse_id = $verse_id_containers.html();
    var named_entity_data = {}
    $task_3_entity_table.find("select").each(function(select_index, select_element) {
        const token_id = select_element.id;
        const boundary_id = $(select_element).data("boundary-id");
        const entity_label_id = $(select_element).selectpicker('val');
        named_entity_data[token_id] = {
            'boundary_id': boundary_id,
            'label_id': entity_label_id
        }
    });

    $.post(API_URL, {
        action: TASK_3_SUBMIT_ACTION,
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
            refresh_row_data(verse_id);
            const first_task = response.first_task;
            const next_task = response.next_task;
            $tabs[next_task].click();
            if (next_task == first_task) {
                $corpus_table.bootstrapTable('check', storage.getItem("next_index"));
            }
        }
    });
});

/* *********************************** END Task 3 *********************************** */

/* ********************************** BEGIN Task 4 ********************************** */
// Task 4: Token Graph (e.g. Action Graph)
// Setup-4

function setup_token_graph(verse_id) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const row = $corpus_table.bootstrapTable('getRowByUniqueId', verse_id);

    $task_4_token_graph_input_container.html("");

    var all_tokens = {};
    var boundary_tokens = {};

    for (const [boundary_id, sentence_tokens] of Object.entries(row.sentences)) {
        $.extend(all_tokens, sentence_tokens);
        if (boundary_id != "extra") {
            boundary_tokens[boundary_id] = row.anvaya[boundary_id];
        }
    }

    // record existing relations
    var existing_relations = {};
    for (const relation of row.relation) {
        if (relation.is_deleted) {
            continue;
        }
        if (!existing_relations.hasOwnProperty(relation.boundary_id)) {
            existing_relations[relation.boundary_id] = [];
        }
        existing_relations[relation.boundary_id].push([
            relation.src_id,
            relation.label_id,
            relation.dst_id
        ]);
    }
    console.log(existing_relations);

    for (const [boundary_id, used_token_ids] of Object.entries(boundary_tokens)) {
        const $graph_input = $task_4_sample_token_graph_input.clone();
        $graph_input.prop("id", `token-graph-input-${boundary_id}`);
        $graph_input.addClass(sentence_token_graph_input_container_class);
        $graph_input.data("boundary-id", boundary_id);
        $graph_input.appendTo($task_4_token_graph_input_container);

        const $graph_input_header = $graph_input.find(".boundary-token-graph-header");

        // populate options
        var options = {};
        var header_html = [];
        for (const token_id of used_token_ids) {
            const token = all_tokens[token_id];
            const $token = generate_token_button({
                token: token,
                token_class_common: "btn-sm"
            });
            const token_text = $token.html();
            const token_html = $token.wrapAll('<div>').parent().html();
            header_html.push(token_text);
            options[token_id] = {
                text: token_text,
                content: token_html
            };
        }
        const header_text = header_html.join(" ");
        $graph_input_header.html(header_text);

        // Re-Bind Add Triplet Row Function
        const $add_triplet_button = $graph_input.find(".add-triplet-button");
        const $triplet_location = $graph_input.find(".token-graph-input");
        $triplet_location.data("triplet-count", 0);
        $triplet_location.data("header-text", header_text);
        $triplet_location.data("source-options", options);
        $triplet_location.data("target-options", options);

        $add_triplet_button.off("click");
        $add_triplet_button.click(function () {
            add_triplet_row($triplet_location);
        });

        if (existing_relations.hasOwnProperty(boundary_id)) {
            for (const [_src_id, _label_id, _dst_id] of existing_relations[boundary_id]) {
                const $triple_row = add_triplet_row($triplet_location);
                $triple_row.find(".source-entity").selectpicker('val', _src_id);
                $triple_row.find(".relation-label").selectpicker('val', _label_id);
                $triple_row.find(".target-entity").selectpicker('val', _dst_id);
            }
        } else {
            // $add_triplet_button.click();
        }
    }
}

function add_triplet_row($location) {
    const source_entity_options = $location.data("source-options");
    const target_entity_options = $location.data("target-options");

    // Create and Insert Triplet Row Element
    const $row = $('<div />').addClass(`form-row mt-1 px-0`).appendTo($location);
    $row.addClass('triplet-row');

    const triplet_count = $location.data("triplet-count") + 1;
    $location.data("triplet-count", triplet_count);

    // Create Action Entity Input Element
    const $input_source_entity = $task_4_sample_source_entity.clone();
    $input_source_entity.attr("id", `element-source-entity-${triplet_count}`);
    var current_value = $input_source_entity.attr("title");
    var updated_value = current_value.replace(
        "{}",
        `${VARIABLE_PREFIX}a${triplet_count}${VARIABLE_SUFFIX}`
    );
    $input_source_entity.attr("title", updated_value);
    $input_source_entity.addClass("source-entity");

    // Add Options
    for (const [option_value, option] of Object.entries(source_entity_options)) {
        const $option = $("<option />", {
            value: option_value,
            html: option.text
        });
        $option.attr("data-content", option.content);
        $option.appendTo($input_source_entity);
    }


    // Insert Action Entity Input Element
    var $column = $('<div />').addClass(`col-sm mx-0 pr-0`).appendTo($row);
    $input_source_entity.appendTo($column);
    // $input_source_entity.autoComplete();

    // Create Actor Label Selector Element
    const $input_relation_label = $task_4_sample_relation_label.clone();
    $input_relation_label.attr("id", `element-relation-label-${triplet_count}`);
    var current_value = $input_relation_label.attr("title");
    var updated_value = current_value.replace(
        "{}",
        `${VARIABLE_PREFIX}r${triplet_count}${VARIABLE_SUFFIX}`
    );
    $input_relation_label.attr("title", updated_value);
    $input_relation_label.addClass("relation-label");

    // Insert Actor Label Selector Element
    var $column = $('<div />').addClass(`col-sm mx-1 px-0`).appendTo($row);
    $input_relation_label.appendTo($column);

    // Create Target Entity Input Element
    const $input_target_entity = $task_4_sample_target_entity.clone();
    $input_target_entity.attr("id", `element-target-entity-${triplet_count}`);
    var current_value = $input_target_entity.attr("title");
    var updated_value = current_value.replace(
        "{}",
        `${VARIABLE_PREFIX}t${triplet_count}${VARIABLE_SUFFIX}`
    );
    $input_target_entity.attr("title", updated_value);
    $input_target_entity.addClass("target-entity");

    // Add Options
    for (const [option_value, option] of Object.entries(target_entity_options)) {
        const $option = $("<option />", {
            value: option_value,
            html: option.text
        });
        $option.attr("data-content", option.content);
        $option.appendTo($input_target_entity);
    }

    // Insert Target Entity Input Element
    var $column = $('<div />').addClass(`col-sm mx-0 pl-0`).appendTo($row);
    const $form_group = $('<div />').addClass('form-group').appendTo($column);
    $input_target_entity.appendTo($form_group);
    // $input_target_entity.autoComplete();

    // Create Remove Triplet Button
    const $remove_triplet_button = $('<button />').addClass("btn btn-danger");
    $remove_triplet_button.attr("id", `remove-triplet-button-${triplet_count}`);
    $remove_triplet_button.attr("title", "Remove Relation");
    const $remove_icon = $('<i />').addClass(`fas fa-minus`);

    // Insert Remove Triplet Button
    var $column = $('<div />').addClass(`col-sm-1 mx-0 px-0`).appendTo($row);
    $remove_icon.appendTo($remove_triplet_button);
    $remove_triplet_button.appendTo($column);
    $remove_triplet_button.click(function () {
        $(this).parent().parent().remove();
    });

    $input_source_entity.selectpicker();
    $input_relation_label.selectpicker();
    $input_target_entity.selectpicker();

    return $row;
}

function prepare_token_graph_data($data_location) {
    var data = {
        nodes: [],
        edges: []
    };

    // temporary id store
    // TODO: consider replacing it with actual node_ids
    //       don't think there's any real benefit either way
    var node_ids = {};
    var node_id = 0;
    function get_node_id() {
        return ++node_id;
    }

    $data_location.children(".triplet-row").each(function (triplet_index, triplet_row) {
        const $triplet_row = $(triplet_row);
        const $source_entity = $triplet_row.find('.source-entity');
        const $target_entity = $triplet_row.find('.target-entity');
        const $relation_label = $triplet_row.find('.relation-label');

        const source_entity_value = $source_entity.selectpicker('val');
        const target_entity_value = $target_entity.selectpicker('val');
        const relation_label_value = $relation_label.selectpicker('val');

        if (!source_entity_value || !relation_label_value || !relation_label_value) {
            return;
            // "return;" in .each() ==> "continue;"
            // "return false;" in .each() ==> "break;"
        }

        const source_entity = $source_entity.find(`[value=${source_entity_value}]`).html();
        const target_entity = $source_entity.find(`[value=${target_entity_value}]`).html();
        const relation_label = $relation_label.find(`[value=${relation_label_value}]`).data("subtext");

        if (!node_ids.hasOwnProperty(source_entity)) {
            node_ids[source_entity] = get_node_id();

            data.nodes.push({
                id: node_ids[source_entity],
                label: source_entity, // label
                title: `Token ID: ${source_entity_value}`, // title (visible on hover)
                value: 3,
                group: null // group-id (upos/xpos based?)
            });
        }
        if (!node_ids.hasOwnProperty(target_entity)) {
            node_ids[target_entity] = get_node_id();

            data.nodes.push({
                id: node_ids[target_entity],
                label: target_entity, // label
                title: `Token ID: ${target_entity_value}`, // title (visible on hover)
                value: 3,
                group: null // group-id (upos/xpos based?)
            });
        }

        data.edges.push({
            from: node_ids[source_entity], // start-id
            to: node_ids[target_entity],  // end-id
            label: relation_label, // label
            title: `Label ID: ${relation_label_value}`, // title (visible on hover)
            arrows: {
                to: {
                    enabled: true
                }
            },
            value: 3,
        });
    });

    console.log("Graph Data: ");
    console.log(data);
    return data;
}

// Show Graph Modal
$show_graph_modal.on('shown.bs.modal', function(e) {
    const $trigger_button = $(e.relatedTarget);
    const source_task = $trigger_button.data("task");

    if (source_task == "token_graph") {
        // triggered from token_graph task
        const $target_card = $trigger_button.parents(`.${sentence_token_graph_input_container_class}`);
        const $target_location = $target_card.find(".token-graph-input");

        const sentence_text = $target_location.data("header-text");
        $show_graph_modal_label.html(sentence_text);

        const graph_data = prepare_token_graph_data($target_location);
        draw_graph(graph_data);

    } else if (source_task == "intersentence_connection") {
        // triggered from intersentence_connection task
        const graph_data = prepare_intersentence_connection_data();
        draw_graph(graph_data);
    }
});

/* Task-4 Actions */

// Capture Graph Snapshot
/* Logic:
    * Create a dummy 'anchor' (<a>) with 'href' as image data.
    * Simulate a click on it.
    * Remove the dummy  anchor.
*/
$snapshot_graph_button.click(function() {
    const download_anchor = document.createElement('a');
    download_anchor.href = $snapshot_graph_button.data('src');
    /* TODO: name using verse_id / boundary_idx ? */
    download_anchor.download = 'graph.png';
    document.body.appendChild(download_anchor);
    download_anchor.click();
    document.body.removeChild(download_anchor);
});

// Submit-4
$task_4_submit.click(function () {
    const verse_id = $verse_id_containers.html();

    if (!$task_4_form[0].checkValidity()) {
        $task_4_form[0].reportValidity();
        return;
    }

    var graph_data = [];

    // NOTE: selector cannot be constant, due to being dynamic
    $(`.${sentence_token_graph_input_container_class}`).each(function (_container_index, _container) {
        const $container = $(_container);
        const boundary_id = $container.data("boundary-id");
        console.log($container);
        $container.find(".triplet-row").each(function (_row_index, _triplet_row) {
            const $triplet_row = $(_triplet_row);
            const $source_entity = $triplet_row.find('.source-entity');
            const $relation_label = $triplet_row.find('.relation-label');
            const $target_entity = $triplet_row.find('.target-entity');

            const source_entity_id = $source_entity.selectpicker('val');
            const relation_label_id = $relation_label.selectpicker('val');
            const target_entity_id = $target_entity.selectpicker('val');
            graph_data.push({
                "boundary_id": boundary_id,
                "src_id": source_entity_id,
                "label_id": relation_label_id,
                "dst_id": target_entity_id
            });
        });
    });
    console.log("Submit Graph Data: ");
    console.log(graph_data);

    $.post(API_URL, {
        action: TASK_4_SUBMIT_ACTION,
        verse_id: verse_id,
        graph_data: JSON.stringify(graph_data)
    },
    function (response) {
        $.notify({
            message: response.message
        }, {
            type: response.style
        });

        if (response.success) {
            refresh_row_data(verse_id);
            const first_task = response.first_task;
            const next_task = response.next_task;
            $tabs[next_task].click();
            if (next_task == first_task) {
                $corpus_table.bootstrapTable('check', storage.getItem("next_index"));
            }
        }
    });
});

/* *********************************** END Task 4 *********************************** */

/* ********************************** BEGIN Task 5 ********************************** */
// Task 5: Co-reference Resolution

// Setup-5


function setup_coreference(verse_id) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const row = $corpus_table.bootstrapTable('getRowByUniqueId', verse_id);
    const data = $corpus_table.bootstrapTable('getData');

    // calculate pre-context
    const current_index = data.findIndex(function(r) {
        return r.verse_id == verse_id;
    });

    const start_index = (current_index > 2) ? (current_index - 3) : 0;
    const context = data.slice(start_index, current_index + 1);

    var all_tokens = {};
    var boundary_tokens = [];

    var existing_coreferences = [];

    for (const verse_data of context) {
        // verse_data
        for (const [boundary_id, sentence_tokens] of Object.entries(verse_data.sentences)) {
            $.extend(all_tokens, sentence_tokens);
            if (boundary_id != "extra") {
                boundary_tokens.push([boundary_id, verse_data.anvaya[boundary_id]]);
            }
            // ensure that every boundary in the previous n verses has anvaya
            // if one is doing anvaya in order, this won't be an issue
        }
        for (const coreference of verse_data.coreference) {
            if (coreference.is_deleted) {
                continue;
            }
            existing_coreferences.push(coreference);
        }
    };
    console.log(existing_coreferences);

    $task_5_coref_context_container.html("");
    $task_5_coref_reset_button.click();
    $task_5_coref_annotation_container.html("");

    for (const [boundary_id, used_tokens] of boundary_tokens) {
        const $boundary_container = $("<div />", {
            id: `coref-boundary-container-${boundary_id}`,
            class: "border border-secondary rounded px-1 pt-1 pb-0 ml-1 mt-1 mb-0 boundary-container"
        });
        $boundary_container.appendTo($task_5_coref_context_container);
        $boundary_container.data("boundary-id", boundary_id);

        for (const token_id of used_tokens) {
            const token = all_tokens[token_id];
            const $token = generate_token_button({
                token: token,
                token_element: "<button />",
                id_prefix: "coref-token",
                token_data: {token_id: token_id, boundary_id: boundary_id},
                onclick: function($element) {
                    const $annotation_token = $element.clone();
                    $annotation_token.removeAttr("id");
                    $annotation_token.data("token-id", token_id);
                    $annotation_token.data("boundary-id", boundary_id);

                    if (!$task_5_coref_source_container.html().trim()) {
                        $annotation_token.addClass("coref-source-token");
                        $annotation_token.appendTo($task_5_coref_source_container);
                        $element.prop("disabled", true);
                    } else {
                        if (!$task_5_coref_target_container.html().trim()) {
                            $annotation_token.addClass("coref-target-token");
                            $annotation_token.appendTo($task_5_coref_target_container);
                            $task_5_coref_confirm_button.prop("disabled", false);
                            $element.prop("disabled", true);
                        } else {
                            $.notify({
                                message: "Please confirm or reset the current coreference first."
                            }, {
                                type: "danger"
                            });
                        }
                        $task_5_coref_confirm_button.focus();
                    }
                }
            });
            $token.addClass("mr-1 mb-1");
            $token.appendTo($boundary_container);
        }
    }

    // add existing references
    for (const coreference of existing_coreferences) {
        const $source_token = $(`#coref-token-${coreference.src_id}`).clone();
        $source_token.removeAttr("id");
        $source_token.data("token-id", coreference.src_id);
        $source_token.data("boundary-id", coreference.boundary_id);
        $source_token.addClass("coref-source-token");

        const $target_token = $(`#coref-token-${coreference.dst_id}`).clone();
        const target_token_boundary_id = $(`#coref-token-${coreference.dst_id}`).data("boundary-id");
        $target_token.removeAttr("id");
        $target_token.data("token-id", coreference.dst_id);
        $target_token.data("boundary-id", target_token_boundary_id);
        $target_token.addClass("coref-target-token");

        add_coref_row($source_token, $target_token);
    }

}


function add_coref_row($source_token, $target_token) {
    const $row = $('<div />').addClass("row").prependTo($task_5_coref_annotation_container);
    $row.addClass('coref-annotation-row');

    // add source token
    var $column = $("<div />", {
        class: "col-sm",
    }).appendTo($row);
    $source_token.appendTo($column);

    // add arrow
    var $column = $("<div />", {
        class: "col-sm-2",
        html: '<span class="btn btn-secondary mb-1 mr-1"><i class="fas fa-arrows-left-right"></i></span>'
    }).appendTo($row);

    // add target token
    var $column = $("<div />", {
        class: "col-sm",
    }).appendTo($row);
    $target_token.appendTo($column);

    // add remove button
    const $remove_coref_button = $('<button />').addClass(`btn btn-danger float-right mx-1`);
    $remove_coref_button.attr("title", "Remove Coreference");
    const $remove_icon = $('<i />').addClass(`fas fa-minus`);
    var $column = $('<div />').addClass("col-sm-2").appendTo($row);
    $remove_icon.appendTo($remove_coref_button);
    $remove_coref_button.appendTo($column);
    $remove_coref_button.click(function () {
        $(this).parent().parent().remove();
    });
}

$task_5_coref_confirm_button.click(function () {
    const $source_token = $task_5_coref_source_container.children(".coref-source-token");
    const $target_token = $task_5_coref_target_container.children(".coref-target-token");

    add_coref_row($source_token, $target_token);

    // reset
    $task_5_coref_reset_button.click();
    $task_5_coref_confirm_button.prop("disabled", true);
});

$task_5_coref_reset_button.click(function () {
    // enable all buttons
    $task_5_coref_context_container.find("button").prop("disabled", false);

    $task_5_coref_source_container.html("");
    $task_5_coref_target_container.html("");
});

/* Task-5 Actions */

// Submit-5
$task_5_submit.click(function() {
    const verse_id = $verse_id_containers.html();

    var context_data = [];
    var coreference_data = [];
    $task_5_coref_context_container.find(".boundary-container").each(function (_index, _boundary_container) {
        context_data.push($(_boundary_container).data("boundary-id"));
    });

    const $coref_annotation_rows = $task_5_coref_annotation_container.find('.coref-annotation-row');
    $coref_annotation_rows.each(function(coref_index, coref_row) {
        const $coref_row = $(coref_row);
        const $source_token = $coref_row.find(".coref-source-token");
        const $target_token = $coref_row.find(".coref-target-token");

        coreference_data.push({
            "boundary_id": $source_token.data("boundary-id"),
            "src_id": $source_token.data("token-id"),
            "dst_id": $target_token.data("token-id")
        });
    });
    $.post(API_URL, {
        action: TASK_5_SUBMIT_ACTION,
        verse_id: verse_id,
        context_data: JSON.stringify(context_data),
        coreference_data: JSON.stringify(coreference_data)
    },
    function (response) {
        $.notify({
            message: response.message
        }, {
            type: response.style
        });
        if (response.success) {
            refresh_row_data(verse_id);
            const first_task = response.first_task;
            const next_task = response.next_task;
            $tabs[next_task].click();
            if (next_task == first_task) {
                $corpus_table.bootstrapTable('check', storage.getItem("next_index"));
            }
        }
    });
});

/* *********************************** END Task 5 *********************************** */

/* ********************************** BEGIN Task 6 ********************************** */
// Task 6: Sentence Classification

// Setup-6

function setup_sentence_classification(verse_id) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const row = $corpus_table.bootstrapTable('getRowByUniqueId', verse_id);

    $task_6_sentence_classification_input_container.html("");

    var all_tokens = {};
    var boundary_tokens = {};

    for (const [boundary_id, sentence_tokens] of Object.entries(row.sentences)) {
        $.extend(all_tokens, sentence_tokens);
        if (boundary_id != "extra") {
            boundary_tokens[boundary_id] = row.anvaya[boundary_id];
        }
    }

    // record existing sentence classification
    var existing_sentence_classification = {};
    for (const sentence of row.sentence_classification) {
        if (!existing_sentence_classification.hasOwnProperty(sentence.boundary_id)) {
            existing_sentence_classification[sentence.boundary_id] = [];
        }
        existing_sentence_classification[sentence.boundary_id] = sentence.label_id;
    }

    for (const [boundary_id, used_token_ids] of Object.entries(boundary_tokens)) {
        var header_html = [];
        for (const token_id of used_token_ids) {
            const token = all_tokens[token_id];
            const $token = generate_token_button({
                token: token,
                token_class_common: "btn-sm"
            });
            const token_text = $token.html();
            header_html.push(token_text);
        }
        const header_text = header_html.join(" ");
        const $sentence = $task_6_sample_sentence_classification_input.clone();
        $sentence.attr("id", `sentence-classification-boundary-${boundary_id}`);
        $sentence.appendTo($task_6_sentence_classification_input_container);

        const $sentence_text = $sentence.find(".sentence-text");
        $sentence_text.html(header_text);
        $sentence_text.data("boundary-id", boundary_id);

        const $sentence_label_select = $sentence.find(".sentence-label");
        $sentence_label_select.attr("id", `sentence-classification-select-${boundary_id}`);

        console.log(existing_sentence_classification);
        if (existing_sentence_classification.hasOwnProperty(boundary_id)) {
            $sentence_label_select.selectpicker("val", existing_sentence_classification[boundary_id]);
        } else {
            $sentence_label_select.selectpicker();
        }
    }
}

/* Task-6 Actions */

// Submit-6
$task_6_submit.click(function() {
    const verse_id = $verse_id_containers.html();

    if (!$task_6_form[0].checkValidity()) {
        $task_6_form[0].reportValidity();
        return;
    }

    var sentence_classification_data = [];

    $task_6_sentence_classification_input_container.find(".sentence-text").each(function (_index, _text_element) {
        const $text_element = $(_text_element);
        const boundary_id = $text_element.data("boundary-id");
        const $selector = $(`#sentence-classification-select-${boundary_id}`);
        const label_id = $selector.selectpicker("val");
        sentence_classification_data.push({
            boundary_id: boundary_id,
            label_id: label_id
        });
    });

    $.post(API_URL, {
        action: TASK_6_SUBMIT_ACTION,
        verse_id: verse_id,
        classification_data: JSON.stringify(sentence_classification_data)
    },
    function (response) {
        $.notify({
            message: response.message
        }, {
            type: response.style
        });

        if (response.success) {
            // ....
            refresh_row_data(verse_id);
            const first_task = response.first_task;
            const next_task = response.next_task;
            $tabs[next_task].click();
            if (next_task == first_task) {
                $corpus_table.bootstrapTable('check', storage.getItem("next_index"));
            }
        }
    });
});

/* *********************************** END Task 6 *********************************** */

/* ********************************** BEGIN Task 7 ********************************** */
// Task 7: Intersentence Connections (e.g. Discourse Graph)

// Setup-7
function setup_intersentence_connection(verse_id) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const row = $corpus_table.bootstrapTable('getRowByUniqueId', verse_id);
    const data = $corpus_table.bootstrapTable('getData');

    // calculate pre-context
    const current_index = data.findIndex(function(r) {
        return r.verse_id == verse_id;
    });

    const start_index = (current_index > 2) ? (current_index - 3) : 0;
    const context = data.slice(start_index, current_index + 1);

    var all_tokens = {};
    var boundary_tokens = [];
    var boundary_marker_tokens = {};

    var existing_intersentence_connections = [];

    for (const verse_data of context) {
        // verse_data
        $.extend(boundary_marker_tokens, verse_data.boundary);
        for (const [boundary_id, sentence_tokens] of Object.entries(verse_data.sentences)) {
            $.extend(all_tokens, sentence_tokens);
            if (boundary_id != "extra") {
                boundary_tokens.push([boundary_id, verse_data.anvaya[boundary_id]]);
            }
            // ensure that every boundary in the previous n verses has anvaya
            // if one is doing anvaya in order, this won't be an issue
        }
        for (const intersentence_connection of verse_data.intersentence_connection) {
            if (intersentence_connection.is_deleted) {
                continue;
            }
            existing_intersentence_connections.push(intersentence_connection);
        }
    };
    console.log(boundary_marker_tokens);
    console.log(existing_intersentence_connections);

    $task_7_intersentence_connection_context_container.html("");
    $task_7_intersentence_connection_reset_button.click();
    $task_7_intersentence_connection_annotation_container.html("");

    for (const [boundary_id, used_tokens] of boundary_tokens) {
        const $boundary_container = $("<div />", {
            id: `intersentence-connection-boundary-container-${boundary_id}`,
            class: "border border-secondary rounded px-1 pt-1 pb-0 ml-1 mt-1 mb-0 boundary-container"
        });
        $boundary_container.appendTo($task_7_intersentence_connection_context_container);
        $boundary_container.data("boundary-id", boundary_id);

        var sentence_text = [];

        const boundary_token_id = boundary_marker_tokens[boundary_id]["token_id"];
        for (const token_id of used_tokens) {
            const token = all_tokens[token_id];
            const $token = generate_token_button({
                token: token,
                token_element: "<button />",
                id_prefix: "intersentence-connection-token",
                token_class_common: "btn intersentence-connection-context-token",
                token_data: {"token-id": token_id, "boundary-id": boundary_id},
                onclick: function($element) {
                    const $annotation_token = $element.clone();
                    $annotation_token.removeAttr("id");
                    $annotation_token.data("token-id", token_id);
                    $annotation_token.data("boundary-id", boundary_id);

                    if (!$task_7_intersentence_connection_source_container.html().trim()) {
                        $annotation_token.addClass("intersentence-connection-source-token");
                        $annotation_token.appendTo($task_7_intersentence_connection_source_container);
                        $element.parent().children("button").prop("disabled", true);
                    } else {
                        if (!$task_7_intersentence_connection_target_container.html().trim()) {
                            $annotation_token.addClass("intersentence-connection-target-token");
                            $annotation_token.appendTo($task_7_intersentence_connection_target_container);
                            $task_7_intersentence_connection_confirm_button.prop("disabled", false);
                            $element.parent().children("button").prop("disabled", true);
                        } else {
                            $.notify({
                                message: "Please confirm or reset the current intersentence_connection first."
                            }, {
                                type: "danger"
                            });
                        }
                        $task_7_intersentence_connection_confirm_button.focus();
                    }
                }
            });
            sentence_text.push($token.html());
            $token.addClass("mr-1 mb-1");
            if (token_id == boundary_token_id) {
                const token_element_id = $token.attr("id");
                const boundary_token_element_id = token_element_id.replace("token", "sentence-token");

                const $boundary_token = $token.clone(true);
                $boundary_token.html(`S-${boundary_id}`);
                $boundary_token.attr("id", boundary_token_element_id);
                $boundary_token.removeClass("btn-light btn-secondary btn-warning");
                $boundary_token.removeClass("intersentence-connection-context-token");
                $boundary_token.addClass("btn-dark");
                $boundary_token.addClass("intersentence-connection-context-sentence-token");
                $boundary_token.prependTo($boundary_container);
            }
            $token.appendTo($boundary_container);
        }
        $boundary_container.children(".intersentence-connection-context-sentence-token").attr("title", sentence_text.join(" "));
    }

    // add existing references
    for (const intersentence_connection of existing_intersentence_connections) {
        const relation_relation_type = intersentence_connection.relation_type;

        // type == 0: token-token connection
        // type == 1: token-sentence connection
        // type == 2: sentence-token connection
        // type == 3: sentence-sentence connection

        var $source_token, $target_token;
        if ((relation_relation_type == 0) || (relation_relation_type == 1)) {
            $source_token = $(`#intersentence-connection-token-${intersentence_connection.src_token_id}`).clone();
        } else {
            $source_token = $(`#intersentence-connection-sentence-token-${intersentence_connection.src_token_id}`).clone();
        }
        $source_token.removeAttr("id");
        $source_token.data("token-id", intersentence_connection.src_token_id);
        $source_token.data("boundary-id", intersentence_connection.src_boundary_id);
        $source_token.addClass("intersentence-connection-source-token");

        if ((relation_relation_type == 0) || (relation_relation_type == 2)) {
            $target_token = $(`#intersentence-connection-token-${intersentence_connection.dst_token_id}`).clone();
        } else {
            $target_token = $(`#intersentence-connection-sentence-token-${intersentence_connection.dst_token_id}`).clone();
        }
        $target_token.removeAttr("id");
        $target_token.data("token-id", intersentence_connection.dst_token_id);
        $target_token.data("boundary-id", intersentence_connection.dst_boundary_id);
        $target_token.addClass("intersentence-connection-target-token");

        const relation_label_id = intersentence_connection.label_id;

        add_intersentence_connection_row($source_token, $target_token, relation_label_id);
    }
}

function add_intersentence_connection_row($source_token, $target_token, relation_label_id) {
    const $row = $('<div />').addClass("row").prependTo($task_7_intersentence_connection_annotation_container);
    $row.addClass('intersentence-connection-annotation-row');

    // add source token
    var $column = $("<div />", {
        class: "col-sm",
    }).appendTo($row);
    $source_token.appendTo($column);

    // add relation
    const $relation_selector = $task_7_intersentence_connection_relation_selector.clone();
    $relation_selector.removeAttr("id");
    $relation_selector.addClass("intersentence-connection-relation");

    var $column = $("<div />", {
        class: "col-sm-4",
    }).appendTo($row);
    $relation_selector.appendTo($column);
    $relation_selector.selectpicker("val", relation_label_id);

    // add target token
    var $column = $("<div />", {
        class: "col-sm",
    }).appendTo($row);
    $target_token.appendTo($column);

    // add remove button
    const $remove_intersentence_connection_button = $('<button />').addClass(`btn btn-danger float-right mx-1`);
    $remove_intersentence_connection_button.attr("title", "Remove Discourse Relation");
    const $remove_icon = $('<i />').addClass(`fas fa-minus`);
    var $column = $('<div />').addClass("col-sm-2").appendTo($row);
    $remove_icon.appendTo($remove_intersentence_connection_button);
    $remove_intersentence_connection_button.appendTo($column);
    $remove_intersentence_connection_button.click(function () {
        $(this).parent().parent().remove();
    });

}

function prepare_intersentence_connection_data($data_location) {
    var data = {
        nodes: [],
        edges: []
    };

    var node_ids = {};
    var node_id = 0;
    function get_node_id() {
        return ++node_id;
    }

    const $intersentence_connection_annotation_rows = $task_7_intersentence_connection_annotation_container.find('.intersentence-connection-annotation-row');
    $intersentence_connection_annotation_rows.each(function(_index, intersentence_connection_row) {
        const $intersentence_connection_row = $(intersentence_connection_row);
        const $source_token = $intersentence_connection_row.find(".intersentence-connection-source-token");
        const $target_token = $intersentence_connection_row.find(".intersentence-connection-target-token");
        const $relation = $intersentence_connection_row.find(".intersentence-connection-relation");

        const source_is_sentence_token = $source_token.hasClass("intersentence-connection-context-sentence-token");
        const target_is_sentence_token = $target_token.hasClass("intersentence-connection-context-sentence-token");

        // type == 0: token-token connection
        // type == 1: token-sentence connection
        // type == 2: sentence-token connection
        // type == 3: sentence-sentence connection

        var relation_type = 0
        if (source_is_sentence_token && target_is_sentence_token) {
            relation_type = 3;
        } else {
            if (source_is_sentence_token) {
                relation_type = 2;
            }
            if (target_is_sentence_token) {
                relation_type = 1;
            }
        }

        if (!$relation.selectpicker("val")) {
            return;
            // "return;" in .each() ==> "continue;"
            // "return false;" in .each() ==> "break;"
        }

        const source_entity = $source_token.html();
        const target_entity = $target_token.html();

        const relation_label_value = $relation.selectpicker("val");
        const relation_label = $relation.find(`[value=${relation_label_value}]`).data("subtext");

        if (!node_ids.hasOwnProperty(source_entity)) {
            node_ids[source_entity] = get_node_id();

            data.nodes.push({
                id: node_ids[source_entity],
                label: source_entity, // label
                title: [
                    `Sentence ID: ${$source_token.data("boundary-id")}`,
                    `Token ID: ${$source_token.data("token-id")}`,
                ].join("\n"), // title (visible on hover)
                value: 3,
                group: null // group-id (upos/xpos based?)
            });
        }
        if (!node_ids.hasOwnProperty(target_entity)) {
            node_ids[target_entity] = get_node_id();

            data.nodes.push({
                id: node_ids[target_entity],
                label: target_entity, // label
                title: [
                    `Sentence ID: ${$target_token.data("boundary-id")}`,
                    `Token ID: ${$target_token.data("token-id")}`,
                ].join("\n"), // title (visible on hover)
                value: 3,
                group: null // group-id (upos/xpos based?)
            });
        }

        data.edges.push({
            from: node_ids[source_entity], // start-id
            to: node_ids[target_entity],  // end-id
            label: relation_label, // label
            title: `Label ID: ${relation_label_value}`, // title (visible on hover)
            arrows: {
                to: {
                    enabled: true
                }
            },
            value: 3,
        });
    });

    console.log("Graph Data: ");
    console.log(data);
    return data;
}

$task_7_intersentence_connection_confirm_button.click(function () {
    const $source_token = $task_7_intersentence_connection_source_container.children(".intersentence-connection-source-token");
    const $target_token = $task_7_intersentence_connection_target_container.children(".intersentence-connection-target-token");

    const relation_label_id = $task_7_intersentence_connection_relation_selector.selectpicker("val");
    $task_7_intersentence_connection_relation_selector.selectpicker("val", null);

    add_intersentence_connection_row($source_token, $target_token, relation_label_id);

    // reset
    $task_7_intersentence_connection_reset_button.click();
    $task_7_intersentence_connection_confirm_button.prop("disabled", true);
});

$task_7_intersentence_connection_reset_button.click(function () {
    // enable all buttons
    $task_7_intersentence_connection_context_container.find("button").prop("disabled", false);

    $task_7_intersentence_connection_source_container.html("");
    $task_7_intersentence_connection_target_container.html("");
});

/* Task-7 Actions */

// Submit-7
$task_7_submit.click(function () {
    const verse_id = $verse_id_containers.html();

    if (!$task_7_form[0].checkValidity()) {
        $task_7_form[0].reportValidity();
        return;
    }

    var context_data = [];
    var intersentence_connection_data = [];
    $task_7_intersentence_connection_context_container.find(".boundary-container").each(function (_index, _boundary_container) {
        context_data.push($(_boundary_container).data("boundary-id"));
    });

    const $intersentence_connection_annotation_rows = $task_7_intersentence_connection_annotation_container.find('.intersentence-connection-annotation-row');
    $intersentence_connection_annotation_rows.each(function(_index, intersentence_connection_row) {
        const $intersentence_connection_row = $(intersentence_connection_row);
        const $source_token = $intersentence_connection_row.find(".intersentence-connection-source-token");
        const $target_token = $intersentence_connection_row.find(".intersentence-connection-target-token");
        const $relation = $intersentence_connection_row.find(".intersentence-connection-relation");

        const source_is_sentence_token = $source_token.hasClass("intersentence-connection-context-sentence-token");
        const target_is_sentence_token = $target_token.hasClass("intersentence-connection-context-sentence-token");

        // type == 0: token-token connection
        // type == 1: token-sentence connection
        // type == 2: sentence-token connection
        // type == 3: sentence-sentence connection

        var relation_type = 0
        if (source_is_sentence_token && target_is_sentence_token) {
            relation_type = 3;
        } else {
            if (source_is_sentence_token) {
                relation_type = 2;
            }
            if (target_is_sentence_token) {
                relation_type = 1;
            }
        }

        intersentence_connection_data.push({
            "src_boundary_id": $source_token.data("boundary-id"),
            "src_token_id": $source_token.data("token-id"),
            "label_id": $relation.selectpicker("val"),
            "dst_boundary_id": $target_token.data("boundary-id"),
            "dst_token_id": $target_token.data("token-id"),
            "relation_type": relation_type
        });
    });
    $.post(API_URL, {
        action: TASK_7_SUBMIT_ACTION,
        verse_id: verse_id,
        context_data: JSON.stringify(context_data),
        intersentence_connection_data: JSON.stringify(intersentence_connection_data)
    },
    function (response) {
        $.notify({
            message: response.message
        }, {
            type: response.style
        });

        if (response.success) {
            refresh_row_data(verse_id);
            const first_task = response.first_task;
            const next_task = response.next_task;
            $tabs[next_task].click();
            if (next_task == first_task) {
                $corpus_table.bootstrapTable('check', storage.getItem("next_index"));
            }
        }
    },
    'json');
});

/* *********************************** END Task 7 *********************************** */
