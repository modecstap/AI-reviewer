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
        - caution.json
        - conciseness.json
        - consistency.json
        - correctness.json
        - impersonality.json
        - literacy.json
        - objectivity.json
        - structure.json
    - 2
        - ...
    - ...
- report.json

article.docx - исходный текст статьи
refine - папка содержащая подпапки с главами. подпапки содержат {number}.txt файлы где number это номер параграфа. создаётся `ai_reviewer/splitter/`.
- id главы = имя её папки; это `place.chapter` в problems/*.json и `chapter` в report.json.
- текст до первого заголовка идёт в главу `Без заголовка`.
- chapters.json - главы в порядке документа: `[{"chapter": string, "title": string | null}]`, где chapter = имя папки, title = текст заголовка (`null` для `Без заголовка`).
problems - папка с подпапками прогонов ревью. каждый прогон (`AIPool.execute`, `ai_reviewer/ai_pool.py`) создаёт подпапку {N} = максимальный существующий номер + 1 (первая - `1`). в ней `article.txt` - размеченный текст, отданный агентам, и `<property>.json` только успешных агентов. .json файлы с найденными проблемами имеют общий формат:
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
                description: string
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

report.json - итоговый документ в формате
[
    {
        "chapter": string,
        "number": num,
        "problems": [
            {
                "scope": string,
                "quote": string,
                "types": [
                    {
                        "number": num,
                        "description": string
                    }
                ],
                "problem": string,
                "corrections": [
                    string,
                    ...
                ]
            },
            ...
        ],
    },
    ...
]
