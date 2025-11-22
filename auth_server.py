# auth_server.py
from flask import Flask, request, jsonify
import os
import time
import requests
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ====== 配置 ======
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://你的项目.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "你的 anon key")
WHITELIST = {
    "QWEEE1": 1893456000,
    "QWEEE2": 1893456000,
    "QWEEE3": 1893456000,
    "QWEEE4": 1893456000,
    "QWEEE5": 1893456000,
}

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

def is_activated(license_key):
    """检查授权码是否已在 Supabase 中激活"""
    url = f"{SUPABASE_URL}/rest/v1/activations"
    params = {"license": f"eq.{license_key}"}
    try:
        res = requests.get(url, headers=HEADERS, params=params, timeout=5)
        if res.status_code == 200:
            data = res.json()
            return len(data) > 0
        else:
            logger.error(f"Supabase 查询失败: {res.status_code} {res.text}")
            return False
    except Exception as e:
        logger.error(f"Supabase 查询异常: {e}")
        return False

def record_activation(license_key, machine_id):
    """将激活记录写入 Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/activations"
    payload = {
        "license": license_key,
        "machine_id": machine_id
    }
    try:
        res = requests.post(url, json=payload, headers=HEADERS, timeout=5)
        if res.status_code in (200, 201):
            return True
        else:
            logger.error(f"Supabase 写入失败: {res.status_code} {res.text}")
            return False
    except Exception as e:
        logger.error(f"Supabase 写入异常: {e}")
        return False

# ====== 路由 ======
@app.route('/health')
def health():
    return jsonify(status="ok")

@app.route('/activate', methods=['POST'])
def activate():
    try:
        data = request.get_json()
        if not data:
            return jsonify(ok=False, msg="无效的 JSON 格式"), 400

        license_key = data.get('license')
        machine_id = data.get('machine_id', 'unknown')

        if not license_key:
            return jsonify(ok=False, msg="缺少授权码字段"), 400

        # 1. 检查是否在白名单
        expire_ts = WHITELIST.get(license_key)
        if expire_ts is None:
            return jsonify(ok=False, msg="无效授权码"), 400

        if time.time() > expire_ts:
            return jsonify(ok=False, msg="授权已过期"), 400

        # 2. 检查是否已激活（查 Supabase）
        if is_activated(license_key):
            return jsonify(ok=False, msg="该授权码已被使用"), 400

        # 3. 记录激活
        if not record_activation(license_key, machine_id):
            return jsonify(ok=False, msg="激活失败（数据库错误）"), 500

        logger.info(f"✅ 激活成功: {license_key} on {machine_id}")
        return jsonify(ok=True, msg="激活成功！")

    except Exception as e:
        logger.exception("服务器内部错误")
        return jsonify(ok=False, msg=f"服务器错误: {str(e)}"), 500

# ====== 启动 ======
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
