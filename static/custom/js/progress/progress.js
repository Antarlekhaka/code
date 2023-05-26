/* ------------------------------- Elements ------------------------------- */

const $progress_table = $("#annotation-progress-viewer");

/* ----------------------------- Table Columns ----------------------------- */

const ANNOTATOR_TABLE_COLUMNS = [{
        field: "annotator_id",
        title: "ID",
        sortable: true,
    },
    {
        field: "annotator_email",
        title: "Email",
        sortable: true,
    },
    {
        field: "chapter_count",
        title: "Chapters",
        sortable: true,
    },
    {
        field: "verse_count",
        title: "Annotated Verses",
        sortable: true,
    },
    {
        field: "total_verse_count",
        title: "Total Verses",
        sortable: true,
    },
    {
        field: "task_count",
        title: "Tasks",
        cellStyle: task_count_style,
        formatter: task_count_formatter
    },
];

const ANNOTATOR_CHAPTER_TABLE_COLUMNS = [{
        field: "chapter_id",
        title: "Chapter ID",
        sortable: true,
    },
    {
        field: "chapter_name",
        title: "Chapter",
        sortable: true,
    },
    {
        field: "verse_count",
        title: "Annotated Verses",
        sortable: true,
    },
    {
        field: "total_verse_count",
        title: "Total Verses",
        sortable: true,
    },
    {
        field: "task_count",
        title: "Tasks",
        cellStyle: task_count_style,
        formatter: task_count_formatter
    }
];

const ANNOTATOR_CHAPTER_VERSE_TABLE_COLUMNS = [{
        field: "verse_id",
        title: "Verse ID",
        sortable: true,
    },
    {
        field: "task_list",
        title: "Tasks",
    },
    {
        field: "task_count",
        title: "Tasks",
        sortable: true,
    },
];


/* -------------------------------- Globals ------------------------------- */

var ANNOTATOR_DATA = [];
var ANNOTATOR_CHAPTERS = {};
var ANNOTATOR_CHAPTERS_VERSES = {};

/* ------------------------------- Functions ------------------------------- */

/* ----------------------------- Prepare Data ----------------------------- */

function prepare_data() {

    for (const [annotator_id, chapter_record] of Object.entries(PROGRESS)) {
        const annotator_email = USER[annotator_id].email;
        const annotator_chapter_count = Object.keys(chapter_record).length;
        ANNOTATOR_CHAPTERS_VERSES[annotator_id] = {};
        var annotator_verse_count = 0;
        var total_verse_count = 0;
        var annotator_tasks = {};
        var annotator_chapter_data = [];
        for (const [chapter_id, verse_record] of Object.entries(chapter_record)) {
            const annotator_chapter_verse_count = verse_record.length;
            const total_chapter_verse_count = CHAPTER[chapter_id].verse_count;
            const chapter_name = CHAPTER[chapter_id].chapter_name;
            annotator_verse_count += annotator_chapter_verse_count;
            total_verse_count += total_chapter_verse_count;
            var annotator_chapter_tasks = {};
            var annotator_chapter_verse_data = [];
            for (const verse_row of verse_record) {
                const verse_id = verse_row.verse_id;
                const task_list = verse_row.task_list.split(",").sort((x, y) => Number(x) - Number(y));
                for (const task_id of task_list) {
                    annotator_tasks[task_id] = (annotator_tasks[task_id] || 0) + 1;
                    annotator_chapter_tasks[task_id] = (annotator_chapter_tasks[task_id] || 0) + 1;
                }
                const task_count = verse_row.task_count;
                const first_update_at = verse_row.first_update_at;
                const last_update_at = verse_row.last_update_at;
                annotator_chapter_verse_data.push({
                    "verse_id": verse_id,
                    "task_list": task_list,
                    "task_count": task_count,
                });
            }
            ANNOTATOR_CHAPTERS_VERSES[annotator_id][chapter_id] = annotator_chapter_verse_data;
            annotator_chapter_data.push({
                "chapter_id": chapter_id,
                "chapter_name": chapter_name,
                "verse_count": annotator_chapter_verse_count,
                "total_verse_count": total_chapter_verse_count,
                "task_count": annotator_chapter_tasks
            });
        }
        annotator_chapter_data.sort((x, y) => y.verse_count - x.verse_count);
        ANNOTATOR_CHAPTERS[annotator_id] = annotator_chapter_data;
        ANNOTATOR_DATA.push({
            "annotator_id": annotator_id,
            "annotator_email": annotator_email,
            "chapter_count": annotator_chapter_count,
            "verse_count": annotator_verse_count,
            "total_verse_count": total_verse_count,
            "task_count": annotator_tasks
        });
    }

    ANNOTATOR_DATA.sort((x, y) => y.verse_count - x.verse_count);
}

