# Input and output

## Input

The agent receives the full text of the article in the following format:

```text
!! chapter: string
!! paragraph: 1
paragraph text...

!! paragraph: 2
paragraph text...

!! chapter: string
!! paragraph: 1
paragraph text...
```

### Input data structure

* `chapter` — the title of the article chapter.
* `paragraph` — the ordinal number of the paragraph within the corresponding chapter.
* The line `!! paragraph: N` is followed by the full text of the corresponding paragraph.
* Paragraph numbering starts at `1` and is kept separately for each chapter.
* The article may contain any number of chapters and paragraphs.

The agent is also provided with:

* `reference.md`;
* `instruction.md`.

## Output

The result must be valid JSON only, without Markdown, comments, explanations, or any other text outside the JSON.
The root element of the result is an array of objects.
The file must be named {assessed property}.json
Each object describes one place in the article that contains one or more violations.

Format:
```json
[
  {
    "place": {
      "chapter": "string",
      "paragraph": 1
    },
    "quote": "string",
    "types": [
      {
        "number": 1,
        "name": "string"
      }
    ],
    "problem": "string"
  }
]
```

### Object fields

#### `place`
An object that indicates the location of the violation found.
* `chapter` — the exact chapter title from the input text.
* `paragraph` — the paragraph number from the input text.
```json
"place": {
  "chapter": "Introduction",
  "paragraph": 3
}
```

#### `quote`
An exact quote from the source text of the article.
Requirements:
* the quote must match the article text verbatim;
* the quote must not be corrected, paraphrased, or altered;
* the quote must be a continuous fragment of the source text;
* the quote must contain the minimal fragment needed to identify the violation.

#### `types`
An array of violation types related to this quote.
Each element contains:
* `number` — the violation type number according to `reference.md`;
* `name` — the exact violation type name according to `reference.md`.
If one quote contains several violation types, all of them are listed in a single `types` array.

#### `problem`
One human-readable description of the problem found in the given quote.
It states what violates the norm and then says in words what must change to fix it: the fix hint.
The fix hint names the change. It does not give a ready replacement wording of the quote.
If the quote contains several violation types, all the issues with it are combined into a single `problem` value.

All content string values (`quote`, `problem`) must be written in the language of the corresponding article fragment.

### Grouping rules
If the same quote contains several violations, **one object** is created, and all violation types are listed in its `types` field.
If violations relate to different quotes, separate objects are created for them.

### No violations
If the article has no violations, the result must be an empty array:
```json
[]
```

### Format constraints
Each result object must contain only the following fields:
* `place`;
* `quote`;
* `types`;
* `problem`.
Inside `place`, only the following are allowed:
* `chapter`;
* `paragraph`.
Inside each `types` element, only the following are allowed:
* `number`;
* `name`.
Do not add extra fields.
The result must be syntactically valid JSON.
