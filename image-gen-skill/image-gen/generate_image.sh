#!/usr/bin/env bash
# generate_image.sh — curl-based image generation via gpt-image-2
# Usage: bash generate_image.sh --prompt "..." --image "/path/a.png" [--image "/path/b.png"] --output "output.png"
# Multiple --image flags accepted.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$SCRIPT_DIR/image-gen-config.json"

# ---------- parse args ----------
PROMPT=""
IMAGE_PATHS=()
OUTPUT="output.png"
SIZE="auto"
QUALITY="auto"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prompt)   PROMPT="$2";                  shift 2 ;;
    --image)    IMAGE_PATHS+=("$2");          shift 2 ;;
    --output)   OUTPUT="$2";                  shift 2 ;;
    --size)     SIZE="$2";                    shift 2 ;;
    --quality)  QUALITY="$2";                 shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

[[ -z "$PROMPT" ]]           && echo "ERROR: --prompt is required" >&2 && exit 1
[[ ${#IMAGE_PATHS[@]} -eq 0 ]] && echo "ERROR: at least one --image is required" >&2 && exit 1

# ---------- read config ----------
if [[ ! -f "$CONFIG" ]]; then
  echo "ERROR: Config file not found at $CONFIG" >&2
  exit 1
fi

if command -v python3 &>/dev/null; then
  API_KEY=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c['api_key'])")
  API_KEY_ID=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c['api_key_id'])")
  BASE_URL=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c.get('base_url','http://aigw.fx.ctripcorp.com/llm'))")
  TIMEOUT=$(python3 -c "import json; c=json.load(open('$CONFIG')); print(c.get('timeout_seconds',300))")
elif command -v jq &>/dev/null; then
  API_KEY=$(jq -r '.api_key' "$CONFIG")
  API_KEY_ID=$(jq -r '.api_key_id' "$CONFIG")
  BASE_URL=$(jq -r '.base_url // "http://aigw.fx.ctripcorp.com/llm"' "$CONFIG")
  TIMEOUT=$(jq -r '.timeout_seconds // 300' "$CONFIG")
else
  API_KEY=$(grep '"api_key"' "$CONFIG" | sed 's/.*"api_key"[[:space:]]*:[[:space:]]*"\(.*\)".*/\1/')
  API_KEY_ID=$(grep '"api_key_id"' "$CONFIG" | sed 's/.*"api_key_id"[[:space:]]*:[[:space:]]*"\(.*\)".*/\1/')
  BASE_URL=$(grep '"base_url"' "$CONFIG" | sed 's/.*"base_url"[[:space:]]*:[[:space:]]*"\(.*\)".*/\1/')
  BASE_URL="${BASE_URL:-http://aigw.fx.ctripcorp.com/llm}"
  TIMEOUT=300
fi

if [[ "$API_KEY" == "YOUR_API_KEY_HERE" ]]; then
  echo "ERROR: Please fill in your api_key in $CONFIG" >&2
  exit 1
fi

# ---------- validate images ----------
for IMG in "${IMAGE_PATHS[@]}"; do
  [[ ! -f "$IMG" ]] && echo "ERROR: Image file not found: $IMG" >&2 && exit 1
done

URL="${BASE_URL}/${API_KEY_ID}/images/edits"

echo "Calling API: $URL" >&2
echo "Images (${#IMAGE_PATHS[@]}): ${IMAGE_PATHS[*]}" >&2
echo "Prompt: $PROMPT" >&2
echo "Timeout: ${TIMEOUT}s" >&2

# ---------- build curl -F image args ----------
# First image: -F "image=@path", subsequent: -F "image[]=@path"
IMAGE_ARGS=()
for i in "${!IMAGE_PATHS[@]}"; do
  if [[ $i -eq 0 ]]; then
    IMAGE_ARGS+=(-F "image=@${IMAGE_PATHS[$i]}")
  else
    IMAGE_ARGS+=(-F "image[]=@${IMAGE_PATHS[$i]}")
  fi
done

# ---------- call API ----------
RESPONSE=$(curl -s --max-time "$TIMEOUT" -w "\n__HTTP_CODE__:%{http_code}" \
  -X POST "$URL" \
  -H "Authorization: Bearer $API_KEY" \
  "${IMAGE_ARGS[@]}" \
  -F "model=gpt-image-2" \
  -F "prompt=${PROMPT}" \
  -F "size=${SIZE}" \
  -F "quality=${QUALITY}" \
  -F "n=1")

HTTP_CODE=$(echo "$RESPONSE" | tail -1 | sed 's/__HTTP_CODE__://')
BODY=$(echo "$RESPONSE" | sed '$d')

if [[ "$HTTP_CODE" != "200" ]]; then
  echo "ERROR: API returned $HTTP_CODE: $BODY" >&2
  exit 1
fi

# ---------- decode base64 image ----------
if command -v python3 &>/dev/null; then
  B64=$(python3 -c "import json,sys; d=json.loads(sys.stdin.read()); print(d['data'][0]['b64_json'])" <<< "$BODY")
  python3 -c "import base64,sys; open('$OUTPUT','wb').write(base64.b64decode(sys.stdin.read().strip()))" <<< "$B64"
elif command -v jq &>/dev/null; then
  jq -r '.data[0].b64_json' <<< "$BODY" | base64 --decode > "$OUTPUT"
else
  B64=$(echo "$BODY" | grep -o '"b64_json":"[^"]*"' | sed 's/"b64_json":"//;s/"//')
  echo "$B64" | base64 --decode > "$OUTPUT"
fi

echo "SUCCESS: Image saved to $OUTPUT"
