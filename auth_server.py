# auth_server.py
from flask import Flask, request, jsonify
import time
import os
import requests

app = Flask(__name__)

# ====== 初始授权码白名单（只定义未使用的有效码）======
# 注意：这些码是否已被使用，最终以 Supabase 为准（启动时可同步）
INITIAL_LICENSES = {
    "TEST-12345": {"expire": 2000000000},
    "TEST-12347": {"expire": 1893456000},
    "TEST-12346": {"expire": 1893456000},
    "TEST-12348": {"expire": 1893456000},
    "TEST-12349": {"expire": 1893456000},
    "TEST-12344": {"expire": 1893456000},
}

# ====== Supabase 配置 ======
SUPABASE_URL = "https://nhrsuhsvptcovenvwoxi.supabase.co"
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5ocnN1aHN2cHRjb3ZlbnZ3b3hpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM3OTg2NDQsImV4cCI6MjA3OTM3NDY0NH0.I5UeFdwPAnWvYhONmLc8xcQbMKQyDkSVvxAl1CZ60eg"

def is_license_activated_in_supabase(license_key: str) -> tuple[bool, str | None]:
    """查询该 license 是否已在 Supabase 中激活"""
    url = f"{SUPABASE_URL}/rest/v1/activations"
    headers = {
        "apikey": ANON_KEY,
        "Authorization": f"Bearer {ANON_KEY}",
        "Content-Type": "application/json"
    }
    params = {
        "license": f"eq.{license_key}",
        "select": "machine_id"
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                return True, data[0]["machine_id"]
        return False, None
    except Exception as e:
        print(f"[!] 查询 Supabase 失败: {e}")
        # 保守策略：如果查不到，当作未激活（避免误拒）
        return False, None

def record_activation_to_supabase(license_key: str, machine_id: str) -> tuple[bool, str]:
    """将激活记录写入 Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/activations"
    headers = {
        "apikey": ANON_KEY,
        "Authorization": f"Bearer {ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    data = {"license": license_key, "machine_id": machine_id}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 201:
            return True, "记录成功"
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except Exception as e:
        return False, f"异常: {str(e)}"

@app.route('/activate', methods=['POST'])
def activate():
    try:
        data = request.get_json()
        if not data:
            return jsonify(ok=False, msg="无效请求体"), 400

        license_key = data.get('license')
        machine_id = data.get('machine_id', 'unknown')

        if not license_key:
            return jsonify(ok=False, msg="缺少授权码"), 400

        # 1. 检查是否在初始白名单中
        if license_key not in INITIAL_LICENSES:
            return jsonify(ok=False, msg="无效授权码"), 400

        lic_info = INITIAL_LICENSES[license_key]
        now = time.time()

        if now > lic_info['expire']:
            return jsonify(ok=False, msg="授权已过期"), 400

        # 2. 检查 Supabase 是否已激活
        activated, bound_to = is_license_activated_in_supabase(license_key)
        if activated:
            return jsonify(ok=False, msg=f"该授权码已被使用（绑定设备: {bound_to}）"), 400

        # 3. 写入 Supabase
        success, msg = record_activation_to_supabase(license_key, machine_id)
        if not success:
            return jsonify(ok=False, msg=f"激活失败（Supabase 错误）: {msg}"), 500

        return jsonify(ok=True, msg="激活成功！")

    except Exception as e:
        return jsonify(ok=False, msg=f"服务器内部错误: {str(e)}"), 500

@app.route('/health')
def health():
    return jsonify(status="ok", supabase_url=SUPABASE_URL)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
