---
description: /list-unread-gmail で表示された番号を指定してメールを既読にする（例: /mark-read 3）
---

$ARGUMENTS

上記の番号を引数として以下のコマンドを実行し、出力をそのまま表示してください:

```bash
python3 "${CLAUDE_SKILL_DIR}/main.py" $ARGUMENTS
```

番号が指定されていない場合は「既読にするメールの番号を指定してください（例: /mark-read 3）」と伝えてください。
エラーが出た場合はエラーメッセージをそのまま伝えてください。

## 出力JSON形式

```json
{
  "marked_no": 3,
  "subject": "件名",
  "sender": "送信者名",
  "date": "4月11日"
}
```

### フィールド説明

| フィールド | 型 | 説明 |
|---|---|---|
| `marked_no` | int | 既読にしたメールの番号 |
| `subject` | string | 既読にしたメールの件名 |
| `sender` | string | 既読にしたメールの送信者名 |
| `date` | string | 既読にしたメールの受信日時 |

### エラー時

```json
{
  "error": "エラーメッセージ"
}
```

> 事前に `list-unread-gmail` を実行して `/tmp/gmail_unread_list.json` を生成しておく必要がある。
