# Machine Readable Skills — Rules

Machine Readable Skills are Claude Code skills that output structured JSON,
making them directly consumable by automated systems such as
[MyWant](https://github.com/onelittlenightmusic/mywant) want types via `onFetchData` JSON path mappings.

---

## 1. Directory Structure

Each skill lives in its own directory:

```
<skill-name>/
├── <skill-name>.md   # Skill descriptor (Claude Code skill definition + JSON schema)
└── main.py           # Executable entry point
```

---

## 2. stdout Must Be Valid JSON

The script **must** output a single valid JSON object to stdout and nothing else.

```python
# ✅ correct
print(json.dumps(result, ensure_ascii=False))

# ❌ wrong — plain text breaks automated consumers
print("処理が完了しました")
```

Diagnostic messages, progress logs, and third-party warnings must go to **stderr** only,
or be suppressed (e.g. `2>/dev/null` at the call site).

---

## 3. Error Output Format

On failure the script must output a JSON object containing an `"error"` key
and exit with a **non-zero** exit code.

```json
{ "error": "エラーの説明文" }
```

```python
def error_out(message: str) -> None:
    print(json.dumps({"error": message}, ensure_ascii=False))
    sys.exit(1)
```

Any domain-specific fields should be included with safe empty defaults so that
consumers can always parse the output regardless of success or failure:

```json
{ "error": "ブラウザに接続できません", "count": 0, "emails": [] }
```

---

## 4. Skill Descriptor (`<skill-name>.md`)

The `.md` file serves dual purpose:

1. **Claude Code skill definition** — frontmatter `description` and invocation instructions
2. **JSON schema documentation** — so both humans and want-type authors know the output contract

### Required sections

```markdown
---
description: <one-line description for Claude Code skill picker>
---

<!-- invocation instructions -->

## 出力JSON形式

​```json
{ ... example output ... }
​```

### フィールド説明

| フィールド | 型 | 説明 |
|---|---|---|
| `field` | type | description |

### エラー時

​```json
{ "error": "エラーメッセージ" }
​```
```

---

## 5. JSON Schema Stability

Field names in the output JSON are part of the public contract.
They are referenced by `onFetchData` JSON paths in MyWant want type definitions:

```yaml
# want type YAML example
state:
  - name: email_count
    type: int
    label: current
    persistent: true
    initialValue: 0
    onFetchData: "count"          # ← must match JSON output key exactly

  - name: first_subject
    type: string
    label: current
    persistent: true
    initialValue: ""
    onFetchData: "emails[0].subject"   # ← dot-notation + array index supported
```

Supported JSON path syntax: `key`, `key.subkey`, `array[n]`, `array[n].key`, `a[n].b[m].c`

**Breaking changes to field names require a version bump in the skill descriptor.**

---

## 6. stderr Usage

stderr is for runtime warnings that do not affect the JSON output contract
(e.g. Node.js deprecation warnings from Playwright, debug logs).
Call sites should suppress stderr when consuming the skill programmatically:

```sh
OUTPUT=$(python3 main.py "$ARG" 2>/dev/null)
```

---

## 7. Skill Checklist

Before adding a new skill to this repository, verify:

- [ ] `main.py` outputs only valid JSON to stdout on success
- [ ] `main.py` outputs `{"error": "..."}` to stdout and exits non-zero on failure
- [ ] No human-readable text is written to stdout
- [ ] Stderr warnings do not bleed into stdout
- [ ] `<skill-name>.md` contains the `## 出力JSON形式` section with field table
- [ ] All output fields are documented and named stably
- [ ] The skill directory is named identically to the `.md` file and the Claude Code skill name
