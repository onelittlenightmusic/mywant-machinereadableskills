# mywant-machinereadableskills — Agent Context

This file follows the [AGENTS.md](https://Agents.md) open specification
(Agentic AI Foundation / Linux Foundation) to provide AI coding agents
with the context they need to work effectively in this repository.

---

## What this repository is

A collection of **Machine Readable Skills**: Claude Code skills where
`main.py` always outputs structured JSON to stdout, making each skill
directly consumable by automated systems (e.g. [MyWant](https://github.com/onelittlenightmusic/mywant)
want types via `onFetchData` JSON path mappings).

Machine Readable Skills are a **superset** of the AGENTS.md format:
every skill descriptor (`<skill-name>.md`) is a valid AGENTS.md file,
with additional mandatory sections defined in `RULE.md`.

---

## Repository structure

```
<skill-name>/
├── <skill-name>.md   # AGENTS.md-compatible skill descriptor
│                     # + Claude Code frontmatter + JSON output schema
└── main.py           # Python entry point — always outputs JSON to stdout
AGENTS.md             # This file (project-level agent context)
README.md             # Human-facing documentation
RULE.md               # Machine Readable Skills specification
```

---

## Skills in this repository

| Skill | Description | Arguments |
|---|---|---|
| `list-unread-gmail` | Gmail未読重要メール一覧をJSON出力 | なし |
| `mark-read` | 指定番号のメールを既読にしてJSON出力 | `<mail-number>` |
| `transit` | Yahoo!路線情報で経路検索してJSON出力 | `<from> <to> [HH:MM] [到着\|出発]` |

---

## Running a skill

```sh
# 引数なし
python3 list-unread-gmail/main.py

# 引数あり
python3 mark-read/main.py 3
python3 transit/main.py 新宿 渋谷 09:30 到着
```

stdout は常に有効な JSON オブジェクト。エラー時は `{"error": "..."}` + 非ゼロ終了コード。

---

## Adding a new skill

1. `RULE.md` のチェックリストをすべて満たしていることを確認する
2. `<skill-name>/` ディレクトリを作成し `main.py` と `<skill-name>.md` を配置する
3. `<skill-name>.md` が AGENTS.md 互換であること（有効な Markdown、frontmatter は任意）を確認する
4. `<skill-name>.md` に `## 出力JSON形式` セクションとフィールドテーブルを記載する
5. `main.py` のパスは `${CLAUDE_SKILL_DIR}/main.py` を使い絶対パスをハードコードしない

---

## JSON output contract

- stdout: 常に単一の有効な JSON オブジェクト
- stderr: ログ・警告のみ（呼び出し側は `2>/dev/null` で抑制）
- 成功: ドメイン固有フィールド（スキルごとに異なる）
- 失敗: `{"error": "<message>"}` + 非ゼロ終了コード

詳細は各スキルの `<skill-name>.md` の `## 出力JSON形式` セクションを参照。
