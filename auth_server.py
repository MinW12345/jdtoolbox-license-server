import os
import logging
from flask import Flask, request, jsonify
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("❌ 缺少 SUPABASE_URL 或 SUPABASE_ANON_KEY")
    raise EnvironmentError("请在 Render 设置环境变量")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

app = Flask(__name__)

def is_valid_license(license_key):
    """检查 license 是否在 licenses 表中"""
    url = f"{SUPABASE_URL}/rest/v1/licenses"
    params = {"license_key": f"eq.{license_key}"}
    try:
        res = requests.get(url, headers=HEADERS, params=params, timeout=10)
        return res.status_code == 200 and len(res.json()) > 0
    except Exception as e:
        logger.error(f"验证 license 异常: {e}")
        return False

def is_already_activated(license_key):
    """检查是否已激活"""
    url = f"{SUPABASE_URL}/rest/v1/activations"
    params = {"license": f"eq.{license_key}"}
    try:
        res = requests.get(url, headers=HEADERS, params=params, timeout=10)
        return res.status_code == 200 and len(res.json()) > 0
    except Exception as e:
        logger.error(f"查询激活记录异常: {e}")
        return False

def record_activation(license_key, machine_id):
    """记录激活"""
    url = f"{SUPABASE_URL}/rest/v1/activations"
    payload = {"license": license_key, "machine_id": machine_id}
    try:
        res = requests.post(url, json=payload, headers=HEADERS, timeout=10)
        return res.status_code in (200, 201)
    except Exception as e:
        logger.error(f"记录激活失败: {e}")
        return False

@app.route('/activate', methods=['POST'])
def activate():
    data = request.get_json()
    if not data or 'license' not in data or 'machine_id' not in data:
        return jsonify({"ok": False, "msg": "缺少 license 或 machine_id"}), 400

    license_key = data['license']
    machine_id = data['machine_id']

    if not is_valid_license(license_key):
        return jsonify({"ok": False, "msg": "无效的授权码"}), 400

    if is_already_activated(license_key):
        return jsonify({"ok": False, "msg": "该授权码已被使用"}), 403

    if record_activation(license_key, machine_id):
        return jsonify({"ok": True, "msg": "激活成功！"})
    else:
        return jsonify({"ok": False, "msg": "数据库写入失败"}), 500

@app.route('/')
def home():
    return jsonify({"status": "License server is running"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
