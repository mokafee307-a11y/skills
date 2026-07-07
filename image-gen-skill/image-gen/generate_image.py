#!/usr/bin/env python3
"""
Config is read from the same directory as this script: image-gen-config.json
Usage: python generate_image.py --prompt "..." --image "/path/to/a.png" [--image "/path/to/b.png"] --output "output.png"
Multiple --image flags accepted; sent as image, image[], image[]...
"""

import requests
import base64
import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()


def load_config() -> dict:
    config_path = SCRIPT_DIR / "image-gen-config.json"
    if not config_path.exists():
        print(f"ERROR: Config file not found at {config_path}", file=sys.stderr)
        sys.exit(1)
    with open(config_path) as f:
        cfg = json.load(f)
    if cfg.get("api_key") == "YOUR_API_KEY_HERE":
        print("ERROR: Please fill in your api_key in image-gen-config.json", file=sys.stderr)
        sys.exit(1)
    return cfg


def generate_image(prompt: str, image_paths: list, output_path: str,
                   size: str = "auto", quality: str = "auto", n: int = 1) -> str:
    config = load_config()
    api_key = config["api_key"]
    api_key_id = config["api_key_id"]
    base_url = config.get("base_url", "http://aigw.fx.ctripcorp.com/llm")
    timeout = int(config.get("timeout_seconds", 300))
    url = f"{base_url}/{api_key_id}/images/edits"

    mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}

    # First image uses key "image", additional images use "image[]"
    files = []
    for i, image_path in enumerate(image_paths):
        img = Path(image_path)
        if not img.exists():
            print(f"ERROR: Image file not found: {image_path}", file=sys.stderr)
            sys.exit(1)
        mime_type = mime_map.get(img.suffix.lower(), "image/png")
        key = "image" if i == 0 else "image[]"
        files.append((key, (img.name, open(image_path, "rb"), mime_type)))

    data = {"model": "gpt-image-2", "prompt": prompt, "size": size, "n": n, "quality": quality}
    headers = {"Authorization": f"Bearer {api_key}"}

    print(f"Calling API: {url}", file=sys.stderr)
    print(f"Images ({len(image_paths)}): {image_paths}", file=sys.stderr)
    print(f"Prompt: {prompt}", file=sys.stderr)
    print(f"Timeout: {timeout}s", file=sys.stderr)

    response = requests.post(url, headers=headers, files=files, data=data, timeout=timeout)

    if response.status_code != 200:
        print(f"ERROR: API returned {response.status_code}: {response.text}", file=sys.stderr)
        sys.exit(1)

    result = response.json()

    if "data" in result and len(result["data"]) > 0:
        image_bytes = base64.b64decode(result["data"][0]["b64_json"])
        with open(output_path, "wb") as f:
            f.write(image_bytes)
        print(f"SUCCESS: Image saved to {output_path}")
        return output_path
    else:
        print(f"ERROR: Unexpected API response: {result}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate/edit image using gpt-image-2")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--image", action="append", required=True, dest="images",
                        help="Input image path (repeat flag for multiple images)")
    parser.add_argument("--output", default="output.png")
    parser.add_argument("--size", default="auto")
    parser.add_argument("--quality", default="auto")
    parser.add_argument("--n", type=int, default=1)
    args = parser.parse_args()
    generate_image(args.prompt, args.images, args.output, args.size, args.quality, args.n)
