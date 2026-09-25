"""Deploy static web assets with an existing Antideploy account token."""
import io
import json
from pathlib import Path
import tarfile
import time
import urllib.error
import urllib.request
import uuid

BASE = Path(__file__).resolve().parents[1]
API = "https://antideploy.com"


def main():
    credential_file = Path.home() / ".antideploy" / "config.json"
    if not credential_file.exists():
        raise SystemExit("Connect your account first: https://antideploy.com/docs/api/terminal-login")
    token = json.loads(credential_file.read_text(encoding="utf-8-sig"))["token"]
    application = json.loads((BASE / ".antideploy.json").read_text(encoding="utf-8"))["applicationId"]
    archive = io.BytesIO()
    web = BASE / "web"
    with tarfile.open(fileobj=archive, mode="w:gz") as tar:
        for file in sorted(web.rglob("*")):
            if not file.is_file():
                continue
            if file.is_symlink() or file.suffix not in {".html", ".css", ".js", ".svg"}:
                raise SystemExit(f"Unexpected web asset; review before uploading: {file.name}")
            if any(part.startswith(".") for part in file.relative_to(web).parts):
                raise SystemExit("Hidden files must not be deployed.")
            tar.add(file, arcname=file.relative_to(web).as_posix())
    boundary = "jarvis-" + uuid.uuid4().hex
    body = (
        f'--{boundary}\r\nContent-Disposition: form-data; name="archive"; filename="web.tar.gz"\r\n'
        'Content-Type: application/gzip\r\n\r\n'
    ).encode() + archive.getvalue() + f"\r\n--{boundary}--\r\n".encode()

    def call(path, data=None, content_type=None):
        headers = {"Authorization": f"Bearer {token}"}
        if content_type:
            headers["Content-Type"] = content_type
        request = urllib.request.Request(API + path, data=data, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace").replace(token, "[REDACTED]")
            raise SystemExit(f"Antideploy HTTP {exc.code}: {detail}") from None

    result = call(f"/api/v1/deploy?applicationId={application}", body, f"multipart/form-data; boundary={boundary}")
    if result.get("status") == "unchanged":
        print("Web assets unchanged; no new deployment needed.")
        return
    task = result["taskId"]
    print(f"Deployment queued: {task}", flush=True)
    previous = None
    deadline = time.monotonic() + 900
    while time.monotonic() < deadline:
        result = call(f"/api/v1/deployments/{task}")
        state = result.get("status")
        if state != previous:
            print(f"Status: {state}", flush=True)
            previous = state
        if state in {"succeeded", "failed"}:
            print(json.dumps(result, indent=2).replace(token, "[REDACTED]"), flush=True)
            if state == "failed":
                raise SystemExit(1)
            return
        time.sleep(5)
    raise SystemExit(f"Still running after 15 minutes. Inspect task {task} before retrying.")


if __name__ == "__main__":
    main()
