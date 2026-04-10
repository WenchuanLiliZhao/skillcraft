#!/usr/bin/env python3
"""
API 探索辅助脚本。
用于 Prepare 命令的 Phase 1，自动发现 REST API 的端点和能力。

用法:
    python explore_api.py <base_url> [--auth-header "Authorization: Bearer xxx"]
    python explore_api.py <openapi_spec_url> --openapi

输出: 结构化的 API 能力摘要（纯文本）
"""

import argparse
import json
import sys
import urllib.request
import urllib.error


def try_fetch(url, headers=None, method="GET", data=None, timeout=10):
    """尝试请求 URL，返回 (status, body) 或 (None, error_msg)"""
    req = urllib.request.Request(url, method=method)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    if data:
        req.data = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except Exception as e:
        return None, str(e)


def discover_endpoints(base_url, headers):
    """尝试常见的端点发现路径"""
    discovery_paths = [
        "/openapi.json",
        "/swagger.json",
        "/api-docs",
        "/api/v1",
        "/api",
        "/health",
        "/status",
    ]
    results = []
    for path in discovery_paths:
        url = base_url.rstrip("/") + path
        status, body = try_fetch(url, headers)
        if status and 200 <= status < 400:
            results.append({"path": path, "status": status, "body_preview": body[:500]})
    return results


def parse_openapi(spec_url, headers):
    """解析 OpenAPI/Swagger spec"""
    status, body = try_fetch(spec_url, headers)
    if not status or status >= 400:
        return None, f"Failed to fetch spec: {status}"

    try:
        spec = json.loads(body)
    except json.JSONDecodeError:
        return None, "Response is not valid JSON"

    endpoints = []
    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() in ("get", "post", "put", "delete", "patch"):
                endpoints.append({
                    "method": method.upper(),
                    "path": path,
                    "summary": details.get("summary", ""),
                    "parameters": [
                        {
                            "name": p.get("name"),
                            "in": p.get("in"),
                            "required": p.get("required", False),
                            "type": p.get("schema", {}).get("type", "unknown"),
                        }
                        for p in details.get("parameters", [])
                    ],
                })
    return endpoints, None


def main():
    parser = argparse.ArgumentParser(description="API Explorer for Prepare Command")
    parser.add_argument("url", help="Base URL or OpenAPI spec URL")
    parser.add_argument("--auth-header", help='Auth header, e.g. "Authorization: Bearer xxx"')
    parser.add_argument("--openapi", action="store_true", help="Treat URL as OpenAPI spec")
    args = parser.parse_args()

    headers = {}
    if args.auth_header:
        key, _, value = args.auth_header.partition(": ")
        headers[key] = value

    if args.openapi:
        endpoints, err = parse_openapi(args.url, headers)
        if err:
            print(f"Error: {err}", file=sys.stderr)
            sys.exit(1)
        print(f"Found {len(endpoints)} endpoint(s):\n")
        for ep in endpoints:
            print(f"  {ep['method']} {ep['path']}")
            if ep["summary"]:
                print(f"    Summary: {ep['summary']}")
            if ep["parameters"]:
                print(f"    Params: {', '.join(p['name'] for p in ep['parameters'])}")
            print()
    else:
        print(f"Exploring {args.url} ...\n")
        results = discover_endpoints(args.url, headers)
        if not results:
            print("No endpoints discovered. The API may require authentication or use non-standard paths.")
        else:
            print(f"Found {len(results)} reachable path(s):\n")
            for r in results:
                print(f"  {r['path']} (HTTP {r['status']})")
                print(f"    Preview: {r['body_preview'][:200]}...")
                print()


if __name__ == "__main__":
    main()
