/* ************************** Graph Configuration ************************** */

const GRAPH_OPTIONS = {
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

/* **************************** Graph Functions **************************** */

function draw_graph(task_id, chapter_id) {
    const container = document.getElementById(`graph-${task_id}-${chapter_id}`);
    GRAPH_NETWORK[task_id][chapter_id] = new vis.Network(container, GRAPH_DATA[task_id][chapter_id], GRAPH_OPTIONS);

    // get a JSON object
    GRAPH_NETWORK[task_id][chapter_id].on("afterDrawing", function (ctx) {
        const data_url = ctx.canvas.toDataURL();
        $(`#graph-snapshot-button-${task_id}-${chapter_id}`).data("src", data_url);
    });
}

/* ********************************* Main ********************************* */

$(document).ready(function () {
    // Plot Graphs
    for (const task_id of Object.keys(GRAPH_DATA)) {
        console.log(task_id);
        for (const chapter_id of Object.keys(GRAPH_DATA[task_id])) {
            draw_graph(task_id, chapter_id);
        }
    }
});

/* *************************** Tan Change Events *************************** */

$('.task-tab[data-toggle="pill"]').on('shown.bs.tab', function (event) {
    const $active_tab = $(event.target);
    const task_id = $active_tab.data("task-id");
    const task_category = $active_tab.data("task-category");

    if ((task_category == TASK_TOKEN_GRAPH) || (task_category == TASK_SENTENCE_GRAPH)) {
        for (const chapter_id of Object.keys(GRAPH_DATA[task_id])) {
            GRAPH_NETWORK[task_id][chapter_id].fit();
        }
    }
});

/* **************************** Download Events **************************** */

// Text Download
$(".task-download").click(function() {
    const task_id = $(this).data("task-id");
    const task_category = $(this).data("task-category");
    const target_id = $(this).data("target");
    const chapter_id = $(this).data("chapter");
    const text_to_write = document.getElementById(target_id).innerText;
    const text_file_as_blob = new Blob([text_to_write], {type:'text/plain'});
    const filename_to_save_as = `${task_category}_${task_id}_${chapter_id}.txt`;

    const download_link = document.createElement("a");
    download_link.download = filename_to_save_as;
    download_link.innerHTML = "Download File";
    if (window.webkitURL != null)
    {
        // Chrome allows the link to be clicked
        // without actually adding it to the DOM.
        download_link.href = window.webkitURL.createObjectURL(text_file_as_blob);
    }
    else
    {
        // Firefox requires the link to be added to the DOM
        // before it can be clicked.
        download_link.href = window.URL.createObjectURL(text_file_as_blob);
        download_link.onclick = function(){
            document.body.removeChild(download_link);
        };
        download_link.style.display = "none";
        document.body.appendChild(download_link);
    }

    download_link.click();
});

// Graph Download
$(".graph-snapshot").click(function() {
    const $snapshot_button = $(this);
    const task_id = $snapshot_button.data("task-id");
    const task_category = $snapshot_button.data("task-category");
    const chapter_id = $snapshot_button.data("chapter");
    const download_anchor = document.createElement("a");
    download_anchor.href = $snapshot_button.data("src");
    download_anchor.download = `${task_category}_${task_id}_${chapter_id}.png`;
    document.body.appendChild(download_anchor);
    download_anchor.click();
    document.body.removeChild(download_anchor);
});
