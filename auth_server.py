# auth_server.py
from flask import Flask, request, jsonify
import time
import os

app = Flask(__name__)

LICENSES = {
    "TEST-12345": {"used": False, "expire": 2000000000},
    "QWEEE1": {"used": False, "expire": 1893456000},
    "QWEEE2": {"used": False, "expire": 1893456000},
    "QWEEE3": {"used": False, "expire": 1893456000},
    "QWEEE4": {"used": False, "expire": 1893456000},
    "QWEEE5": {"used": False, "expire": 1893456000},
}

@app.route('/activate', methods=['POST'])
def activate():
    try:
        data = request.get_json()
        if not data:
            return jsonify(ok=False, msg="无效的 JSON"), 400
        
        license_key = data.get('license')
        if not license_key:
            return jsonify(ok=False, msg="缺少授权码"), 400

        if license_key not in LICENSES:
            return jsonify(ok=False, msg="无效授权码"), 400

        lic = LICENSES[license_key]
        if time.time() > lic['expire']:
            return jsonify(ok=False, msg="授权已过期"), 400

        if lic['used']:
            return jsonify(ok=False, msg="该授权码已被使用"), 400

        lic['used'] = True
        return jsonify(ok=True, msg="激活成功！")

    except Exception as e:
        return jsonify(ok=False, msg=f"服务器错误: {str(e)}"), 500

@app.route('/health')
def health():
    return jsonify(status="ok")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
