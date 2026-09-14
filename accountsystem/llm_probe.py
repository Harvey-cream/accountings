import json
import os
import socket
import ssl
from urllib.parse import urlparse

import httpx
from config.dotenv_loader import env_str, load_project_dotenv


def _print_title(title: str) -> None:
    print("\n" + "=" * 16 + f" {title} " + "=" * 16)


def _safe_text(text: str, limit: int = 500) -> str:
    if not text:
        return ""
    return text[:limit] + ("..." if len(text) > limit else "")


def main() -> None:
    load_project_dotenv()

    base_url = env_str("LLM_AGENT_BASE_URL", "https://api4.mygptlife.com/v1/")
    api_key = env_str("LLM_AGENT_API_KEY")
    model = env_str("LLM_AGENT_MODEL", "claude-sonnet-4-6")

    _print_title("ENV")
    print("LLM_AGENT_BASE_URL:", base_url)
    print("LLM_AGENT_MODEL:", model)
    print("LLM_AGENT_API_KEY:", f"{api_key[:8]}..." if api_key else "(empty)")
    print("HTTPS_PROXY:", os.getenv("HTTPS_PROXY") or "(not set)")
    print("HTTP_PROXY:", os.getenv("HTTP_PROXY") or "(not set)")

    parsed = urlparse(base_url)
    host = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    _print_title("DNS")
    try:
        infos = socket.getaddrinfo(host, port)
        addrs = sorted({item[4][0] for item in infos})
        print("Host:", host)
        print("Resolved IPs:", ", ".join(addrs))
    except Exception as e:
        print("DNS FAILED:", repr(e))
        return

    _print_title("TCP")
    try:
        with socket.create_connection((host, port), timeout=8):
            print(f"TCP CONNECT OK: {host}:{port}")
    except Exception as e:
        print("TCP FAILED:", repr(e))
        return

    _print_title("TLS")
    if parsed.scheme == "https":
        try:
            context = ssl.create_default_context()
            with socket.create_connection((host, port), timeout=8) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    print("TLS HANDSHAKE OK")
                    print("TLS VERSION:", ssock.version())
                    print("CERT SUBJECT:", cert.get("subject"))
                    print("CERT ISSUER:", cert.get("issuer"))
        except Exception as e:
            print("TLS FAILED:", repr(e))
    else:
        print("Skip TLS test for non-https URL")

    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    _print_title("HTTP /models (verify=True)")
    try:
        with httpx.Client(timeout=15.0, verify=True) as client:
            r = client.get(base_url.rstrip("/") + "/models", headers=headers)
            print("STATUS:", r.status_code)
            print("BODY:", _safe_text(r.text))
    except Exception as e:
        print("REQUEST FAILED:", repr(e))

    _print_title("HTTP /models (verify=False)")
    try:
        with httpx.Client(timeout=15.0, verify=False) as client:
            r = client.get(base_url.rstrip("/") + "/models", headers=headers)
            print("STATUS:", r.status_code)
            print("BODY:", _safe_text(r.text))
    except Exception as e:
        print("REQUEST FAILED:", repr(e))

    _print_title("HTTP /chat/completions (verify=False)")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 8,
    }
    try:
        with httpx.Client(timeout=20.0, verify=False) as client:
            r = client.post(
                base_url.rstrip("/") + "/chat/completions",
                headers={**headers, "Content-Type": "application/json"},
                content=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            )
            print("STATUS:", r.status_code)
            print("BODY:", _safe_text(r.text))
    except Exception as e:
        print("REQUEST FAILED:", repr(e))


if __name__ == "__main__":
    main()
