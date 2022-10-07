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

function row_attribute_handler(row, index) {
    return {}
}
