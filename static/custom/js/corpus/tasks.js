/* ********************************** */
// Task Related Constants, Functions, Events etc.
/* ********************************** */
// NOTE: Constants/Variables in capital are declared in the HTML template.

// Constants

const default_token_class_common = "btn";
const default_token_class_normal = "btn-light";
const default_token_class_subtoken = "btn-warning token-subtoken";
const default_token_class_manual = "btn-secondary token-manual";
const default_token_class_multitoken = "btn-info token-multitoken";

const default_token_element = "<span />";
const default_token_data = {};

// Boundary State
const BOUNDARY_STATE_TOKEN_DECISION = "boundary_status_token_decision";
const BOUNDARY_STATE_HEURISTIC = "boundary_status_heuristic";
const BOUNDARY_STATE_SORT = "boundary_status_sort";

// Text Boundary Status
const TEXT_BOUNDARY_STATE_TOKEN_DECISION = "Confirm Tokens?";
const TEXT_BOUNDARY_STATE_HEURISTIC = "Heuristic";
const TEXT_BOUNDARY_STATE_SORT = "Pending";

// Class Boundary Status
const CLASS_BOUNDARY_STATE_TOKEN_DECISION = "primary";
const CLASS_BOUNDARY_STATE_HEURISTIC = "info";
const CLASS_BOUNDARY_STATE_SORT = "warning";

const sentence_token_graph_input_container_class = "sentence-token-graph-input-container";

/* *************************** Generic Functions *************************** */

function add_badge(badge_id, badge_text, badge_style, $parent, hidden=false) {
    const $badge = $("<span />", {
        id: badge_id,
        class: `badge badge-${badge_style} float-right mb-1 ml-1`,
        html: badge_text
    });
    $badge.appendTo($parent);
    if (hidden) {
        $badge.hide();
    }
    return $badge;
};

function update_badge(badge_id, badge_text, badge_style="info") {
    const $badge = $(`#${badge_id}`);
    const badge_class = `badge-${badge_style}`;
    if (!$badge.hasClass(badge_class)) {
        $badge.removeClass(function(index, class_name) {
            return (class_name.match(/\bbadge-\S+/g) || []).join(" ");
        });
        $badge.addClass(badge_class);
    }
    $badge.text(badge_text);
    $badge.show();
}

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
    if (token.analysis.misc.Unsandhied && token.analysis.misc.Unsandhied != "_" && false) {
        token_text = token.analysis.misc.Unsandhied;
    }

    if (!token.text || (token.text == "_")) {
        // subtoken (result of sandhi or samaasa split)
        token_class = token_class_subtoken;
        token_text = token.analysis.misc.Unsandhied;
        // setting token_text again is actually redundant
        // since we already use token.analysis.misc.Unsandhied whenever available
        // although, we may need it if the logic of always using
        // token.analysis.misc.Unsandhied changes (due to errors)
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

    // merged tokens take higher priority than manual
    // i.e. merged token will appear with token_class_multitoken
    // instead of with token_class_manual, despite having token_annotator_id != null
    if (token.inner_id.includes("group_")) {
        token_class = token_class_multitoken;
    }

    // split tokens appear with token_class_subtoken and similar to a merged token
    // take higher priority than manual
    if (token.inner_id.includes("split_")) {
        token_class = token_class_subtoken;
    }

    var token_hover_text = [
        `ID: ${token.id}`,
        `Text: ${token.text}`,
        `Lemma: ${token.lemma}`,
    ]
    if (token.analysis.misc.Unsandhied && token.analysis.misc.Unsandhied != "_") {
        token_hover_text.push(`Padapāṭha: ${token.analysis.misc.Unsandhied}`); // corpus-specific
    }

    const $token = $(token_element, {
        class: [token_class_common, token_class].join(" "),
        title: token_hover_text.join("\n"),
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

function refresh_row_data(unique_id, _callback, _callback_options) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);
    const verse_data_url = SAMPLE_VERSE_DATA_URL.replace('0', unique_id);
    $.get(verse_data_url, function (data) {
        $corpus_table.bootstrapTable('updateByUniqueId', {
            id: unique_id,
            row: data[unique_id],
            replace: true
        });
        $corpus_table.bootstrapTable('collapseRowByUniqueId', unique_id);
        $corpus_table.bootstrapTable('check', storage.getItem(KEY_CURRENT_INDEX));

        if (_callback) {
            _callback(_callback_options);
        }
    }, 'json');
    console.log(`Verse data updated for ID: ${unique_id}`);
}

function draw_graph_displacy(data) {
    const displacy = new displaCy('', {
        container: graph_displacy_container_selector,
    });
    displacy.render(data, {color: '#000042'});
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

/* **************************** Generic Events **************************** */

$refresh_verse_buttons.click(function() {
    const verse_id = $verse_id_containers.html();
    refresh_row_data(verse_id);
});

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

$snapshot_graph_displacy_button.click(function() {
    const svg_element = $graph_displacy.find("svg.displacy")[0];
    const serializer = new XMLSerializer();
    var source = serializer.serializeToString(svg_element);

    // add name spaces.
    if(!source.match(/^<svg[^>]+xmlns="http\:\/\/www\.w3\.org\/2000\/svg"/)){
        source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
    }
    if(!source.match(/^<svg[^>]+"http\:\/\/www\.w3\.org\/1999\/xlink"/)){
        source = source.replace(/^<svg/, '<svg xmlns:xlink="http://www.w3.org/1999/xlink"');
    }

    // add xml declaration
    source = '<?xml version="1.0" standalone="no"?>\r\n' + source;

    // convert svg source to URI data scheme.
    const url = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(source);

    const download_anchor = document.createElement('a');
    download_anchor.href = url;
    download_anchor.download = 'graph.svg';
    document.body.appendChild(download_anchor);
    download_anchor.click();
    document.body.removeChild(download_anchor);
});


/* ************************** Generic Task Setup ************************** */

function setup_task(task_category, task_id, verse_id) {
    switch (task_category) {
        case TASK_SENTENCE_BOUNDARY:
            setup_task_sentence_boundary(task_id, verse_id);
            break;
        case TASK_WORD_ORDER:
            setup_task_word_order(task_id, verse_id);
            break;
        case TASK_TOKEN_TEXT_ANNOTATION:
            setup_task_token_text_annotation(task_id, verse_id);
            break;
        case TASK_TOKEN_CLASSIFICATION:
            setup_task_token_classification(task_id, verse_id);
            break;
        case TASK_TOKEN_GRAPH:
            setup_task_token_graph(task_id, verse_id);
            break;
        case TASK_TOKEN_CONNECTION:
            setup_task_token_connection(task_id, verse_id);
            break;
        case TASK_SENTENCE_CLASSIFICATION:
            setup_task_sentence_classification(task_id, verse_id);
            break;
        case TASK_SENTENCE_GRAPH:
            setup_task_sentence_graph(task_id, verse_id);
            break;

        default:
            break;
    }
}

/* ************************** Generic Task Submit ************************** */

function submit_task(task_category, task_id) {
    switch (task_category) {
        case TASK_SENTENCE_BOUNDARY:
            submit_task_sentence_boundary(task_id);
            break;
        case TASK_WORD_ORDER:
            submit_task_word_order(task_id);
            break;
        case TASK_TOKEN_TEXT_ANNOTATION:
            submit_task_token_text_annotation(task_id);
            break;
        case TASK_TOKEN_CLASSIFICATION:
            submit_task_token_classification(task_id);
            break;
        case TASK_TOKEN_GRAPH:
            submit_task_token_graph(task_id);
            break;
        case TASK_TOKEN_CONNECTION:
            submit_task_token_connection(task_id);
            break;
        case TASK_SENTENCE_CLASSIFICATION:
            submit_task_sentence_classification(task_id);
            break;
        case TASK_SENTENCE_GRAPH:
            submit_task_sentence_graph(task_id);
            break;

        default:
            break;
    }
}

/* ********************* BEGIN Task: Sentence Boundary ********************* */
// Task: Sentence Boundary

// Setup: Sentence Boundary
function setup_task_sentence_boundary(task_id, verse_id) {
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
        // console.log(verse[TASK_SENTENCE_BOUNDARY]);

        var verse_text = [`${verse_data.verse_id}`];
        var boundary_tokens = new Set();

        for (const [boundary_id, boundary] of Object.entries(verse_data[TASK_SENTENCE_BOUNDARY])) {
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

                    if (token.inner_id.includes("-")) {
                        var id_parts = token.inner_id.split("-");
                        // if token id is of composite word,
                        // we want the marker to be after the last component
                        token_id += id_parts[1] - id_parts[0] + 1;
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

// Submit: Sentence Boundary
function submit_task_sentence_boundary(task_id) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const task_category = TASK_SENTENCE_BOUNDARY;
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
        action: TASK_UPDATE_ACTIONS[task_category],
        task_id: task_id,
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
                $corpus_table.bootstrapTable('check', storage.getItem(KEY_NEXT_INDEX));
            }
        }
    },
    'json');
};

/* ********************** END Task: Sentence Boundary ********************** */

/* ************************ BEGIN Task: Token Order ************************ */
// Task: Token Order

// Setup: Token Order
function setup_sortable() {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    $('.connected-sortable').sortable({
        items: "> div",
        opacity: 0.75,
        revert: true,
        cursor: "move",
        tolerance: "pointer",
        placeholder: 'btn btn-secondary py-3 px-5 mb-1 mr-1',
        connectWith: ".sortable"
    }).on("sortremove", function(e, ui) {
        const toggle_id = ui.item[0].id.replace("button", "toggle");
        $(`#${toggle_id}`).prop("disabled", false);
        $(`#${toggle_id}`).parent().find('[name="token-split"]').prop("disabled", false);
        $(`#${toggle_id}`).parent().find('[name="token-merge"]').prop("disabled", false);
    });
    $('.sortable').sortable({
        items: "> div",
        opacity: 0.75,
        revert: true,
        cursor: "move",
        tolerance: "pointer",
        placeholder: 'btn btn-secondary py-3 px-5 mb-1 mr-1',
    }).on("sortupdate", function(e, ui) {
        // ui.item contains the current dragged element.
        // Triggered when the user stopped sorting and the DOM position has changed.
        const boundary_element_id = this.id;
        // store token order to localStorage for restoring (stored as ',' joined list of token-ids)
        const word_order_order = $(this).sortable("toArray").join(",");
        storage.setItem(`${PREFIX_KEY_BOUNDARY_WORD_ORDER}_${boundary_element_id}`, word_order_order);
        const boundary_state_key = `${PREFIX_KEY_BOUNDARY_STATE}_${boundary_element_id}`;
        const boundary_state = storage.getItem(boundary_state_key);
        if ((boundary_state != BOUNDARY_STATE_TOKEN_DECISION) && (boundary_state != BOUNDARY_STATE_SORT)) {
            storage.setItem(boundary_state_key, BOUNDARY_STATE_SORT);
            update_badge(`boundary-status-${boundary_element_id}`, TEXT_BOUNDARY_STATE_SORT, CLASS_BOUNDARY_STATE_SORT);
        }
        console.log(`Saved Order (${boundary_element_id}): ${word_order_order}`);
    });
}

