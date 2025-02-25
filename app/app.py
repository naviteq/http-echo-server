from flask import Flask, request, jsonify
import os

app = Flask(__name__)


@app.route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def info():
    headers = dict(request.headers)
    client_ip = request.remote_addr
    method = request.method
    json_body = request.get_json(force=True, silent=True) or {}
    query_params = request.args.to_dict()
    form_data = request.form.to_dict()
    response_data = {
        "client_ip": client_ip,
        "method": method,
        "headers": headers,
        "query_params": query_params,
        "json_body": json_body,
        "form_data": form_data,
    }

    return jsonify(response_data)


if __name__ == "__main__":
    port = os.getenv("SERVER_PORT", 5001)
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    app.run(debug=True, host=host, port=port)
