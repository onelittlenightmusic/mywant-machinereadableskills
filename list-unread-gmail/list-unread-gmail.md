---
description: Playwright経由でGmailにアクセスし、未読の重要メールを番号付きリストで表示する
---

以下のコマンドを実行して出力をそのまま表示してください:

```bash
python3 /Users/hiroyukiosaki/.mywant/skills/list-unread-gmail/main.py
```

エラーが出た場合はエラーメッセージをそのまま伝えてください。

## 出力JSON形式

```json
{
  "count": 3,
  "emails": [
    {
      "no": 1,
      "sender": "送信者名",
      "subject": "件名",
      "date": "4月11日",
      "thread_id": "18f3a2b..."
    }
  ]
}
```

### フィールド説明

| フィールド | 型 | 説明 |
|---|---|---|
| `count` | int | 未読重要メールの件数 |
| `emails` | array | メール一覧（未読順） |
| `emails[].no` | int | 番号（mark-read に渡す値） |
| `emails[].sender` | string | 送信者名 |
| `emails[].subject` | string | 件名 |
| `emails[].date` | string | 受信日時 |
| `emails[].thread_id` | string | GmailスレッドID（内部用） |

### エラー時

```json
{
  "error": "エラーメッセージ",
  "count": 0,
  "emails": []
}
```

> 結果は `/tmp/gmail_unread_list.json` にもキャッシュされ、`mark-read` スキルから参照される。
