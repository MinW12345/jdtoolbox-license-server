from flask import Flask, request, jsonify
import time
import os
import requests

app = Flask(__name__)

# ====== 授权码数据库（可随时修改）======
LICENSES = {
    "TEST-12345": {"used": False, "expire": 2000000000},
    "QWEEE1": {"used": False, "expire": 1893456000},
    "QWEEE2": {"used": False, "expire": 1893456000},
    "QWEEE3": {"used": False, "expire": 1893456000},
    "QWEEE4": {"used": False, "expire": 1893456000},
    "QWEEE5": {"used": False, "expire": 1893456000},
}

# ====== Supabase 配置 ======
SUPABASE_URL = "https://nhrsuhsvptcovenvwoxi.supabase.co"
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5ocnN1aHN2cHRjb3ZlbnZ3b3hpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM3OTg2NDQsImV4cCI6MjA3OTM3NDY0NH0.I5UeFdwPAnWvYhONmLc8xcQbMKQyDkSVvxAl1CZ60eg"

def record_activation_to_supabase(license_key: str, machine_id: str):
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
            return False, f"Supabase 错误: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"网络错误: {str(e)}"

@app.route('/activate', methods=['POST'])
def activate():
    try:
        data = request.get_json()
        if not data:
            return jsonify(ok=False, msg="无效请求"), 400

        license_key = data.get('license')
        machine_id = data.get('machine_id', 'unknown')

        if not license_key:
            return jsonify(ok=False, msg="缺少授权码"), 400

        if license_key not in LICENSES:
            return jsonify(ok=False, msg="无效授权码"), 400

        lic = LICENSES[license_key]
        now = time.time()

        if now > lic['expire']:
            return jsonify(ok=False, msg="授权已过期"), 400
        if lic['used']:
            return jsonify(ok=False, msg="该授权码已被使用"), 400

        # ✅ 验证通过，先写入 Supabase
        success, msg = record_activation_to_supabase(license_key, machine_id)
        if not success:
            # 可选：是否回滚？这里选择不标记为已用（保守策略）
            return jsonify(ok=False, msg=f"激活失败: {msg}"), 500

        # ✅ 写入成功，标记为已使用
        lic['used'] = True
        lic['bound_to'] = machine_id

        return jsonify(ok=True, msg="激活成功！")

    except Exception as e:
        return jsonify(ok=False, msg=f"服务器错误: {str(e)}"), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
