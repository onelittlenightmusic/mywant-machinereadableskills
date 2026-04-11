# mywant-machinereadableskills

Claude Code skills that output structured JSON — ready to be converted into [MyWant](https://github.com/onelittlenightmusic/mywant) want types.

---

## What are Machine Readable Skills?

A **Machine Readable Skill** is a Claude Code skill where `main.py` always writes a single valid JSON object to stdout. This makes the skill usable not just interactively (via `/skill-name`) but also programmatically by automated pipelines.

### Format hierarchy

This format is a **superset of both [AGENTS.md](https://Agents.md) and [AgentSkills](https://Agentskills.md)**:

```
AGENTS.md  ⊂  AgentSkills (SKILL.md)  ⊂  Machine Readable Skills
```

| Standard | Governed by | Key requirement |
|---|---|---|
| [AGENTS.md](https://Agents.md) | Agentic AI Foundation / Linux Foundation | Pure Markdown, no required fields |
| [AgentSkills](https://Agentskills.md) | Originally Anthropic, now open standard | `SKILL.md` with `name` + `description` frontmatter |
| Machine Readable Skills | This repo | Above + `main.py` outputs JSON + `## 出力JSON形式` section |

Every skill `SKILL.md` in this repository is a valid AgentSkills skill, and every AgentSkills `SKILL.md` is a valid AGENTS.md file.

---

## Skills

| Skill | Command | Description |
|---|---|---|
| [list-unread-gmail](./list-unread-gmail/) | `/list-unread-gmail` | Gmail未読重要メール一覧をJSON取得 |
| [mark-read](./mark-read/) | `/mark-read <number>` | 指定番号のメールを既読にしてJSON出力 |
| [transit](./transit/) | `/transit <from> <to> [HH:MM] [到着\|出発]` | Yahoo!路線情報で経路検索 |

---

## Usage

### As a Claude Code / AgentSkills skill

`SKILL.md` は AgentSkills 標準に準拠しているため、Claude Code、GitHub Copilot、Cursor 等で利用できます。

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

対応する want type YAML が `~/.mywant/custom-types/` にあれば MyWant から直接呼び出せます:

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
├── SKILL.md    # AgentSkills-compliant descriptor (name + description frontmatter)
│               # + AGENTS.md-compatible Markdown
│               # + JSON output schema (## 出力JSON形式)
└── main.py     # Entry point — stdout is always valid JSON
AGENTS.md       # Project-level context for AI agents (per Agents.md spec)
README.md       # This file
RULE.md         # Machine Readable Skills specification
```

---

## Adding a skill

See [RULE.md](./RULE.md) for the full specification and checklist.
