#!/usr/bin/env python3
"""Serve the CourseTune test UI and proxy chat requests to a local model API."""

from __future__ import annotations

import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib import error, request


DEFAULT_SYSTEM = "你是 EBU5606 产品开发课程资料智能答疑助手。只根据课程资料回答；如果资料不足，就说明无法从资料中确定。"


class CourseTuneHandler(SimpleHTTPRequestHandler):
    api_url = "http://127.0.0.1:8000/v1/chat/completions"
    model_name = "coursetune-product-development"

    def do_POST(self) -> None:
        if self.path != "/api/chat":
            self.send_error(404)
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)
            client_payload = json.loads(raw_body.decode("utf-8"))
            model_payload = {
                "model": self.model_name,
                "messages": normalize_messages(client_payload.get("messages", [])),
                "temperature": float(client_payload.get("temperature", 0.5)),
                "stream": False,
            }
            response_payload = post_json(self.api_url, model_payload)
            self.write_json(200, response_payload)
        except Exception as exc:  # noqa: BLE001 - return readable browser errors.
            self.write_json(502, {"error": str(exc)})

    def write_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def normalize_messages(messages: list[dict]) -> list[dict[str, str]]:
    normalized = []
    has_system = False
    for message in messages:
        role = message.get("role")
        content = str(message.get("content", "")).strip()
        if role not in {"system", "user", "assistant"} or not content:
            continue
        has_system = has_system or role == "system"
        normalized.append({"role": role, "content": content})
    if not has_system:
        normalized.insert(0, {"role": "system", "content": DEFAULT_SYSTEM})
    return normalized


def post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    http_request = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(http_request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Model API returned {exc.code}: {detail}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--api-url", default=CourseTuneHandler.api_url)
    parser.add_argument("--model-name", default=CourseTuneHandler.model_name)
    args = parser.parse_args()

    CourseTuneHandler.api_url = args.api_url
    CourseTuneHandler.model_name = args.model_name
    web_dir = Path(__file__).resolve().parent
    handler = lambda *handler_args: CourseTuneHandler(*handler_args, directory=str(web_dir))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"CourseTune UI: http://{args.host}:{args.port}")
    print(f"Model API: {args.api_url}")
    server.serve_forever()


if __name__ == "__main__":
    main()
