import os
import re
import json
import anthropic

# --- Claude APIで新しい記録を検索 ---

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

prompt = """
あなたは芸能人・有名人のフルマラソン記録を収集するアシスタントです。

以下のジャンルの有名人がフルマラソンを完走した記録を思い出せる限り挙げてください。
ジャンル: 俳優・女優、アスリート（マラソン以外の競技）、タレント・MC、ミュージシャン、医師・研究者、その他

出力はJSON配列のみで返してください。他の文章は不要です。
フォーマット:
[
  {"name": "名前", "genre": "ジャンル", "time": "h:mm:ss", "event": "大会名 年"},
  ...
]

ジャンルは必ず以下のいずれかにしてください:
俳優, アスリート, タレント, ミュージシャン, 医師, その他

タイムが不明な場合はそのエントリを含めないでください。
できるだけ多くの実在する記録を挙げてください。
"""

print("Claude APIに問い合わせ中...")
response = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=2000,
    messages=[{"role": "user", "content": prompt}]
)

raw = response.content[0].text.strip()

# JSONを抽出
json_match = re.search(r'\[.*\]', raw, re.DOTALL)
if not json_match:
    print("JSONが見つかりませんでした。処理を終了します。")
    exit(0)

new_records = json.loads(json_match.group())
print(f"{len(new_records)} 件の記録を取得しました")

# --- 既存のindex.htmlからデータを読み込む ---

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 既存レコードを名前ベースで抽出（正規表現でname:の値を取る）
existing_names = set(re.findall(r'name:"([^"]+)"', html))
print(f"既存レコード数: {len(existing_names)} 件")

# タイムを秒数に変換
def time_to_sec(t):
    parts = t.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 99999

# 新しいレコードだけ追加用リストに入れる
to_add = []
for r in new_records:
    if r["name"] not in existing_names:
        r["sec"] = time_to_sec(r["time"])
        to_add.append(r)
        print(f"  追加: {r['name']} ({r['genre']}) {r['time']} / {r['event']}")

print(f"新規追加: {len(to_add)} 件")

if not to_add:
    print("追加する新規レコードはありませんでした。")
    exit(0)

# --- index.htmlのrecords配列の末尾に追記 ---

new_entries = ""
for r in to_add:
    new_entries += (
        f'\n  {{name:"{r["name"]}",genre:"{r["genre"]}",'
        f'time:"{r["time"]}",sec:{r["sec"]},event:"{r["event"]}"}},'
    )

# records = [ ... ]; の閉じ括弧の直前に挿入
updated_html = re.sub(
    r'(let records = \[)(.*?)(\];)',
    lambda m: m.group(1) + m.group(2).rstrip() + new_entries + '\n' + m.group(3),
    html,
    flags=re.DOTALL
)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(updated_html)

print("index.html を更新しました")