/* --------------------------- Column Formatters --------------------------- */

function task_count_style(value, row, index) {
    return {classes: "p-0 m-0"};
}

function task_count_formatter(value, row) {
    var html = ['<table class="w-100">'];
    var total = 0;
    for (const [task_id, task_count] of Object.entries(value)) {
        total += task_count;
        html.push(`<tr><td>${TASK[task_id].title}</td><td>${task_count}</td></tr>`);
    }
    html.push(`<tr class="font-weight-bold"><td>Total</td><td>${total}</td></tr>`);
    html.push('</table>');
    return html.join("\n");
}

/* ----------------------------- Render Tables ----------------------------- */

const COMMON_TABLE_OPTIONS = {
    search: true,
    searchHighlight: true,
    showColumns: true,
    pagination: true,
    pageList: [10, 20, 30, 50, 100],
    showJumpTo: true,
    showJumpToByPages: 20,
    stickyHeader: true,
    stickyHeaderOffsetLeft: 0,
    stickyHeaderOffsetRight: 0,
    showExport: true,
    exportTypes: ['csv', 'json', 'txt'],
}

function make_annotator_table($target) {
    $target.bootstrapTable('destroy');
    $target.bootstrapTable({
        columns: ANNOTATOR_TABLE_COLUMNS,
        data: ANNOTATOR_DATA,
        toolbar: "#annotation-progress-toolbar",
        ...COMMON_TABLE_OPTIONS,
        exportOptions: {
            fileName: () => 'progress',
        },
        detailView: true,
        detailViewIcon: true,
        detailViewByClick: true,
        onExpandRow: function (index, row, $detail) {
            const annotator_id = row.annotator_id;
            // toolbar
            const $toolbar = $("<div />", {id: `annotator-${annotator_id}-progress-toolbar`});
            const $title = $("<h5 />", {html: `Chapter-wise Annotation Progress`});
            $detail.append($toolbar);
            $toolbar.append($title);
            // table
            const $table = $('<table />');
            $table.attr("id", `annotation-progress-${annotator_id}`);
            $detail.append($table);
            make_annotator_chapter_table($table, annotator_id);
        },
    });
}

function make_annotator_chapter_table($target, annotator_id) {
    $target.bootstrapTable('destroy');
    $target.bootstrapTable({
        columns: ANNOTATOR_CHAPTER_TABLE_COLUMNS,
        data: ANNOTATOR_CHAPTERS[annotator_id],
        toolbar: `#annotator-${annotator_id}-progress-toolbar`,
        ...COMMON_TABLE_OPTIONS,
        exportOptions: {
            fileName: () => `progress_${annotator_id}_chapters`
        },
        detailView: true,
        detailViewIcon: true,
        detailViewByClick: true,
        onExpandRow: function (index, row, $detail) {
            const chapter_id = row.chapter_id;
            // toolbar
            const $toolbar = $("<div />", {id: `annotator-${annotator_id}-chapter-${chapter_id}-progress-toolbar`});
            const $title = $("<h5 />", {html: `Verse-wise Annotation Progress`});
            $detail.append($toolbar);
            $toolbar.append($title);
            // title
            const $table = $('<table />');
            $table.attr("id", `annotation-progress-${annotator_id}-${chapter_id}`);
            $detail.append($table);
            make_annotator_chapter_verse_table($table, annotator_id, chapter_id);
        },
    });
}

function make_annotator_chapter_verse_table($target, annotator_id, chapter_id) {
    $target.bootstrapTable('destroy');
    $target.bootstrapTable({
        columns: ANNOTATOR_CHAPTER_VERSE_TABLE_COLUMNS,
        data: ANNOTATOR_CHAPTERS_VERSES[annotator_id][chapter_id],
        toolbar: `#annotator-${annotator_id}-chapter-${chapter_id}-progress-toolbar`,
        ...COMMON_TABLE_OPTIONS,
        detailView: false,
        exportOptions: {
            fileName: () => `progress_${annotator_id}_chapter_${chapter_id}_verses`
        },
    });
}

/* --------------------------------- Main --------------------------------- */

$(document).ready(function () {
    prepare_data();
    make_annotator_table($progress_table, "Annotator Progress");
});

/* ------------------------------------------------------------------------ */
