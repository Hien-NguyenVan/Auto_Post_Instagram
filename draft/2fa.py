import re, json, requests

KEY = "BLUO JVWA VVNV LFJN VIAK QMT5 RNUD A6V2"

key = re.sub(r'\s+', '', KEY).upper()
url = f"https://2fa.live/tok/{key}"

try:
    r = requests.get(url, timeout=8)
    data = r.json()
    code = data.get("token", "No token")
except Exception as e:
    code = f"Error: {e}"

print(json.dumps({"key": key, "code": code}, ensure_ascii=False))