// apply specific token order to a sentence
function apply_word_order(boundary_element_id, proposed_word_order) {
    // proposed_word_order is list of token ids (either <integer> or token-button-<integer>)
    // only those token_id from proposed_word_order that are already in $sentence_container will be used

    const $extra_container = $task_2_word_order_container.find("div.extra-token-container");
    const $sentence_container = $(`#${boundary_element_id}`);
    const $unused_container = $(`#${boundary_element_id.replace("boundary", "unused")}`);
    var sentence_tokens = [];

    // temporarily disable sortable
    $sentence_container.sortable("cancel");
    // first move all sentence tokens to unused
    // populate sentence_tokens array
    $sentence_container.children("div").each(function(token_button_idx, token_button) {
        sentence_tokens.push(token_button.id);
        const $token_button = $(token_button);
        if ($token_button.hasClass("token-manual")) {
            $token_button.appendTo($extra_container);
        } else {
            $token_button.appendTo($unused_container);
        }
    });
    // add extra tokens to possible sentence_tokens as well
    $extra_container.children("div").each(function(token_button_idx, token_button) {
        sentence_tokens.push(token_button.id);
    });

    // move tokens from proposed order to sentence container if they are valid sentence tokens
    proposed_word_order.forEach(token_id => {
        const token_button_id = (Number.isInteger(Number(token_id))) ? `token-button-${token_id}` : token_id;
        const $token_button = $(`#${token_button_id}`);
        const $token_toggle = $token_button.find('[name="token-toggle"]');
        if (sentence_tokens.includes(token_button_id)) {
            $token_button.appendTo($sentence_container);
            // NOTE: Heuristics don't contain extra tokens
            // So when the heuristic is applied, it will remove extra token from sentence
            if ($token_toggle.prop("disabled")) {
                $token_toggle.prop("disabled", false);
            }
        }
    });
    // fix toggles
    // BUG: this is triggering state change it seems
    $extra_container.children("div").each(function(token_button_idx, token_button) {
        const $token_button = $(`#${token_button.id}`);
        // hide Split and Merge buttons when moving to extra container
        $token_button.find('[name="token-split"]').prop("disabled", true);
        $token_button.find('[name="token-merge"]').prop("disabled", true);
        // style toggle correctly
        const $token_toggle = $token_button.find('[name="token-toggle"]');
        $token_toggle.attr("title", "");
    });
    $unused_container.children("div").each(function(token_button_idx, token_button) {
        const $token_button = $(`#${token_button.id}`);
        // hide Split and Merge buttons when moving to extra container
        $token_button.find('[name="token-split"]').prop("disabled", true);
        $token_button.find('[name="token-merge"]').prop("disabled", true);
        // style toggle correctly
        const $token_toggle = $token_button.find('[name="token-toggle"]');
        $token_toggle.attr("title", "Include");
        if ($token_toggle.hasClass("exclude-token")) {
            // CAUTION: performing $token_toggle.click() would trigger "sortupdate", so avoid that.
            $token_toggle.removeClass("exclude-token");
            $token_toggle.removeClass("btn-secondary");
            $token_toggle.addClass("btn-info");
            $token_toggle.html('<i class="fa fa-plus"></i>');
        }
    })
    // refresh sortable
    $sentence_container.sortable("refresh");
}

// restore saved token order
function restore_word_order(boundary_element_id) {
    const saved_order = storage.getItem(`${PREFIX_KEY_BOUNDARY_WORD_ORDER}_${boundary_element_id}`);
    if (saved_order) {
        apply_word_order(boundary_element_id, saved_order.split(","));
        console.log(`Restored Saved Token Order to ${boundary_element_id}`);
    }
}

function setup_task_word_order(task_id, verse_id) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    // // TODO: Do we want to disable task-submit button without token confirmation?
    // // Current approach is flawed since we are enabling button even if state changes for
    // // any boundary. Issue when multiple boundaries.
    // const $task_submit_button = $(`#task-${task_id}_submit`);
    // $task_submit_button.prop("disabled", true);

    const row = $corpus_table.bootstrapTable('getRowByUniqueId', verse_id);

    $task_2_word_order_container.html("");
    const $extra = $("<div />", {
        id: `extra-${verse_id}`,
        class: "border px-1 pt-1 m-1 rounded connected-sortable extra-token-container clearfix",
        style: "background-color: #eeeeff; border-color: #aaaaff !important;"
    });
    add_badge("about-boundary-extra", "Custom", "info", $extra);
    $task_2_word_order_container.append($extra);
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
        for (const token_id of row[TASK_WORD_ORDER][boundary_id]) {
            if (extra_tokens.hasOwnProperty(token_id)) {
                used_extra_tokens.push(token_id);
            }
        }
    }
    for (const [boundary_id, sentence_tokens] of Object.entries(row.sentences)) {
        var token_order = [];
        var heuristic_order = [];
        var unused_tokens = [];
        if (boundary_id !== "extra") {
            token_order = row[TASK_WORD_ORDER][boundary_id];
            heuristic_order = row["heuristics"][TASK_WORD_ORDER][boundary_id];
            for (const [_token_id_string, _token] of Object.entries(sentence_tokens)) {
                if (!token_order.includes(_token.id)) {
                    unused_tokens.push(_token.id);
                }
            }
            // ensure in server_sqla.py that row[TASK_WORD_ORDER] isn't empty
            // either it is annotated word_order, or it's obtained via heuristic
        } else {
            // order doesn't really matter, just need extra tokens
            token_order = Object.keys(sentence_tokens);
        }
        console.log(`Token Order (${boundary_id}): ${token_order}`);

        const $sentence = $("<div />", {
            id: `boundary-${boundary_id}`,
            class: "sortable border px-1 pt-1 m-1 rounded sentence-token-container clearfix",
            style: "background-color: #eeffee; border-color: #aaffaa !important;"
        });

        const $unused = $("<div />", {
            id: `unused-${boundary_id}`,
            class: "border px-1 pt-1 m-1 rounded unused-token-container clearfix",
            style: "background-color: #ffeeee; border-color: #ffaaaa !important;"
        });
        if (boundary_id != "extra") {
            const boundary_element_id = `boundary-${boundary_id}`;
            const boundary_storage_key = `${PREFIX_KEY_BOUNDARY_STATE}_${boundary_element_id}`;
            $task_2_word_order_container.append($sentence);
            $task_2_word_order_container.append($unused);
            add_badge(`about-boundary-${boundary_id}`, "Sentence", "success", $sentence);
            add_badge(`about-boundary-${boundary_id}`, "Unused", "danger", $unused);

            // add status badge once as hidden, only update later
            const status_badge_id = `boundary-status-${boundary_element_id}`;
            add_badge(status_badge_id, "...", "dark", $sentence, true);

            if (heuristic_order && heuristic_order.length > 0) {
                // presence of heuristic order ==> no annotation for current boundary (logic in `utils/database.py`)
                storage.setItem(`${PREFIX_KEY_BOUNDARY_HEURISTIC_WORD_ORDER}_${boundary_element_id}`, heuristic_order.join(","));
                if (!storage.getItem(boundary_storage_key)) {
                    storage.setItem(boundary_storage_key, BOUNDARY_STATE_TOKEN_DECISION);
                }
            } else {
                // $task_submit_button.prop("disabled", false);
            }
            const boundary_state = storage.getItem(boundary_storage_key);

            switch (boundary_state) {
                case BOUNDARY_STATE_TOKEN_DECISION:
                    update_badge(status_badge_id, TEXT_BOUNDARY_STATE_TOKEN_DECISION, CLASS_BOUNDARY_STATE_TOKEN_DECISION);
                    break;
                case BOUNDARY_STATE_HEURISTIC:
                    update_badge(status_badge_id, TEXT_BOUNDARY_STATE_HEURISTIC, CLASS_BOUNDARY_STATE_HEURISTIC);
                    break;
                case BOUNDARY_STATE_SORT:
                    update_badge(status_badge_id, TEXT_BOUNDARY_STATE_SORT, CLASS_BOUNDARY_STATE_SORT);
                    break;

                default:
                    break;
            }
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
                id_prefix: "token",
                token_data: token
            });
            $token_button.append($token);

            /* BEGIN: Split and Merge buttons */
            const $token_split = $("<button />", {
                id: `token-split-${token.id}`,
                name: "token-split",
                class: "btn btn-secondary bright-2 split-token",
                html: '<i class="fas fa-up-right-and-down-left-from-center"></i>',
                title: "Split",
                on: {
                    click: function() {
                        $split_token_modal_header_span.empty();
                        $split_token_form.data("row-id", 0);
                        $split_token_form.empty();
                        $split_token_row_add_button.click();
                        $split_token_row_add_button.click();
                        const $clicked_token_clone = $(this).parent().find("span").clone(true);
                        $clicked_token_clone.removeAttr("id");
                        $clicked_token_clone.attr("style", "pointer-events: none; -webkit-user-select: text; -moz-user-select: text; -ms-user-select: text; user-select: text;");
                        $clicked_token_clone.addClass("btn-lg");
                        $clicked_token_clone.appendTo($split_token_modal_header_span);
                    }
                }
            });
            $token_split.attr("data-toggle", "modal");
            $token_split.attr("data-target", "#split-token-modal");
            $token_button.append($token_split);

            const $token_merge = $("<button />", {
                id: `token-merge-next-${token.id}`,
                name: "token-merge",
                class: "btn btn-secondary bright-1 merge-token",
                html: '<i class="fa fa-right-to-bracket"></i>',
                title: "Merge with Next",
                on: {
                    click: function() {
                        const $clicked_token_clone = $(this).parent().find("span").clone(true);
                        const clicked_token_text = $clicked_token_clone.data("text");

                        const $merge_with_token_clone = $(this).parent().next().find("span").clone(true);
                        const merge_with_token_text = $merge_with_token_clone.data("text");

                        const merged_token_text = [
                            clicked_token_text,
                            merge_with_token_text
                        ].join("_");
                        const $merged_token_prototype = generate_token_button({
                            token: {
                                text: merged_token_text,
                                analysis: {misc: {}},
                                inner_id: "group_"
                            }
                        });
                        console.log($merged_token_prototype);

                        $merge_token_clicked_token_container.empty();
                        $merge_token_merge_with_token_container.empty();
                        $merge_token_merged_token_container.empty();

                        $clicked_token_clone.appendTo($merge_token_clicked_token_container);
                        $merge_with_token_clone.appendTo($merge_token_merge_with_token_container);
                        $merged_token_prototype.appendTo($merge_token_merged_token_container);

                        $merge_token_modal.modal('show');
                    }
                }
            });
            $token_button.append($token_merge);
            /* END: Split and Merge buttons */

            if (token.annotator_id == null) {
                if (is_token_used) {
                    var token_class = "btn btn-secondary exclude-token";
                    var token_html = '<i class="fa fa-times"></i>';
                    var token_title = "Exclude";
                } else {
                    var token_class = "btn btn-info";
                    var token_html = '<i class="fa fa-plus"></i>';
                    var token_title = "Include";
                }
                const $token_toggle = $("<button />", {
                    id: `token-toggle-${token.id}`,
                    name: "token-toggle",
                    class: token_class,
                    title: token_title,
                    html: token_html,
                    on: {
                        click: function() {
                            if ($(this).hasClass("exclude-token")) {
                                $(this).removeClass("exclude-token");
                                $(this).removeClass("btn-secondary");
                                $(this).addClass("btn-info");
                                $(this).prop("title", "Include");
                                $(this).html('<i class="fa fa-plus"></i>');
                                $(this).parent().find('[name="token-split"]').prop("disabled", true);
                                $(this).parent().find('[name="token-merge"]').prop("disabled", true);
                                $(this).parent().appendTo($(`#unused-${boundary_id}`));
                            } else {
                                $(this).removeClass("btn-info");
                                $(this).addClass("btn-secondary");
                                $(this).addClass("exclude-token");
                                $(this).prop("title", "Exclude");
                                $(this).html('<i class="fa fa-times"></i>');
                                $(this).parent().find('[name="token-split"]').prop("disabled", false);
                                $(this).parent().find('[name="token-merge"]').prop("disabled", false);
                                $(this).parent().appendTo($(`#boundary-${boundary_id}`));
                            }
                            $(`#boundary-${boundary_id}`).trigger("sortupdate");
                        }
                    }
                });
                $token_button.append($token_toggle);
            } else {
                const $token_toggle = $("<button />", {
                    id: `token-toggle-${token.id}`,
                    name: "token-toggle",
                    class: "btn btn-secondary exclude-extra-token",
                    title: "Exclude",
                    html: '<i class="fa fa-times"></i>',
                    disabled: is_extra_unused,
                    on: {
                        click: function() {
                            $(this).prop("disabled", true);
                            $(this).parent().find('[name="token-split"]').prop("disabled", true);
                            $(this).parent().find('[name="token-merge"]').prop("disabled", true);
                            $(this).parent().appendTo($(`#extra-${verse_id}`));
                            const $boundary_element = $(this).parent().parent();
                            $boundary_element.trigger("sortupdate");
                        }
                    }
                });
                $token_button.append($token_toggle);
            }
        };
    }
    setup_sortable();
    for (const boundary_id of Object.keys(row.sentences)) {
        const boundary_element_id = `boundary-${boundary_id}`;
        const $boundary_element = $(`#${boundary_element_id}`);
        const boundary_storage_key = `${PREFIX_KEY_BOUNDARY_STATE}_${boundary_element_id}`;
        const status_badge_id = `boundary-status-${boundary_element_id}`;
        const $status_badge = $(`#${status_badge_id}`);
        restore_word_order(boundary_element_id);
        var boundary_state = storage.getItem(boundary_storage_key);
        switch (boundary_state) {
            case BOUNDARY_STATE_TOKEN_DECISION:
                $status_badge.data("boundary-id", boundary_id);
                $status_badge.click(function () {
                    const _boundary_id = $(this).data("boundary-id");
                    const _boundary_element_id = `boundary-${_boundary_id}`;
                    const _boundary_state = storage.getItem(`${PREFIX_KEY_BOUNDARY_STATE}_${boundary_element_id}`);
                    // second step: apply heuristic
                    if (_boundary_state == BOUNDARY_STATE_TOKEN_DECISION) {
                        const _heuristic_order = storage.getItem(`${PREFIX_KEY_BOUNDARY_HEURISTIC_WORD_ORDER}_${boundary_element_id}`);
                        console.log("Heuristic Token Order: " + _heuristic_order);
                        apply_word_order(_boundary_element_id, _heuristic_order.split(","));
                        update_badge(`boundary-status-${_boundary_element_id}`, "Heuristic", "info");
                        storage.setItem(`${PREFIX_KEY_BOUNDARY_STATE}_${boundary_element_id}`, BOUNDARY_STATE_HEURISTIC);
                    } else {
                        // will this ever be the case?!
                        console.log("Why is this happening?");
                    }
                    // $task_submit_button.prop("disabled", false);
                    $(this).off('click');
                });
                break;
            case BOUNDARY_STATE_HEURISTIC:
                // $task_submit_button.prop("disabled", false);
                const _heuristic_order = storage.getItem(`${PREFIX_KEY_BOUNDARY_HEURISTIC_WORD_ORDER}_${boundary_element_id}`);
                console.log("Heuristic Token Order: " + _heuristic_order);
                apply_word_order(boundary_element_id, _heuristic_order.split(","));
                break;
            case BOUNDARY_STATE_SORT:
                // $task_submit_button.prop("disabled", false);
                break;

            default:
                break;
        }
    }
}

