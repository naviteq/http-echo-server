import os
from flask import Flask, request, jsonify

app = Flask(__name__)


def read_k8s_directory(dir_path):
    """
    Recursively read all files in /etc/k8s and return a dict
    mapping relative file paths -> file contents.
    """
    k8s_info = {}
    if not os.path.exists(dir_path):
        return k8s_info

    for root, dirs, files in os.walk(dir_path):
        for filename in files:
            full_path = os.path.join(root, filename)
            relative_path = os.path.relpath(full_path, dir_path)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                k8s_info[relative_path] = content
            except Exception as e:
                # TODO: Remove it after testing
                k8s_info[relative_path] = f"<Error reading file: {e}>"
    return k8s_info


@app.route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def info():
    headers = dict(request.headers)
    client_ip = request.remote_addr
    method = request.method
    query_params = request.args.to_dict()
    json_body = request.get_json(force=True, silent=True) or {}
    form_data = request.form.to_dict()
    k8s_data = read_k8s_directory(os.getenv("DOWNWARD_PATH", "/etc/k8s"))
    response_data = {
        "client_ip": client_ip,
        "method": method,
        "headers": headers,
        "query_params": query_params,
        "json_body": json_body,
        "form_data": form_data,
        "kubernetes": k8s_data,  # The K8S info is added here
    }
    return jsonify(response_data)


if __name__ == "__main__":
    port = os.getenv("SERVER_PORT", 5000)
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    app.run(debug=True, host=host, port=port)
