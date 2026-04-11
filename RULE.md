# Machine Readable Skills — Specification

Machine Readable Skills are Claude Code skills that output structured JSON,
making them directly consumable by automated systems such as
[MyWant](https://github.com/onelittlenightmusic/mywant) want types via `onFetchData` JSON path mappings.

## Relation to AGENTS.md and AgentSkills

This format is a **superset of both**:

- **[AGENTS.md](https://Agents.md)** (Agentic AI Foundation / Linux Foundation) — a "README for agents"; no required fields, pure Markdown
- **[AgentSkills](https://Agentskills.md)** (originally by Anthropic, now open standard) — `SKILL.md` with required `name` + `description` frontmatter

```
AGENTS.md format  ⊂  AgentSkills (SKILL.md) format  ⊂  Machine Readable Skill format
```

Every Machine Readable Skill `SKILL.md` is a valid AgentSkills `SKILL.md`.
Every AgentSkills `SKILL.md` is a valid AGENTS.md file.
The Machine Readable Skills format adds JSON output requirements on top.

### Compatibility table

| Requirement | AGENTS.md | AgentSkills | Machine Readable Skills |
|---|---|---|---|
| Valid Markdown | required | required | required |
| `name` frontmatter | — | **required** | **required** |
| `description` frontmatter | — | **required** | **required** |
| File named `SKILL.md` | — | **required** | **required** |
| `name` matches directory name | — | required | required |
| `license` / `compatibility` / `metadata` | — | optional | optional |
| `## 出力JSON形式` section | — | — | **required** |
| Field description table | — | — | **required** |
| `### エラー時` section | — | — | **required** |
| `main.py` outputs only valid JSON | — | — | **required** |
| `AGENTS.md` at repo root | best practice | — | **required** |

---

## 1. Directory Structure

```
<skill-name>/
├── SKILL.md          # Required: AgentSkills-compliant descriptor + JSON output schema
└── main.py           # Executable entry point (outputs JSON to stdout)
AGENTS.md             # Project-level agent context (required per Agents.md spec)
RULE.md               # This file
README.md             # Human-facing documentation
```

The `name` field in `SKILL.md` frontmatter must match the parent directory name exactly.

---

## 2. SKILL.md Frontmatter

```yaml
---
name: <skill-name>           # Required (AgentSkills). Must match directory name.
description: <description>   # Required (AgentSkills). Max 1024 chars. Describe what
                             # the skill does AND when to use it, with specific keywords.
compatibility: ...           # Optional. Runtime requirements (Python version, system tools, etc.)
metadata:                    # Optional. Arbitrary key-value pairs.
  output-format: json
  json-schema: see "出力JSON形式" section below
---
```

---

## 3. stdout Must Be Valid JSON

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

## 4. Error Output Format

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

Any domain-specific fields should be included with safe empty defaults:

```json
{ "error": "ブラウザに接続できません", "count": 0, "emails": [] }
```

---

## 5. SKILL.md Body — Required Sections

```markdown
<!-- invocation instructions using ${CLAUDE_SKILL_DIR}/main.py -->

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

## 6. Portable Paths — Use `${CLAUDE_SKILL_DIR}`

`SKILL.md` must **not** contain hardcoded absolute paths.
Use `${CLAUDE_SKILL_DIR}` which resolves to the skill's directory at runtime:

```bash
# ✅ correct
python3 "${CLAUDE_SKILL_DIR}/main.py" $ARGUMENTS

# ❌ wrong
python3 /Users/someone/.mywant/skills/transit/main.py $ARGUMENTS
```

---

## 7. JSON Schema Stability

Field names in the output JSON are part of the public contract,
referenced by `onFetchData` JSON paths in MyWant want type definitions:

```yaml
state:
  - name: email_count
    onFetchData: "count"               # ← must match JSON key exactly
  - name: first_subject
    onFetchData: "emails[0].subject"   # ← dot-notation + array index
```

Supported syntax: `key`, `key.subkey`, `array[n]`, `array[n].key`, `a[n].b[m].c`

**Breaking changes to field names require a version bump (`metadata.version`).**

---

## 8. stderr Usage

stderr is for runtime warnings only (e.g. Node.js deprecation warnings).
Suppress at call sites:

```sh
OUTPUT=$(python3 "${CLAUDE_SKILL_DIR}/main.py" "$ARG" 2>/dev/null)
```

---

## 9. Skill Checklist

- [ ] Directory named with lowercase alphanumeric + hyphens (AgentSkills `name` rules)
- [ ] `SKILL.md` present (not `<skill-name>.md`)
- [ ] `name:` frontmatter matches directory name exactly
- [ ] `description:` frontmatter is non-empty and ≤ 1024 chars, includes when-to-use keywords
- [ ] `compatibility:` lists runtime requirements
- [ ] `SKILL.md` uses `${CLAUDE_SKILL_DIR}/main.py` — no hardcoded absolute paths
- [ ] `SKILL.md` contains `## 出力JSON形式` section with field table
- [ ] `SKILL.md` contains `### エラー時` section
- [ ] `main.py` outputs only valid JSON to stdout on success
- [ ] `main.py` outputs `{"error": "..."}` + exits non-zero on failure
- [ ] No human-readable text written to stdout
- [ ] Stderr warnings do not bleed into stdout
- [ ] Root `AGENTS.md` updated if new skill changes project overview