/* Task: Token Order: Actions */

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
        misc: {}
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
            $add_token_form[0].reset();
        }
    });
});

// Merge Token
$merge_token_button.click(function() {
    const verse_id = $verse_id_containers.html();

    const $clicked_token = $merge_token_clicked_token_container.find("span");
    const clicked_token_id = $clicked_token.data("id");
    const clicked_token_text = $clicked_token.data("text");
    const clicked_token_analysis = $clicked_token.data("analysis");

    const $merge_with_token = $merge_token_merge_with_token_container.find("span").clone(true);
    const merge_with_token_id = $merge_with_token.data("id");
    const merge_with_token_text = $merge_with_token.data("text");
    const merge_with_token_analysis = $merge_with_token.data("analysis");

    const merged_token_text = [
        clicked_token_text,
        merge_with_token_text
    ].join("_");

    const merged_token_parts = [];
    if (clicked_token_analysis.misc && clicked_token_analysis.misc.parts) {
        merged_token_parts.push(...clicked_token_analysis.misc.parts);
    } else {
        merged_token_parts.push(clicked_token_id);
    }
    if (merge_with_token_analysis.misc && merge_with_token_analysis.misc.parts) {
        merged_token_parts.push(...merge_with_token_analysis.misc.parts);
    } else {
        merged_token_parts.push(merge_with_token_id);
    }

    $merge_token_modal.modal('hide');
    $.post(API_URL, {
        action: "add_token",
        verse_id: verse_id,
        token_data: JSON.stringify({
            text: merged_token_text,
            inner_id: `group_${merged_token_parts.join("_")}`,
            lemma: "_",
            analysis: {
                form: merged_token_text,
                lemma: "_",
                feats: {},
                misc: {
                    parts: merged_token_parts
                },
            }
        })
    },
    function (response) {
        $.notify({
            message: response.message
        }, {
            type: response.style
        });

        if (response.success) {
            const added_token_id = response.data.id;
            refresh_row_data(verse_id, function merge_token_handler(options) {
                console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

                const added_token_id = options.added_token_id;
                const clicked_token_id = options.clicked_token_id;
                const merge_with_token_id = options.merge_with_token_id;

                const $added_token_button = $(`#token-button-${added_token_id}`);
                const $clicked_token_button = $(`#token-button-${clicked_token_id}`);
                const $merge_with_token_button = $(`#token-button-${merge_with_token_id}`);

                $added_token_button.insertAfter($clicked_token_button);
                $added_token_button.find('[name="token-split"]').prop("disabled", false);
                $added_token_button.find('[name="token-merge"]').prop("disabled", false);
                $added_token_button.find('[name="token-toggle"]').prop("disabled", false);

                const $clicked_token_boundary = $clicked_token_button.parent();

                $clicked_token_button.find('[name="token-toggle"]').click();
                $merge_with_token_button.find('[name="token-toggle"]').click();

                $clicked_token_boundary.trigger("sortupdate");
            }, {
                added_token_id: added_token_id,
                clicked_token_id: clicked_token_id,
                merge_with_token_id: merge_with_token_id
            });
        }
    });

});

// Split Token Add Row
$split_token_row_add_button.click(function() {
    const row_id = $split_token_form.data("row-id") + 1;

    // clone sample row
    const $split_token_token_row = $split_token_sample_token_row.clone();

    // set ids and other necessary attributes
    $split_token_token_row.attr("id", `split-token-row-${row_id}`);
    $split_token_token_row.find(".split-token-basic-row").attr("id", `split-token-basic-row-${row_id}`);
    $split_token_token_row.find(".split-token-analysis-row").attr("id", `split-token-analysis-row-${row_id}`);
    $split_token_token_row.find(".split-token-analysis-row-toggle").attr("data-target", `#split-token-analysis-row-${row_id}`);
    $split_token_token_row.find(".split-token-analysis-row-toggle").attr("aria-controls", `split-token-analysis-row-${row_id}`);

    $split_token_token_row.removeClass("d-none");
    $split_token_token_row.appendTo($split_token_form);
    $split_token_token_row.find(".split-token-analysis-row-toggle").collapse();

    $split_token_form.data("row-id", row_id);
});


// NOTE: Currently there are several portions that are repeated in Add-Token and Split-Token
// This is primarily because Split-Token is a special form of adding tokens, which involves
// removing the token to be split and adding multiple tokens in its place.
// It is worth exploring if code can be made a bit more DRY.

// Split Token
$split_token_button.click(function() {
    if (!$split_token_form[0].checkValidity()) {
        $split_token_form[0].reportValidity();
        return;
    }
    const verse_id = $verse_id_containers.html();
    const token_id = $split_token_modal_header_span.find("span").data("id");
    const token_split_data = [];

    $(".split-token-token-row").each(function(token_index, token_element) {
        if ($(this).hasClass("d-none")) {
            return;
            // "return;" in .each() ==> "continue;"
            // "return false;" in .each() ==> "break;"
        }
        const token_text = $(token_element).find("input.split-token-input-text").val();
        const token_lemma =  $(token_element).find("input.split-token-input-lemma").val();
        const token_analysis_upos = $(token_element).find("input.split-token-analysis-input-upos").val();
        const token_analysis_xpos = $(token_element).find("input.split-token-analysis-input-xpos").val();
        const token_features = {};

        $split_token_feature_items.each(function(_index, _element){
            const $element = $(_element);
            const label = $element.find(split_token_feature_label_selector).html().trim();
            const value = $element.find(split_token_feature_input_selector).val();
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
            misc: {}
        }
        const split_token_token = {
            text: token_text,
            lemma: token_lemma,
            analysis: token_analysis,
        };
        token_split_data.push(split_token_token);
    });
    $split_token_modal.modal('hide');
    $.post(API_URL, {
        action: "split_token",
        verse_id: verse_id,
        token_id: token_id,
        token_split_data: JSON.stringify(token_split_data),
    },
    function (response) {
        $.notify({
            message: response.message
        }, {
            type: response.style
        });

        if (response.success) {
            const split_ids = response.data.splits;
            console.log(split_ids);
            refresh_row_data(verse_id, function split_token_handler(options) {
                console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

                const $clicked_token_button = $(`#token-button-${token_id}`);
                for (const split_id of [...options.split_ids].reverse()) {
                    // insert in reversed order since we use "insertAfter"
                    const $added_token_button = $(`#token-button-${split_id}`);
                    $added_token_button.insertAfter($clicked_token_button);
                    $added_token_button.find('[name="token-split"]').prop("disabled", false);
                    $added_token_button.find('[name="token-merge"]').prop("disabled", false);
                    $added_token_button.find('[name="token-toggle"]').prop("disabled", false);
                }
                const $clicked_token_boundary = $clicked_token_button.parent();

                $clicked_token_button.find('[name="token-toggle"]').click();

                $clicked_token_boundary.trigger("sortupdate");
            }, {
                split_ids: split_ids,
            });
            // NOTE: The following may be redundant, as we also do this when launching a fresh modal.
            $split_token_form.data("row-id", 0);
            $split_token_form.empty();
        }
    });
});

// Submit: Token Order
function submit_task_word_order(task_id) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const verse_id = $verse_id_containers.html();
    const task_category = TASK_WORD_ORDER;

    var word_order_data = {}
    $('.sortable').each(function(sentence_index, sentence_element) {
        const boundary_id = sentence_element.id;
        word_order_data[boundary_id] = $(sentence_element).sortable("toArray");
    });
    // console.log("Token Order Data: ");
    // console.log(word_order_data);

    $.post(API_URL, {
        action: TASK_UPDATE_ACTIONS[task_category],
        task_id: task_id,
        verse_id: verse_id,
        word_order: JSON.stringify(word_order_data)
    },
    function (response) {
        $.notify({
            message: response.message
        }, {
            type: response.style
        });

        if (response.success) {
            for (const boundary_element_id of Object.keys(word_order_data)) {
                storage.removeItem(`${PREFIX_KEY_BOUNDARY_WORD_ORDER}_${boundary_element_id}`);
                storage.removeItem(`${PREFIX_KEY_BOUNDARY_HEURISTIC_WORD_ORDER}_${boundary_element_id}`);
                storage.removeItem(`${PREFIX_KEY_BOUNDARY_STATE}_${boundary_element_id}`);
                console.log(`Removed stored token order for ${boundary_element_id} after a successful submit.`);
            }
            refresh_row_data(verse_id);
            const first_task = response.first_task;
            const next_task = response.next_task;
            $tabs[next_task].click();
            if (next_task == first_task) {
                $corpus_table.bootstrapTable('check', storage.getItem(KEY_NEXT_INDEX));
            }
        }
    });
};

