создать сервер предоставляющий API для создания рецензии на статью содержащую претензии к её тексту разбитые по параграфам.
при получении файла программа запускает AI агенты которые проверяют статью на соответствие свойствам академичности и составляют файлы с отчётами по своей области. после того как все агенты вернут отчёты собирается отчёт по статье где на каждый параграф к главе собираются претензии по различным свойствам.

формат файловой структуры для каждой статьи:
- article.docx
- refine
    - chapters.json
    - first chapter name
        - 1.txt
        - 2.txt
        - ...
    - second chapter name
        - ...
    - ...
- problems
    - 1
        - article.txt
        - Caution.json
        - Conciseness.json
        - Consistency.json
        - Correctness.json
        - Impersonality.json
        - Literacy.json
        - Objectivity.json
        - Structure.json
        - report.json
        - report.html
        - report.css
        - report.pdf
    - 2
        - ...
    - ...

article.docx - исходный текст статьи
refine - папка содержащая подпапки с главами. подпапки содержат {number}.txt файлы где number это номер параграфа. создаётся `ai_reviewer/splitter/`.
- id главы = имя её папки; это `place.chapter` в problems/*.json и `chapter` в report.json.
- текст до первого заголовка идёт в главу `Без заголовка`.
- chapters.json - главы в порядке документа: `[{"chapter": string, "title": string | null}]`, где chapter = имя папки, title = текст заголовка (`null` для `Без заголовка`).
problems - папка с подпапками прогонов ревью. каждый прогон (`AIPool.execute`, `ai_reviewer/ai_pool/`) создаёт подпапку {N} = максимальный существующий номер + 1 (первая - `1`). в ней `article.txt` - размеченный текст, отданный агентам, и `<property>.json` только успешных агентов, где `<property>` - `AgentDefinition.name` (например `Caution`). после сборки отчёта в ней же лежит `report.json`. .json файлы с найденными проблемами имеют общий формат:
[
    {
        place: {
            chapter: string,
            paragraph: num
        },
        quote: string,
        types: [
            {
                number: num,
                name: string
            },
            ...
        ],
        problem: string
        corrections: [
            string,
            ...
        ]
    },
]

report.json - итоговый документ прогона в `problems/<N>/`. собирается `ai_reviewer/report/` из `article.txt` и файлов свойств этой папки в формате
[
    {
        "chapter": string,
        "claims": [
            {
                "paragraph": num,
                "<property>": [
                    {quote: string, types: [{number: num, name: string}, ...], problem: string, corrections: [string, ...]},
                    ...
                ],
                ...
            },
            ...
        ]
    },
    ...
]
- претензия - все поля исходного элемента файла свойства, кроме `place`.
- ключ свойства, параграф и глава без претензий не пишутся; нет претензий - файл равен `[]`.
- главы идут в порядке `article.txt`, параграфы - по возрастанию, ключи свойств - по алфавиту, претензии свойства - в порядке его файла.
- одинаковые цитаты разных свойств не сливаются.
- претензии с неверным `place` (нет главы или параграфа в `article.txt`) и битые файлы свойств пропускаются с warning.
- UTF-8, кириллица хранится как есть.

report.html, report.css, report.pdf - печатная версия report.json. пишет `PrintedReportWriter` (`ai_reviewer/printed_report_writer.py`) через `ai_reviewer/report/printer/`. report.html - HTML-фрагмент, report.css - его стили (шрифты указаны как `fonts/…` относительно CSS), report.pdf - PDF, собранный WeasyPrint из этих HTML и CSS плюс разрывы страниц перед параграфами, вычисленные при сборке PDF (в report.css их нет). титульная страница: VSRT, AI-Reviewer, дата создания, число претензий всего и список свойств с числом претензий. дальше каждая глава с новой страницы: слева текст параграфа, где цитаты его претензий выделены заливкой, справа его претензии. параграф, чья подпись и текст не влезают в остаток страницы, начинается с новой страницы; претензии не учитываются, первый параграф главы остаётся под заголовком, текст длиннее страницы разрывается. имена свойств и типов печатаются на языке печати (`ReportLabels`): русские берутся из словаря в `labels.py` по ключу свойства и номеру типа, без перевода печатается исходное имя из report.json.
