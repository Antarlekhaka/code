/*
Frequently Used SQL Queries
Author: Hrishikesh Terdalkar
*/

/* Q1: Annotation Progress Report */
/* annotation progress per user per chapter */
select
    row_number() over(
        order by
            a.completed_tasks * 25 / b.total_verse_count desc,
            completed_tasks desc
    ) as idx,
    a.email,
    b.chapter_id,
    b.chapter_name,
    a.annotator_verse_count,
    b.total_verse_count,
    a.completed_tasks,
    a.completed_tasks * 25 / b.total_verse_count as percent_progress
from
    (
        /* group by user and chapter -- one row for every (user, chapter) */
        select
            email,
            chapter_id,
            count(verse_id) as annotator_verse_count,
            sum(progress) as completed_tasks
        from
            (
                /* group submit_log by verse and user one row for every (user, verse) */
                select
                    user.email,
                    submit_log.verse_id,
                    verse.chapter_id,
                    count(distinct(submit_log.task_id)) as progress,
                    max(submit_log.updated_at) as last_submit
                from
                    submit_log,
                    user,
                    verse
                where
                    user.id = submit_log.annotator_id
                    and submit_log.verse_id = verse.id
                group by
                    annotator_id,
                    verse_id
            )
        group by
            email,
            chapter_id
    ) as a,
    (
        select
            chapter_id,
            chapter.name as chapter_name,
            count(*) as total_verse_count
        from
            verse,
            chapter
        where
            chapter.id = verse.chapter_id
        group by
            chapter_id
    ) as b
where
    a.chapter_id = b.chapter_id
order by
    percent_progress desc,
    completed_tasks desc;