/* ************************* END Task: Token Order ************************* */

/* ******************* BEGIN Task: Token Classification ******************* */
// Task: Token Classification

// Setup: Token Classification
function setup_task_token_classification(task_id, verse_id) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const row = $corpus_table.bootstrapTable('getRowByUniqueId', verse_id);

    const $token_classification_table = $(`#token-classification-table-${task_id}`);
    const $token_null_class_table = $(`#token-null-class-table-${task_id}`);
    const $sample_token_classification_type = $(`#sample-token-type-${task_id}`);

    const $include_exclude_token_button = $(`#include-exclude-button-token-classification-${task_id}`);
    $include_exclude_token_button.click(function () {
        const include_class = "include-all-token-classification";
        const include_text = "Include All Tokens";
        const exclude_class = "exclude-all-token-classification";
        const exclude_text = "Exclude All Tokens";
        if ($include_exclude_token_button.hasClass(include_class)) {
            console.log("Including all tokens.");
            $token_null_class_table.find('[name="tokclf-toggle"]').click();
            $include_exclude_token_button.removeClass(include_class);
            $include_exclude_token_button.removeClass("btn-success");
            $include_exclude_token_button.addClass(exclude_class);
            $include_exclude_token_button.addClass("btn-danger");
            $include_exclude_token_button.attr("title", exclude_text);
        } else if ($include_exclude_token_button.hasClass(exclude_class)) {
            console.log("Excluding all tokens.");
            $token_classification_table.find('[name="tokclf-toggle"]').click();
            $include_exclude_token_button.removeClass(exclude_class);
            $include_exclude_token_button.removeClass("btn-danger");
            $include_exclude_token_button.addClass(include_class);
            $include_exclude_token_button.addClass("btn-success");
            $include_exclude_token_button.attr("title", include_text);
        }
    });

    $token_classification_table.html("");
    $token_null_class_table.html("");

    var all_tokens = {};
    var used_tokens = [];
    var boundary_tokens = {};

    for (const [boundary_id, sentence_tokens] of Object.entries(row.sentences)) {
        $.extend(all_tokens, sentence_tokens);
        if (boundary_id !== "extra") {
            [].push.apply(used_tokens, row[TASK_WORD_ORDER][boundary_id]);
            boundary_tokens[boundary_id] = row[TASK_WORD_ORDER][boundary_id];
        }
    }

    // record existing labels
    // existing_token_classification array could be avoided perhaps
    // in that case, .includes() can be replaced with .hasOwnProperty() check
    var existing_token_classification = [];
    var existing_labels = {};
    for (const tokclf of row[TASK_TOKEN_CLASSIFICATION]) {
        if (tokclf.is_deleted || tokclf.task_id != task_id) {
            continue;
        }
        existing_token_classification.push(tokclf.token_id);
        existing_labels[tokclf.token_id] = tokclf.label_id;
    }

    for (const [boundary_id, used_token_ids] of Object.entries(boundary_tokens)) {
        for (const token_id of used_token_ids) {
            const token = all_tokens[token_id];
            var has_token_class = false;
            var tokclf_label_id = null;
            const $tokclf_row = $("<tr />", {});
            if (existing_token_classification.includes(token.id)) {
                $token_classification_table.append($tokclf_row);
                has_token_class = true;
                tokclf_label_id = existing_labels[token.id];
            } else {
                $token_null_class_table.append($tokclf_row);
            }

            const $tokclf_cell = $("<td />", {});
            $tokclf_row.append($tokclf_cell);

            const $tokclf = generate_token_button({
                token: token,
                id_prefix: `tokclf-${task_id}`
            });
            $tokclf_cell.append($tokclf);

            const $token_type_cell = $("<td />");
            $tokclf_row.append($token_type_cell);

            const $token_class_selector_element = $sample_token_classification_type.clone();
            $token_class_selector_element.data("boundary-id", boundary_id);
            $token_type_cell.append($token_class_selector_element);

            const token_class_selector_id = `token-class-selector-${task_id}-${token.id}`;
            $token_class_selector_element.attr("id", token_class_selector_id);

            if (has_token_class) {
                $token_class_selector_element.selectpicker('val', tokclf_label_id);
            } else {
                $token_class_selector_element.selectpicker('hide');
            }

            const $tokclf_toggle_cell = $("<td />", {
                class: "col-sm-1",
            });
            $tokclf_row.append($tokclf_toggle_cell);

            const tokclf_class = (has_token_class) ? "btn btn-secondary" : "btn btn-info include-tokclf";
            const tokclf_html = (has_token_class) ? '<i class="fa fa-times"></i>' : '<i class="fa fa-plus"></i>';

            const $tokclf_toggle = $("<span />", {
                id: `tokclf-toggle-${task_id}-${token.id}`,
                name: "tokclf-toggle",
                class: tokclf_class,
                html: tokclf_html,
                on: {
                    click: function() {
                        const select_selector = `#${token_class_selector_id}`;

                        if ($(this).hasClass("include-tokclf")) {
                            $(this).removeClass("include-tokclf");
                            $(this).removeClass("btn-info");
                            $(this).addClass("btn-secondary");
                            $(this).html('<i class="fa fa-times"></i>');
                            $(select_selector).selectpicker('show');
                            $token_classification_table.append($(this).parents('tr'));
                        } else {
                            $(this).removeClass("btn-secondary");
                            $(this).addClass("btn-info");
                            $(this).addClass("include-tokclf");
                            $(this).html('<i class="fa fa-plus"></i>');
                            $(select_selector).selectpicker('hide');
                            $token_null_class_table.append($(this).parents('tr'));
                        }
                    }
                }
            });
            $tokclf_toggle_cell.append($tokclf_toggle);
        }
    }
}

/* Task: Token Classification: Actions */

// Submit: Token Classification
function submit_task_token_classification(task_id) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const $token_classification_form = $(`#token-classification-form-${task_id}`);
    const $token_classification_table = $(`#token-classification-table-${task_id}`);

    if (!$token_classification_form[0].checkValidity()) {
        $token_classification_form[0].reportValidity();
        return;
    }

    const verse_id = $verse_id_containers.html();
    const task_category = TASK_TOKEN_CLASSIFICATION;

    var token_classification_data = {}
    $token_classification_table.find("select").each(function(select_index, select_element) {
        const token_id = select_element.id;
        const boundary_id = $(select_element).data("boundary-id");
        const token_label_id = $(select_element).selectpicker('val');
        token_classification_data[token_id] = {
            'boundary_id': boundary_id,
            'label_id': token_label_id
        }
    });

    $.post(API_URL, {
        action: TASK_UPDATE_ACTIONS[task_category],
        task_id: task_id,
        verse_id: verse_id,
        token_classification_data: JSON.stringify(token_classification_data)
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
                $corpus_table.bootstrapTable('check', storage.getItem(KEY_NEXT_INDEX));
            }
        }
    });
};

/* ******************** END Task: Token Classification ******************** */

/* ************************ BEGIN Task: Token Graph ************************ */
// Task: Token Graph (e.g. Action Graph)
// Setup: Token Graph

function setup_task_token_graph(task_id, verse_id) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const row = $corpus_table.bootstrapTable('getRowByUniqueId', verse_id);

    const $token_graph_container = $(`#token-graph-container-${task_id}`);
    const $token_graph_input_container = $(`#token-graph-input-container-${task_id}`);

    const $sample_token_graph_input_container = $(`#sample-token-graph-input-container-${task_id}`);
    const $sample_token_graph_input = $(`#sample-token-graph-input-${task_id}`);

    $token_graph_input_container.html("");

    var all_tokens = {};
    var boundary_tokens = {};

    for (const [boundary_id, sentence_tokens] of Object.entries(row.sentences)) {
        $.extend(all_tokens, sentence_tokens);
        if (boundary_id != "extra") {
            boundary_tokens[boundary_id] = row[TASK_WORD_ORDER][boundary_id];
        }
    }

    // record existing relations
    var existing_relations = {};
    var heuristic_relations = {};
    for (const tokrel of row[TASK_TOKEN_GRAPH]) {
        if (tokrel.is_deleted || tokrel.task_id != task_id) {
            continue;
        }
        if (!existing_relations.hasOwnProperty(tokrel.boundary_id)) {
            existing_relations[tokrel.boundary_id] = [];
        }
        existing_relations[tokrel.boundary_id].push([
            tokrel.src_id,
            tokrel.label_id,
            tokrel.dst_id
        ]);
    }
    for (const tokrel of row["heuristics"][TASK_TOKEN_GRAPH]) {
        // NOTE: get_token_graph() heuristic should return a list of dicts
        // every dict should have at least 5 properties: boundary_id, task_id, src_id, label_id, dst_id
        // NOTE: It is unclear how to provide task_id etc yet, for now, the heuristic is pretty ad-hoc
        // Some notable pitfalls:
        // * Same heuristic will apply to all token_graph tasks
        // * tokrel.relation_id provision is pretty hard to provide

        // if (tokrel.task_id != task_id) {
        //     continue;
        // }

        // continue if there is at least one annotated relation for this boundary
        if (existing_relations.hasOwnProperty(tokrel.boundary_id)) {
            continue
        }
        if (!heuristic_relations.hasOwnProperty(tokrel.boundary_id)) {
            heuristic_relations[tokrel.boundary_id] = [];
        }
        heuristic_relations[tokrel.boundary_id].push([
            tokrel.src_id,
            tokrel.label_id,
            tokrel.dst_id
        ]);
    }

    console.log(existing_relations);

    for (const [boundary_id, used_token_ids] of Object.entries(boundary_tokens)) {
        const $graph_input = $sample_token_graph_input.clone();
        $graph_input.prop("id", `token-graph-input-${task_id}-${boundary_id}`);
        $graph_input.addClass(sentence_token_graph_input_container_class);
        $graph_input.data("boundary-id", boundary_id);
        $graph_input.appendTo($token_graph_input_container);

        const $graph_input_header = $graph_input.find(".boundary-token-graph-header");

        // populate options
        var options = [];
        var header_html = [];
        var header_html_elements = [];
        for (const token_id of used_token_ids) {
            const token = all_tokens[token_id];
            const $token = generate_token_button({
                token: token,
                token_class_common: "btn-sm"
            });
            const token_text = $token.html();
            const $token_text = $('<span />', {
                text: token_text,
                title: `ID: ${token_id}`
            });
            $token_text.data("token_id", token_id);
            const token_html = $token.wrapAll('<div>').parent().html();
            header_html.push(token_text);
            header_html_elements.push($token_text);
            options.push({
                value: token_id,
                text: token_text,
                content: token_html
            });
        }
        const header_text = header_html.join(" ");
        $graph_input_header.html("");
        for (const $header_element of header_html_elements) {
            $graph_input_header.append($header_element);
            $graph_input_header.append($("<span />", {text: " "}));
        }

        // Re-Bind Add Triplet Row Function
        const $add_triplet_button = $graph_input.find(".add-triplet-button");
        const $triplet_location = $graph_input.find(".token-graph-input");
        $triplet_location.data("triplet-count", 0);
        $triplet_location.data("header-text", header_text);
        $triplet_location.data("tokens", options);
        $triplet_location.data("source-options", options);
        $triplet_location.data("target-options", options);

        $add_triplet_button.off("click");
        $add_triplet_button.click(function () {
            add_token_graph_row($triplet_location, task_id);
        });

        if (existing_relations.hasOwnProperty(boundary_id)) {
            for (const [_src_id, _label_id, _dst_id] of existing_relations[boundary_id]) {
                const $triple_row = add_token_graph_row($triplet_location, task_id, false);
                $triple_row.find(".source-entity").selectpicker('val', _src_id);
                $triple_row.find(".relation-label").selectpicker('val', _label_id);
                $triple_row.find(".target-entity").selectpicker('val', _dst_id);
            }
        } else {
            if (heuristic_relations.hasOwnProperty(boundary_id)) {
                for (const [_src_id, _label_id, _dst_id] of heuristic_relations[boundary_id]) {
                    const $triple_row = add_token_graph_row($triplet_location, task_id, true);
                    $triple_row.find(".source-entity").selectpicker('val', _src_id);
                    $triple_row.find(".relation-label").selectpicker('val', _label_id);
                    $triple_row.find(".target-entity").selectpicker('val', _dst_id);
                }
            } else {
                // Initiate empty row?
                // $add_triplet_button.click();
            }
        }
    }
}

