# auth_server.py
from flask import Flask, request, jsonify
import time
import os
import requests

app = Flask(__name__)

# ===== 授权码白名单（只定义有效码，是否使用由 Supabase 决定）====
VALID_LICENSES = {
    "TEST-12345": 2000000000,
    "QWEEE1": 1893456000,
    "QWEEE2": 1893456000,
    "QWEEE3": 1893456000,
    "QWEEE4": 1893456000,
    "QWEEE5": 1893456000,
}

# ===== Supabase 配置 ====
SUPABASE_URL = "https://nhrsuhsvptcovenvwoxi.supabase.co"
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5ocnN1aHN2cHRjb3ZlbnZ3b3hpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM3OTg2NDQsImV4cCI6MjA3OTM3NDY0NH0.I5UeFdwPAnWvYhONmLc8xcQbMKQyDkSVvxAl1CZ60eg"

def is_activated_in_supabase(license_key: str) -> bool:
    url = f"{SUPABASE_URL}/rest/v1/activations"
    headers = {"apikey": ANON_KEY}
    params = {"license": f"eq.{license_key}"}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        return len(res.json()) > 0
    except:
        return False  # 保守：查不到当作未激活

def record_activation(license_key: str, machine_id: str) -> tuple[bool, str]:
    url = f"{SUPABASE_URL}/rest/v1/activations"
    headers = {
        "apikey": ANON_KEY,
        "Authorization": f"Bearer {ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    data = {"license": license_key, "machine_id": machine_id}
    try:
        res = requests.post(url, headers=headers, json=data, timeout=10)
        if res.status_code == 201:
            return True, "ok"
        else:
            return False, f"HTTP {res.status_code}: {res.text}"
    except Exception as e:
        return False, str(e)

@app.route('/activate', methods=['POST'])
def activate():
    try:
        data = request.get_json()
        license_key = data.get('license')
        machine_id = data.get('machine_id', 'unknown')

        if not license_key:
            return jsonify(ok=False, msg="缺少授权码"), 400

        # 1. 检查是否是有效授权码
        if license_key not in VALID_LICENSES:
            return jsonify(ok=False, msg="无效授权码"), 400

        expire_ts = VALID_LICENSES[license_key]
        if time.time() > expire_ts:
            return jsonify(ok=False, msg="授权已过期"), 400

        # 2. 检查是否已在 Supabase 激活
        if is_activated_in_supabase(license_key):
            return jsonify(ok=False, msg="该授权码已被使用"), 400

        # 3. 写入 Supabase
        success, msg = record_activation(license_key, machine_id)
        if not success:
            return jsonify(ok=False, msg=f"激活失败（数据库错误）: {msg}"), 500

        return jsonify(ok=True, msg="激活成功！")

    except Exception as e:
        return jsonify(ok=False, msg=f"服务器错误: {str(e)}"), 500

@app.route('/health')
def health():
    return jsonify(status="ok")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
