#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def strip_inline_comment(raw: str) -> str:
    in_quote = False
    escaped = False
    result: list[str] = []

    for char in raw:
        if char == "\\" and not escaped:
            escaped = True
            result.append(char)
            continue

        if char == '"' and not escaped:
            in_quote = not in_quote

        if char == "#" and not in_quote:
            break

        result.append(char)
        escaped = False

    return "".join(result).strip()


def parse_string(raw: str) -> str:
    if raw.startswith('"') and raw.endswith('"'):
        raw = raw[1:-1]
    return raw.replace('\\"', '"')


def parse_array(raw: str) -> list[object]:
    inner = raw[1:-1].strip()
    if not inner:
        return []

    items: list[str] = []
    current: list[str] = []
    in_quote = False
    escaped = False

    for char in inner:
        if char == "\\" and not escaped:
            escaped = True
            current.append(char)
            continue

        if char == '"' and not escaped:
            in_quote = not in_quote

        if char == "," and not in_quote:
            items.append("".join(current).strip())
            current = []
            escaped = False
            continue

        current.append(char)
        escaped = False

    if current:
        items.append("".join(current).strip())

    return [parse_value(item) for item in items if item]


def parse_value(raw: str) -> object:
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        return parse_array(raw)
    if raw.startswith('"') and raw.endswith('"'):
        return parse_string(raw)
    if raw == "true":
        return True
    if raw == "false":
        return False
    try:
        return int(raw)
    except ValueError:
        return raw


def load_asset_map(map_path: Path) -> dict[str, object]:
    root: dict[str, object] = {}
    mappings: list[dict[str, object]] = []
    current: dict[str, object] | None = None

    for line_no, line in enumerate(map_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = strip_inline_comment(line)
        if not stripped:
            continue

        if stripped == "[[mapping]]":
            current = {}
            mappings.append(current)
            continue

        if "=" not in stripped:
            raise ValueError(f"Line {line_no}: expected `key = value`.")

        key, value = stripped.split("=", 1)
        key = key.strip()
        parsed = parse_value(value)

        if current is None:
            root[key] = parsed
        else:
            current[key] = parsed

    root["mapping"] = mappings
    return root


def resolve_source(raw: str, skill_root: Path, map_dir: Path) -> Path:
    candidate = Path(raw).expanduser()
    if candidate.is_absolute():
        return candidate

    trimmed = raw[2:] if raw.startswith("./") else raw
    primary = skill_root / trimmed
    secondary = map_dir / raw
    return primary if primary.exists() or not secondary.exists() else secondary


def main() -> int:
    skill_root = Path(__file__).resolve().parent.parent
    default_map = skill_root / "assets/svg/asset-map.toml"

    parser = argparse.ArgumentParser(description="Validate train-prototype-creator SVG asset map.")
    parser.add_argument("map_path", nargs="?", default=str(default_map), help="Path to asset-map.toml")
    args = parser.parse_args()

    map_path = Path(args.map_path).expanduser()
    if not map_path.is_absolute():
        map_path = (Path.cwd() / map_path).resolve()

    if not map_path.exists():
        print(f"ERROR: asset map not found: {map_path}")
        return 1

    data = load_asset_map(map_path)
    mappings = data.get("mapping", [])

    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(mappings, list):
        print("ERROR: `mapping` must be an array of tables.")
        return 1

    seen_keys: set[str] = set()
    seen_output_names: dict[str, str] = {}
    existing_files = 0
    required_missing = 0

    for index, item in enumerate(mappings, start=1):
        key = str(item.get("key", "")).strip()
        source = str(item.get("source", "")).strip()
        output_name = str(item.get("output_name", "")).strip()
        required = bool(item.get("required", False))

        label = key or f"<missing-key:{index}>"

        if not key:
            errors.append(f"mapping[{index}] is missing `key`.")
        elif key in seen_keys:
            errors.append(f"duplicate key: {key}")
        else:
            seen_keys.add(key)

        if not source:
            if required:
                required_missing += 1
                errors.append(f"{label}: required mapping is missing `source`.")
            else:
                warnings.append(f"{label}: no `source` configured yet.")
        else:
            source_path = resolve_source(source, skill_root, map_path.parent)
            if source_path.exists():
                existing_files += 1
            else:
                if required:
                    required_missing += 1
                    errors.append(f"{label}: required source file missing: {source_path}")
                else:
                    warnings.append(f"{label}: source file not found yet: {source_path}")

        if output_name:
            owner = seen_output_names.get(output_name)
            if owner and owner != key:
                warnings.append(f"{label}: output_name `{output_name}` already used by `{owner}`.")
            else:
                seen_output_names[output_name] = key or label

    print(f"Asset map: {map_path}")
    print(f"Mappings: {len(mappings)}")
    print(f"Existing SVG files: {existing_files}")
    print(f"Missing required files: {required_missing}")

    if warnings:
        print("\nWarnings:")
        for message in warnings:
            print(f"- {message}")

    if errors:
        print("\nErrors:")
        for message in errors:
            print(f"- {message}")
        return 1

    print("\nValidation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