function add_token_graph_row($location, task_id, is_heuristic) {
    const source_entity_options = $location.data("source-options");
    const target_entity_options = $location.data("target-options");

    const $sample_token_graph_source_entity = $(`#sample-token-graph-source-entity-${task_id}`);
    const $sample_token_graph_target_entity = $(`#sample-token-graph-target-entity-${task_id}`);
    const $sample_token_graph_relation_label = $(`#sample-token-graph-relation-label-${task_id}`);

    // Create and Insert Triplet Row Element
    const $row = $('<div />').addClass(`form-row mx-0 mt-1 px-0`).appendTo($location);
    $row.addClass('triplet-row');
    if (is_heuristic) {
        $row.addClass("border border-warning rounded rounded py-1")
    }

    const triplet_count = $location.data("triplet-count") + 1;
    $location.data("triplet-count", triplet_count);

    // Create Action Entity Input Element
    const $input_source_entity = $sample_token_graph_source_entity.clone();
    $input_source_entity.attr("id", `element-source-entity-${task_id}-${triplet_count}`);
    var current_value = $input_source_entity.attr("title");
    var updated_value = current_value.replace(
        "{}",
        `${VARIABLE_PREFIX}a${triplet_count}${VARIABLE_SUFFIX}`
    );
    $input_source_entity.attr("title", updated_value);
    $input_source_entity.addClass("source-entity");

    // Add Options
    for (const option of source_entity_options) {
        const $option = $("<option />", {
            value: option.value,
            html: option.text
        });
        $option.attr("data-content", option.content);
        $option.appendTo($input_source_entity);
    }


    // Insert Action Entity Input Element
    var $column = $('<div />').addClass(`col-sm mx-0 pr-0 my-auto`).appendTo($row);
    $input_source_entity.appendTo($column);
    // $input_source_entity.autoComplete();

    // Create Actor Label Selector Element
    const $input_relation_label = $sample_token_graph_relation_label.clone();
    $input_relation_label.attr("id", `element-relation-label-${task_id}-${triplet_count}`);
    var current_value = $input_relation_label.attr("title");
    var updated_value = current_value.replace(
        "{}",
        `${VARIABLE_PREFIX}r${triplet_count}${VARIABLE_SUFFIX}`
    );
    $input_relation_label.attr("title", updated_value);
    $input_relation_label.addClass("relation-label");

    // Insert Actor Label Selector Element
    var $column = $('<div />').addClass(`col-sm mx-1 px-0 my-auto`).appendTo($row);
    $input_relation_label.appendTo($column);

    // Create Target Entity Input Element
    const $input_target_entity = $sample_token_graph_target_entity.clone();
    $input_target_entity.attr("id", `element-target-entity-${task_id}-${triplet_count}`);
    var current_value = $input_target_entity.attr("title");
    var updated_value = current_value.replace(
        "{}",
        `${VARIABLE_PREFIX}t${triplet_count}${VARIABLE_SUFFIX}`
    );
    $input_target_entity.attr("title", updated_value);
    $input_target_entity.addClass("target-entity");

    // Add Options
    for (const option of target_entity_options) {
        const $option = $("<option />", {
            value: option.value,
            html: option.text
        });
        $option.attr("data-content", option.content);
        $option.appendTo($input_target_entity);
    }

    // Insert Target Entity Input Element
    var $column = $('<div />').addClass(`col-sm mx-0 pl-0 my-auto`).appendTo($row);
    $input_target_entity.appendTo($column);
    // $input_target_entity.autoComplete();

    // Create Remove Triplet Button
    const $remove_triplet_button = $('<button />').addClass("btn btn-danger");
    $remove_triplet_button.attr("id", `remove-triplet-button-${task_id}-${triplet_count}`);
    $remove_triplet_button.attr("title", "Remove Relation");
    const $remove_icon = $('<i />').addClass(`fas fa-minus`);

    // Insert Remove Triplet Button
    var $column = $('<div />').addClass(`col-sm-1 mx-0 px-0 my-auto`).appendTo($row);
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

function prepare_token_graph_data_displacy($data_location) {
    var data = {
        words: [],
        arcs: []
    };

    // temporary id store
    const node_ids = {};
    var node_id = 0;
    function get_node_id() {
        return node_id++;
    }

    const tokens = $data_location.data("tokens");
    for (const token of tokens) {
        node_ids[token.value] = get_node_id();
        data.words.push({
            text: token.text
        });
    }

    $data_location.children(".triplet-row").each(function (triplet_index, triplet_row) {
        // CAUTION: The ID on entity selectors is currently repeated for each row.
        // We aren't using it and instead looping on all elements having a particular class,
        // so this still works, but might as well get rid of it or make it unique!

        const $triplet_row = $(triplet_row);
        const $source_entity = $triplet_row.find('.source-entity');
        const $target_entity = $triplet_row.find('.target-entity');
        const $relation_label = $triplet_row.find('.relation-label');

        const source_entity_value = $source_entity.selectpicker('val'); // node_id of source entity
        const target_entity_value = $target_entity.selectpicker('val'); // node_id of target entity
        const relation_label_value = $relation_label.selectpicker('val');

        const source_entity_is_custom = $source_entity.find(`[value=${source_entity_value}]`).data('content').indexOf('token-manual') > -1;
        const target_entity_is_custom = $target_entity.find(`[value=${target_entity_value}]`).data('content').indexOf('token-manual') > -1;

        if (!source_entity_value || !relation_label_value || !relation_label_value) {
            return;
            // "return;" in .each() ==> "continue;"
            // "return false;" in .each() ==> "break;"
        }

        const source_entity = $source_entity.find(`[value=${source_entity_value}]`).html();
        const target_entity = $target_entity.find(`[value=${target_entity_value}]`).html();
        const relation_label = $relation_label.find(`[value=${relation_label_value}]`).data("subtext");
        data.arcs.push({
            start: Math.min(node_ids[source_entity_value], node_ids[target_entity_value]),
            end: Math.max(node_ids[source_entity_value], node_ids[target_entity_value]),
            dir: (node_ids[source_entity_value] < node_ids[target_entity_value]) ? "right" : "left",
            label: relation_label
        });
    });

    return data;
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
        // CAUTION: The ID on entity selectors is currently repeated for each row.
        // We aren't using it and instead looping on all elements having a particular class,
        // so this still works, but might as well get rid of it or make it unique!

        const $triplet_row = $(triplet_row);
        const $source_entity = $triplet_row.find('.source-entity');
        const $target_entity = $triplet_row.find('.target-entity');
        const $relation_label = $triplet_row.find('.relation-label');

        const source_entity_value = $source_entity.selectpicker('val'); // node_id of source entity
        const target_entity_value = $target_entity.selectpicker('val'); // node_id of target entity
        const relation_label_value = $relation_label.selectpicker('val');

        const source_entity_is_custom = $source_entity.find(`[value=${source_entity_value}]`).data('content').indexOf('token-manual') > -1;
        const target_entity_is_custom = $target_entity.find(`[value=${target_entity_value}]`).data('content').indexOf('token-manual') > -1;

        if (!source_entity_value || !relation_label_value || !relation_label_value) {
            return;
            // "return;" in .each() ==> "continue;"
            // "return false;" in .each() ==> "break;"
        }

        const source_entity = $source_entity.find(`[value=${source_entity_value}]`).html();
        const target_entity = $target_entity.find(`[value=${target_entity_value}]`).html();
        const relation_label = $relation_label.find(`[value=${relation_label_value}]`).data("subtext");

        if (!node_ids.hasOwnProperty(source_entity)) {
            node_ids[source_entity] = get_node_id();

            data.nodes.push({
                id: node_ids[source_entity],
                label: source_entity, // label
                title: `Token ID: ${source_entity_value}`, // title (visible on hover)
                value: 3,
                group: source_entity_is_custom ? 1 : 0, // group-id (0: present in corpus, 1: custom tokens)
            });
        }
        if (!node_ids.hasOwnProperty(target_entity)) {
            node_ids[target_entity] = get_node_id();

            data.nodes.push({
                id: node_ids[target_entity],
                label: target_entity, // label
                title: `Token ID: ${target_entity_value}`, // title (visible on hover)
                value: 3,
                group: target_entity_is_custom ? 1 : 0, // group-id (upos/xpos based?)
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

    // sort to get nodes with group: 0 at the start,
    // so that non-manual tokens (group: 1) always get second colour
    data.nodes.sort(function(a, b) {
        if (a.group < b.group) {
            return -1;
        }
        if (a.group > b.group) {
            return 1;
        }
        return 0;
    });
    console.log("Graph Data: ");
    console.log(data);
    return data;
}

// Show Graph Modal
$show_graph_modal.on('shown.bs.modal', function(event) {
    // TODO: Maybe need to add task_id identifier in case of
    // multiple graph tasks from same category
    const $trigger_button = $(event.relatedTarget);
    const trigger_task_category = $trigger_button.data("task-category");
    const trigger_task_id = $trigger_button.data("task-id");

    if (trigger_task_category == TASK_TOKEN_GRAPH) {
        // triggered from token_graph task
        const $target_card = $trigger_button.parents(`.${sentence_token_graph_input_container_class}`);
        const $target_location = $target_card.find(".token-graph-input");

        const sentence_text = $target_location.data("header-text");
        $show_graph_modal_label.html(sentence_text);
        const token_graph_data = prepare_token_graph_data($target_location);
        draw_graph(token_graph_data);

        const token_graph_data_displacy = prepare_token_graph_data_displacy($target_location);
        draw_graph_displacy(token_graph_data_displacy);
    } else if (trigger_task_category == TASK_SENTENCE_GRAPH) {
        // triggered from sentence_graph task
        const $target_location = $(`#sentence-graph-annotation-container-${trigger_task_id}`);
        const sentence_graph_data = prepare_sentence_graph_data($target_location);
        draw_graph(sentence_graph_data);
    }
});

/* Task: Token Graph: Actions */

// Submit: Token Graph
function submit_task_token_graph(task_id) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const $token_graph_form = $(`#token-graph-form-${task_id}`);

    if (!$token_graph_form[0].checkValidity()) {
        $token_graph_form[0].reportValidity();
        return;
    }

    const task_category = TASK_TOKEN_GRAPH;
    const verse_id = $verse_id_containers.html();

    var token_graph_data = [];

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
            token_graph_data.push({
                "boundary_id": boundary_id,
                "src_id": source_entity_id,
                "label_id": relation_label_id,
                "dst_id": target_entity_id
            });
        });
    });
    console.log("Submit Token Graph Data: ");
    console.log(token_graph_data);

    $.post(API_URL, {
        action: TASK_UPDATE_ACTIONS[task_category],
        task_id: task_id,
        verse_id: verse_id,
        token_graph_data: JSON.stringify(token_graph_data)
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
                $corpus_table.bootstrapTable('check', storage.getItem(KEY_NEXT_INDEX));
            }
        }
    });
};

