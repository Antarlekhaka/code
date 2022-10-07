function response_handler(response) {
    $('#corpus-title').html(response.title);
    return response.data;
}

function generic_row_detail_formatter(index, row) {
    var html = [];

    var rows = {};
    if(!row.display) {
        html.push('<tr><td>No details available.</td></tr>');
    } else {
        for (const display of row.display) {
            html.push('<div class="table-responsive">')
            html.push('<table class="table table-striped">');
            var first_word = display[0];
            for (const k in first_word) {
                if (k == "ID") {
                    continue;
                }
                rows[k] = [];
            }
            for (const word of display) {
                for (const [k, v] of Object.entries(word)) {
                    if (k == "ID") {
                        continue;
                    }
                    rows[k].push(v);
                }
            }
            for (const [name, data] of Object.entries(rows)) {
                html.push(`<tr><th scope="row">${name}</th><td>${data.join("</td><td>")}</td></tr>`);
            }
            html.push('</table>');
            html.push('</div>');
        }
    }
    return html.join("\n");
}

function column_progress_formatter(progress_value, row) {;
    const percent = Math.round(progress_value.length / 7 * 100);
    const title = []
    for (const task of progress_value) {
        title.push(`Task ${task.task_short} - ${task.updated_at}`);
    }
    if (title.length == 0) {
        title.push("No progress")
    }

    const $progress_bar_container = $("<div />", {
        class: "progress",
        title: title.join("\n")
    });
    const $progress_bar = $("<div />", {
        class: "progress-bar progress-bar-striped bg-success",
        role: "progressbar",
        style: `width: ${percent}%`
    });
    $progress_bar.attr("aria-valuenow", percent);
    $progress_bar.attr("aria-valuemin", "0");
    $progress_bar.attr("aria-valuemax", "100");
    $progress_bar_container.append($progress_bar);
    return $progress_bar_container.wrapAll("<div>").parent().html();
}

function column_text_formatter(value, row, index, field) {
    return value.join("<br>");
}

// function entity_formatter(root, type, li_classes = "", annotator = "") {
//     var entity_value = [root, type].join('$');
//     var li_class = 'list-group-item';
//     if (li_classes !== "") {
//         li_class += " " + li_classes;
//     }
//     var entity_html = [
//         annotator ? `<li title="${annotator}" class="${li_class}">` : `<li class="${li_class}">`,
//         '<div class="row">',
//         `<div class="col-sm-4">${root}</div>`,
//         `<div class="col-sm-4 text-secondary">${type}</div>`,
//         '<div class="col-sm-4">',
//         '<span class="float-right">',
//         `<input type="checkbox" name="entity" value="${entity_value}" class="mr-5"`,
//         ' data-toggle="toggle" data-size="sm" data-on="<i class=\'fa fa-check\'></i>" ',
//         ' data-off="<i class=\'fa fa-times\'></i>" data-onstyle="success"',
//         ' data-offstyle="danger" checked>',
//         '</span>',
//         '</div>',
//         '</div>',
//         '</li>'
//     ];
//     return entity_html.join("");
// }

// function unnamed_formatter(line_id, text) {
//     // 'unnamed_prefix' is a global constant
//     // It must be set before running this function
//     // It is set in corpus.html
//     var upper_text = text.toUpperCase();
//     var pattern = new RegExp('^'+ unnamed_prefix +'[0-9]$');
//     if (upper_text.match(pattern)) {
//         return upper_text + '-' + line_id;
//     }
//     return text;
// }

// function relation_formatter(source, label, target, detail, li_classes = "", annotator = "") {
//     if (detail == null) {
//         detail = "";
//     }
//     var relation_value = [source, label, target, detail].join('$');
//     var li_class = 'list-group-item';
//     if (li_classes !== "") {
//         li_class += " " + li_classes;
//     }
//     var relation_html = [
//         annotator ? `<li title="${annotator}" class="${li_class}">` : `<li class="${li_class}">`,
//         '<div class="row">',
//         '<div class="col-sm">',
//         `(${source})`,
//         ` <span class="text-muted">⊢ [${label} (${detail})] →</span> `,
//         `(${target})`,
//         '</div>',
//         '<div class="col-sm-3">',
//         '<span class="float-right">',
//         `<input type="checkbox" name="relation" value="${relation_value}" class="mr-5"`,
//         ' data-toggle="toggle" data-size="sm" data-on="<i class=\'fa fa-check\'></i>" ',
//         ' data-off="<i class=\'fa fa-times\'></i>" data-onstyle="success"',
//         ' data-offstyle="danger" checked>',
//         '</span>',
//         '</div>',
//         '</div>',
//         '</li>'
//     ];
//     return relation_html.join("");
// }

// function action_formatter(label, actor_label, actor, li_classes = "", annotator = "") {
//     var action_value = [label, actor_label, actor].join('$');
//     var li_class = 'list-group-item';
//     if (li_classes !== "") {
//         li_class += " " + li_classes;
//     }
//     var action_html = [
//         annotator ? `<li title="${annotator}" class="${li_class}">` : `<li class="${li_class}">`,
//         '<div class="row">',
//         '<div class="col-sm">',
//         `(${label})`,
//         ` <span class="text-muted">⊢ [${actor_label}] →</span> `,
//         `(${actor})`,
//         '</div>',
//         '<div class="col-sm-3">',
//         '<span class="float-right">',
//         `<input type="checkbox" name="action" value="${action_value}" class="mr-5"`,
//         ' data-toggle="toggle" data-size="sm" data-on="<i class=\'fa fa-check\'></i>" ',
//         ' data-off="<i class=\'fa fa-times\'></i>" data-onstyle="success"',
//         ' data-offstyle="danger" checked>',
//         '</span>',
//         '</div>',
//         '</div>',
//         '</li>'
//     ];
//     return action_html.join("");
// }

function row_attribute_handler(row, index) {
    return {}
}
