import os
import re
import json
import urllib.request

GAS_URL    = os.environ["GAS_URL"]
GAS_SECRET = os.environ["GAS_SECRET"]

# スプレッドシートから全データを取得
print("スプレッドシートからデータを取得中...")
req = urllib.request.Request(f"{GAS_URL}?secret={GAS_SECRET}", method="GET")
with urllib.request.urlopen(req) as res:
    all_records = json.loads(res.read().decode("utf-8"))
print(f"合計 {len(all_records)} 件のデータを取得しました")

# index.htmlを更新
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