/* ************************* END Task: Token Graph ************************* */

/* ********************* BEGIN Task: Token Connection ********************* */
// Task: Token Connection (e.g. Co-reference Resolution)

// Setup: Token Connection


function setup_task_token_connection(task_id, verse_id, context_window) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const row = $corpus_table.bootstrapTable('getRowByUniqueId', verse_id);
    const data = $corpus_table.bootstrapTable('getData');

    const $token_connection_context_container = $(`#tokcon-context-container-${task_id}`);

    const $token_connection_intermediate_row_container = $(`#tokcon-intermediate-row-container-${task_id}`);
    const $token_connection_source_container = $(`#tokcon-source-token-container-${task_id}`);
    const $token_connection_target_container = $(`#tokcon-target-token-container-${task_id}`);
    const $token_connection_reset_button = $(`#tokcon-reset-button-${task_id}`);
    const $token_connection_confirm_button = $(`#tokcon-confirm-button-${task_id}`);

    const $token_connection_annotation_container = $(`#tokcon-annotation-container-${task_id}`);

    // calculate pre-context
    const current_index = data.findIndex(function(r) {
        return r.verse_id == verse_id;
    });

    if (!context_window) {
        context_window = 3;
    }

    const start_index = (current_index > (context_window - 1)) ? (current_index - context_window) : 0;
    const context = data.slice(start_index, current_index + 1);

    var all_tokens = {};
    var boundary_tokens = [];

    var existing_token_connections = [];

    for (const verse_data of context) {
        // verse_data
        for (const [boundary_id, sentence_tokens] of Object.entries(verse_data.sentences)) {
            $.extend(all_tokens, sentence_tokens);
            if (boundary_id != "extra") {
                boundary_tokens.push([boundary_id, verse_data[TASK_WORD_ORDER][boundary_id]]);
            }
            // ensure that every boundary in the previous n verses has word_order
            // if one is doing word_order in order, this won't be an issue
        }
        for (const token_connection of verse_data[TASK_TOKEN_CONNECTION]) {
            if (token_connection.is_deleted || token_connection.task_id != task_id) {
                continue;
            }
            existing_token_connections.push(token_connection);
        }
    };
    console.log(existing_token_connections);

    $token_connection_context_container.html("");
    $token_connection_reset_button.click();
    $token_connection_annotation_container.html("");

    for (const [boundary_id, used_tokens] of boundary_tokens) {
        const $boundary_container = $("<div />", {
            id: `tokcon-boundary-container-${task_id}-${boundary_id}`,
            class: "border border-secondary rounded px-1 pt-1 pb-0 ml-1 mt-1 mb-0 boundary-container"
        });
        $boundary_container.appendTo($token_connection_context_container);
        $boundary_container.data("boundary-id", boundary_id);

        for (const token_id of used_tokens) {
            const token = all_tokens[token_id];
            const $token = generate_token_button({
                token: token,
                token_element: "<button />",
                id_prefix: `tokcon-token-${task_id}`,
                token_data: {"token-id": token_id, "boundary-id": boundary_id},
                onclick: function($element) {
                    const $annotation_token = $element.clone();
                    $annotation_token.removeAttr("id");
                    $annotation_token.data("token-id", token_id);
                    $annotation_token.data("boundary-id", boundary_id);

                    if (!$token_connection_source_container.html().trim()) {
                        $annotation_token.addClass("tokcon-source-token");
                        $annotation_token.appendTo($token_connection_source_container);
                        $element.prop("disabled", true);
                    } else {
                        if (!$token_connection_target_container.html().trim()) {
                            $annotation_token.addClass("tokcon-target-token");
                            $annotation_token.appendTo($token_connection_target_container);
                            $token_connection_confirm_button.prop("disabled", false);
                            $element.prop("disabled", true);
                        } else {
                            $.notify({
                                message: "Please confirm or reset the current token_connection first."
                            }, {
                                type: "danger"
                            });
                        }
                        $token_connection_confirm_button.focus();
                    }
                }
            });
            $token.addClass("mr-1 mb-1");
            $token.appendTo($boundary_container);
        }
    }

    // add existing references
    for (const token_connection of existing_token_connections) {
        const $original_source_token = $(`#tokcon-token-${task_id}-${token_connection.src_id}`);
        const $original_target_token = $(`#tokcon-token-${task_id}-${token_connection.dst_id}`);

        if (($original_source_token.length == 0) || ($original_target_token.length == 0)) {
            // If either token is out of context, don't show that relation.
            continue;
        }

        const $source_token = $original_source_token.clone();
        $source_token.removeAttr("id");
        $source_token.data("token-id", token_connection.src_id);
        $source_token.data("boundary-id", token_connection.boundary_id);
        $source_token.addClass("tokcon-source-token");

        const $target_token = $original_target_token.clone();
        const target_token_boundary_id = $(`#tokcon-token-${task_id}-${token_connection.dst_id}`).data("boundary-id");
        $target_token.removeAttr("id");
        $target_token.data("token-id", token_connection.dst_id);
        $target_token.data("boundary-id", target_token_boundary_id);
        $target_token.addClass("tokcon-target-token");

        const is_context_connection = (verse_id != token_connection.verse_id);
        add_token_connection_row($token_connection_annotation_container, $source_token, $target_token, is_context_connection);
    }

    /* setup event listeners */
    $token_connection_reset_button.unbind("click");
    $token_connection_reset_button.click(function () {
        // enable all buttons
        $token_connection_context_container.find("button").prop("disabled", false);

        $token_connection_source_container.html("");
        $token_connection_target_container.html("");
    });

    $token_connection_confirm_button.unbind("click");
    $token_connection_confirm_button.click(function () {
        const $source_token = $token_connection_source_container.children(".tokcon-source-token");
        const $target_token = $token_connection_target_container.children(".tokcon-target-token");

        add_token_connection_row($token_connection_annotation_container, $source_token, $target_token);

        // reset
        $token_connection_reset_button.click();
        $token_connection_confirm_button.prop("disabled", true);
    });

}


function add_token_connection_row($location, $source_token, $target_token, is_context_connection) {
    const $row = $('<div />').addClass("row p-0 m-0").prependTo($location);
    $row.addClass('tokcon-annotation-row');
    if (is_context_connection) {
        $row.addClass("bg-light pt-1 mb-1 border rounded");
    }

    // add source token
    var $column = $("<div />", {
        class: "col-sm px-1",
    }).appendTo($row);
    $source_token.appendTo($column);

    // add arrow
    var $column = $("<div />", {
        class: "col-sm-2",
        html: '<span class="btn btn-secondary mb-1 mr-1"><i class="fas fa-arrows-left-right"></i></span>'
    }).appendTo($row);

    // add target token
    var $column = $("<div />", {
        class: "col-sm px-1",
    }).appendTo($row);
    $target_token.appendTo($column);

    // add remove button
    const $remove_tokcon_button = $('<button />').addClass(`btn btn-danger float-right mx-1`);
    $remove_tokcon_button.attr("title", "Remove Token Connection");
    const $remove_icon = $('<i />').addClass(`fas fa-minus`);
    var $column = $('<div />').addClass("col-sm-2 px-0").appendTo($row);
    $remove_icon.appendTo($remove_tokcon_button);
    $remove_tokcon_button.appendTo($column);
    $remove_tokcon_button.click(function () {
        $(this).parent().parent().remove();
    });
    if (is_context_connection) {
        $remove_tokcon_button.attr("title", "Go to the source verse to remove the token connection.");
        $remove_tokcon_button.prop("disabled", true);
    }
}

/* Task: Token Connection: Actions */

// Submit: Token Connection
function submit_task_token_connection(task_id) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const task_category = TASK_TOKEN_CONNECTION;
    const verse_id = $verse_id_containers.html();

    const $token_connection_context_container = $(`#tokcon-context-container-${task_id}`);
    const $token_connection_annotation_container = $(`#tokcon-annotation-container-${task_id}`);

    var context_data = [];
    var token_connection_data = [];
    $token_connection_context_container.find(".boundary-container").each(function (_index, _boundary_container) {
        context_data.push($(_boundary_container).data("boundary-id"));
    });

    const $tokcon_annotation_rows = $token_connection_annotation_container.find('.tokcon-annotation-row');
    $tokcon_annotation_rows.each(function(tokcon_index, tokcon_row) {
        const $tokcon_row = $(tokcon_row);
        const $source_token = $tokcon_row.find(".tokcon-source-token");
        const $target_token = $tokcon_row.find(".tokcon-target-token");

        token_connection_data.push({
            "boundary_id": $source_token.data("boundary-id"),
            "src_id": $source_token.data("token-id"),
            "dst_id": $target_token.data("token-id")
        });
    });
    $.post(API_URL, {
        action: TASK_UPDATE_ACTIONS[task_category],
        task_id: task_id,
        verse_id: verse_id,
        context_data: JSON.stringify(context_data),
        token_connection_data: JSON.stringify(token_connection_data)
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
                $corpus_table.bootstrapTable('check', storage.getItem(KEY_NEXT_INDEX));
            }
        }
    });
};

/* ********************** END Task: Token Connection ********************** */

/* ****************** BEGIN Task: Sentence Classification ****************** */
// Task: Sentence Classification

// Setup: Sentence Classification

function setup_task_sentence_classification(task_id, verse_id) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const row = $corpus_table.bootstrapTable('getRowByUniqueId', verse_id);

    const $sentence_classification_container = $(`#sentence-classification-container-${task_id}`);
    const $sentence_classification_input_container = $(`#sentence-classification-input-container-${task_id}`);

    const $sample_sentence_classification_input_container = $(`#sample-sentence-classification-input-container-${task_id}`);
    const $sample_sentence_classification_input = $(`#sample-sentence-classification-input-${task_id}`);

    $sentence_classification_input_container.html("");

    var all_tokens = {};
    var boundary_tokens = {};

    for (const [boundary_id, sentence_tokens] of Object.entries(row.sentences)) {
        $.extend(all_tokens, sentence_tokens);
        if (boundary_id != "extra") {
            boundary_tokens[boundary_id] = row[TASK_WORD_ORDER][boundary_id];
        }
    }

    // record existing sentence classification
    var existing_sentence_classification = {};
    for (const sentclf of row[TASK_SENTENCE_CLASSIFICATION]) {
        if (sentclf.task_id != task_id) {
            continue;
        }
        if (!existing_sentence_classification.hasOwnProperty(sentclf.boundary_id)) {
            existing_sentence_classification[sentclf.boundary_id] = [];
        }
        existing_sentence_classification[sentclf.boundary_id] = sentclf.label_id;
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
        const $sentence = $sample_sentence_classification_input.clone();
        $sentence.attr("id", `sentence-classification-boundary-${task_id}-${boundary_id}`);
        $sentence.appendTo($sentence_classification_input_container);

        const $sentence_text = $sentence.find(".sentence-text");
        $sentence_text.html(header_text);
        $sentence_text.data("boundary-id", boundary_id);

        const $sentence_label_select = $sentence.find(".sentence-label");
        $sentence_label_select.attr("id", `sentence-classification-select-${task_id}-${boundary_id}`);

        console.log(existing_sentence_classification);
        if (existing_sentence_classification.hasOwnProperty(boundary_id)) {
            $sentence_label_select.selectpicker("val", existing_sentence_classification[boundary_id]);
        } else {
            $sentence_label_select.selectpicker();
        }
    }
}

