# Machine Readable Skills — Specification

Machine Readable Skills are Claude Code skills that output structured JSON,
making them directly consumable by automated systems such as
[MyWant](https://github.com/onelittlenightmusic/mywant) want types via `onFetchData` JSON path mappings.

## Relation to AGENTS.md

This format is a **superset of [AGENTS.md](https://Agents.md)**
(Agentic AI Foundation / Linux Foundation open specification):

```
AGENTS.md format  ⊂  Machine Readable Skill format
```

- Every Machine Readable Skill descriptor (`<skill-name>.md`) is a valid AGENTS.md file.
- Not every AGENTS.md file is a Machine Readable Skill descriptor (the additional sections below are required).
- Repositories using this format must also have an `AGENTS.md` at the root per the spec.

### What AGENTS.md requires

The AGENTS.md spec has **no required fields** — it is pure Markdown used as a
"README for agents". Machine Readable Skills respect this by never violating Markdown structure
and by keeping all additional requirements additive (new sections, not new constraints on existing content).

### What Machine Readable Skills add

On top of the AGENTS.md baseline, this format requires:

| Addition | Where |
|---|---|
| Claude Code `description:` frontmatter | `<skill-name>.md` |
| `## 出力JSON形式` section with example JSON | `<skill-name>.md` |
| Field description table | `<skill-name>.md` |
| `### エラー時` section | `<skill-name>.md` |
| `main.py` outputting only valid JSON | `main.py` |
| `AGENTS.md` at repository root | repo root |

---

## 1. Directory Structure

```
<skill-name>/
├── <skill-name>.md   # Skill descriptor (AGENTS.md-compatible + Claude Code frontmatter + JSON schema)
└── main.py           # Executable entry point
AGENTS.md             # Project-level agent context (required per Agents.md spec)
RULE.md               # This file
README.md             # Human-facing documentation
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

The `.md` file serves three purposes:

1. **AGENTS.md context** — valid Markdown that AI agents can read for project context
2. **Claude Code skill definition** — frontmatter `description` and invocation instructions
3. **JSON schema documentation** — output contract for automated consumers

### Required structure

```markdown
---
description: <one-line description for Claude Code skill picker>
---

<!-- invocation instructions using ${CLAUDE_SKILL_DIR}/main.py — no hardcoded absolute paths -->

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

## 5. Portable Paths — Use `${CLAUDE_SKILL_DIR}`

Skill descriptors must **not** contain hardcoded absolute paths.
Use the Claude Code built-in variable `${CLAUDE_SKILL_DIR}` which resolves to
the directory containing the skill's `.md` file at runtime:

```bash
# ✅ correct — portable across installations
python3 "${CLAUDE_SKILL_DIR}/main.py" $ARGUMENTS

# ❌ wrong — breaks on any machine other than the original author's
python3 /Users/hiroyukiosaki/.mywant/skills/transit/main.py $ARGUMENTS
```

---

## 6. JSON Schema Stability

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
    onFetchData: "count"                  # ← must match JSON output key exactly

  - name: first_subject
    type: string
    label: current
    persistent: true
    initialValue: ""
    onFetchData: "emails[0].subject"      # ← dot-notation + array index supported
```

Supported JSON path syntax: `key`, `key.subkey`, `array[n]`, `array[n].key`, `a[n].b[m].c`

**Breaking changes to field names require a version bump in the skill descriptor.**

---

## 7. stderr Usage

stderr is for runtime warnings that do not affect the JSON output contract
(e.g. Node.js deprecation warnings from Playwright, debug logs).
Call sites should suppress stderr when consuming the skill programmatically:

```sh
OUTPUT=$(python3 "${CLAUDE_SKILL_DIR}/main.py" "$ARG" 2>/dev/null)
```

---

## 8. Skill Checklist

Before adding a new skill to this repository, verify:

- [ ] `main.py` outputs only valid JSON to stdout on success
- [ ] `main.py` outputs `{"error": "..."}` to stdout and exits non-zero on failure
- [ ] No human-readable text is written to stdout
- [ ] Stderr warnings do not bleed into stdout
- [ ] `<skill-name>.md` uses `${CLAUDE_SKILL_DIR}/main.py` — no hardcoded absolute paths
- [ ] `<skill-name>.md` contains the `## 出力JSON形式` section with field table
- [ ] `<skill-name>.md` contains the `### エラー時` section
- [ ] All output fields are documented and named stably
- [ ] The skill directory is named identically to the `.md` file and the Claude Code skill name
- [ ] `<skill-name>.md` is valid Markdown (AGENTS.md compatible)
- [ ] Root `AGENTS.md` updated if new skill changes the project overview
