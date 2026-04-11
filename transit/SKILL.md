---
name: transit
description: Yahoo!路線情報で乗り換え案内を検索し結果をJSONで返す。電車・バスの経路検索、出発・到着時刻の確認、乗換回数・料金の取得が必要なときに使用する（例: /transit 新宿 渋谷 / /transit 新宿 渋谷 09:30 到着）。
compatibility: Requires Python 3.x, playwright, and a running Chrome/Chromium CDP server at localhost:9222
metadata:
  output-format: json
  json-schema: see "出力JSON形式" section below
---

$ARGUMENTS

上記を引数として以下のコマンドを実行し、出力をそのまま表示してください:

```bash
python3 "${CLAUDE_SKILL_DIR}/main.py" $ARGUMENTS
```

引数が不足している場合は「出発地と目的地を指定してください（例: /transit 新宿 渋谷）」と伝えてください。
エラーが出た場合はエラーメッセージをそのまま伝えてください。

## 出力JSON形式

```json
{
  "from": "新宿",
  "to": "渋谷",
  "query_time": "09:30",
  "query_type": "到着",
  "routes": [
    {
      "index": 1,
      "departure": "09:05",
      "arrival": "09:30",
      "duration_minutes": 25,
      "fare": 199,
      "transfers": 0,
      "summary": "09:05発→09:30着25分（乗車25分）",
      "legs": [
        {
          "type": "depart",
          "time": "09:05",
          "station": "新宿",
          "line": "ＪＲ山手線内回り",
          "direction": "渋谷・品川方面"
        },
        {
          "type": "arrive",
          "time": "09:30",
          "station": "渋谷"
        }
      ],
      "legs_text": "新宿(09:05) ─[ＪＲ山手線内回り]→ 渋谷(09:30)"
    }
  ],
  "raw_text": "路線情報トップ > 乗換案内 新宿から渋谷\n..."
}
```

### フィールド説明

| フィールド | 型 | 説明 |
|---|---|---|
| `from` | string | 出発地（引数のまま） |
| `to` | string | 目的地（引数のまま） |
| `query_time` | string | 指定時刻（HH:MM）。未指定時は空文字 |
| `query_type` | string | `"出発"` or `"到着"` |
| `routes` | array | 検索結果ルート一覧（最大3件） |
| `routes[].index` | int | ルート番号（1〜3） |
| `routes[].departure` | string | 出発時刻（HH:MM） |
| `routes[].arrival` | string | 到着時刻（HH:MM） |
| `routes[].duration_minutes` | int | 所要時間（分） |
| `routes[].fare` | int | 料金（円）。IC優先運賃 |
| `routes[].transfers` | int | 乗換回数 |
| `routes[].summary` | string | サマリー文字列（例: `"09:05発→09:30着25分（乗車25分）"` ） |
| `routes[].legs` | array | 区間ごとの詳細 |
| `routes[].legs[].type` | string | `"depart"`（出発）or `"arrive"`（到着） |
| `routes[].legs[].time` | string | 時刻（HH:MM） |
| `routes[].legs[].station` | string | 駅名 |
| `routes[].legs[].line` | string | 路線名（`type: depart` のみ） |
| `routes[].legs[].direction` | string | 方面（`type: depart` のみ） |
| `routes[].legs_text` | string | 経路の人間可読サマリー |
| `raw_text` | string | ページ全体のテキスト（先頭80行） |

### エラー時

```json
{
  "error": "エラーメッセージ",
  "routes": []
}
```