/* Task: Sentence Classification: Actions */

// Submit: Sentence Classification
function submit_task_sentence_classification(task_id) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const $sentence_classification_form = $(`#sentence-classification-form-${task_id}`);
    const $sentence_classification_input_container = $(`#sentence-classification-input-container-${task_id}`);

    if (!$sentence_classification_form[0].checkValidity()) {
        $sentence_classification_form[0].reportValidity();
        return;
    }

    const task_category = TASK_SENTENCE_CLASSIFICATION;
    const verse_id = $verse_id_containers.html();

    var sentence_classification_data = [];

    $sentence_classification_input_container.find(".sentence-text").each(function (_index, _text_element) {
        const $text_element = $(_text_element);
        const boundary_id = $text_element.data("boundary-id");
        const $selector = $(`#sentence-classification-select-${task_id}-${boundary_id}`);
        const label_id = $selector.selectpicker("val");
        sentence_classification_data.push({
            boundary_id: boundary_id,
            label_id: label_id
        });
    });

    $.post(API_URL, {
        action: TASK_UPDATE_ACTIONS[task_category],
        task_id: task_id,
        verse_id: verse_id,
        sentence_classification_data: JSON.stringify(sentence_classification_data)
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
                $corpus_table.bootstrapTable('check', storage.getItem(KEY_NEXT_INDEX));
            }
        }
    });
};

/* ******************* END Task: Sentence Classification ******************* */

/* ********************** BEGIN Task: Sentence Graphs ********************** */
// Task: Sentence Graph (e.g. Discourse Graph)

