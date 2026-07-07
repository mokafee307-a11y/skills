#!/usr/bin/env python3

import argparse
import datetime as dt
import getpass
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Optional
from urllib.parse import urlparse


DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_REASONING_EFFORT = "xhigh"
NON_AGENT_MODELS = {
    "dall-e-2",
    "dall-e-3",
    "gpt-image-1",
    "image-2",
}


def toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def toml_array(values) -> str:
    return json.dumps(list(values), ensure_ascii=False)


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def collapse_blank_lines(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    if text:
        return text + "\n"
    return ""


def strip_root_keys(text: str, keys) -> str:
    out = text
    for key in keys:
        out = re.sub(rf"(?m)^{re.escape(key)}\s*=.*\n?", "", out)
    return out.lstrip("\n")


def remove_section(text: str, header: str) -> str:
    pattern = re.compile(rf"(?ms)^\[{re.escape(header)}\]\n.*?(?=^\[|\Z)")
    return pattern.sub("", text)


def prepend_root_block(text: str, lines) -> str:
    block = "\n".join(lines).rstrip() + "\n"
    body = text.lstrip("\n")
    if not body:
        return block
    return block + "\n" + body


def append_section(text: str, section: str) -> str:
    base = text.rstrip()
    if not base:
        return section.rstrip() + "\n"
    return base + "\n\n" + section.rstrip() + "\n"


def derive_provider_id(base_url: str) -> str:
    parsed = urlparse(base_url)
    candidate = "_".join(
        part
        for part in [
            parsed.hostname or "",
            parsed.path.strip("/").replace("/", "_"),
        ]
        if part
    )
    candidate = re.sub(r"[^a-zA-Z0-9]+", "_", candidate).strip("_").lower()
    if not candidate:
        candidate = "custom_provider"
    if candidate[0].isdigit():
        candidate = f"provider_{candidate}"
    return candidate[:80]


def get_current_provider_id(config_text: str) -> Optional[str]:
    match = re.search(r'(?m)^model_provider\s*=\s*"([^"]+)"\s*$', config_text)
    if match:
        return match.group(1)
    return None


def normalize_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def find_provider_id_by_base_url(config_text: str, base_url: str) -> Optional[str]:
    normalized_target = normalize_base_url(base_url)
    pattern = re.compile(r"(?ms)^\[model_providers\.([^\]]+)\]\n(.*?)(?=^\[|\Z)")
    for match in pattern.finditer(config_text):
        provider_id = match.group(1)
        body = match.group(2)
        base_match = re.search(r'(?m)^base_url\s*=\s*"([^"]+)"\s*$', body)
        if base_match and normalize_base_url(base_match.group(1)) == normalized_target:
            return provider_id
    return None


def find_existing_keychain_service(config_text: str, provider_id: str) -> Optional[str]:
    pattern = re.compile(
        rf"(?ms)^\[model_providers\.{re.escape(provider_id)}\.auth\]\n(.*?)(?=^\[|\Z)"
    )
    match = pattern.search(config_text)
    if not match:
        return None

    args_match = re.search(r"(?m)^args\s*=\s*(\[[^\n]+\])\s*$", match.group(1))
    if not args_match:
        return None

    try:
        args = json.loads(args_match.group(1))
    except json.JSONDecodeError:
        return None

    for index, value in enumerate(args):
        if value == "-s" and index + 1 < len(args):
            return args[index + 1]
    return None


def find_existing_provider_name(config_text: str, provider_id: str) -> Optional[str]:
    pattern = re.compile(rf"(?ms)^\[model_providers\.{re.escape(provider_id)}\]\n(.*?)(?=^\[|\Z)")
    match = pattern.search(config_text)
    if not match:
        return None

    name_match = re.search(r'(?m)^name\s*=\s*"([^"]+)"\s*$', match.group(1))
    if name_match:
        return name_match.group(1)
    return None


def is_agent_model(model: str) -> bool:
    normalized = model.strip().lower()
    if normalized in NON_AGENT_MODELS:
        return False
    if normalized.startswith("image-"):
        return False
    if normalized.startswith("dall-e"):
        return False
    if "image" in normalized and normalized.endswith(("-1", "-2", "-3")):
        return False
    return True


def build_model_root_lines(model: str) -> list[str]:
    root_lines = [f"model = {toml_string(model)}"]
    if is_agent_model(model):
        root_lines.append(f'model_reasoning_effort = {toml_string(DEFAULT_REASONING_EFFORT)}')
    return root_lines


def backup_file(path: Path) -> Optional[Path]:
    if not path.exists():
        return None
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_name(f"{path.name}.bak-{timestamp}")
    shutil.copy2(path, backup_path)
    return backup_path


def run(cmd, *, cwd=None, check=True, capture_output=True):
    return subprocess.run(
        cmd,
        cwd=cwd,
        check=check,
        text=True,
        capture_output=capture_output,
    )


def keychain_item_exists(account: str, service: str) -> bool:
    result = subprocess.run(
        ["/usr/bin/security", "find-generic-password", "-a", account, "-s", service, "-w"],
        text=True,
        capture_output=True,
    )
    return result.returncode == 0


def store_key_in_keychain(account: str, service: str, api_key: str) -> None:
    run(
        [
            "/usr/bin/security",
            "add-generic-password",
            "-U",
            "-a",
            account,
            "-s",
            service,
            "-w",
            api_key,
        ]
    )


def build_provider_section(provider_id: str, provider_name: str, base_url: str) -> str:
    return "\n".join(
        [
            f"[model_providers.{provider_id}]",
            f"name = {toml_string(provider_name)}",
            f'base_url = {toml_string(base_url.rstrip("/"))}',
            'wire_api = "responses"',
        ]
    )


def build_provider_auth_section(provider_id: str, account: str, service: str) -> str:
    args = ["find-generic-password", "-a", account, "-s", service, "-w"]
    return "\n".join(
        [
            f"[model_providers.{provider_id}.auth]",
            'command = "/usr/bin/security"',
            f"args = {toml_array(args)}",
            "timeout_ms = 5000",
            "refresh_interval_ms = 300000",
        ]
    )


def build_project_trust_section(project_dir: Path) -> str:
    header = f'[projects.{toml_string(str(project_dir))}]'
    return "\n".join(
        [
            header,
            'trust_level = "trusted"',
        ]
    )


def update_user_config(
    *,
    config_path: Path,
    provider_id: str,
    provider_name: str,
    base_url: Optional[str],
    project_dir: Path,
    account: str,
    keychain_service: str,
    global_model: Optional[str],
) -> Optional[Path]:
    backup_path = backup_file(config_path)
    text = read_text(config_path)
    root_keys = ["model_provider"]
    if global_model:
        root_keys.extend(["model", "model_reasoning_effort"])
    text = strip_root_keys(text, root_keys)
    if base_url:
        text = remove_section(text, f"model_providers.{provider_id}.auth")
        text = remove_section(text, f"model_providers.{provider_id}")
    text = remove_section(text, f'projects.{toml_string(str(project_dir))}')
    root_lines = [f"model_provider = {toml_string(provider_id)}"]
    if global_model:
        root_lines.extend(build_model_root_lines(global_model))
    text = prepend_root_block(text, root_lines)
    if base_url:
        text = append_section(text, build_provider_section(provider_id, provider_name, base_url))
        if platform.system() == "Darwin":
            text = append_section(
                text,
                build_provider_auth_section(provider_id, account, keychain_service),
            )
    text = append_section(text, build_project_trust_section(project_dir))
    write_text(config_path, collapse_blank_lines(text))
    return backup_path


def update_project_config(*, config_path: Path, model: str) -> None:
    text = read_text(config_path)
    text = strip_root_keys(text, ["model", "model_reasoning_effort"])
    root_lines = build_model_root_lines(model)
    text = prepend_root_block(text, root_lines)
    write_text(config_path, collapse_blank_lines(text))


def verify_doctor(*, project_dir: Path, model: str, provider_id: str) -> dict:
    result = subprocess.run(
        ["codex", "doctor", "--json"],
        cwd=project_dir,
        text=True,
        capture_output=True,
    )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Unable to parse `codex doctor --json`: {exc}") from exc

    checks = payload.get("checks", {})
    config_details = checks.get("config.load", {}).get("details", {})
    doctor_model = config_details.get("model")
    doctor_provider = config_details.get("model provider")
    if doctor_model != model:
        raise RuntimeError(f"`codex doctor` model mismatch: expected {model}, got {doctor_model}")
    if doctor_provider != provider_id:
        raise RuntimeError(
            f"`codex doctor` provider mismatch: expected {provider_id}, got {doctor_provider}"
        )

    reachability = checks.get("network.provider_reachability", {})
    return {
        "raw": payload,
        "doctor_exit_code": result.returncode,
        "reachability_status": reachability.get("status"),
        "reachability_summary": reachability.get("summary"),
    }


def verify_global_doctor(*, model: str, provider_id: str) -> dict:
    with tempfile.TemporaryDirectory(prefix="codex-global-doctor-") as tmpdir:
        result = subprocess.run(
            ["codex", "doctor", "--json"],
            cwd=tmpdir,
            text=True,
            capture_output=True,
        )
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Unable to parse global `codex doctor --json`: {exc}") from exc

    checks = payload.get("checks", {})
    config_details = checks.get("config.load", {}).get("details", {})
    doctor_model = config_details.get("model")
    doctor_provider = config_details.get("model provider")
    if doctor_model != model:
        raise RuntimeError(
            f"global `codex doctor` model mismatch: expected {model}, got {doctor_model}"
        )
    if doctor_provider != provider_id:
        raise RuntimeError(
            f"global `codex doctor` provider mismatch: expected {provider_id}, got {doctor_provider}"
        )

    reachability = checks.get("network.provider_reachability", {})
    return {
        "raw": payload,
        "doctor_exit_code": result.returncode,
        "reachability_status": reachability.get("status"),
        "reachability_summary": reachability.get("summary"),
    }


def run_smoke_test(*, project_dir: Path) -> str:
    with tempfile.NamedTemporaryFile(prefix="codex-provider-smoke-", suffix=".txt", delete=False) as tmp:
        output_path = Path(tmp.name)

    try:
        result = subprocess.run(
            [
                "codex",
                "exec",
                "--ephemeral",
                "-C",
                str(project_dir),
                "-s",
                "read-only",
                "-o",
                str(output_path),
                "Reply with exactly OK and nothing else.",
            ],
            cwd=project_dir,
            text=True,
            capture_output=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "smoke test failed")

        message = output_path.read_text(encoding="utf-8").strip()
        if message != "OK":
            raise RuntimeError(f"unexpected smoke test response: {message!r}")
        return message
    finally:
        output_path.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Set up a Codex custom provider, trust the project, and pin the project model."
    )
    parser.add_argument("--base-url", help="Provider base URL. Required on first bootstrap.")
    parser.add_argument("--api-key", help="Provider API key. Recommended on first bootstrap.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Project model. Default: {DEFAULT_MODEL}")
    parser.add_argument("--project-dir", default=os.getcwd(), help="Target project directory. Default: cwd.")
    parser.add_argument("--provider-id", help="Optional custom provider id.")
    parser.add_argument("--provider-name", help="Optional custom provider display name.")
    parser.add_argument("--account", default=getpass.getuser(), help="Keychain account name on macOS.")
    parser.add_argument("--skip-smoke-test", action="store_true", help="Skip the `codex exec` smoke test.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir).expanduser().resolve()
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser().resolve()
    user_config_path = codex_home / "config.toml"
    project_config_path = project_dir / ".codex" / "config.toml"
    user_config_text = read_text(user_config_path)

    provider_id = args.provider_id
    if not provider_id and args.base_url:
        provider_id = find_provider_id_by_base_url(user_config_text, args.base_url)
    if not provider_id and args.base_url:
        provider_id = derive_provider_id(args.base_url)
    if not provider_id:
        provider_id = get_current_provider_id(user_config_text)
    if not provider_id:
        print("error: unable to resolve a provider id; pass --base-url for first bootstrap", file=sys.stderr)
        return 2

    provider_name = (
        args.provider_name
        or find_existing_provider_name(user_config_text, provider_id)
        or provider_id.replace("_", " ").title()
    )
    keychain_service = find_existing_keychain_service(user_config_text, provider_id) or f"codex-{provider_id}"

    if platform.system() == "Darwin":
        if args.api_key:
            store_key_in_keychain(args.account, keychain_service, args.api_key)
        elif args.base_url and not keychain_item_exists(args.account, keychain_service):
            print(
                "error: no keychain item found for this provider; pass --api-key on first bootstrap",
                file=sys.stderr,
            )
            return 2
    elif args.api_key:
        print(
            "warning: non-macOS environment detected; this script does not persist API keys securely outside Keychain",
            file=sys.stderr,
        )

    global_model = args.model if is_agent_model(args.model) else None
    backup_path = update_user_config(
        config_path=user_config_path,
        provider_id=provider_id,
        provider_name=provider_name,
        base_url=args.base_url,
        project_dir=project_dir,
        account=args.account,
        keychain_service=keychain_service,
        global_model=global_model,
    )
    update_project_config(config_path=project_config_path, model=args.model)

    doctor_summary = verify_doctor(project_dir=project_dir, model=args.model, provider_id=provider_id)
    global_doctor_summary = None
    if global_model:
        global_doctor_summary = verify_global_doctor(model=global_model, provider_id=provider_id)

    smoke_test = {
        "status": "skipped",
        "reason": None,
        "response": None,
    }
    if args.skip_smoke_test:
        smoke_test["reason"] = "user skipped smoke test"
    elif not is_agent_model(args.model):
        smoke_test["reason"] = f"model `{args.model}` is likely not an agent-compatible Codex chat model"
    else:
        try:
            smoke_test["response"] = run_smoke_test(project_dir=project_dir)
            smoke_test["status"] = "ok"
        except Exception as exc:
            smoke_test["status"] = "failed"
            smoke_test["reason"] = str(exc)

    result = {
        "project_dir": str(project_dir),
        "project_config": str(project_config_path),
        "user_config": str(user_config_path),
        "user_config_backup": str(backup_path) if backup_path else None,
        "provider_id": provider_id,
        "provider_name": provider_name,
        "model": args.model,
        "keychain_service": keychain_service if platform.system() == "Darwin" else None,
        "machine_wide_note": (
            "Provider configuration is machine-wide because Codex ignores project-local provider keys. "
            "For agent-compatible models, this script also syncs the user-level fallback model so new "
            "non-project threads do not fall back to an unauthorized default."
        ),
        "global_model_sync": {
            "status": "ok" if global_model else "skipped",
            "model": global_model,
            "reason": None
            if global_model
            else f"model `{args.model}` is likely not an agent-compatible Codex chat model",
        },
        "doctor": doctor_summary,
        "global_doctor": global_doctor_summary,
        "smoke_test": smoke_test,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
