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

# スプレッドシートが時間を日付変換してしまった場合の修正
def fix_time(t):
    t = str(t)
    m = re.search(r'T(\d+):(\d+):(\d+)', t)
    if m:
        h  = int(m.group(1))
        mi = int(m.group(2))
        s  = int(m.group(3))
        if '1899-12-29' in t:
            total = h * 3600 + mi * 60 + s
            h  = total // 3600
            mi = (total % 3600) // 60
            s  = total % 60
        return f"{h}:{mi:02d}:{s:02d}"
    return t

def time_to_sec(t):
    parts = t.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 99999

# index.htmlを更新
with open("index.html", "r", encoding="utf-8") as f:
    html = f.read()

entries = ""
for r in all_records:
    name  = str(r.get("name","")).replace('"', '\\"')
    genre = str(r.get("genre","")).replace('"', '\\"')
    time  = fix_time(r.get("time",""))
    event = str(r.get("event","")).replace('"', '\\"')
    sec   = time_to_sec(time)
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
