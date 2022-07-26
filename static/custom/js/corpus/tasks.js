function setup_anvaya(verse_id) {
    const row = $corpus_table.bootstrapTable('getRowByUniqueId', verse_id);

    $task_2_anvaya_container.html("");
    for (const [boundary_id, sentence_tokens] of Object.entries(row.sentences)) {
        var $sentence = $("<div>", {
            id: `boundary-${boundary_id}`,
            class: "sortable border border-success px-1 pt-1 m-1 rounded"
        });
        var $unused = $("<div>", {
            id: `unused-${boundary_id}`,
            class: "border border-danger px-1 pt-1 m-1 rounded"
        })
        $task_2_anvaya_container.append($sentence);
        $task_2_anvaya_container.append($unused);

        console.log(row);
        const token_order = row.anvaya[boundary_id] || Object.keys(sentence_tokens);
        console.log("Token Order:");
        console.log(token_order);
        for (const token_id of token_order) {
            const token = sentence_tokens[token_id];
            var token_class = "btn btn-light";
            var token_text = token.text;

            if (token.text === "_") {
                token_class = "btn btn-warning";
                token_text = token.analysis.unsandhied;
            }
            const $token_button = $("<div>", {
                id: `token-button-${token.id}`,
                role: "group",
                class: "btn-group mr-1 mb-1",
            });
            $sentence.append($token_button);

            const $token = $("<span>", {
                id: `token-${token.id}`,
                class: token_class,
                title: `ID: ${token.id}\nText:${token.text}\nLemma: ${token.lemma}\nPadapāṭha: ${token.analysis.unsandhied}`,
                html: token_text
            });
            $token_button.append($token);

            const $token_toggle = $("<span>", {
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
                    }
                }
            });
            $token_button.append($token_toggle);
        };
    }
    setup_sortable();
}

function setup_named_entity(verse_id) {
    const row = $corpus_table.bootstrapTable('getRowByUniqueId', verse_id);

    $task_3_entity_table.html("");
    $task_3_non_entity_table.html("");

    for (const line_tokens  of row.tokens) {
        for (const token of line_tokens) {
            const $entity_row = $("<tr>", {});
            $task_3_entity_table.append($entity_row);

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
            $entity_selector_element.attr("id", entity_selector_id),
            $entity_selector_element.selectpicker();

            const $entity_toggle_cell = $("<td>", {
                class: "col-sm-1",
            });
            $entity_row.append($entity_toggle_cell);

            const $entity_toggle = $("<span>", {
                id: `entity-toggle-${token.id}`,
                name: "entity-toggle",
                class: "btn btn-secondary exclude-entity",
                html: '<i class="fa fa-times"></i>',
                on: {
                    click: function() {
                        const select_selector = `#${entity_selector_id}`;

                        if ($(this).hasClass("exclude-entity")) {
                            $(this).removeClass("exclude-entity");
                            $(this).removeClass("btn-secondary");
                            $(this).addClass("btn-info");
                            $(this).html('<i class="fa fa-plus"></i>');
                            $(select_selector).selectpicker('hide');
                            $task_3_non_entity_table.append($(this).parents('tr'));
                        } else {
                            $(this).removeClass("btn-info");
                            $(this).addClass("btn-secondary");
                            $(this).addClass("exclude-entity");
                            $(this).html('<i class="fa fa-times"></i>');
                            $(select_selector).selectpicker('show');
                            $task_3_entity_table.append($(this).parents('tr'));
                        }
                    }
                }
            });
            $entity_toggle_cell.append($entity_toggle);
        }
    }
}