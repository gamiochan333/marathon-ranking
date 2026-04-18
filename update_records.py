import os
import re
import json
import urllib.request
import anthropic

GAS_URL    = os.environ["GAS_URL"]
GAS_SECRET = os.environ["GAS_SECRET"]

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
json_match = re.search(r'\[.*\]', raw, re.DOTALL)
if not json_match:
    print("JSONが見つかりませんでした。終了します。")
    exit(0)

new_records = json.loads(json_match.group())
print(f"{len(new_records)} 件の記録を取得しました")

# タイムを秒数に変換
def time_to_sec(t):
    parts = t.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 99999

for r in new_records:
    r["sec"] = time_to_sec(r["time"])

# --- スプレッドシートに新しい記録を追加 ---

print("スプレッドシートに書き込み中...")
post_data = json.dumps({"secret": GAS_SECRET, "records": new_records}).encode("utf-8")
req = urllib.request.Request(GAS_URL, data=post_data, method="POST",
      headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as res:
    result = json.loads(res.read().decode("utf-8"))
print(f"スプレッドシートに {result.get('added', 0)} 件追加しました")

# --- スプレッドシートから全データを取得 ---

print("スプレッドシートからデータを取得中...")
req2 = urllib.request.Request(f"{GAS_URL}?secret={GAS_SECRET}", method="GET")
with urllib.request.urlopen(req2) as res:
    all_records = json.loads(res.read().decode("utf-8"))
print(f"合計 {len(all_records)} 件のデータを取得しました")

# --- index.htmlを更新 ---

with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

entries = ""
for r in all_records:
    name  = str(r.get("name","")).replace('"','\\"')
    genre = str(r.get("genre","")).replace('"','\\"')
    time  = str(r.get("time","")).replace('"','\\"')
    event = str(r.get("event","")).replace('"','\\"')
    sec   = int(r.get("sec", 0))
    entries += f'\n  {{name:"{name}",genre:"{genre}",time:"{time}",sec:{sec},event:"{event}"}},'

updated_html = re.sub(
    r'let records = \[.*?\];',
    f'let records = [{entries}\n];',
    html,
    flags=re.DOTALL
)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(updated_html)

print("index.html を更新しました")
