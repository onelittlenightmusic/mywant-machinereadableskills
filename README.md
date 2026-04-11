# mywant-machinereadableskills

Claude Code skills that output structured JSON — ready to be converted into [MyWant](https://github.com/onelittlenightmusic/mywant) want types.

---

## What are Machine Readable Skills?

A **Machine Readable Skill** is a Claude Code skill where `main.py` always writes a single valid JSON object to stdout. This makes the skill usable not just interactively (via `/skill-name`) but also programmatically by automated pipelines.

This format is a **superset of [AGENTS.md](https://Agents.md)**: every skill descriptor (`<skill-name>.md`) is a valid AGENTS.md file, with additional mandatory sections (Claude Code frontmatter + JSON output schema) layered on top.

```
AGENTS.md format  ⊂  Machine Readable Skill format
```

---

## Skills

| Skill | Command | Description |
|---|---|---|
| [list-unread-gmail](./list-unread-gmail/) | `/list-unread-gmail` | Gmail未読重要メール一覧をJSON取得 |
| [mark-read](./mark-read/) | `/mark-read <number>` | 指定番号のメールを既読にしてJSON出力 |
| [transit](./transit/) | `/transit <from> <to> [HH:MM] [到着\|出発]` | Yahoo!路線情報で経路検索 |

---

## Usage

### As a Claude Code skill

スキルディレクトリを `~/.mywant/skills/` に配置することで `/skill-name` コマンドとして使用できます:

```sh
git clone https://github.com/onelittlenightmusic/mywant-machinereadableskills
cp -r mywant-machinereadableskills/* ~/.mywant/skills/
```

Claude Code から:
```
/list-unread-gmail
/mark-read 3
/transit 新宿 渋谷 09:30 到着
```

### As a MyWant want type

各スキルに対応した want type YAML が `~/.mywant/custom-types/` に配置されていれば、MyWant から直接呼び出せます:

```yaml
wants:
  - metadata:
      name: check-gmail
      type: gmail_list_unread
    spec:
      params: {}
```

---

## Structure

```
<skill-name>/
├── <skill-name>.md   # Claude Code skill descriptor (AGENTS.md-compatible)
│                     # + JSON output schema documentation
└── main.py           # Python entry point — stdout is always valid JSON
AGENTS.md             # Project-level context for AI agents (per Agents.md spec)
README.md             # This file
RULE.md               # Machine Readable Skills specification
```

---

## Adding a skill

See [RULE.md](./RULE.md) for the full specification and contribution checklist.

---

## Relation to AGENTS.md

This repository follows the [AGENTS.md](https://Agents.md) open specification at two levels:

1. **Repository level**: `AGENTS.md` at the root provides project context for AI agents per the spec.
2. **Skill level**: Each `<skill-name>.md` is a valid AGENTS.md file (pure Markdown, no required fields violated) extended with Claude Code frontmatter and a mandatory JSON schema section.

The Machine Readable Skills format adds these requirements on top of AGENTS.md:
- Claude Code `description:` frontmatter
- `## 出力JSON形式` section with example JSON and field table
- `### エラー時` section documenting error output