// Setup: Sentence Graph
function setup_task_sentence_graph(task_id, verse_id, context_window) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const row = $corpus_table.bootstrapTable('getRowByUniqueId', verse_id);
    const data = $corpus_table.bootstrapTable('getData');

    const $sentence_graph_context_container = $(`#sentence-graph-context-container-${task_id}`);

    const $sentence_graph_intermediate_row_container = $(`#sentence-graph-intermediate-row-container-${task_id}`);
    const $sentence_graph_source_container = $(`#sentence-graph-source-token-container-${task_id}`);
    const $sentence_graph_relation_selector = $(`#sentence-graph-relation-selector-${task_id}`);
    const $sentence_graph_target_container = $(`#sentence-graph-target-token-container-${task_id}`);
    const $sentence_graph_reset_button = $(`#sentence-graph-reset-button-${task_id}`);
    const $sentence_graph_confirm_button = $(`#sentence-graph-confirm-button-${task_id}`);

    const $sentence_graph_annotation_container = $(`#sentence-graph-annotation-container-${task_id}`);

    // calculate pre-context
    const current_index = data.findIndex(function(r) {
        return r.verse_id == verse_id;
    });

    if (!context_window) {
        context_window = 3;
    }

    const start_index = (current_index > (context_window - 1)) ? (current_index - context_window) : 0;
    const context = data.slice(start_index, current_index + 1);

    var all_tokens = {};
    var boundary_tokens = [];
    var boundary_marker_tokens = {};

    var existing_sentence_graphs = [];

    for (const verse_data of context) {
        // verse_data
        $.extend(boundary_marker_tokens, verse_data[TASK_SENTENCE_BOUNDARY]);
        for (const [boundary_id, sentence_tokens] of Object.entries(verse_data.sentences)) {
            $.extend(all_tokens, sentence_tokens);
            if (boundary_id != "extra") {
                boundary_tokens.push([boundary_id, verse_data[TASK_WORD_ORDER][boundary_id]]);
            }
            // ensure that every boundary in the previous n verses has word_order
            // if one is doing word_order in order, this won't be an issue
        }
        for (const sentrel of verse_data[TASK_SENTENCE_GRAPH]) {
            if (sentrel.is_deleted || sentrel.task_id != task_id) {
                continue;
            }
            existing_sentence_graphs.push(sentrel);
        }
    };
    console.log(boundary_marker_tokens);
    console.log(existing_sentence_graphs);

    $sentence_graph_context_container.html("");
    $sentence_graph_reset_button.click();
    $sentence_graph_annotation_container.html("");

    for (const [boundary_id, used_tokens] of boundary_tokens) {
        const $boundary_container = $("<div />", {
            id: `sentence-graph-boundary-container-${task_id}-${boundary_id}`,
            class: "border border-secondary rounded px-1 pt-1 pb-0 ml-1 mt-1 mb-0 boundary-container"
        });
        $boundary_container.appendTo($sentence_graph_context_container);
        $boundary_container.data("boundary-id", boundary_id);

        var sentence_text = [];

        const boundary_token_id = boundary_marker_tokens[boundary_id]["token_id"];
        for (const token_id of used_tokens) {
            const token = all_tokens[token_id];
            const $token = generate_token_button({
                token: token,
                token_element: "<button />",
                id_prefix: `sentence-graph-token-${task_id}`,
                token_class_common: "btn sentence-graph-context-token",
                token_data: {"token-id": token_id, "boundary-id": boundary_id},
                onclick: function($element) {
                    const $annotation_token = $element.clone();
                    $annotation_token.removeAttr("id");
                    $annotation_token.data("token-id", token_id);
                    $annotation_token.data("boundary-id", boundary_id);

                    if (!$sentence_graph_source_container.html().trim()) {
                        $annotation_token.addClass("sentence-graph-source-token");
                        $annotation_token.appendTo($sentence_graph_source_container);
                        $element.parent().children("button").prop("disabled", true);
                    } else {
                        if (!$sentence_graph_target_container.html().trim()) {
                            $annotation_token.addClass("sentence-graph-target-token");
                            $annotation_token.appendTo($sentence_graph_target_container);
                            $sentence_graph_confirm_button.prop("disabled", false);
                            $element.parent().children("button").prop("disabled", true);
                        } else {
                            $.notify({
                                message: "Please confirm or reset the current sentence_graph first."
                            }, {
                                type: "danger"
                            });
                        }
                        $sentence_graph_confirm_button.focus();
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
                $boundary_token.removeClass("sentence-graph-context-token");
                $boundary_token.addClass("btn-dark");
                $boundary_token.addClass("sentence-graph-context-sentence-token");
                $boundary_token.prependTo($boundary_container);
            }
            $token.appendTo($boundary_container);
        }
        $boundary_container.children(".sentence-graph-context-sentence-token").attr("title", sentence_text.join(" "));
    }

    // add existing references
    for (const sentrel of existing_sentence_graphs) {
        const relation_relation_type = sentrel.relation_type;

        // type == 0: token-token connection
        // type == 1: token-sentence connection
        // type == 2: sentence-token connection
        // type == 3: sentence-sentence connection

        var $original_source_token, $original_target_token;
        if ((relation_relation_type == 0) || (relation_relation_type == 1)) {
            $original_source_token = $(`#sentence-graph-token-${task_id}-${sentrel.src_token_id}`);
        } else {
            $original_source_token = $(`#sentence-graph-sentence-token-${task_id}-${sentrel.src_token_id}`);
        }
        if ((relation_relation_type == 0) || (relation_relation_type == 2)) {
            $original_target_token = $(`#sentence-graph-token-${task_id}-${sentrel.dst_token_id}`);
        } else {
            $original_target_token = $(`#sentence-graph-sentence-token-${task_id}-${sentrel.dst_token_id}`);
        }

        if (($original_source_token.length == 0) || ($original_target_token.length == 0)) {
            // If either token is out of context, don't show that relation.
            continue;
        }

        const $source_token = $original_source_token.clone();
        $source_token.removeAttr("id");
        $source_token.data("token-id", sentrel.src_token_id);
        $source_token.data("boundary-id", sentrel.src_boundary_id);
        $source_token.addClass("sentence-graph-source-token");

        const $target_token = $original_target_token.clone();
        $target_token.removeAttr("id");
        $target_token.data("token-id", sentrel.dst_token_id);
        $target_token.data("boundary-id", sentrel.dst_boundary_id);
        $target_token.addClass("sentence-graph-target-token");

        const relation_label_id = sentrel.label_id;
        const is_context_connection = ((verse_id != sentrel.src_verse_id) && (verse_id != sentrel.dst_verse_id));
        add_sentence_graph_row(
            $sentence_graph_annotation_container,
            $sentence_graph_relation_selector,
            $source_token,
            $target_token,
            relation_label_id,
            is_context_connection
        );
    }

    /* setup event listeners */
    $sentence_graph_reset_button.unbind("click");
    $sentence_graph_reset_button.click(function () {
        // enable all buttons
        $sentence_graph_context_container.find("button").prop("disabled", false);

        $sentence_graph_source_container.html("");
        $sentence_graph_target_container.html("");
    });

    $sentence_graph_confirm_button.unbind("click");
    $sentence_graph_confirm_button.click(function () {
        const $source_token = $sentence_graph_source_container.children(".sentence-graph-source-token");
        const $target_token = $sentence_graph_target_container.children(".sentence-graph-target-token");

        const relation_label_id = $sentence_graph_relation_selector.selectpicker("val");
        $sentence_graph_relation_selector.selectpicker("val", null);

        add_sentence_graph_row(
            $sentence_graph_annotation_container,
            $sentence_graph_relation_selector,
            $source_token,
            $target_token,
            relation_label_id
        );

        // reset
        $sentence_graph_reset_button.click();
        $sentence_graph_confirm_button.prop("disabled", true);
    });



}

function add_sentence_graph_row($location, $selector, $source_token, $target_token, relation_label_id, is_context_connection) {
    const $row = $('<div />').addClass("row").prependTo($location);
    $row.addClass('sentence-graph-annotation-row p-0 m-0');
    if (is_context_connection) {
        $row.addClass("bg-light pt-1 mb-1 border rounded");
    }

    // add source token
    var $column = $("<div />", {
        class: "col-sm px-1",
    }).appendTo($row);
    $source_token.appendTo($column);

    // add relation
    const $relation_selector = $selector.clone();
    $relation_selector.removeAttr("id");
    $relation_selector.addClass("sentence-graph-relation");

    var $column = $("<div />", {
        class: "col-sm-4",
    }).appendTo($row);
    $relation_selector.appendTo($column);
    $relation_selector.selectpicker("val", relation_label_id);

    // add target token
    var $column = $("<div />", {
        class: "col-sm px-1",
    }).appendTo($row);
    $target_token.appendTo($column);

    // add remove button
    var $column = $('<div />').addClass("col-sm-2 px-0").appendTo($row);
    const $remove_sentence_graph_button = $('<button />').addClass(`btn btn-danger float-right mx-1`);
    $remove_sentence_graph_button.attr("title", "Remove Sentence Relation");
    const $remove_icon = $('<i />').addClass(`fas fa-minus`);
    $remove_icon.appendTo($remove_sentence_graph_button);
    $remove_sentence_graph_button.appendTo($column);
    $remove_sentence_graph_button.click(function () {
        $(this).parent().parent().remove();
    });
    if (is_context_connection) {
        $remove_sentence_graph_button.attr("title", "Go to the source verse to remove the token connection.");
        $remove_sentence_graph_button.prop("disabled", true);
    }
}

function prepare_sentence_graph_data($data_location) {
    var data = {
        nodes: [],
        edges: []
    };

    var node_ids = {};
    var node_id = 0;
    function get_node_id() {
        return ++node_id;
    }

    const $sentence_graph_annotation_rows = $data_location.find('.sentence-graph-annotation-row');
    $sentence_graph_annotation_rows.each(function(_index, sentence_graph_row) {
        const $sentence_graph_row = $(sentence_graph_row);
        const $source_token = $sentence_graph_row.find(".sentence-graph-source-token");
        const $target_token = $sentence_graph_row.find(".sentence-graph-target-token");
        const $relation = $sentence_graph_row.find(".sentence-graph-relation");

        const source_is_sentence_token = $source_token.hasClass("sentence-graph-context-sentence-token");
        const target_is_sentence_token = $target_token.hasClass("sentence-graph-context-sentence-token");

        // type == 0: token-token connection
        // type == 1: token-sentence connection
        // type == 2: sentence-token connection
        // type == 3: sentence-sentence connection

        var relation_type = 0
        var source_group_id = 0;
        var target_group_id = 0;

        if (source_is_sentence_token && target_is_sentence_token) {
            relation_type = 3;
            source_group_id = 1;
            target_group_id = 1;
        } else {
            if (source_is_sentence_token) {
                relation_type = 2;
                source_group_id = 1;
            }
            if (target_is_sentence_token) {
                relation_type = 1;
                target_group_id = 1;
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
                group: source_group_id
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
                group: target_group_id
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

/* Task: Sentence Graph: Actions */

// Submit: Sentence Graph
function submit_task_sentence_graph(task_id) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const $sentence_graph_form = $(`#sentence-graph-form-${task_id}`);
    const $sentence_graph_context_container = $(`#sentence-graph-context-container-${task_id}`);
    const $sentence_graph_annotation_container = $(`#sentence-graph-annotation-container-${task_id}`);

    if (!$sentence_graph_form[0].checkValidity()) {
        $sentence_graph_form[0].reportValidity();
        return;
    }

    const task_category = TASK_SENTENCE_GRAPH;
    const verse_id = $verse_id_containers.html();

    var context_data = [];
    var sentence_graph_data = [];
    $sentence_graph_context_container.find(".boundary-container").each(function (_index, _boundary_container) {
        context_data.push($(_boundary_container).data("boundary-id"));
    });

    const $sentence_graph_annotation_rows = $sentence_graph_annotation_container.find('.sentence-graph-annotation-row');
    $sentence_graph_annotation_rows.each(function(_index, sentence_graph_row) {
        const $sentence_graph_row = $(sentence_graph_row);
        const $source_token = $sentence_graph_row.find(".sentence-graph-source-token");
        const $target_token = $sentence_graph_row.find(".sentence-graph-target-token");
        const $relation = $sentence_graph_row.find(".sentence-graph-relation");

        const source_is_sentence_token = $source_token.hasClass("sentence-graph-context-sentence-token");
        const target_is_sentence_token = $target_token.hasClass("sentence-graph-context-sentence-token");

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

        sentence_graph_data.push({
            "src_boundary_id": $source_token.data("boundary-id"),
            "src_token_id": $source_token.data("token-id"),
            "label_id": $relation.selectpicker("val"),
            "dst_boundary_id": $target_token.data("boundary-id"),
            "dst_token_id": $target_token.data("token-id"),
            "relation_type": relation_type
        });
    });
    $.post(API_URL, {
        action: TASK_UPDATE_ACTIONS[task_category],
        task_id: task_id,
        verse_id: verse_id,
        context_data: JSON.stringify(context_data),
        sentence_graph_data: JSON.stringify(sentence_graph_data)
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
                $corpus_table.bootstrapTable('check', storage.getItem(KEY_NEXT_INDEX));
            }
        }
    },
    'json');
};

/* *********************** END Task: Sentence Graph *********************** */

/* ******************* BEGIN Task: Token Text Annotation ******************* */
// Task: Token Text Annotation

// Setup: Token Text Annotation
function setup_task_token_text_annotation(task_id, verse_id) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const row = $corpus_table.bootstrapTable('getRowByUniqueId', verse_id);

    const $token_text_annotation_table = $(`#token-text-annotation-table-${task_id}`);
    const $token_non_annotation_table = $(`#token-non-annotation-table-${task_id}`);
    const $sample_token_text_annotation_text = $(`#sample-token-text-annotation-text-${task_id}`);

    const $include_exclude_token_button = $(`#include-exclude-button-token-text-annotation-${task_id}`);
    $include_exclude_token_button.click(function () {
        const include_class = "include-all-token-text-annotation";
        const include_text = "Include All Tokens";
        const exclude_class = "exclude-all-token-text-annotation";
        const exclude_text = "Exclude All Tokens";
        if ($include_exclude_token_button.hasClass(include_class)) {
            console.log("Including all tokens.");
            $token_non_annotation_table.find('[name="token-text-annotation-toggle"]').click();
            $include_exclude_token_button.removeClass(include_class);
            $include_exclude_token_button.removeClass("btn-success");
            $include_exclude_token_button.addClass(exclude_class);
            $include_exclude_token_button.addClass("btn-danger");
            $include_exclude_token_button.attr("title", exclude_text);
        } else if ($include_exclude_token_button.hasClass(exclude_class)) {
            console.log("Excluding all tokens.");
            $token_text_annotation_table.find('[name="token-text-annotation-toggle"]').click();
            $include_exclude_token_button.removeClass(exclude_class);
            $include_exclude_token_button.removeClass("btn-danger");
            $include_exclude_token_button.addClass(include_class);
            $include_exclude_token_button.addClass("btn-success");
            $include_exclude_token_button.attr("title", include_text);
        }
    });

    $token_text_annotation_table.html("");
    $token_non_annotation_table.html("");

    var all_tokens = {};
    var used_tokens = [];
    var boundary_tokens = {};

    for (const [boundary_id, sentence_tokens] of Object.entries(row.sentences)) {
        $.extend(all_tokens, sentence_tokens);
        if (boundary_id !== "extra") {
            [].push.apply(used_tokens, row[TASK_WORD_ORDER][boundary_id]);
            boundary_tokens[boundary_id] = row[TASK_WORD_ORDER][boundary_id];
        }
    }

    // record existing annotation texts
    // existing_token_text_annotations array could be avoided perhaps
    // in that case, .includes() can be replaced with .hasOwnProperty() check
    var existing_token_text_annotations = [];
    var existing_texts = {};
    for (const token_text_annotation of row[TASK_TOKEN_TEXT_ANNOTATION]) {
        if (token_text_annotation.is_deleted || token_text_annotation.task_id != task_id) {
            continue;
        }
        existing_token_text_annotations.push(token_text_annotation.token_id);
        existing_texts[token_text_annotation.token_id] = token_text_annotation.text;
    }

    for (const [boundary_id, used_token_ids] of Object.entries(boundary_tokens)) {
        for (const token_id of used_token_ids) {
            const token = all_tokens[token_id];
            var has_text_annotation = false;
            var token_text_annotation_text = null;
            const $token_text_annotation_row = $("<tr />", {});
            if (existing_token_text_annotations.includes(token.id)) {
                $token_text_annotation_table.append($token_text_annotation_row);
                has_text_annotation = true;
                token_text_annotation_text = existing_texts[token.id];
            } else {
                $token_non_annotation_table.append($token_text_annotation_row);
            }

            const $token_text_annotation_cell = $("<td />", {});
            $token_text_annotation_row.append($token_text_annotation_cell);

            const $token_text_annotation = generate_token_button({
                token: token,
                id_prefix: `token-text-annotation-${task_id}`
            });
            $token_text_annotation_cell.append($token_text_annotation);

            const $token_text_annotation_text_cell = $("<td />");
            $token_text_annotation_row.append($token_text_annotation_text_cell);

            const $token_text_annotation_input_element = $sample_token_text_annotation_text.clone();
            $token_text_annotation_input_element.data("boundary-id", boundary_id);
            $token_text_annotation_text_cell.append($token_text_annotation_input_element);

            const token_text_annotation_input_id = `token-text-annotation-input-${task_id}-${token.id}`;
            $token_text_annotation_input_element.attr("id", token_text_annotation_input_id);

            if (has_text_annotation) {
                $token_text_annotation_input_element.val(token_text_annotation_text);
            } else {
                $token_text_annotation_input_element.hide();
            }

            const $token_text_annotation_toggle_cell = $("<td />", {
                class: "col-sm-1",
            });
            $token_text_annotation_row.append($token_text_annotation_toggle_cell);

            const token_text_annotation_class = (has_text_annotation) ? "btn btn-secondary" : "btn btn-info include-token-text-annotation";
            const token_text_annotation_html = (has_text_annotation) ? '<i class="fa fa-times"></i>' : '<i class="fa fa-plus"></i>';

            const $token_text_annotation_toggle = $("<span />", {
                id: `token-text-annotation-toggle-${task_id}-${token.id}`,
                name: "token-text-annotation-toggle",
                class: token_text_annotation_class,
                html: token_text_annotation_html,
                on: {
                    click: function() {
                        const input_selector = `#${token_text_annotation_input_id}`;

                        if ($(this).hasClass("include-token-text-annotation")) {
                            $(this).removeClass("include-token-text-annotation");
                            $(this).removeClass("btn-info");
                            $(this).addClass("btn-secondary");
                            $(this).html('<i class="fa fa-times"></i>');
                            $(input_selector).show();
                            $token_text_annotation_table.append($(this).parents('tr'));
                        } else {
                            $(this).removeClass("btn-secondary");
                            $(this).addClass("btn-info");
                            $(this).addClass("include-token-text-annotation");
                            $(this).html('<i class="fa fa-plus"></i>');
                            $(input_selector).hide();
                            $token_non_annotation_table.append($(this).parents('tr'));
                        }
                    }
                }
            });
            $token_text_annotation_toggle_cell.append($token_text_annotation_toggle);
        }
    }
}

/* Task: Token Text Annotation: Actions */

// Submit: Token Text Annotation
function submit_task_token_text_annotation(task_id) {
    console.log(`Called ${arguments.callee.name}(${Object.values(arguments).join(", ")});`);

    const $token_text_annotation_form = $(`#token-text-annotation-form-${task_id}`);
    const $token_text_annotation_table = $(`#token-text-annotation-table-${task_id}`);

    if (!$token_text_annotation_form[0].checkValidity()) {
        $token_text_annotation_form[0].reportValidity();
        return;
    }

    const task_category = TASK_TOKEN_TEXT_ANNOTATION;
    const verse_id = $verse_id_containers.html();

    var token_text_annotation_data = {}
    $token_text_annotation_table.find("input").each(function(input_index, input_element) {
        const token_id = input_element.id;
        const boundary_id = $(input_element).data("boundary-id");
        const token_text_annotation_text = $(input_element).val();
        token_text_annotation_data[token_id] = {
            'boundary_id': boundary_id,
            'text_annotation': token_text_annotation_text
        }
    });

    $.post(API_URL, {
        action: TASK_UPDATE_ACTIONS[task_category],
        task_id: task_id,
        verse_id: verse_id,
        text_annotation_data: JSON.stringify(token_text_annotation_data)
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
                $corpus_table.bootstrapTable('check', storage.getItem(KEY_NEXT_INDEX));
            }
        }
    });
};

/* ******************** END Task: Token Text Annotation ******************** */
