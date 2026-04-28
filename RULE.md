# Machine Readable Skills — Specification

Machine Readable Skills are Claude Code skills that output structured JSON,
making them directly consumable by automated systems such as
[MyWant](https://github.com/onelittlenightmusic/mywant) want types via `onFetchData` JSON path mappings.

## Relation to AgentSkills

This format is a **superset of [AgentSkills](https://Agentskills.md)**:

- **[AgentSkills](https://Agentskills.md)** (originally by Anthropic, now open standard) — `SKILL.md` with required `name` + `description` frontmatter

```
AgentSkills (SKILL.md) format  ⊂  Machine Readable Skill format
```

Every Machine Readable Skill `SKILL.md` is a valid AgentSkills `SKILL.md`.
The Machine Readable Skills format adds JSON output requirements and MyWant want type generation rules on top.

### Compatibility table

| Requirement | AgentSkills | Machine Readable Skills |
|---|---|---|
| Valid Markdown | required | required |
| `name` frontmatter | **required** | **required** |
| `description` frontmatter | **required** | **required** |
| File named `SKILL.md` | **required** | **required** |
| `name` matches directory name | required | required |
| `license` / `compatibility` / `metadata` | optional | optional |
| `## 実行特性` section | — | **required** |
| `## パラメータ` section | — | required if parameterized |
| `## 出力フィールド` section | — | **required** |
| `## エラー時` section | — | **required** |
| `main.py` outputs only valid JSON | — | **required** |
| `agent.yaml` present in directory | — | **required** |

---

## 1. Directory Structure

```
<skill-name>/
├── SKILL.md          # Required: AgentSkills-compliant descriptor + JSON output schema
├── main.py           # Executable entry point (outputs JSON to stdout)
└── agent.yaml        # Required: MRS plugin agent declaration (capability + state_updates)
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
compatibility:               # Optional. Runtime requirements.
  python: ">=3.10"
  requires:
    - playwright (sync_api)
    - Chrome with remote debugging on port 9222
metadata:                    # Optional. Controls want type YAML generation.
  output-format: json        # json (default) | agent-based
  type-name: <snake_case>    # Generated want type name. Defaults to name slug.
  category: <category>       # Want type category. Inferred from name/description if omitted.
  final-result-field: <field> # State field to use as finalResultField. Auto-selected if omitted.
---
```

### `metadata` field reference

| Field | Default when omitted | Effect on generated YAML |
|---|---|---|
| `output-format` | `json` | `json` → MRS agent-based generation. `agent-based` → skip YAML generation. |
| `type-name` | Slug of `name` (e.g. `mywant-foo-plugin` → `foo`) | `wantType.metadata.name` |
| `category` | Inferred from name/description keywords | `wantType.metadata.category` |
| `final-result-field` | First `永続化: true` field in `## 出力フィールド` | `wantType.finalResultField` |

---

## 3. `agent.yaml` — Plugin Agent Declaration

Each skill directory must contain an `agent.yaml` that registers a plugin agent into the MyWant
`AgentRegistry`. The engine loads these automatically at startup from `~/.mywant/custom-types/`.

### Format

```yaml
agent:
  metadata:
    name: <agent-name>           # Unique agent identifier (snake_case)
    capability: <capability>     # Capability name referenced by want type's `requires`
    type: do | monitor           # do → foreground, monitor → background
  script:
    path: ./main.py              # Relative to this directory
    timeout_seconds: 120         # Max execution time
  state_updates:                 # Output fields extracted directly from script JSON
    - name: <field-name>
      type: string | int | float | bool | object
      label: current
      persistent: true | false
      onFetchData: "<json-path>"  # Dot-notation path into script output (e.g. "routes[0].summary")
```

### Rules

| Field | Rule |
|---|---|
| `metadata.capability` | Must match the value used in `requires:` in the want type YAML |
| `metadata.type` | `do` for `実行モデル: foreground`, `monitor` for `実行モデル: background` |
| `script.path` | Relative path from the skill directory; `./main.py` is standard |
| `state_updates[].onFetchData` | Same JSON path as `onFetchData` in the old `fetchFrom: mrs_raw_output` pattern |
| `state_updates[].name` | Must match the field name declared in the want type's `state` block |

### `onFetchData` path syntax

| Syntax | Example | Meaning |
|---|---|---|
| top-level key | `"status"` | `output["status"]` |
| nested key | `"confirmation.service"` | `output["confirmation"]["service"]` |
| array index | `"routes[0].summary"` | `output["routes"][0]["summary"]` |
| deep nested | `"routes[0].legs[0].line"` | `output["routes"][0]["legs"][0]["line"]` |

### Example — foreground (do) agent

```yaml
agent:
  metadata:
    name: smartgolf_book_agent
    capability: smartgolf_book
    type: do
  script:
    path: ./main.py
    timeout_seconds: 120
  state_updates:
    - name: summary
      type: string
      label: current
      persistent: true
      onFetchData: "summary"
    - name: reservation_datetime
      type: string
      label: current
      persistent: true
      onFetchData: "confirmation.reservation_datetime"
```

### Example — background (monitor) agent

```yaml
agent:
  metadata:
    name: smartgolf_list_available_agent
    capability: smartgolf_list_available
    type: monitor
  script:
    path: ./main.py
    timeout_seconds: 120
  state_updates:
    - name: smartgolf_all_available_times
      type: object
      label: current
      persistent: true
      onFetchData: "available_times"
    - name: first_room
      type: string
      label: current
      persistent: true
      onFetchData: "available_times[0].room"
```

---

## 4. stdout Protocol

The script **must** output a valid JSON object to stdout as its final result.
Before the final result, it may emit **progress report lines** to report intermediate status in real time.

### 4.1 Progress reporting

```python
def report_progress(percentage: int, message: str = "") -> None:
    print(json.dumps({"_progress": percentage, "_message": message}, ensure_ascii=False), flush=True)
```

Progress lines use the reserved key `_progress` (integer, 0–100) and optional `_message` (string).
The engine reads these in real time and updates `achieving_percentage` and `summary` in the want state.

```python
# ✅ correct — progress lines before final result
report_progress(5,  "ブラウザ起動中")
report_progress(20, "ページ読み込み中")
report_progress(80, "データ取得中")
report_progress(100, "Done")
print(json.dumps(result, ensure_ascii=False), flush=True)
```

### 4.2 Final result

The **last non-progress JSON line** is used as the final result and stored in `mrs_raw_output`.
All `state_updates` `onFetchData` paths are evaluated against this object.

```python
# ❌ wrong — plain text breaks automated consumers
print("処理が完了しました")

# ❌ wrong — flush=True missing (output may not arrive until process exits)
print(json.dumps(result, ensure_ascii=False))

# ❌ wrong — _progress key must not appear in final result
print(json.dumps({"_progress": 100, "routes": [...]}, ensure_ascii=False))
```

Non-JSON lines and blank lines are silently ignored.
Diagnostic messages must go to **stderr** only.

### 4.3 `ImportError` guard

Wrap the `playwright` import (and any other optional heavy dependency) at the module level so the
script can report a useful JSON error even when the library is not installed:

```python
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print(json.dumps({
        "error": "playwright module not found. Install with: pip3 install playwright && playwright install chromium"
    }, ensure_ascii=False), flush=True)
    sys.exit(1)
```

---

## 5. Error Output Format

On failure the script must output a JSON object containing an `"error"` key
and exit with a **non-zero** exit code.

```json
{ "error": "エラーの説明文" }
```

```python
def error_out(message: str) -> None:
    print(json.dumps({"error": message}, ensure_ascii=False), flush=True)
    sys.exit(1)
```

Any domain-specific fields should be included with safe empty defaults:

```json
{ "error": "ブラウザに接続できません", "count": 0, "emails": [] }
```

---

## 6. SKILL.md Body — Required Sections

### 6.1 `## 実行特性` (required)

Declares the execution model. This single field mechanically determines `child-role` and which MRS agent to use.

```markdown
## 実行特性

| 項目 | 値 | 説明 |
|---|---|---|
| 実行モデル | `foreground` | トリガーされて1回実行し完了する |
```

**Allowed values:**

| 値 | Meaning | → child-role | → agent.yaml type | → requires |
|---|---|---|---|---|
| `foreground` | Triggered externally, runs once and completes | `doer` | `do` | `<capability>` (e.g. `transit_search`) |
| `background` | Runs autonomously and repeatedly in the background | `monitor` | `monitor` | `<capability>` (e.g. `gmail_list_unread`) |

The value of `実行モデル` alone fully determines `child-role`, `agent.yaml` type, and `requires`.

---

### 6.2 `## パラメータ` (required if the skill takes arguments)

Describes input parameters. Each row becomes a `parameters[]` entry and a mirrored `state` field.

```markdown
## パラメータ

| フィールド | 型 | 必須 | デフォルト | 説明 |
|---|---|---|---|---|
| `room` | string | ✓ | — | 部屋名（例: 中野新橋店/打席予約(Room02)） |
| `date` | string | ✓ | — | 日付（YYYY-MM-DD形式、JST） |
| `time` | string | — | (グローバルパラメータ from: time_global_param) | 時刻（HH:MM形式、JST） |
| `time_global_param` | string | — | `selected_slot` | time のデフォルト参照先となるグローバルパラメータキー |
```

**Column spec:**

| Column | Required | Content |
|---|---|---|
| `フィールド` | ✓ | Parameter name in backticks |
| `型` | ✓ | `string` / `int` / `float` / `bool` / `object` / `array` |
| `必須` | ✓ | `✓` = `required: true`, blank or `—` = `required: false` |
| `デフォルト` | — | Literal value, or global parameter syntax (see below) |
| `説明` | ✓ | Human-readable description |

**Type mapping (SKILL.md → YAML):**

| SKILL.md type | YAML `type` |
|---|---|
| `string` | `string` |
| `number` / `float` | `float64` |
| `integer` / `int` | `int` |
| `boolean` / `bool` | `bool` |
| `object` | `object` |
| `array` / `[]T` | `[]string` or `[]interface{}` |

**Global parameter syntax in `デフォルト` column:**

| Notation | Generated YAML field |
|---|---|
| `(グローバルパラメータ: selected_slot)` | `defaultGlobalParameter: selected_slot` |
| `(グローバルパラメータ from: time_global_param)` | `defaultGlobalParameterFrom: time_global_param` |

`defaultGlobalParameterFrom` reads another parameter's value as the global parameter key (indirect lookup). Use it when the global parameter name itself should be configurable.

---

### 6.3 `## 出力フィールド` (required)

Describes each field in the JSON output. Each row becomes a `state_updates` entry in `agent.yaml` (with `onFetchData`) and a corresponding field declaration in the want type `state` block (without `fetchFrom`/`onFetchData`).

```markdown
## 出力フィールド

| フィールド名 | 型 | JSONパス | 永続化 | 説明 |
|---|---|---|---|---|
| `reservation_datetime` | string | `confirmation.reservation_datetime` | true | 予約日時テキスト |
| `service`              | string | `confirmation.service`              | true | 店舗名 |
| `payment`              | string | `confirmation.payment`              | true | 支払い方法 |
```

**Column spec:**

| Column | Required | Content |
|---|---|---|
| `フィールド名` | ✓ | State field name in backticks |
| `型` | ✓ | `string` / `int` / `float` / `bool` / `object` |
| `JSONパス` | ✓ | Dot-notation path in MRS output JSON → used as `onFetchData` |
| `永続化` | ✓ | `true` / `false` → used as `persistent` |
| `説明` | ✓ | Human-readable description |

**Supported `JSONパス` syntax:** `key`, `key.subkey`, `array[n]`, `array[n].key`

**Special rule:** `error` is always generated as a fixed scaffold field — omit it from this table.
`status` is **no longer** a scaffold field; use `finalizeWhen` in the want type YAML for completion detection instead (see §10.3 Layer 3).

---

### 6.4 `## 使用例` (recommended)

Provides example invocations and outputs. Used to generate `examples:` in the want type YAML.

````markdown
## 使用例

### 基本: 日時指定で予約確認画面へ

```bash
python3 "${CLAUDE_SKILL_DIR}/main.py" '{"room": "中野新橋店/打席予約(Room02)", "date": "2026-04-13", "time": "20:00"}'
```

出力:
```json
{
  "status": "ready_to_confirm",
  "confirmation": {
    "reservation_datetime": "2026-04-13 20:00",
    "service": "中野新橋店",
    "payment": "クレジットカード"
  }
}
```
````

---

### 6.5 `## エラー時` (required)

```markdown
## エラー時

```json
{ "error": "エラーメッセージ" }
```
```

---

## 7. Portable Paths — Use `${CLAUDE_SKILL_DIR}`

`SKILL.md` must **not** contain hardcoded absolute paths.
Use `${CLAUDE_SKILL_DIR}` which resolves to the skill's directory at runtime:

```bash
# ✅ correct
python3 "${CLAUDE_SKILL_DIR}/main.py" $ARGUMENTS

# ❌ wrong
python3 /Users/someone/.mywant/skills/transit/main.py $ARGUMENTS
```

---

## 8. JSON Schema Stability

Field names in the output JSON are part of the public contract,
referenced by `onFetchData` JSON paths in MyWant want type definitions.

**Breaking changes to field names require a version bump (`metadata.version`).**

---

## 9. stderr Usage

stderr is for runtime warnings only. Suppress at call sites:

```sh
OUTPUT=$(python3 "${CLAUDE_SKILL_DIR}/main.py" "$ARG" 2>/dev/null)
```

---

## 10. Want Type YAML Generation Rules

This section defines how to generate a complete, GCP-compliant want type YAML from a `SKILL.md`.
An LLM generating YAML must follow all rules in this section exactly.

### 10.1 Overall structure

Two files are generated per skill: `agent.yaml` (see §3) and the want type YAML.

```yaml
wantType:
  metadata:         # from frontmatter + 実行特性
  finalResultField: # from metadata.final-result-field or auto-selected
  parameters:       # from ## パラメータ table
  state:            # param mirrors + execution status + output fields (see §10.3)
  onInitialize:     # see §11.4
  requires:         # capability name from agent.yaml (see §10.5)
  examples:         # from ## 使用例
```

---

### 10.2 `metadata` block

```yaml
metadata:
  name: <metadata.type-name OR slug(frontmatter.name)>
  title: <human-readable title from name>
  description: |
    <frontmatter description>
  version: '1.0'
  category: <metadata.category OR inferred>
  pattern: independent          # Always independent for MRS types
  labels:
    child-role: <doer|monitor>  # From 実行モデル. Omit if standalone (no parent coordinator).
```

**`child-role` determination (GCP rule):**

| `実行モデル` | `child-role` label |
|---|---|
| `foreground` | `doer` |
| `background` | `monitor` |

`child-role` controls what the want is permitted to write to the parent coordinator's state.
`doer` and `monitor` can both write fields labeled `label: current` on the parent.
Omit `child-role` only when the want has no parent coordinator.

---

### 10.3 `state` block

Generate the following state fields in order. Every field must have a `label` (GCP requirement — see §11.4).

**Layer 1 — Argument fields** (only when the skill takes CLI arguments):

For skills with JSON-arg style (`skill_json_arg`):

```yaml
state:
  - name: skill_json_arg
    description: JSON string argument passed to the skill script (built from params)
    type: string
    label: current
    persistent: false
    initialValue: ""
```

For skills with positional-arg style (`skill_args_keys`):

```yaml
state:
  - name: skill_args_keys
    description: Space-separated state field names used as positional CLI args
    type: string
    label: current
    persistent: false
    initialValue: ""
```

Omit Layer 1 entirely if the skill takes no arguments.

**Layer 2 — Parameter mirrors** (one per `## パラメータ` row):

```yaml
  - name: <param name>
    description: <param description> (copied from param)
    type: <param type>
    label: current
    persistent: false
    initialValue: <zero value for type>
```

**Layer 3 — Execution status fields** (convention-required):

`error` and `summary` are strong conventions — omit them only with a clear reason.
`achieving_percentage` is written automatically by the engine from `_progress` lines; declare it here so the value is persisted.
Do **not** include a `status` field — use `finalizeWhen` in the want type YAML instead.

```yaml
  - name: error
    description: Error message if execution failed
    type: string
    label: current
    persistent: true
    initialValue: ""

  - name: summary
    description: Summary of execution result
    type: string
    label: current
    persistent: true
    initialValue: ""

  - name: achieving_percentage
    description: Execution progress percentage (0-100), updated from _progress lines
    type: int
    label: current
    persistent: false
    initialValue: 0
```

**Completion detection — `finalizeWhen` (required):**

Declare `finalizeWhen` at the top level of the want type YAML (sibling of `state`).
The engine evaluates these conditions after each execution cycle instead of relying on a `status` field.

```yaml
finalizeWhen:
  achieved:
    field: mrs_raw_output     # non-null once the script produces a successful JSON result
    operator: "!="
    value: null
  failed:
    field: error
    operator: "!="
    value: ""
```

Supported operators: `==`, `!=`, `>`, `>=`, `<`, `<=`.
`mrs_raw_output` is the raw JSON object from the last successful script execution; it is `null` before the script runs.

**Layer 4 — Output fields** (one per `## 出力フィールド` row):

Output field values are written **directly by the plugin agent** via `agent.yaml`'s `state_updates`.
Do NOT add `fetchFrom` or `onFetchData` to the want type YAML — those belong in `agent.yaml`.

```yaml
  - name: <フィールド名>
    description: <説明>
    type: <型>
    label: current
    persistent: <永続化>
    initialValue: <zero value for type>
```

**Skip** any row whose `フィールド名` is `status` or `error` (already in Layer 3).

> **Note:** The corresponding `onFetchData` JSON paths live in `agent.yaml`'s `state_updates`,
> not in the want type YAML. The engine's `SetWantTypeDefinition` automatically injects any
> `state_updates` fields declared in `agent.yaml` that are not already in the want type YAML.

---

### 10.4 GCP state label reference

Every state field must have one of these labels:

| `label` | Use |
|---|---|
| `goal` | Operator-set configuration / limits |
| `current` | Runtime values observed or written during execution |
| `plan` | Planned actions written by a thinker (not used in MRS types) |

MRS want types use `current` only (and `goal` if operator-settable limits are needed).

**GCP governance rule:**
- `child-role: doer` → may write parent state fields labeled `label: current`
- `child-role: monitor` → may write parent state fields labeled `label: current`
- No `child-role` → all parent writes are denied

---

### 10.5 `onInitialize` block

For JSON-arg skills:

```yaml
onInitialize:
  current:
    skill_json_arg: '<JSON template built from parameter names>'
```

**`skill_json_arg` construction rule:**
- Include all parameters from `## パラメータ` as `"<name>": "${<name>}"`
- Order: same as table order
- Result: a single-quoted JSON string, e.g. `'{"room":"${room}","date":"${date}","time":"${time}"}'`

For positional-arg skills:

```yaml
onInitialize:
  current:
    skill_args_keys: "<space-separated param names>"
```

Omit `onInitialize` entirely if the skill takes no arguments.

---

### 10.6 `requires` block

`requires` references the **capability name** declared in `agent.yaml`'s `metadata.capability`.
This is always the slug of the skill's want type name.

```yaml
# foreground skill (agent.yaml type: do)
requires:
  - <metadata.capability from agent.yaml>   # e.g. smartgolf_book

# background skill (agent.yaml type: monitor)
requires:
  - <metadata.capability from agent.yaml>   # e.g. smartgolf_list_available
```

**Mapping table:**

| `実行モデル` | `agent.yaml` type | `requires` value |
|---|---|---|
| `foreground` | `do` | `<capability>` (e.g. `transit_search`) |
| `background` | `monitor` | `<capability>` (e.g. `smartgolf_list_available`) |

---

### 10.7 `finalResultField`

Selection priority:
1. `metadata.final-result-field` in frontmatter (explicit)
2. First field in `## 出力フィールド` with `永続化: true`
3. `summary` (Layer 3 fallback)

---

### 10.8 `examples` block

From `## 使用例`, extract parameter values from the bash invocation line and generate:

```yaml
examples:
  - name: <section heading>
    description: <section sub-heading or description>
    want:
      metadata:
        name: <slug of section heading>
        type: <wantType.metadata.name>
      spec:
        params:
          <parameter name>: <value from example invocation>
```

---

### 10.9 Complete generated example (`smartgolf_book`)

**`agent.yaml`** (generated alongside the want type):

```yaml
agent:
  metadata:
    name: smartgolf_book_agent
    capability: smartgolf_book
    type: do
  script:
    path: ./main.py
    timeout_seconds: 120
  state_updates:
    - name: summary
      type: string
      label: current
      persistent: true
      onFetchData: "summary"
    - name: reservation_datetime
      type: string
      label: current
      persistent: true
      onFetchData: "confirmation.reservation_datetime"
    - name: service
      type: string
      label: current
      persistent: true
      onFetchData: "confirmation.service"
    - name: payment
      type: string
      label: current
      persistent: true
      onFetchData: "confirmation.payment"
```

**`smartgolf_book.yaml`** (want type):

```yaml
wantType:
  metadata:
    name: smartgolf_book
    title: SmartGolf Book
    description: |
      北新宿・中野新橋・新中野スマートゴルフの指定部屋・日付・時間帯の予約確認画面まで進める。
      最終確認ボタン（Confirm Reservation）は押さずに停止する。
    version: '1.0'
    category: smartgolf
    pattern: independent
    labels:
      child-role: doer          # foreground → doer

  finalResultField: summary

  parameters:
    - name: room
      description: 部屋名（例: 中野新橋店/打席予約(Room02)）
      type: string
      required: true
    - name: date
      description: 日付（YYYY-MM-DD形式、JST）
      type: string
      required: true
    - name: time
      description: 時刻（HH:MM形式、JST）
      type: string
      required: false
      defaultGlobalParameterFrom: time_global_param
    - name: time_global_param
      description: time のデフォルト参照先となるグローバルパラメータキー
      type: string
      required: false
      default: "selected_slot"

  state:
    # Layer 1: Argument field
    - name: skill_json_arg
      description: JSON string argument passed to the skill script (built from params)
      type: string
      label: current
      persistent: false
      initialValue: ""

    # Layer 2: Parameter mirrors
    - name: room
      description: 部屋名 (copied from param)
      type: string
      label: current
      persistent: false
      initialValue: ""
    - name: date
      description: 日付 (copied from param)
      type: string
      label: current
      persistent: false
      initialValue: ""
    - name: time
      description: 時刻 (copied from param)
      type: string
      label: current
      persistent: false
      initialValue: ""

    # Layer 3: Execution status fields
    - name: error
      description: Error message if execution failed
      type: string
      label: current
      persistent: true
      initialValue: ""
    - name: summary
      description: Summary of execution result
      type: string
      label: current
      persistent: true
      initialValue: ""
    - name: achieving_percentage
      description: Execution progress percentage (0-100)
      type: int
      label: current
      persistent: false
      initialValue: 0

    # Layer 4: Output fields (values written by agent via agent.yaml state_updates)
    - name: reservation_datetime
      description: 予約日時テキスト
      type: string
      label: current
      persistent: true
      initialValue: ""
    - name: service
      description: 店舗名
      type: string
      label: current
      persistent: true
      initialValue: ""
    - name: payment
      description: 支払い方法
      type: string
      label: current
      persistent: true
      initialValue: ""

  finalizeWhen:
    achieved:
      field: mrs_raw_output
      operator: "!="
      value: null
    failed:
      field: error
      operator: "!="
      value: ""

  onInitialize:
    current:
      skill_json_arg: '{"room":"${room}","date":"${date}","time":"${time}"}'

  requires:
    - smartgolf_book       # capability name from agent.yaml

  examples:
    - name: Book SmartGolf Room
      description: 指定部屋・時間の予約確認画面へ進む
      want:
        metadata:
          name: book-smartgolf-room
          type: smartgolf_book
        spec:
          params:
            room: "中野新橋店/打席予約(Room02)"
            date: "2026-04-13"
            time: "20:00"
```

---

## 11. Skill Checklist

**AgentSkills compliance:**
- [ ] Directory named with lowercase alphanumeric + hyphens
- [ ] `SKILL.md` present
- [ ] `name:` frontmatter matches directory name exactly (e.g. directory `save-as-want` → `name: save-as-want`)
- [ ] `description:` frontmatter is non-empty and ≤ 1024 chars
- [ ] `SKILL.md` contains no hardcoded absolute paths — use `${CLAUDE_SKILL_DIR}` for any path references

**Machine Readable Skills extensions (agent.yaml がある場合に追加で適用):**
- [ ] `agent.yaml` present in skill directory
- [ ] `agent.yaml` の `script.path` が指す実行可能ファイルが存在する（言語・形式は問わない）
- [ ] 実行可能ファイルは有効なJSONオブジェクトを stdout の最終行に出力する
- [ ] 実行可能ファイルは失敗時に `{"error": "..."}` を stdout に出力し非ゼロで終了する
- [ ] `## 実行特性` section exists with `実行モデル` = `foreground` or `background`
- [ ] `## パラメータ` section exists (if skill takes arguments), all rows have `フィールド` / `型` / `必須` / `デフォルト` / `説明`
- [ ] `## 出力フィールド` section exists, all rows have `フィールド名` / `型` / `JSONパス` / `永続化` / `説明`
- [ ] `JSONパス` values match actual output JSON keys exactly
- [ ] `status` and `error` are NOT listed in `## 出力フィールド` (handled by Layer 3 status fields)
- [ ] `## 使用例` section has at least one invocation example + JSON output pair
- [ ] `## エラー時` section present

**実行可能スクリプトの実装:**
- [ ] stdout への出力は即時フラッシュする（Python なら `flush=True`、シェルなら標準動作）
- [ ] 進捗は `{"_progress": <0-100>, "_message": "..."}` 形式で随時出力する
- [ ] 最終結果の前に `_progress` キーを含めない
- [ ] `error_out()` 相当の処理でJSON errorを出力し非ゼロ終了する

**`agent.yaml` (MRS required):**
- [ ] `metadata.capability` matches the value in want type's `requires:`
- [ ] `metadata.type` matches `実行モデル` (`foreground` → `do`, `background` → `monitor`)
- [ ] `script.path` points to an executable file (any language)
- [ ] `state_updates` entries have correct `onFetchData` paths matching actual JSON output keys
- [ ] `state_updates` includes all fields from `## 出力フィールド` (no `status` — do NOT add `status`)

**Want type YAML (GCP compliance):**
- [ ] `child-role` label matches `実行モデル` (`foreground` → `doer`, `background` → `monitor`)
- [ ] All state fields have a `label:` (`goal` / `current`)
- [ ] Argument/param-mirror fields have `persistent: false`
- [ ] Status/result/output fields have `persistent: true`
- [ ] No `fetchFrom` or `onFetchData` in want type YAML (those are in `agent.yaml`)
- [ ] `requires` references the capability name from `agent.yaml` (NOT `do_mrs_agent`/`monitor_mrs_agent`)
- [ ] `finalResultField` refers to a field defined in state
- [ ] `finalizeWhen` block present with `achieved` (`mrs_raw_output != null`) and `failed` (`error != ""`) conditions
- [ ] No `status` field in state (completion is detected via `finalizeWhen`, not a `status` field)
- [ ] Root `AGENTS.md` updated if new skill changes project overview
