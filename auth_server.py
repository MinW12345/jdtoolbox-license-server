# auth_server.py
from flask import Flask, request, jsonify
import time
import os

app = Flask(__name__)

# ====== 在这里管理你的授权码 ======
# 格式: "授权码": {"used": False, "expire": Unix时间戳}
# 使用 https://www.epochconverter.com/ 转换日期为时间戳
LICENSES = {
    "TEST-12345": {"used": False, "expire": 2000000000},  # 永不过期（2033年）
    "ALICE-SITE": {"used": False, "expire": 1893456000},  # 2030-01-01 过期
    # 添加更多授权码...
}

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

        if license_key not in LICENSES:
            return jsonify(ok=False, msg="无效授权码"), 400

        lic = LICENSES[license_key]
        now = time.time()

        if now > lic['expire']:
            return jsonify(ok=False, msg="授权已过期"), 400
        if lic['used']:
            return jsonify(ok=False, msg="该授权码已被使用"), 400

        # 激活成功
        lic['used'] = True
        lic['bound_to'] = machine_id

        return jsonify(ok=True, msg="激活成功！")

    except Exception as e:
        return jsonify(ok=False, msg=f"服务器错误: {str(e)}"), 500

# 健康检查（可选）
@app.route('/health')
def health():
    return jsonify(status="ok")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
