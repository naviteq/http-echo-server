import os
import json
import logging
import requests
from flask import Flask, request, jsonify


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON strings."""

    def format(self, record):
        # Prepare a dict with key log fields
        log_record = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "filename": record.filename,
            "lineno": record.lineno,
            "funcName": record.funcName,
        }
        # Include any 'extra' fields added via `logger.info(..., extra={})`
        if record.__dict__.get("extra_fields"):
            log_record.update(record.__dict__["extra_fields"])
        return json.dumps(log_record)


logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
app = Flask(__name__)


def get_geo_info(ip_address):
    """
    Call a 3rd party geo IP API (e.g., ip-api.com) to retrieve IP location info.
    Returns a dict with geo details or an empty dict on error.
    """
    if not ip_address:
        return {}
    try:
        # ip-api.com example endpoint (free tier).
        # 'fields' can specify which data points you want; 66846719 = "all fields"
        # as per their docs. Adjust as needed:
        url = f"http://ip-api.com/json/{ip_address}?fields=66846719"
        response = requests.get(url, timeout=2)  # short timeout for example
        if response.status_code == 200:
            data = response.json()
            # ip-api.com might have 'success' or 'fail' status in JSON
            if data.get("status") == "success":
                return data
            else:
                logger.warning(
                    f"Geo API returned a fail status for IP {ip_address}",
                    extra={"extra_fields": {"ip": ip_address, "api_response": data}},
                )
                return {}
        else:
            logger.error(
                f"Geo API returned status code {response.status_code}",
                extra={"extra_fields": {"ip": ip_address}},
            )
            return {}
    except requests.RequestException as e:
        logger.error(
            "Exception while calling geo API. Critical error - exiting",
            extra={"extra_fields": {"ip": ip_address, "error": str(e)}},
        )
        raise e


def parse_downward_file(filename, content):
    """
    Attempt to parse the content of certain known downward API files
    (e.g., labels, annotations) into dictionaries.

    Other files simply return the raw text.
    """
    basename = os.path.basename(filename)

    # For downward API "labels" or "annotations" files, typically key=value lines
    if basename in ["labels", "annotations"]:
        lines = content.strip().split("\n")
        parsed_data = {}
        for line in lines:
            # e.g.: each line is something like:   key=value
            if "=" in line:
                k, v = line.split("=", 1)
                parsed_data[k] = v
        return parsed_data

    # For everything else, treat it as raw text
    return content.strip()


def read_k8s_directory(dir_path="/etc/k8s"):
    """
    Recursively read all files in /etc/k8s and return a dict
    { "<relative_file_path>": <parsed_content_or_error> }.
    """
    k8s_info = {}
    if not os.path.exists(dir_path):
        logger.info(
            "K8S directory does not exist; skipping",
            extra={"extra_fields": {"directory": dir_path}},
        )
        return k8s_info

    for root, dirs, files in os.walk(dir_path):
        for filename in files:
            full_path = os.path.join(root, filename)
            base_name = os.path.basename(full_path)
            # Relative path (e.g., "labels" or "some/subfolder/annotations")
            relative_path = os.path.relpath(full_path, dir_path)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    raw_content = f.read()
                parsed_content = parse_downward_file(relative_path, raw_content)
                k8s_info[base_name] = parsed_content
            except Exception as e:
                logger.error(
                    error_message,
                    extra={
                        "extra_fields": {"file": relative_path, "exception": str(e)}
                    },
                )
    return k8s_info


@app.before_request
def log_incoming_request():
    """Optional: log each incoming request in JSON."""
    logger.info(
        "Incoming request",
        extra={
            "extra_fields": {
                "method": request.method,
                "url": request.url,
                "remote_addr": request.remote_addr,
            }
        },
    )


@app.route("/", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def info():
    headers = dict(request.headers)
    client_ip = request.remote_addr
    method = request.method
    query_params = request.args.to_dict()
    json_body = request.get_json(force=True, silent=True) or {}
    form_data = request.form.to_dict()
    x_forwarded_for = headers.get("X-Forwarded-For", "")
    forwarded_ip = ""
    if x_forwarded_for:
        # X-Forwarded-For can be multiple IPs, "client, proxy1, proxy2..."
        # Usually the first is the real client
        forwarded_ip = x_forwarded_for.split(",")[0].strip()
    geo_info = {}
    if forwarded_ip:
        geo_info = get_geo_info(forwarded_ip)
    k8s_data = read_k8s_directory(os.getenv("DOWNWARD_PATH", "/etc/k8s"))
    response_data = {
        "server_ip": client_ip,
        "original_ip": forwarded_ip,
        "geo_info": geo_info,
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
