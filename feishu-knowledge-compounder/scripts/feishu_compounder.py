#!/usr/bin/env python3
"""Bootstrap a Feishu Base, sync distilled notes, and send reminders."""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import io
import json
import math
import os
import re
import sys
import time
import unicodedata
import uuid
import zlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from urllib import error, parse, request

DEFAULT_CONFIG_ENV = "FEISHU_COMPOUNDER_CONFIG"
API_ROOT = "https://open.feishu.cn"
SKILL_ROOT = Path(__file__).resolve().parents[1]
PLACEHOLDER_ELLIPSIS_RE = re.compile(r"\.\.\.|…")
MARKDOWN_EMPHASIS_RE = re.compile(r"(\*\*|__)(.*?)\1")

TABLE_SPECS = {
    "conversations": {
        "name": "对话沉淀",
        "fields": [
            "标题",
            "对话ID",
            "日期",
            {"field_name": "标签", "type": 4},
            {"field_name": "对话Agent", "type": 4},
            {"field_name": "贡献者", "type": 11, "property": {"multiple": True}},
            {"field_name": "摘要", "type": 15},
            "来源",
            "TLDR主题",
            "本次新增",
            "价值",
            "核心资产",
            "方法论",
            "认知演进",
            "知识演化图谱",
            "下一步行动",
            "关联资产",
            "参考案例",
            "同步时间",
        ],
    },
    "gaps": {
        "name": "不足追踪",
        "fields": [
            "标题",
            "对话ID",
            "日期",
            "来源主题",
            "不足",
            "重要性",
            "弥补动作",
            "复盘日期",
            "优先级",
            "状态",
        ],
    },
    "reading": {
        "name": "阅读队列",
        "fields": [
            "书名",
            "对话ID",
            "日期",
            "来源主题",
            "作者",
            "推荐理由",
            "优先级",
            "类型",
            "状态",
            {"field_name": "推荐次数", "type": 2, "property": {"formatter": "0"}},
            {"field_name": "封面图", "type": 17},
            {"field_name": "在线地址", "type": 15},
            {"field_name": "提及频率", "type": 2, "property": {"formatter": "0"}},
            {"field_name": "精华标签", "type": 4},
        ],
    },
}

CONVERSATION_LEGACY_FIELD_NAMES = (
    "主题",
    "讨论问题",
    "摘要正文",
    "工作流",
    "核心洞察",
    "心智模型",
    "知识缺口",
    "后续思考方向",
    "行动建议",
    "阅读建议",
    "原始上下文",
    "提醒摘要",
    "领域",
)
LEGACY_TABLE_KEYS = ("gaps", "reading")

READING_GALLERY_VIEW_NAME = "阅读画册"
READING_GALLERY_CONFIG_KEY = "reading_gallery_url"
DASHBOARD_DOC_CONFIG_KEY = "dashboard_doc_url"
DASHBOARD_DOC_ID_CONFIG_KEY = "dashboard_doc_document_id"
DASHBOARD_TARGET_URL_CONFIG_KEY = "dashboard_target_url"
TARGET_FALLBACK_CONFIRMATION_CONFIG_KEY = "require_confirmation_before_target_fallback"
DOC_ROOT_URL_CONFIG_KEY = "document_root_url"
DEFAULT_DASHBOARD_TITLE = "AI 知识复利仪表盘"
RECENT_ACTIVITY_WINDOW_DAYS = 30
BOOK_METADATA_PATH = SKILL_ROOT / "references" / "book-metadata.json"
DEFAULT_BOOK_COVER_PATH = SKILL_ROOT / "assets" / "default-book-cover.png"
NO_NETWORK_LINK_TEXT = "暂无网络链接"
CONVERSATION_TITLE_FIELDS = ("标题", "主题")
DOCX_URL_PREFIX = "https://trip.larkenterprise.com/docx"
WIKI_URL_PREFIX = "https://trip.larkenterprise.com/wiki"
TEAM_ASSET_MAX_ITEMS = 5
TEAM_ASSET_MAX_CHARS = 32
MAX_TOPIC_TAGS = 3
LOW_PRIORITY_TOPIC_TAG_MARKERS = (
    "html",
    "png",
    "svg",
    "figma",
    "ctrip",
    "mcommute",
    "uikit",
    "skill",
    "token",
    "demo",
    "push",
    "deployed",
    "rollback",
    "sourceoftruth",
    "scopecontrol",
)
KNOWLEDGE_GRAPH_FIELD_NAME = "知识演化图谱"
KNOWLEDGE_GRAPH_SECTION_TITLE = "知识演化图谱"
CONTRIBUTOR_FIELD_NAME = "贡献者"
DOC_PERMISSION_HINT = (
    "当前飞书应用还没有开通教程文档所需权限。"
    "请在飞书开放平台为这个应用开通 docx:document 或 docx:document:create；"
    "如果你希望走文件上传链路，也可以补 drive:file:upload。"
)
WIKI_PERMISSION_HINT = (
    "如果你想把教程文档挂到某个知识库页面下面，"
    "请在飞书开放平台为这个应用开通 wiki:node:read 与 wiki:node:create，"
    "或直接开通 wiki:wiki。"
)

DESIGN_STAGE_RULES = [
    {
        "name": "问题定义",
        "keywords": [
            "需求",
            "问题",
            "目标",
            "用户",
            "场景",
            "现状",
            "洞察",
            "定义",
            "why",
        ],
        "chart_type": "横向条形图",
    },
    {
        "name": "方法搭建",
        "keywords": [
            "工作流",
            "workflow",
            "skill",
            "自动化",
            "知识库",
            "知识复利",
            "飞书",
            "schema",
            "结构",
            "搭建",
            "系统",
            "agent",
        ],
        "chart_type": "柱状图",
    },
    {
        "name": "方案设计",
        "keywords": [
            "方案",
            "策略",
            "框架",
            "信息架构",
            "交互",
            "仪表盘",
            "页面",
            "模版",
            "设计",
        ],
        "chart_type": "堆叠条形图",
    },
    {
        "name": "原型验证",
        "keywords": [
            "原型",
            "prototype",
            "figma",
            "html",
            "png",
            "验证",
            "测试",
            "评测",
            "交互原型",
        ],
        "chart_type": "折线图",
    },
    {
        "name": "协作交付",
        "keywords": [
            "发布",
            "权限",
            "提醒",
            "推送",
            "同步",
            "文档",
            "交付",
            "通知",
            "链接",
        ],
        "chart_type": "漏斗图",
    },
    {
        "name": "复盘沉淀",
        "keywords": [
            "复盘",
            "沉淀",
            "总结",
            "教程",
            "知识缺口",
            "阅读建议",
            "思考方向",
            "复利",
            "学习",
        ],
        "chart_type": "环形图",
    },
]


class FeishuError(RuntimeError):
    """Raised when a Feishu API request fails."""


def now_iso() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def today_str() -> str:
    return datetime.now().date().isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_dotenv_file(path: Path, *, override: bool = False) -> bool:
    if not path.exists():
        return False

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if override or key not in os.environ:
            os.environ[key] = value
    return True


def auto_load_dotenv(explicit_path: str | None = None) -> list[str]:
    candidates: list[Path] = []
    if explicit_path:
        candidates.append(Path(explicit_path).expanduser())
    else:
        candidates.extend([Path.cwd() / ".env", SKILL_ROOT / ".env"])

    loaded: list[str] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve() if candidate.exists() else candidate
        if resolved in seen:
            continue
        seen.add(resolved)
        if load_dotenv_file(candidate):
            loaded.append(str(candidate))
    return loaded


def env_nonempty(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    value = value.strip()
    return value or None


def first_present(mapping: dict[str, Any], *keys: str, default: Any = "") -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return default


def as_list(value: Any) -> list[Any]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]


def compact_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return "\n".join(compact_text(item) for item in value if compact_text(item))
    return json.dumps(value, ensure_ascii=False)


def sanitize_tutorial_text(value: Any) -> str:
    text = compact_text(value)
    if not text:
        return ""
    previous = None
    while previous != text:
        previous = text
        text = MARKDOWN_EMPHASIS_RE.sub(r"\2", text)
    text = text.replace("**", "").replace("__", "")
    return text.strip()


def simple_sentence_excerpt(value: Any, *, max_chars: int = 90) -> str:
    text = re.sub(r"\s+", " ", sanitize_tutorial_text(value)).strip()
    if not text:
        return ""
    text = re.split(r"[。！？!?；;\n]", text, maxsplit=1)[0].strip(" ，,;；。")
    if len(text) <= max_chars:
        return text
    clauses = re.split(r"([，,])", text)
    selected: list[str] = []
    pending = ""
    for part in clauses:
        pending += part
        if part in {"，", ","}:
            candidate = "".join(selected + [pending]).rstrip("，, ")
            if selected and len(candidate) > max_chars:
                break
            selected.append(pending)
            pending = ""
    if pending.strip():
        candidate = "".join(selected + [pending]).rstrip("，, ")
        if not selected or len(candidate) <= max_chars:
            selected.append(pending)
    return "".join(selected).rstrip("，, ") or text


def ellipsis_paths(value: Any, path: str = "$") -> list[str]:
    if isinstance(value, str):
        return [path] if PLACEHOLDER_ELLIPSIS_RE.search(value) else []
    if isinstance(value, list):
        paths: list[str] = []
        for index, item in enumerate(value):
            paths.extend(ellipsis_paths(item, f"{path}[{index}]"))
        return paths
    if isinstance(value, dict):
        paths = []
        for key, item in value.items():
            paths.extend(ellipsis_paths(item, f"{path}.{key}"))
        return paths
    return []


def validate_no_placeholder_ellipsis(raw_note: dict[str, Any]) -> None:
    paths = ellipsis_paths(raw_note)
    if not paths:
        return
    preview = "、".join(paths[:8])
    extra = f" 等 {len(paths)} 处" if len(paths) > 8 else ""
    raise FeishuError(
        f"Note JSON 里还有省略号占位：{preview}{extra}。"
        "请把内容改写成完整短句，言简意赅说清楚事情，不要用 ... 或 … 代替具体内容。"
    )


def parse_boolish(value: Any, default: bool = False) -> bool:
    text = compact_text(value).lower()
    if not text:
        return default
    if text in {"1", "true", "yes", "y", "on", "是", "好", "需要"}:
        return True
    if text in {"0", "false", "no", "n", "off", "否", "不要", "不需要"}:
        return False
    return default


def bullet_block(items: list[str]) -> str:
    cleaned = [item.strip() for item in items if item and item.strip()]
    return "\n".join(f"- {item}" for item in cleaned)


def sanitized_bullet_block(items: list[str]) -> str:
    return bullet_block([sanitize_tutorial_text(item) for item in items])


def reusable_asset_label(value: Any, *, max_chars: int = TEAM_ASSET_MAX_CHARS) -> str:
    text = re.sub(r"\s+", " ", sanitize_tutorial_text(value)).strip(" -，,。；;")
    if not text:
        return ""
    text = re.sub(r"^(?:可复用|可直接复用|核心资产|资产|输出|产出|沉淀)\s*[:：]\s*", "", text)
    if len(text) <= max_chars:
        return text
    for separator in ("而不是", "不是", "需要", "应该", "：", ":", "，", ",", "；", ";", "。", "是", "包括", "用于", "比", "与"):
        if separator in text:
            head = text.split(separator, 1)[0].strip(" -，,。；;")
            if 4 <= len(head) <= max_chars:
                return head
    return first_sentence_excerpt(text, max_chars=max_chars)


def reusable_asset_points(values: list[Any], *, max_items: int = TEAM_ASSET_MAX_ITEMS) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for value in values:
        source_items = split_bullets(compact_text(value)) or [compact_text(value)]
        for source_item in source_items:
            label = reusable_asset_label(source_item)
            if not label:
                continue
            key = normalize_general_key(label) or label
            if key in seen:
                continue
            seen.add(key)
            items.append(label)
            if len(items) >= max_items:
                return items
    return items


def join_tags(items: list[str]) -> str:
    cleaned = [item.strip() for item in items if item and item.strip()]
    return ", ".join(cleaned)


def normalize_general_key(value: Any) -> str:
    text = compact_text(value)
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKC", text).lower()
    normalized = re.sub(r"[\s\-_/]+", "", normalized)
    normalized = re.sub(r"[^\w\u4e00-\u9fff]+", "", normalized)
    return normalized


def normalize_lookup_key(value: Any) -> str:
    text = compact_text(value)
    if not text:
        return ""
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return " ".join(part for part in normalized.split() if part)


def normalize_field_spec(field: Any) -> dict[str, Any]:
    if isinstance(field, str):
        return {"field_name": field, "type": 1}
    return {
        "field_name": field["field_name"],
        "type": field["type"],
        **({"property": field["property"]} if field.get("property") else {}),
    }


def table_field_specs(table_spec: dict[str, Any]) -> list[dict[str, Any]]:
    return [normalize_field_spec(field) for field in table_spec["fields"]]


def table_field_names(table_spec: dict[str, Any]) -> list[str]:
    return [field["field_name"] for field in table_field_specs(table_spec)]


def create_legacy_tables_by_default() -> bool:
    return parse_boolish(env_nonempty("FEISHU_CREATE_LEGACY_TABLES"), default=False)


def active_table_specs(*, include_legacy: bool | None = None) -> dict[str, dict[str, Any]]:
    use_legacy = create_legacy_tables_by_default() if include_legacy is None else include_legacy
    if use_legacy:
        return TABLE_SPECS
    return {"conversations": TABLE_SPECS["conversations"]}


def split_multi_value_text(text: str) -> list[str]:
    raw = compact_text(text)
    if not raw:
        return []
    parts = re.split(r"\s*(?:,|，|、|/|;|；|\n)\s*", raw)
    return [part.strip() for part in parts if part and part.strip()]


def normalize_multi_values(value: Any) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for entry in as_list(value):
        if isinstance(entry, str):
            parts = split_multi_value_text(entry)
        else:
            text = compact_text(entry)
            parts = [text] if text else []
        for part in parts:
            key = normalize_general_key(part) or part
            if key in seen:
                continue
            seen.add(key)
            items.append(part)
    return items


def merge_bullet_blocks(values: list[Any]) -> str:
    items: list[str] = []
    seen: set[str] = set()
    for value in values:
        for item in split_bullets(compact_text(value)):
            key = normalize_general_key(item) or item
            if key in seen:
                continue
            seen.add(key)
            items.append(item)
    return bullet_block(items)


def load_book_metadata_overrides() -> dict[str, dict[str, Any]]:
    if not BOOK_METADATA_PATH.exists():
        return {}
    raw = read_json(BOOK_METADATA_PATH)
    return {normalize_lookup_key(key): value for key, value in raw.items()}


def reading_online_field(title: Any, url: Any) -> dict[str, str]:
    label = compact_text(title) or NO_NETWORK_LINK_TEXT
    link = compact_text(url)
    if link:
        return {"text": label, "link": link}
    return {"text": NO_NETWORK_LINK_TEXT, "link": "about:blank"}


def reading_online_link(value: Any) -> str:
    if isinstance(value, dict):
        text = compact_text(value.get("text"))
        link = compact_text(value.get("link"))
        if text == NO_NETWORK_LINK_TEXT and link in ("", "about:blank", "http://暂无网络链接"):
            return ""
        return link
    text = compact_text(value)
    if text == NO_NETWORK_LINK_TEXT:
        return ""
    return text


def reading_online_text(value: Any) -> str:
    if isinstance(value, dict):
        return compact_text(value.get("text")) or compact_text(value.get("link"))
    return compact_text(value)


def has_reading_cover(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0


@dataclass
class GapItem:
    gap: str
    why_it_matters: str = ""
    suggested_practice: str = ""
    review_on: str = ""
    priority: str = "medium"
    status: str = "待行动"


@dataclass
class BookItem:
    title: str
    author: str = ""
    reason: str = ""
    priority: str = "medium"
    kind: str = "book"
    status: str = "待读"
    online_url: str = ""
    cover_url: str = ""
    tags: list[str] | None = None


@dataclass
class TldrPayload:
    topic: str = ""
    new_this_round: str = ""
    value: str = ""


@dataclass
class MethodologyPayload:
    name: str = ""
    steps: list[str] | None = None


@dataclass
class EvolutionPayload:
    previous_belief: str = ""
    current_belief: str = ""


@dataclass
class ActionItem:
    todo: str
    priority: str = "medium"
    status: str = "todo"


@dataclass
class ReferenceItem:
    name: str
    why: str = ""
    url: str = ""


@dataclass
class SourcePayload:
    type: str = ""
    name: str = ""
    url: str = ""
    date: str = ""


@dataclass
class ContributorPayload:
    name: str = ""
    open_id: str = ""


@dataclass
class RelatedAssetItem:
    title: str
    relation: str = ""
    url: str = ""


@dataclass
class NotePayload:
    conversation_key: str
    title: str
    conversation_date: str
    tags: list[str]
    agent: str
    tldr: TldrPayload
    core_outputs: list[str]
    workflow: list[str]
    methodology: MethodologyPayload
    evolution: EvolutionPayload
    next_actions: list[ActionItem]
    related_assets: list[RelatedAssetItem]
    references: list[ReferenceItem]
    source: SourcePayload
    contributors: list[ContributorPayload]
    discussion_points: list[str]
    summary: str
    key_insights: list[str]
    mental_models: list[str]
    blind_spots: list[GapItem]
    next_thinking_directions: list[str]
    actions: list[str]
    recommended_books: list[BookItem]
    source_context: str
    reminder: str


def normalize_gap(item: Any) -> GapItem:
    if isinstance(item, str):
        return GapItem(gap=item.strip())
    if not isinstance(item, dict):
        return GapItem(gap=compact_text(item))
    return GapItem(
        gap=first_present(item, "gap", "blind_spot", "不足", "缺口"),
        why_it_matters=first_present(item, "why_it_matters", "importance", "重要性", "原因"),
        suggested_practice=first_present(
            item,
            "suggested_practice",
            "next_step",
            "suggested_action",
            "弥补动作",
            "下一步",
        ),
        review_on=first_present(item, "review_on", "review_date", "复盘日期", "复习日期"),
        priority=first_present(item, "priority", "优先级", default="medium"),
        status=first_present(item, "status", "状态", default="待行动"),
    )


def normalize_book(item: Any) -> BookItem:
    if isinstance(item, str):
        return BookItem(title=item.strip())
    if not isinstance(item, dict):
        return BookItem(title=compact_text(item))
    tags = [
        compact_text(tag)
        for tag in as_list(first_present(item, "tags", "labels", "精华标签", default=[]))
        if compact_text(tag)
    ]
    return BookItem(
        title=first_present(item, "title", "book", "书名"),
        author=first_present(item, "author", "作者"),
        reason=first_present(item, "reason", "why", "推荐理由"),
        priority=first_present(item, "priority", "优先级", default="medium"),
        kind=first_present(item, "type", "kind", "类型", default="book"),
        status=first_present(item, "status", "状态", default="待读"),
        online_url=first_present(item, "online_url", "url", "link", "在线地址"),
        cover_url=first_present(item, "cover_url", "cover", "封面图", "封面地址"),
        tags=tags or None,
    )


def normalize_tldr(raw: dict[str, Any], *, title: str) -> TldrPayload:
    value = first_present(raw, "tldr", "TLDR", "tl;dr", "速览", default={})
    if isinstance(value, dict):
        topic = first_present(value, "topic", "主题", default=title)
        new_this_round = first_present(
            value,
            "new_this_round",
            "new",
            "本次新增",
            "新增",
            default="",
        )
        asset_value = first_present(value, "value", "价值", default="")
    else:
        topic = title
        new_this_round = value
        asset_value = ""

    legacy_summary = compact_text(first_present(raw, "summary", "摘要", default=""))
    return TldrPayload(
        topic=compact_text(topic) or title,
        new_this_round=compact_text(new_this_round) or simple_sentence_excerpt(legacy_summary, max_chars=72),
        value=compact_text(asset_value),
    )


def normalize_methodology(item: Any) -> MethodologyPayload:
    if isinstance(item, dict):
        name = first_present(item, "name", "名称", "方法名", default="")
        steps = [
            compact_text(step)
            for step in as_list(first_present(item, "steps", "流程", "步骤", default=[]))
            if compact_text(step)
        ]
        return MethodologyPayload(name=compact_text(name), steps=steps)
    text = compact_text(item)
    return MethodologyPayload(name=text, steps=[])


def normalize_evolution(item: Any) -> EvolutionPayload:
    if isinstance(item, dict):
        return EvolutionPayload(
            previous_belief=first_present(
                item,
                "previous_belief",
                "previous",
                "before",
                "原认知",
                "旧认知",
                default="",
            ),
            current_belief=first_present(
                item,
                "current_belief",
                "current",
                "after",
                "新认知",
                "当前认知",
                default="",
            ),
        )
    text = compact_text(item)
    return EvolutionPayload(current_belief=text)


def normalize_action(item: Any) -> ActionItem:
    if isinstance(item, str):
        return ActionItem(todo=item.strip())
    if not isinstance(item, dict):
        return ActionItem(todo=compact_text(item))
    todo = first_present(item, "todo", "action", "next_action", "任务", "行动", "事项", default="")
    return ActionItem(
        todo=compact_text(todo),
        priority=first_present(item, "priority", "优先级", default="medium"),
        status=first_present(item, "status", "状态", default="todo"),
    )


def action_from_gap(gap: GapItem) -> ActionItem:
    todo = gap.suggested_practice or gap.gap
    return ActionItem(todo=todo, priority=gap.priority, status=gap.status)


def normalize_reference(item: Any) -> ReferenceItem:
    if isinstance(item, str):
        return ReferenceItem(name=item.strip())
    if not isinstance(item, dict):
        return ReferenceItem(name=compact_text(item))
    return ReferenceItem(
        name=first_present(item, "name", "title", "case", "reference", "名称", "案例", "书名", default=""),
        why=first_present(item, "why", "reason", "推荐理由", "参考原因", default=""),
        url=first_present(item, "url", "link", "online_url", "在线地址", default=""),
    )


def normalize_source(item: Any, *, source_context: str = "", conversation_date: str = "") -> SourcePayload:
    if isinstance(item, dict):
        return SourcePayload(
            type=first_present(item, "type", "source_type", "来源类型", default="conversation"),
            name=first_present(item, "name", "title", "description", "来源", "名称", default=source_context),
            url=first_present(item, "url", "link", "source_url", "链接", default=""),
            date=first_present(item, "date", "source_date", "日期", default=conversation_date),
        )
    text = compact_text(item) or source_context
    return SourcePayload(type="conversation", name=text, date=conversation_date)


def default_contributor() -> ContributorPayload:
    return ContributorPayload(
        name=compact_text(env_nonempty("FEISHU_CONTRIBUTOR_NAME") or env_nonempty("CONTRIBUTOR_NAME")),
        open_id=compact_text(
            env_nonempty("FEISHU_CONTRIBUTOR_OPEN_ID")
            or env_nonempty("CONTRIBUTOR_OPEN_ID")
            or env_nonempty("FEISHU_NOTIFY_OPEN_ID")
        ),
    )


def normalize_contributor(item: Any) -> ContributorPayload:
    if isinstance(item, dict):
        return ContributorPayload(
            name=compact_text(first_present(item, "name", "display_name", "title", "名称", "姓名", default="")),
            open_id=compact_text(
                first_present(
                    item,
                    "open_id",
                    "openId",
                    "id",
                    "user_open_id",
                    "飞书open_id",
                    "飞书 Open ID",
                    default="",
                )
            ),
        )
    text = compact_text(item)
    if text.startswith("ou_"):
        return ContributorPayload(open_id=text)
    return ContributorPayload(name=text)


def normalize_contributors(raw: dict[str, Any]) -> list[ContributorPayload]:
    values = as_list(first_present(raw, "contributors", "贡献者", default=[]))
    single = first_present(raw, "contributor", "author", "owner", "沉淀人", "贡献人", default=None)
    if single is not None:
        values.append(single)
    contributors = [
        contributor
        for contributor in (normalize_contributor(item) for item in values)
        if contributor.name or contributor.open_id
    ]
    default_item = default_contributor()
    if not contributors and (default_item.name or default_item.open_id):
        contributors = [default_item]

    seen: set[str] = set()
    unique: list[ContributorPayload] = []
    for contributor in contributors:
        key = contributor.open_id or normalize_general_key(contributor.name)
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(contributor)
    return unique


def normalize_related_asset(item: Any) -> RelatedAssetItem:
    if isinstance(item, str):
        return RelatedAssetItem(title=item.strip())
    if not isinstance(item, dict):
        return RelatedAssetItem(title=compact_text(item))
    return RelatedAssetItem(
        title=first_present(item, "title", "name", "asset", "资产", "标题", default=""),
        relation=first_present(item, "relation", "why", "reason", "关系", "关联原因", default=""),
        url=first_present(item, "url", "link", "链接", default=""),
    )


def reference_from_book(book: BookItem) -> ReferenceItem:
    label = book.title if not book.author else f"{book.title} / {book.author}"
    return ReferenceItem(name=label, why=book.reason, url=book.online_url)


def tldr_as_summary(tldr: TldrPayload) -> str:
    lines = []
    if tldr.topic:
        lines.append(f"主题：{tldr.topic}")
    if tldr.new_this_round:
        lines.append(f"本次新增：{tldr.new_this_round}")
    if tldr.value:
        lines.append(f"价值：{tldr.value}")
    return "\n".join(lines)


def normalize_note(raw: dict[str, Any]) -> NotePayload:
    title = compact_text(
        first_present(raw, "theme_title", "topic", "title", "主题", "标题", default="未命名知识条目")
    ).strip()
    title = title or "未命名知识条目"
    conversation_key = first_present(raw, "conversation_key", "conversation_id", "对话ID")
    if not conversation_key:
        conversation_key = f"{title[:12]}-{uuid.uuid4().hex[:8]}"

    tldr = normalize_tldr(raw, title=title)
    core_outputs = [
        compact_text(item)
        for item in as_list(first_present(raw, "core_outputs", "outputs", "assets", "核心资产", "核心产物", default=[]))
        if compact_text(item)
    ]
    core_outputs = reusable_asset_points(core_outputs)
    workflow = [
        compact_text(item)
        for item in as_list(first_present(raw, "workflow", "工作流", default=[]))
        if compact_text(item)
    ]
    methodology = normalize_methodology(first_present(raw, "methodology", "方法论", default={}))
    evolution = normalize_evolution(first_present(raw, "evolution", "认知演进", "认知升级", default={}))
    legacy_blind_spots = [
        normalize_gap(item)
        for item in as_list(first_present(raw, "blind_spots", "知识缺口", "不足", default=[]))
        if compact_text(item)
    ]
    next_actions = [
        normalize_action(item)
        for item in as_list(first_present(raw, "next_actions", "下一步行动", "actions", "行动建议", default=[]))
        if compact_text(item)
    ] or [action_from_gap(gap) for gap in legacy_blind_spots if compact_text(gap.suggested_practice or gap.gap)]
    legacy_books = [
        normalize_book(item)
        for item in as_list(first_present(raw, "recommended_books", "阅读建议", default=[]))
        if compact_text(item)
    ]
    source_context = compact_text(first_present(raw, "source_context", "原始上下文"))
    conversation_date = compact_text(
        first_present(raw, "conversation_date", "date", "日期", default=today_str())
    )
    source = normalize_source(
        first_present(raw, "source", "来源", default={}),
        source_context=source_context,
        conversation_date=conversation_date,
    )
    related_assets = [
        normalize_related_asset(item)
        for item in as_list(first_present(raw, "related_assets", "关联资产", "related", default=[]))
        if compact_text(item)
    ]
    references = [
        normalize_reference(item)
        for item in as_list(first_present(raw, "references", "参考案例", "参考资料", default=[]))
        if compact_text(item)
    ] or [reference_from_book(book) for book in legacy_books if compact_text(book.title)]

    legacy_summary = compact_text(first_present(raw, "summary", "摘要", default=""))
    summary = tldr_as_summary(tldr) or legacy_summary
    key_insights = [
        compact_text(item)
        for item in as_list(first_present(raw, "key_insights", "核心洞察", default=[]))
        if compact_text(item)
    ] or core_outputs
    mental_models = [
        compact_text(item)
        for item in as_list(first_present(raw, "mental_models", "心智模型", default=[]))
        if compact_text(item)
    ] or workflow

    domain_values = normalize_multi_values(first_present(raw, "domain", "domains", "领域", default=[]))
    tag_values = normalize_multi_values(first_present(raw, "tags", "labels", "标签", default=[]))
    tags = select_core_topic_tags(
        merge_tags([tag_values, domain_values]),
        topic_tag_context_from_note(title, tldr, core_outputs, methodology),
    )

    return NotePayload(
        conversation_key=conversation_key,
        title=title,
        conversation_date=conversation_date,
        tags=tags,
        agent=compact_text(
            first_present(
                raw,
                "agent",
                "conversation_agent",
                "assistant",
                "assistant_name",
                "对话agent",
                "对话Agent",
                default=(
                    os.getenv("FEISHU_CONVERSATION_AGENT")
                    or os.getenv("CONVERSATION_AGENT")
                    or "codex"
                ),
            )
        )
        or "codex",
        tldr=tldr,
        core_outputs=core_outputs,
        workflow=workflow,
        methodology=methodology,
        evolution=evolution,
        next_actions=next_actions,
        related_assets=related_assets,
        references=references,
        source=source,
        contributors=normalize_contributors(raw),
        discussion_points=[
            compact_text(item)
            for item in as_list(
                first_present(
                    raw,
                    "discussion_points",
                    "questions_addressed",
                    "discussion_focus",
                    "讨论问题",
                    "解决问题",
                    default=[],
                )
            )
            if compact_text(item)
        ],
        summary=summary,
        key_insights=key_insights,
        mental_models=mental_models,
        blind_spots=legacy_blind_spots,
        next_thinking_directions=[
            compact_text(item)
            for item in as_list(
                first_present(raw, "next_thinking_directions", "后续思考方向", "思考方向", default=[])
            )
        ],
        actions=[action.todo for action in next_actions if compact_text(action.todo)],
        recommended_books=legacy_books,
        source_context=source_context,
        reminder=compact_text(first_present(raw, "reminder", "提醒摘要")),
    )


def default_note_template() -> dict[str, Any]:
    contributor = default_contributor()
    return {
        "title": "AI 辅助交互原型工作流",
        "conversation_date": today_str(),
        "tags": ["AI 工作流", "交互原型", "设计资产"],
        "agent": "codex",
        "contributor": {
            "name": contributor.name,
            "open_id": contributor.open_id,
        },
        "tldr": {
            "topic": "AI 辅助交互原型工作流",
            "new_this_round": "建立 SVG 映射规范",
            "value": "提升原型还原度并降低重复改稿成本",
        },
        "core_outputs": [
            "HTML 模板规范",
            "SVG 映射规范",
            "Token 体系",
        ],
        "methodology": {
            "name": "AI 交互原型生产流",
            "steps": ["定义页面类型", "匹配模板", "注入 Token", "映射 SVG", "生成页面", "验证 Demo"],
        },
        "evolution": {
            "previous_belief": "Prompt 决定生成质量",
            "current_belief": "Template + Token + 资产映射决定生成质量",
        },
        "next_actions": [
            {"todo": "首页模板化", "priority": "high"},
            {"todo": "补齐 Token 体系", "priority": "medium"},
        ],
        "related_assets": [
            {"title": "飞书知识复利工作流", "relation": "沉淀与复盘入口可以复用同一套资产治理规则"},
        ],
        "references": [
            {"name": "Figma Make", "why": "参考其模板化生成机制"},
        ],
        "source": {
            "type": "conversation",
            "name": "Codex 对话",
            "date": today_str(),
        },
    }


class FeishuClient:
    def __init__(
        self,
        app_id: str | None = None,
        app_secret: str | None = None,
        access_token: str | None = None,
        access_token_kind: str | None = None,
    ):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = access_token
        self.access_token_kind = access_token_kind or ("direct" if access_token else "tenant")
        self._tenant_access_token: str | None = None

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
        auth: bool = True,
        extra_headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        url = f"{API_ROOT}{path}"
        if query:
            encoded = parse.urlencode({k: v for k, v in query.items() if v is not None})
            url = f"{url}?{encoded}"

        body = None
        headers = {"Content-Type": "application/json; charset=utf-8"}
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        if auth:
            headers["Authorization"] = f"Bearer {self.auth_token()}"
        if extra_headers:
            headers.update(extra_headers)

        req = request.Request(url, data=body, method=method.upper(), headers=headers)
        try:
            with request.urlopen(req) as resp:
                raw = resp.read()
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise FeishuError(f"HTTP {exc.code} for {url}: {details}") from exc
        except error.URLError as exc:
            raise FeishuError(f"Request failed for {url}: {exc.reason}") from exc

        data = json.loads(raw.decode("utf-8"))
        if data.get("code") not in (0, None):
            raise FeishuError(f"Feishu API error for {url}: {data}")
        return data

    def auth_token(self) -> str:
        if self.access_token:
            return self.access_token
        return self.tenant_access_token()

    def tenant_access_token(self) -> str:
        if self._tenant_access_token:
            return self._tenant_access_token
        if not self.app_id or not self.app_secret:
            raise FeishuError("Missing FEISHU_APP_ID or FEISHU_APP_SECRET.")
        data = self._request(
            "POST",
            "/open-apis/auth/v3/tenant_access_token/internal",
            payload={"app_id": self.app_id, "app_secret": self.app_secret},
            auth=False,
        )
        token = data.get("tenant_access_token")
        if not token:
            raise FeishuError(f"Missing tenant_access_token in response: {data}")
        self._tenant_access_token = token
        return token

    def create_base(self, name: str, folder_token: str | None = None) -> dict[str, Any]:
        payload = {"name": name}
        if folder_token:
            payload["folder_token"] = folder_token
        data = self._request("POST", "/open-apis/bitable/v1/apps", payload=payload)
        return data["data"]["app"]

    def list_tables(self, app_token: str) -> list[dict[str, Any]]:
        data = self._request(
            "GET",
            f"/open-apis/bitable/v1/apps/{app_token}/tables",
            query={"page_size": 100},
        )
        return data.get("data", {}).get("items", [])

    def create_table(self, app_token: str, name: str, fields: list[Any]) -> str:
        payload = {
            "table": {
                "name": name,
                "default_view_name": "总览",
                "fields": [normalize_field_spec(field) for field in fields],
            }
        }
        data = self._request(
            "POST",
            f"/open-apis/bitable/v1/apps/{app_token}/tables",
            payload=payload,
        )
        return data["data"]["table_id"]

    def list_fields(self, app_token: str, table_id: str) -> list[dict[str, Any]]:
        data = self._request(
            "GET",
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
            query={"page_size": 100},
        )
        return data.get("data", {}).get("items", [])

    def create_field(self, app_token: str, table_id: str, field_spec: dict[str, Any]) -> dict[str, Any]:
        data = self._request(
            "POST",
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
            payload=normalize_field_spec(field_spec),
        )
        return data.get("data", {}).get("field", {})

    def update_field(
        self,
        app_token: str,
        table_id: str,
        field_id: str,
        field_spec: dict[str, Any],
    ) -> dict[str, Any]:
        data = self._request(
            "PUT",
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields/{field_id}",
            payload=field_spec,
        )
        return data.get("data", {}).get("field", {})

    def delete_field(self, app_token: str, table_id: str, field_id: str) -> dict[str, Any]:
        data = self._request(
            "DELETE",
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields/{field_id}",
        )
        return data.get("data", {})

    def create_document(self, title: str, folder_token: str | None = None) -> dict[str, Any]:
        payload = {"title": title}
        if folder_token:
            payload["folder_token"] = folder_token
        data = self._request("POST", "/open-apis/docx/v1/documents", payload=payload)
        body = data.get("data", {})
        return body.get("document", body)

    def get_wiki_node(self, token: str, obj_type: str | None = None) -> dict[str, Any]:
        query: dict[str, Any] = {"token": token}
        if obj_type:
            query["obj_type"] = obj_type
        data = self._request("GET", "/open-apis/wiki/v2/spaces/get_node", query=query)
        return data.get("data", {}).get("node", {})

    def create_wiki_node(
        self,
        space_id: str,
        *,
        parent_node_token: str | None = None,
        obj_type: str = "docx",
        node_type: str = "origin",
        title: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"obj_type": obj_type, "node_type": node_type}
        if parent_node_token:
            payload["parent_node_token"] = parent_node_token
        if title:
            payload["title"] = title
        data = self._request("POST", f"/open-apis/wiki/v2/spaces/{space_id}/nodes", payload=payload)
        return data.get("data", {}).get("node", {})

    def convert_markdown_to_document_blocks(self, markdown: str) -> list[dict[str, Any]]:
        data = self._request(
            "POST",
            "/open-apis/docx/v1/documents/blocks/convert",
            payload={"content_type": "markdown", "content": markdown},
        )
        return data.get("data", {}).get("blocks", [])

    def create_document_children(
        self,
        document_id: str,
        block_id: str,
        children: list[dict[str, Any]],
        *,
        index: int = -1,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"children": children}
        query = {"document_revision_id": -1}
        if index >= 0:
            payload["index"] = index
        data = self._request(
            "POST",
            f"/open-apis/docx/v1/documents/{document_id}/blocks/{block_id}/children",
            payload=payload,
            query=query,
        )
        return data.get("data", {})

    def list_document_children(
        self,
        document_id: str,
        block_id: str,
        *,
        page_size: int = 500,
        page_token: str | None = None,
        with_descendants: bool = False,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {
            "document_revision_id": -1,
            "page_size": min(max(page_size, 1), 500),
            "with_descendants": str(bool(with_descendants)).lower(),
        }
        if page_token:
            query["page_token"] = page_token
        data = self._request(
            "GET",
            f"/open-apis/docx/v1/documents/{document_id}/blocks/{block_id}/children",
            query=query,
        )
        return data.get("data", {})

    def update_document_title(self, document_id: str, title: str) -> dict[str, Any]:
        data = self._request(
            "PATCH",
            f"/open-apis/docx/v1/documents/{document_id}/blocks/{document_id}",
            payload={
                "update_text_elements": {
                    "elements": [
                        {
                            "text_run": {
                                "content": compact_text(title),
                            }
                        }
                    ]
                }
            },
            query={"document_revision_id": -1},
        )
        return data.get("data", {})

    def patch_document_block(
        self,
        document_id: str,
        block_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        data = self._request(
            "PATCH",
            f"/open-apis/docx/v1/documents/{document_id}/blocks/{block_id}",
            payload=payload,
            query={"document_revision_id": -1},
        )
        return data.get("data", {})

    def replace_document_image(
        self,
        document_id: str,
        block_id: str,
        token: str,
        *,
        width: int | None = None,
        height: int | None = None,
        align: int = 2,
        caption: str = "",
    ) -> dict[str, Any]:
        replace_image: dict[str, Any] = {
            "token": token,
            "align": align,
        }
        if width:
            replace_image["width"] = width
        if height:
            replace_image["height"] = height
        if caption:
            replace_image["caption"] = {"content": sanitize_tutorial_text(caption)}
        return self.patch_document_block(document_id, block_id, {"replace_image": replace_image})

    def batch_delete_document_children(
        self,
        document_id: str,
        block_id: str,
        *,
        start_index: int,
        end_index: int,
    ) -> dict[str, Any]:
        data = self._request(
            "DELETE",
            f"/open-apis/docx/v1/documents/{document_id}/blocks/{block_id}/children/batch_delete",
            query={
                "document_revision_id": -1,
                "client_token": str(uuid.uuid4()),
            },
            payload={"start_index": start_index, "end_index": end_index},
        )
        return data.get("data", {})

    def create_record(self, app_token: str, table_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        data = self._request(
            "POST",
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records",
            payload={"fields": fields},
            query={"client_token": str(uuid.uuid4())},
        )
        return data.get("data", {}).get("record", {})

    def update_record(self, app_token: str, table_id: str, record_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        data = self._request(
            "PUT",
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
            payload={"fields": fields},
            query={"ignore_consistency_check": "true"},
        )
        return data.get("data", {}).get("record", {})

    def delete_record(self, app_token: str, table_id: str, record_id: str) -> dict[str, Any]:
        data = self._request(
            "DELETE",
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}",
        )
        return data.get("data", {})

    def add_permission_member(
        self,
        token: str,
        *,
        doc_type: str,
        member_id: str,
        member_type: str = "openid",
        perm: str = "full_access",
        perm_type: str = "container",
        collaborator_type: str = "user",
        need_notification: bool = False,
    ) -> dict[str, Any]:
        data = self._request(
            "POST",
            f"/open-apis/drive/v1/permissions/{token}/members",
            query={
                "need_notification": str(bool(need_notification)).lower(),
                "type": doc_type,
            },
            payload={
                "member_id": member_id,
                "member_type": member_type,
                "perm": perm,
                "perm_type": perm_type,
                "type": collaborator_type,
            },
        )
        return data.get("data", {}).get("member", {})

    def list_records(
        self,
        app_token: str,
        table_id: str,
        *,
        field_names: list[str] | None = None,
        sort: list[str] | None = None,
        page_size: int = 50,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        page_token: str | None = None

        while len(items) < limit:
            query: dict[str, Any] = {"page_size": min(page_size, limit - len(items))}
            if field_names:
                query["field_names"] = json.dumps(field_names, ensure_ascii=False)
            if sort:
                query["sort"] = json.dumps(sort, ensure_ascii=False)
            if page_token:
                query["page_token"] = page_token

            data = self._request(
                "GET",
                f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records",
                query=query,
            )
            page = data.get("data", {})
            items.extend(page.get("items", []))
            if not page.get("has_more"):
                break
            page_token = page.get("page_token")
            if not page_token:
                break

        return items[:limit]

    def list_views(self, app_token: str, table_id: str) -> list[dict[str, Any]]:
        data = self._request(
            "GET",
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/views",
            query={"page_size": 100},
        )
        return data.get("data", {}).get("items", [])

    def create_view(self, app_token: str, table_id: str, view_name: str, view_type: str) -> dict[str, Any]:
        data = self._request(
            "POST",
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/views",
            payload={"view_name": view_name, "view_type": view_type},
        )
        return data.get("data", {}).get("view", {})

    def patch_view(
        self,
        app_token: str,
        table_id: str,
        view_id: str,
        *,
        view_name: str | None = None,
        property_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if view_name:
            payload["view_name"] = view_name
        if property_payload is not None:
            payload["property"] = property_payload
        data = self._request(
            "PATCH",
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/views/{view_id}",
            payload=payload,
        )
        return data.get("data", {}).get("view", {})

    def upload_media(
        self,
        parent_node: str,
        *,
        file_name: str,
        file_bytes: bytes,
        parent_type: str,
    ) -> dict[str, Any]:
        boundary = f"----CodexBoundary{uuid.uuid4().hex}"
        parts: list[bytes] = []

        def add_field(
            name: str,
            value: str | None,
            *,
            filename: str | None = None,
            content_type: str | None = None,
            binary: bytes | None = None,
        ) -> None:
            parts.append(f"--{boundary}".encode("utf-8"))
            disposition = f'Content-Disposition: form-data; name="{name}"'
            if filename:
                disposition += f'; filename="{filename}"'
            parts.append(disposition.encode("utf-8"))
            if content_type:
                parts.append(f"Content-Type: {content_type}".encode("utf-8"))
            parts.append(b"")
            parts.append(binary if binary is not None else compact_text(value).encode("utf-8"))

        suffix = Path(file_name).suffix.lower() or ".jpg"
        content_type = "image/png" if suffix == ".png" else "image/jpeg"

        add_field("file_name", file_name)
        add_field("parent_type", parent_type)
        add_field("parent_node", parent_node)
        add_field("size", str(len(file_bytes)))
        add_field("checksum", str(zlib.adler32(file_bytes) & 0xFFFFFFFF))
        add_field("file", None, filename=file_name, content_type=content_type, binary=file_bytes)
        parts.append(f"--{boundary}--".encode("utf-8"))
        parts.append(b"")

        req = request.Request(
            f"{API_ROOT}/open-apis/drive/v1/medias/upload_all",
            data=b"\r\n".join(parts),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.auth_token()}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        )
        try:
            with request.urlopen(req) as resp:
                raw = resp.read()
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise FeishuError(f"Media upload HTTP {exc.code}: {details}") from exc
        except error.URLError as exc:
            raise FeishuError(f"Media upload failed: {exc.reason}") from exc

        data = json.loads(raw.decode("utf-8"))
        if data.get("code") not in (0, None):
            raise FeishuError(f"Media upload error: {data}")
        return data.get("data", {})

    def upload_bitable_media(
        self,
        app_token: str,
        *,
        file_name: str,
        file_bytes: bytes,
        parent_type: str = "bitable_image",
    ) -> dict[str, Any]:
        return self.upload_media(
            app_token,
            file_name=file_name,
            file_bytes=file_bytes,
            parent_type=parent_type,
        )

    def send_app_message(self, receive_id: str, receive_id_type: str, message: str) -> dict[str, Any]:
        payload = {
            "receive_id": receive_id,
            "msg_type": "text",
            "content": json.dumps({"text": message}, ensure_ascii=False),
            "uuid": str(uuid.uuid4()),
        }
        return self._request(
            "POST",
            "/open-apis/im/v1/messages",
            payload=payload,
            query={"receive_id_type": receive_id_type},
        )

    def send_webhook_message(self, webhook: str, message: str, secret: str | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "msg_type": "text",
            "content": {"text": message},
        }
        if secret:
            timestamp = str(int(time.time()))
            sign_key = f"{timestamp}\n{secret}".encode("utf-8")
            signature = base64.b64encode(
                hmac.new(sign_key, b"", digestmod=hashlib.sha256).digest()
            ).decode("utf-8")
            payload.update({"timestamp": timestamp, "sign": signature})

        req = request.Request(
            webhook,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        try:
            with request.urlopen(req) as resp:
                raw = resp.read()
        except error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise FeishuError(f"Webhook HTTP {exc.code}: {details}") from exc
        except error.URLError as exc:
            raise FeishuError(f"Webhook request failed: {exc.reason}") from exc
        data = json.loads(raw.decode("utf-8"))
        if data.get("code") not in (0, None):
            raise FeishuError(f"Webhook error: {data}")
        return data


def load_runtime_config(config_path: str | None) -> dict[str, Any]:
    path = config_path or os.getenv(DEFAULT_CONFIG_ENV)
    if not path:
        return {}
    return read_json(Path(path))


def resolve_credentials() -> tuple[str | None, str | None]:
    return os.getenv("FEISHU_APP_ID"), os.getenv("FEISHU_APP_SECRET")


def resolve_direct_access_token() -> tuple[str | None, str | None]:
    user_token = env_nonempty("FEISHU_USER_ACCESS_TOKEN")
    if user_token:
        return user_token, "user"
    generic_token = env_nonempty("FEISHU_ACCESS_TOKEN")
    if generic_token:
        return generic_token, env_nonempty("FEISHU_ACCESS_TOKEN_KIND") or "direct"
    return None, None


def build_client() -> FeishuClient:
    access_token, access_token_kind = resolve_direct_access_token()
    if access_token:
        return FeishuClient(access_token=access_token, access_token_kind=access_token_kind)
    app_id, app_secret = resolve_credentials()
    return FeishuClient(app_id=app_id, app_secret=app_secret)


def resolve_storage(config: dict[str, Any]) -> tuple[str, dict[str, str]]:
    app_token = os.getenv("FEISHU_BASE_APP_TOKEN") or config.get("app_token")
    table_ids = dict(config.get("table_ids", {}))
    table_ids["conversations"] = os.getenv("FEISHU_CONVERSATIONS_TABLE_ID") or table_ids.get(
        "conversations"
    )
    table_ids["gaps"] = os.getenv("FEISHU_GAPS_TABLE_ID") or table_ids.get("gaps")
    table_ids["reading"] = os.getenv("FEISHU_READING_TABLE_ID") or table_ids.get("reading")

    missing = [name for name in ("conversations",) if not table_ids.get(name)]
    if not app_token or missing:
        raise FeishuError(
            "Missing storage config. Run bootstrap first or set FEISHU_BASE_APP_TOKEN plus the table IDs."
        )
    return app_token, {key: value for key, value in table_ids.items() if value}


def resolve_base_token(config: dict[str, Any]) -> str:
    app_token = os.getenv("FEISHU_BASE_APP_TOKEN") or config.get("app_token")
    if not app_token:
        raise FeishuError(
            "Missing Base token. Run bootstrap first or set FEISHU_BASE_APP_TOKEN / config.app_token."
        )
    return app_token


def resolve_notify_target() -> dict[str, str]:
    webhook = os.getenv("FEISHU_NOTIFY_WEBHOOK")
    webhook_secret = os.getenv("FEISHU_NOTIFY_WEBHOOK_SECRET")
    open_id = os.getenv("FEISHU_NOTIFY_OPEN_ID")
    chat_id = os.getenv("FEISHU_NOTIFY_CHAT_ID")
    receive_id = os.getenv("FEISHU_NOTIFY_RECEIVE_ID")
    receive_id_type = os.getenv("FEISHU_NOTIFY_RECEIVE_ID_TYPE")

    if webhook:
        target = {"mode": "webhook", "webhook": webhook}
        if webhook_secret:
            target["secret"] = webhook_secret
        return target
    if open_id:
        return {"mode": "app", "receive_id": open_id, "receive_id_type": "open_id"}
    if chat_id:
        return {"mode": "app", "receive_id": chat_id, "receive_id_type": "chat_id"}
    if receive_id:
        return {
            "mode": "app",
            "receive_id": receive_id,
            "receive_id_type": receive_id_type or "open_id",
        }
    return {}


def ensure_table_fields(
    client: FeishuClient,
    app_token: str,
    table_id: str,
    fields: list[Any],
) -> dict[str, dict[str, Any]]:
    normalized_fields = [normalize_field_spec(field) for field in fields]
    existing = {item["field_name"]: item for item in client.list_fields(app_token, table_id)}

    for field_spec in normalized_fields:
        if field_spec["field_name"] in existing:
            continue
        created = client.create_field(app_token, table_id, field_spec)
        if created:
            existing[created["field_name"]] = created

    if any(field_spec["field_name"] not in existing for field_spec in normalized_fields):
        existing = {item["field_name"]: item for item in client.list_fields(app_token, table_id)}

    return existing


def build_reading_gallery_url(app_token: str, table_id: str, view_id: str) -> str:
    return f"https://trip.larkenterprise.com/base/{app_token}?table={table_id}&view={view_id}"


def download_binary(url: str) -> tuple[bytes, str]:
    req = request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with request.urlopen(req, timeout=20) as resp:
            data = resp.read()
            content_type = resp.headers.get_content_type() or "application/octet-stream"
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise FeishuError(f"Download HTTP {exc.code} for {url}: {details}") from exc
    except error.URLError as exc:
        raise FeishuError(f"Download failed for {url}: {exc.reason}") from exc
    return data, content_type


def upload_reading_cover(
    client: FeishuClient,
    app_token: str,
    title: str,
    upload_cache: dict[str, str],
    *,
    cover_url: str = "",
) -> str:
    source_key = compact_text(cover_url) or str(DEFAULT_BOOK_COVER_PATH)
    if source_key in upload_cache:
        return upload_cache[source_key]

    if compact_text(cover_url):
        file_bytes, content_type = download_binary(cover_url)
        suffix = Path(parse.urlparse(cover_url).path).suffix.lower()
        if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
            suffix = ".png" if "png" in content_type else ".jpg"
    else:
        if not DEFAULT_BOOK_COVER_PATH.exists():
            raise FeishuError(f"Default book cover asset not found: {DEFAULT_BOOK_COVER_PATH}")
        file_bytes = DEFAULT_BOOK_COVER_PATH.read_bytes()
        suffix = DEFAULT_BOOK_COVER_PATH.suffix.lower() or ".png"

    safe_name = normalize_lookup_key(title).replace(" ", "-") or "book-cover"
    upload = client.upload_bitable_media(
        app_token,
        file_name=f"{safe_name}{suffix}",
        file_bytes=file_bytes,
    )
    file_token = upload["file_token"]
    upload_cache[source_key] = file_token
    return file_token


def reading_record_key_from_fields(fields: dict[str, Any]) -> str:
    title_key = normalize_lookup_key(fields.get("书名"))
    author_key = normalize_lookup_key(fields.get("作者"))
    return f"{title_key}::{author_key}".strip(":")


def unique_texts(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    items: list[str] = []
    for value in values:
        text = compact_text(value)
        if not text:
            continue
        key = normalize_general_key(text) or normalize_lookup_key(text) or text
        if key in seen:
            continue
        seen.add(key)
        items.append(text)
    return items


def merge_text_block(values: list[Any], *, bullet: bool = False) -> str:
    merged = unique_texts(values)
    if not merged:
        return ""
    if len(merged) == 1 and not bullet:
        return merged[0]
    if len(merged) == 1 and bullet:
        return merged[0]
    return bullet_block(merged) if bullet else "\n".join(merged)


def merge_tags(values: list[Any]) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for value in values:
        for text in normalize_multi_values(value):
            key = normalize_general_key(text) or normalize_lookup_key(text) or text
            if key in seen:
                continue
            seen.add(key)
            items.append(text)
    return items


def topic_tag_context_from_note(
    title: str,
    tldr: TldrPayload,
    core_outputs: list[str],
    methodology: MethodologyPayload,
) -> list[Any]:
    return [
        title,
        tldr.topic,
        tldr.new_this_round,
        tldr.value,
        *core_outputs,
        methodology.name,
        *methodology.steps,
    ]


def topic_tag_context_from_fields(fields: dict[str, Any]) -> list[Any]:
    return [
        conversation_title_value(fields),
        fields.get("TLDR主题"),
        fields.get("本次新增"),
        fields.get("价值"),
        fields.get("核心资产"),
        fields.get("方法论"),
        fields.get("知识演化图谱"),
    ]


def topic_tag_score(tag: str, context_parts: list[Any]) -> int:
    label = compact_text(tag)
    key = normalize_general_key(label)
    primary_text = " ".join(compact_text(part) for part in context_parts[:4] if compact_text(part))
    secondary_text = " ".join(compact_text(part) for part in context_parts[4:] if compact_text(part))
    context_text = " ".join(part for part in (primary_text, secondary_text) if part)
    primary_key = normalize_general_key(primary_text)
    secondary_key = normalize_general_key(secondary_text)
    context_key = normalize_general_key(context_text)
    if not key or not context_key:
        return 0

    score = 0
    if primary_key and key in primary_key:
        score += 300 + min(len(key), 30)
    elif secondary_key and key in secondary_key:
        score += 30 + min(len(key), 20)

    lower_primary = primary_text.lower()
    lower_secondary = secondary_text.lower()
    for token in re.findall(r"[a-zA-Z0-9]+", label.lower()):
        if len(token) < 2:
            continue
        if token in lower_primary:
            score += 40
        elif token in lower_secondary:
            score += 8

    label_chars = {char for char in key if "\u4e00" <= char <= "\u9fff"}
    primary_chars = {char for char in primary_key if "\u4e00" <= char <= "\u9fff"}
    secondary_chars = {char for char in secondary_key if "\u4e00" <= char <= "\u9fff"}
    if label_chars and primary_chars:
        overlap = len(label_chars & primary_chars)
        score += int((overlap / len(label_chars)) * 120)
    if label_chars and secondary_chars:
        overlap = len(label_chars & secondary_chars)
        score += int((overlap / len(label_chars)) * 24)

    if any(marker in key for marker in LOW_PRIORITY_TOPIC_TAG_MARKERS):
        score -= 80

    return max(score, 0)


def select_core_topic_tags(
    tags: list[str],
    context_parts: list[Any],
    *,
    max_tags: int = MAX_TOPIC_TAGS,
) -> list[str]:
    unique_tags = merge_tags([tags])
    if len(unique_tags) <= max_tags:
        return unique_tags

    scored = [
        (topic_tag_score(tag, context_parts), -index, tag)
        for index, tag in enumerate(unique_tags)
    ]
    selected = [
        tag
        for score, _index, tag in sorted(scored, key=lambda item: (item[0], item[1]), reverse=True)
        if score > 0
    ]
    if len(selected) < max_tags:
        selected.extend(tag for tag in unique_tags if tag not in selected)
    return selected[:max_tags]


def parse_intish(value: Any, default: int = 0) -> int:
    text = compact_text(value)
    if not text:
        return default
    try:
        return int(float(text))
    except ValueError:
        return default


def best_priority(values: list[Any]) -> str:
    ordered = sorted(
        [compact_text(value) for value in values if compact_text(value)],
        key=parse_priority,
        reverse=True,
    )
    return ordered[0] if ordered else "medium"


def best_status(values: list[Any]) -> str:
    weights = {
        "已完成": 4,
        "读完": 4,
        "在读": 3,
        "进行中": 3,
        "待读": 2,
        "待行动": 1,
    }
    normalized = [compact_text(value) for value in values if compact_text(value)]
    if not normalized:
        return "待读"
    return max(normalized, key=lambda value: weights.get(value, 0))


def parse_datetimeish(value: Any) -> datetime | None:
    text = compact_text(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    for candidate in (f"{text}T00:00:00", text[:19]):
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            continue
    return None


def latest_text_value(values: list[Any]) -> str:
    pairs = [(parse_datetimeish(value), compact_text(value)) for value in values if compact_text(value)]
    dated = [(parsed, text) for parsed, text in pairs if parsed]
    if dated:
        return max(dated, key=lambda item: item[0])[1]
    return pairs[0][1] if pairs else ""


THEME_PREFIXES = ["搭建", "建立", "打造", "构建", "实现", "优化", "改造", "升级", "复盘", "整理"]
THEME_SUFFIXES = [
    "｜能力资产",
    "|能力资产",
    " 能力资产",
    "能力资产",
    "｜学习教程",
    "|学习教程",
    " 学习教程",
    "学习教程",
    "已完整落地",
    "完整落地",
    "已落地",
    "落地",
    "已完成",
    "完成",
    "已跑通",
    "跑通",
]

CONVERSATION_TITLE_ALIASES = {
    normalize_general_key("知识库skill"): "飞书知识复利工作流",
    normalize_general_key("搭建知识库skill"): "飞书知识复利工作流",
    normalize_general_key("搭建飞书知识复利系统"): "飞书知识复利工作流",
    normalize_general_key("飞书知识复利系统"): "飞书知识复利工作流",
    normalize_general_key("飞书知识复利工作流"): "飞书知识复利工作流",
    normalize_general_key("火车票通勤购票交互原型设计"): "AI 辅助交互原型工作流",
    normalize_general_key("火车票通勤购票交互原型与prototypecreator规范"): "AI 辅助交互原型工作流",
    normalize_general_key("生成式交互原型prototypecreator实践与评测"): "AI 辅助交互原型工作流",
    normalize_general_key("ai辅助交互原型工作流"): "AI 辅助交互原型工作流",
}

CANONICAL_THEME_RULES = [
    {
        "title": "飞书知识复利工作流",
        "min_hits": 2,
        "keywords": [
            "飞书",
            "feishu",
            "知识复利",
            "knowledge-management",
            "knowledge-base",
            "codex-skill",
            "automation",
            "知识沉淀",
            "知识库",
        ],
    },
    {
        "title": "AI 辅助交互原型工作流",
        "min_hits": 2,
        "keywords": [
            "prototype-creator",
            "交互原型",
            "生成式交互",
            "生成式UI",
            "HTML原型",
            "HTML+PNG",
            "Figma-MCP",
            "ota-screen-patterns",
            "Ctrip-UI-Kit",
        ],
    },
    {
        "title": "AI 知识沉淀工作流",
        "min_hits": 2,
        "keywords": [
            "知识沉淀",
            "知识管理",
            "第二大脑",
            "smart-notes",
            "how-to-take-smart-notes",
        ],
    },
]


def strip_theme_affixes(title: Any) -> str:
    text = compact_text(title)
    if not text:
        return ""
    changed = True
    while changed and text:
        changed = False
        for prefix in THEME_PREFIXES:
            if text.startswith(prefix) and len(text) > len(prefix):
                text = text[len(prefix) :].strip()
                changed = True
        for suffix in THEME_SUFFIXES:
            if text.endswith(suffix) and len(text) > len(suffix):
                text = text[: -len(suffix)].strip()
                changed = True
    return text or compact_text(title)


def conversation_field_names(
    field_map: dict[str, dict[str, Any]] | None = None,
    *,
    include_legacy: bool = False,
) -> list[str]:
    names = table_field_names(TABLE_SPECS["conversations"])
    if include_legacy and field_map:
        for name in CONVERSATION_LEGACY_FIELD_NAMES:
            if name in field_map and name not in names:
                names.append(name)
    elif include_legacy:
        for name in CONVERSATION_LEGACY_FIELD_NAMES:
            if name not in names:
                names.append(name)
    return names


def canonical_conversation_field_names() -> set[str]:
    names = set(table_field_names(TABLE_SPECS["conversations"]))
    for name in CONVERSATION_TITLE_FIELDS[:1]:
        if name:
            names.add(name)
    return names


def conversation_title_candidates(fields: dict[str, Any]) -> list[str]:
    candidates: list[str] = []
    for field_name in CONVERSATION_TITLE_FIELDS:
        value = compact_text(fields.get(field_name))
        if not value:
            continue
        candidates.append(strip_theme_affixes(value) or value)
    return unique_texts(candidates)


def conversation_theme_haystack(fields: dict[str, Any]) -> str:
    pieces: list[str] = []
    for field_name in (
        "标题",
        "主题",
        "TLDR主题",
        "本次新增",
        "价值",
        "核心资产",
        "方法论",
        "认知演进",
        "知识演化图谱",
        "下一步行动",
        "关联资产",
        "参考案例",
        "讨论问题",
        "摘要正文",
        "原始上下文",
        "核心洞察",
        "心智模型",
    ):
        value = compact_text(fields.get(field_name))
        if value:
            pieces.append(value)
    for field_name in ("标签", "领域", "对话Agent"):
        pieces.extend(normalize_multi_values(fields.get(field_name)))
    return normalize_general_key(" ".join(piece for piece in pieces if piece))


def conversation_title_preference_key(title: str) -> tuple[int, int, str]:
    normalized = normalize_general_key(title)
    volatile_markers = (
        "prototypecreator",
        "html",
        "png",
        "figmamcp",
        "otascreenpatterns",
        "实践",
        "评测",
        "规范",
        "设计",
        "skill",
        "v1",
        "v2",
    )
    penalty = sum(1 for marker in volatile_markers if marker in normalized)
    return (penalty, len(title), title)


def infer_conversation_title(fields: dict[str, Any]) -> str:
    candidates = conversation_title_candidates(fields)

    haystack = conversation_theme_haystack(fields)
    best_title = ""
    best_score = 0
    for rule in CANONICAL_THEME_RULES:
        score = sum(1 for keyword in rule["keywords"] if normalize_general_key(keyword) in haystack)
        if score >= rule["min_hits"] and score > best_score:
            best_title = rule["title"]
            best_score = score
    if best_title:
        return best_title

    for candidate in candidates:
        aliased = CONVERSATION_TITLE_ALIASES.get(normalize_general_key(candidate))
        if aliased:
            return aliased

    if candidates:
        return min(candidates, key=conversation_title_preference_key)
    return ""


def conversation_title_value(fields: dict[str, Any]) -> str:
    return infer_conversation_title(fields) or compact_text(first_present(fields, *CONVERSATION_TITLE_FIELDS))


def conversation_title_update_fields(
    title: str,
    *,
    current_fields: dict[str, Any] | None = None,
    available_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_title = compact_text(title)
    if not normalized_title:
        return {}

    update_fields: dict[str, Any] = {}
    current_title = compact_text((current_fields or {}).get("标题"))
    if current_title != normalized_title:
        update_fields["标题"] = normalized_title

    has_legacy_theme_field = False
    if current_fields and "主题" in current_fields:
        has_legacy_theme_field = True
    if available_fields and "主题" in available_fields:
        has_legacy_theme_field = True
    if has_legacy_theme_field:
        current_theme = compact_text((current_fields or {}).get("主题"))
        if current_theme != normalized_title:
            update_fields["主题"] = normalized_title

    return update_fields


def canonical_conversation_title_from_text(value: Any) -> str:
    text = compact_text(value)
    if not text:
        return ""
    base = strip_theme_affixes(text) or text
    normalized_candidates = [normalize_general_key(base), normalize_general_key(text)]
    for candidate in normalized_candidates:
        if candidate and candidate in CONVERSATION_TITLE_ALIASES:
            return CONVERSATION_TITLE_ALIASES[candidate]
    return base


def split_source_theme_values(value: Any) -> list[str]:
    raw = compact_text(value)
    if not raw:
        return []
    lines = split_bullets(raw)
    if lines:
        return lines
    return [raw]


def merge_source_theme_values(values: list[Any]) -> str:
    items: list[str] = []
    seen: set[str] = set()
    for value in values:
        for item in split_source_theme_values(value):
            canonical = canonical_conversation_title_from_text(item)
            if not canonical:
                continue
            key = normalize_general_key(canonical) or normalize_lookup_key(canonical) or canonical
            if key in seen:
                continue
            seen.add(key)
            items.append(canonical)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return bullet_block(items)


def conversation_theme_key_from_fields(fields: dict[str, Any]) -> str:
    title = conversation_title_value(fields)
    base = strip_theme_affixes(title)
    return normalize_general_key(base) or normalize_general_key(title)


def is_blank_conversation_record(fields: dict[str, Any]) -> bool:
    unnamed_keys = {normalize_general_key("未命名主题"), normalize_general_key("未命名知识条目")}
    meaningful_fields = (
        "对话ID",
        "TLDR主题",
        "本次新增",
        "价值",
        "核心资产",
        "方法论",
        "认知演进",
        "知识演化图谱",
        "下一步行动",
        "关联资产",
        "参考案例",
        "来源",
        "摘要",
    )
    for field_name in meaningful_fields:
        value = fields.get(field_name)
        if field_name == "摘要" and extract_link_url(value):
            return False
        text = compact_text(value)
        if field_name == "TLDR主题" and normalize_general_key(text) in unnamed_keys:
            continue
        if text:
            return False
    title = strip_theme_affixes(compact_text(first_present(fields, *CONVERSATION_TITLE_FIELDS)))
    return not title or normalize_general_key(title) in unnamed_keys


def canonical_conversation_title(records: list[dict[str, Any]]) -> str:
    base_titles = unique_texts(
        [strip_theme_affixes(conversation_title_value(record.get("fields", {}))) for record in records]
    )
    if len(base_titles) == 1:
        return base_titles[0]
    if base_titles:
        return min(base_titles, key=conversation_title_preference_key)
    titles = [
        conversation_title_value(record.get("fields", {}))
        for record in records
        if conversation_title_value(record.get("fields", {}))
    ]
    return titles[0] if titles else "未命名主题"


def discussion_entry_from_note(note: NotePayload) -> str:
    parts = [
        note.tldr.new_this_round,
        note.tldr.value,
        *note.core_outputs[:2],
    ] or note.discussion_points or [note.title or note.source_context or note.summary]
    issue = "；".join(part.strip() for part in parts if part and part.strip())
    label = issue or note.title
    return f"{note.conversation_date} [{note.agent}] {label}"


def discussion_entry_from_fields(fields: dict[str, Any]) -> str:
    existing = split_bullets(compact_text(fields.get("讨论问题")))
    if existing:
        return existing[0]
    agent_values = normalize_multi_values(fields.get("对话Agent")) or ["codex"]
    date_value = compact_text(fields.get("日期")) or compact_text(fields.get("同步时间"))[:10] or today_str()
    issue = conversation_title_value(fields) or compact_text(fields.get("原始上下文")) or summary_body_from_fields(fields)
    return f"{date_value} [{' / '.join(agent_values)}] {issue}"


def ensure_multiselect_field(
    client: FeishuClient,
    app_token: str,
    table_id: str,
    field_name: str,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    warnings: list[str] = []
    fields = {item["field_name"]: item for item in client.list_fields(app_token, table_id)}
    current = fields.get(field_name)
    if not current or current.get("type") == 4:
        return fields, warnings

    backup_name = f"{field_name}_旧文本"
    counter = 1
    while backup_name in fields:
        counter += 1
        backup_name = f"{field_name}_旧文本{counter}"

    try:
        rename_spec = {
            "field_name": backup_name,
            "type": current["type"],
            **({"property": current["property"]} if current.get("property") else {}),
        }
        client.update_field(app_token, table_id, current["field_id"], rename_spec)
        client.create_field(app_token, table_id, {"field_name": field_name, "type": 4})
    except FeishuError as exc:
        try:
            restore_spec = {
                "field_name": field_name,
                "type": current["type"],
                **({"property": current["property"]} if current.get("property") else {}),
            }
            client.update_field(app_token, table_id, current["field_id"], restore_spec)
        except FeishuError:
            pass
        raise FeishuError(f"{field_name} 字段迁移失败: {exc}") from exc

    records = client.list_records(app_token, table_id, field_names=[backup_name], limit=2000)
    for record in records:
        normalized_values = normalize_multi_values(record.get("fields", {}).get(backup_name))
        if not normalized_values:
            continue
        client.update_record(app_token, table_id, record["record_id"], {field_name: normalized_values})

    migrated_fields = {item["field_name"]: item for item in client.list_fields(app_token, table_id)}
    backup_field = migrated_fields.get(backup_name)
    if backup_field and backup_field.get("field_id"):
        try:
            client.delete_field(app_token, table_id, backup_field["field_id"])
        except FeishuError as exc:
            warnings.append(f"{field_name}: 旧文本备份字段删除失败 - {exc}")

    return {item["field_name"]: item for item in client.list_fields(app_token, table_id)}, warnings


def ensure_summary_url_field(
    client: FeishuClient,
    app_token: str,
    table_id: str,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    warnings: list[str] = []
    fields = {item["field_name"]: item for item in client.list_fields(app_token, table_id)}

    current_summary = fields.get("摘要")
    if not current_summary:
        client.create_field(app_token, table_id, {"field_name": "摘要", "type": 15})
        return {item["field_name"]: item for item in client.list_fields(app_token, table_id)}, warnings

    if current_summary.get("type") == 15:
        return fields, warnings

    if "摘要正文" not in fields:
        created = client.create_field(app_token, table_id, {"field_name": "摘要正文", "type": 1})
        if created:
            fields[created["field_name"]] = created
        else:
            fields = {item["field_name"]: item for item in client.list_fields(app_token, table_id)}

    backup_name = "摘要_旧文本"
    counter = 1
    while backup_name in fields:
        counter += 1
        backup_name = f"摘要_旧文本{counter}"

    rename_spec = {
        "field_name": backup_name,
        "type": current_summary["type"],
        **({"property": current_summary["property"]} if current_summary.get("property") else {}),
    }
    restore_spec = {
        "field_name": "摘要",
        "type": current_summary["type"],
        **({"property": current_summary["property"]} if current_summary.get("property") else {}),
    }

    try:
        client.update_field(app_token, table_id, current_summary["field_id"], rename_spec)
        client.create_field(app_token, table_id, {"field_name": "摘要", "type": 15})
    except FeishuError as exc:
        try:
            client.update_field(app_token, table_id, current_summary["field_id"], restore_spec)
        except FeishuError:
            pass
        raise FeishuError(f"摘要 字段迁移失败: {exc}") from exc

    records = client.list_records(app_token, table_id, field_names=[backup_name, "摘要正文"], limit=2000)
    for record in records:
        raw_summary = compact_text(record.get("fields", {}).get(backup_name))
        existing_body = compact_text(record.get("fields", {}).get("摘要正文"))
        merged_body = merge_text_block([existing_body, raw_summary])
        if not merged_body:
            continue
        client.update_record(app_token, table_id, record["record_id"], {"摘要正文": merged_body})

    refreshed_fields = {item["field_name"]: item for item in client.list_fields(app_token, table_id)}
    backup_field = refreshed_fields.get(backup_name)
    if backup_field and backup_field.get("field_id"):
        try:
            client.delete_field(app_token, table_id, backup_field["field_id"])
        except FeishuError as exc:
            warnings.append(f"摘要: 旧文本备份字段删除失败 - {exc}")

    return {item["field_name"]: item for item in client.list_fields(app_token, table_id)}, warnings


def ensure_person_field(
    client: FeishuClient,
    app_token: str,
    table_id: str,
    field_name: str,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    warnings: list[str] = []
    fields = {item["field_name"]: item for item in client.list_fields(app_token, table_id)}
    current = fields.get(field_name)
    if not current:
        client.create_field(
            app_token,
            table_id,
            {"field_name": field_name, "type": 11, "property": {"multiple": True}},
        )
        return {item["field_name"]: item for item in client.list_fields(app_token, table_id)}, warnings

    if current.get("type") == 11:
        return fields, warnings

    backup_name = f"{field_name}_旧文本"
    counter = 1
    while backup_name in fields:
        counter += 1
        backup_name = f"{field_name}_旧文本{counter}"

    try:
        rename_spec = {
            "field_name": backup_name,
            "type": current["type"],
            **({"property": current["property"]} if current.get("property") else {}),
        }
        client.update_field(app_token, table_id, current["field_id"], rename_spec)
        client.create_field(
            app_token,
            table_id,
            {"field_name": field_name, "type": 11, "property": {"multiple": True}},
        )
        warnings.append(f"{field_name}: 已改为人员字段；原字段保留为 {backup_name}")
    except FeishuError as exc:
        try:
            restore_spec = {
                "field_name": field_name,
                "type": current["type"],
                **({"property": current["property"]} if current.get("property") else {}),
            }
            client.update_field(app_token, table_id, current["field_id"], restore_spec)
        except FeishuError:
            pass
        raise FeishuError(f"{field_name} 字段迁移失败: {exc}") from exc

    return {item["field_name"]: item for item in client.list_fields(app_token, table_id)}, warnings


def prune_conversation_legacy_fields(
    client: FeishuClient,
    app_token: str,
    table_id: str,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    warnings: list[str] = []
    canonical_names = canonical_conversation_field_names()
    fields = {item["field_name"]: item for item in client.list_fields(app_token, table_id)}

    for field_name in CONVERSATION_LEGACY_FIELD_NAMES:
        if field_name in canonical_names:
            continue
        field = fields.get(field_name)
        if not field or not field.get("field_id"):
            continue
        if field.get("is_primary"):
            continue
        try:
            client.delete_field(app_token, table_id, field["field_id"])
            fields.pop(field_name, None)
        except FeishuError as exc:
            warnings.append(f"{field_name}: 旧字段删除失败 - {exc}")

    return {item["field_name"]: item for item in client.list_fields(app_token, table_id)}, warnings


def normalize_primary_title_field(
    client: FeishuClient,
    app_token: str,
    table_id: str,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    warnings: list[str] = []
    fields = {item["field_name"]: item for item in client.list_fields(app_token, table_id)}
    legacy_theme = fields.get("主题")
    title_field = fields.get("标题")
    if not legacy_theme or not legacy_theme.get("is_primary"):
        return fields, warnings

    if title_field and title_field.get("field_id") != legacy_theme.get("field_id"):
        records = client.list_records(app_token, table_id, field_names=["主题", "标题"], limit=2000)
        for record in records:
            record_fields = record.get("fields", {})
            desired_title = compact_text(record_fields.get("标题")) or compact_text(record_fields.get("主题"))
            if desired_title and compact_text(record_fields.get("主题")) != desired_title:
                try:
                    client.update_record(app_token, table_id, record["record_id"], {"主题": desired_title})
                except FeishuError as exc:
                    warnings.append(f"{desired_title}: 主字段标题回填失败 - {exc}")
        try:
            client.delete_field(app_token, table_id, title_field["field_id"])
        except FeishuError as exc:
            warnings.append(f"标题: 合并到主字段后删除重复列失败 - {exc}")
            return {item["field_name"]: item for item in client.list_fields(app_token, table_id)}, warnings
        fields = {item["field_name"]: item for item in client.list_fields(app_token, table_id)}
        legacy_theme = fields.get("主题")

    if legacy_theme and legacy_theme.get("field_id"):
        rename_spec = {
            "field_name": "标题",
            "type": legacy_theme["type"],
            **({"property": legacy_theme["property"]} if legacy_theme.get("property") else {}),
        }
        try:
            client.update_field(app_token, table_id, legacy_theme["field_id"], rename_spec)
        except FeishuError as exc:
            warnings.append(f"主题: 主字段重命名为标题失败 - {exc}")

    return {item["field_name"]: item for item in client.list_fields(app_token, table_id)}, warnings


def ensure_conversation_schema(
    client: FeishuClient,
    app_token: str,
    table_id: str,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    warnings: list[str] = []
    field_map, title_warnings = normalize_primary_title_field(client, app_token, table_id)
    warnings.extend(title_warnings)
    field_map = ensure_table_fields(client, app_token, table_id, TABLE_SPECS["conversations"]["fields"])
    field_map, summary_warnings = ensure_summary_url_field(client, app_token, table_id)
    warnings.extend(summary_warnings)
    field_map, contributor_warnings = ensure_person_field(client, app_token, table_id, CONTRIBUTOR_FIELD_NAME)
    warnings.extend(contributor_warnings)
    for field_name in ("标签",):
        field_map, field_warnings = ensure_multiselect_field(client, app_token, table_id, field_name)
        warnings.extend(field_warnings)
    field_map = ensure_table_fields(client, app_token, table_id, TABLE_SPECS["conversations"]["fields"])
    migration_field_names = conversation_field_names(field_map, include_legacy=True)
    records = client.list_records(app_token, table_id, field_names=migration_field_names, limit=2000)
    for record in records:
        update_fields = normalize_conversation_record_fields(record.get("fields", {}))
        if not update_fields:
            continue
        try:
            client.update_record(app_token, table_id, record["record_id"], update_fields)
        except FeishuError as exc:
            title = conversation_title_value(record.get("fields", {})) or record.get("record_id", "未命名主题")
            warnings.append(f"{title}: 主表字段回填失败 - {exc}")

    if not parse_boolish(env_nonempty("FEISHU_KEEP_LEGACY_CONVERSATION_FIELDS"), default=False):
        field_map, prune_warnings = prune_conversation_legacy_fields(client, app_token, table_id)
        warnings.extend(prune_warnings)
    return field_map, warnings


def normalize_conversation_record_fields(fields: dict[str, Any]) -> dict[str, Any]:
    if is_blank_conversation_record(fields):
        return {}
    canonical_title = conversation_title_value(fields)
    update_fields: dict[str, Any] = conversation_title_update_fields(
        asset_document_title(canonical_title),
        current_fields=fields,
    )
    summary_body = summary_body_from_fields(fields)
    tag_values = select_core_topic_tags(
        merge_tags([fields.get("标签"), fields.get("领域")]),
        topic_tag_context_from_fields(fields),
    )
    if tag_values and fields.get("标签") != tag_values:
        update_fields["标签"] = tag_values
    agent_values = normalize_multi_values(fields.get("对话Agent")) or ["codex"]
    if fields.get("对话Agent") != agent_values:
        update_fields["对话Agent"] = agent_values
    current_contributors = normalize_person_entries(fields.get("贡献者"))
    if not current_contributors:
        default_contributors = default_contributor_person_entries()
        if default_contributors:
            update_fields["贡献者"] = default_contributors
    for text_field_name in (
        "来源",
        "TLDR主题",
        "本次新增",
        "价值",
        "核心资产",
        "方法论",
        "认知演进",
        "知识演化图谱",
        "下一步行动",
        "关联资产",
        "参考案例",
    ):
        raw_text = compact_text(fields.get(text_field_name))
        cleaned_text = sanitize_tutorial_text(raw_text)
        if cleaned_text and raw_text != cleaned_text:
            update_fields[text_field_name] = cleaned_text
    if not compact_text(fields.get("TLDR主题")) and canonical_title:
        update_fields["TLDR主题"] = canonical_title
    if not compact_text(fields.get("本次新增")):
        new_round = simple_sentence_excerpt(summary_body or fields.get("讨论问题"), max_chars=80)
        if new_round:
            update_fields["本次新增"] = new_round
    if not compact_text(fields.get("价值")):
        value = simple_sentence_excerpt(fields.get("核心资产") or fields.get("核心洞察"), max_chars=80)
        if value:
            update_fields["价值"] = value
    if not compact_text(fields.get("核心资产")) and compact_text(fields.get("核心洞察")):
        update_fields["核心资产"] = fields.get("核心洞察")
    if not compact_text(fields.get("方法论")):
        method_steps = compact_text(fields.get("工作流") or fields.get("心智模型"))
        if method_steps:
            update_fields["方法论"] = bullet_block([f"名称：{canonical_title or '未命名主题'} 方法"] + split_bullets(method_steps))
    if not compact_text(fields.get("下一步行动")):
        action_source = fields.get("行动建议") or fields.get("知识缺口") or fields.get("后续思考方向")
        if compact_text(action_source):
            update_fields["下一步行动"] = action_source
    if not compact_text(fields.get("来源")):
        source_text = compact_text(fields.get("原始上下文"))
        if source_text:
            update_fields["来源"] = render_source_snapshot(
                SourcePayload(type="conversation", name=source_text, date=compact_text(fields.get("日期")))
            )
    if not compact_text(fields.get("参考案例")) and compact_text(fields.get("阅读建议")):
        update_fields["参考案例"] = fields.get("阅读建议")
    graph_snapshot = tutorial_knowledge_graph_snapshot_from_fields({**fields, **update_fields})
    if graph_snapshot and compact_text(fields.get("知识演化图谱")) != graph_snapshot:
        update_fields["知识演化图谱"] = graph_snapshot
    return update_fields


def consolidate_conversation_records(
    client: FeishuClient,
    app_token: str,
    table_id: str,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    warnings: list[str] = []
    updated_records = 0
    deleted_records = 0
    merged_groups = 0

    for record in records:
        fields = record.get("fields", {})
        if is_blank_conversation_record(fields):
            try:
                client.delete_record(app_token, table_id, record["record_id"])
                deleted_records += 1
            except FeishuError as exc:
                warnings.append(f"{record.get('record_id', '空记录')}: 删除空主题失败 - {exc}")
            continue
        key = conversation_theme_key_from_fields(fields)
        if not key:
            key = normalize_general_key(record.get("record_id"))
        groups.setdefault(key, []).append(record)

    for group_records in groups.values():
        sorted_group = sorted(
            group_records,
            key=lambda item: parse_datetimeish(item.get("fields", {}).get("同步时间"))
            or parse_datetimeish(item.get("fields", {}).get("日期"))
            or datetime.min,
            reverse=True,
        )
        keeper = sorted_group[0]
        keeper_fields = keeper.get("fields", {})

        if len(sorted_group) == 1:
            update_fields = normalize_conversation_record_fields(keeper_fields)
            if update_fields:
                try:
                    client.update_record(app_token, table_id, keeper["record_id"], update_fields)
                    updated_records += 1
                except FeishuError as exc:
                    warnings.append(f"{conversation_title_value(keeper_fields)}: 主题记录修正失败 - {exc}")
            continue

        merged_groups += 1
        aggregated_fields = [item.get("fields", {}) for item in sorted_group]
        update_fields = {
            "对话ID": merge_text_block([fields.get("对话ID") for fields in aggregated_fields]),
            "日期": latest_text_value([fields.get("日期") for fields in aggregated_fields]),
            "标签": select_core_topic_tags(
                merge_tags(
                    [fields.get("标签") for fields in aggregated_fields]
                    + [fields.get("领域") for fields in aggregated_fields]
                ),
                [part for fields in aggregated_fields for part in topic_tag_context_from_fields(fields)],
            ),
            "对话Agent": merge_tags([fields.get("对话Agent") for fields in aggregated_fields]) or ["codex"],
            "贡献者": merge_person_fields([fields.get("贡献者") for fields in aggregated_fields])
            or default_contributor_person_entries(),
            "来源": merge_text_block([fields.get("来源") for fields in aggregated_fields], bullet=True),
            "TLDR主题": latest_text_value([fields.get("TLDR主题") for fields in aggregated_fields]),
            "本次新增": latest_text_value([fields.get("本次新增") for fields in aggregated_fields]),
            "价值": latest_text_value([fields.get("价值") for fields in aggregated_fields]),
            "核心资产": merge_bullet_blocks([fields.get("核心资产") for fields in aggregated_fields]),
            "方法论": merge_bullet_blocks([fields.get("方法论") for fields in aggregated_fields]),
            "认知演进": merge_text_block([fields.get("认知演进") for fields in aggregated_fields], bullet=True),
            "知识演化图谱": latest_text_value([fields.get("知识演化图谱") for fields in aggregated_fields]),
            "下一步行动": merge_bullet_blocks([fields.get("下一步行动") for fields in aggregated_fields]),
            "关联资产": merge_bullet_blocks([fields.get("关联资产") for fields in aggregated_fields]),
            "参考案例": merge_bullet_blocks([fields.get("参考案例") for fields in aggregated_fields]),
            "同步时间": latest_text_value([fields.get("同步时间") for fields in aggregated_fields]),
        }
        update_fields.update(
            conversation_title_update_fields(
                asset_document_title(canonical_conversation_title(sorted_group)),
                current_fields=keeper_fields,
            )
        )
        graph_snapshot = tutorial_knowledge_graph_snapshot_from_fields({**keeper_fields, **update_fields})
        if graph_snapshot:
            update_fields["知识演化图谱"] = graph_snapshot
        try:
            client.update_record(app_token, table_id, keeper["record_id"], update_fields)
            updated_records += 1
        except FeishuError as exc:
            warnings.append(f"{conversation_title_value(keeper_fields)}: 主题合并失败 - {exc}")
            continue

        for duplicate in sorted_group[1:]:
            try:
                client.delete_record(app_token, table_id, duplicate["record_id"])
                deleted_records += 1
            except FeishuError as exc:
                warnings.append(f"{conversation_title_value(keeper_fields)}: 删除重复主题失败 - {exc}")

    refreshed_records = client.list_records(
        app_token,
        table_id,
        field_names=conversation_field_names(),
        limit=max(len(records), 100),
    )
    return {
        "records": refreshed_records,
        "merged_groups": merged_groups,
        "deleted_records": deleted_records,
        "updated_records": updated_records,
        "warnings": warnings,
    }


def upsert_conversation_record(
    client: FeishuClient,
    app_token: str,
    table_id: str,
    existing_records: list[dict[str, Any]],
    new_fields: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    new_key = conversation_theme_key_from_fields(new_fields)
    matching = [
        record
        for record in existing_records
        if conversation_theme_key_from_fields(record.get("fields", {})) == new_key
    ]

    if not matching:
        created = client.create_record(app_token, table_id, new_fields)
        return "created", created

    target = matching[0]
    fields = target.get("fields", {})
    canonical_title = conversation_title_value({**fields, **new_fields})
    update_fields: dict[str, Any] = {
        "对话ID": merge_text_block([fields.get("对话ID"), new_fields.get("对话ID")]),
        "日期": latest_text_value([fields.get("日期"), new_fields.get("日期")]),
        "标签": select_core_topic_tags(
            merge_tags([fields.get("标签"), fields.get("领域"), new_fields.get("标签")]),
            topic_tag_context_from_fields({**fields, **new_fields}),
        ),
        "对话Agent": merge_tags([fields.get("对话Agent"), new_fields.get("对话Agent")]),
        "贡献者": merge_person_fields([fields.get("贡献者"), new_fields.get("贡献者")])
        or default_contributor_person_entries(),
        "来源": merge_text_block([fields.get("来源"), new_fields.get("来源")], bullet=True),
        "TLDR主题": compact_text(new_fields.get("TLDR主题")) or compact_text(fields.get("TLDR主题")),
        "本次新增": compact_text(new_fields.get("本次新增")) or compact_text(fields.get("本次新增")),
        "价值": compact_text(new_fields.get("价值")) or compact_text(fields.get("价值")),
        "核心资产": merge_bullet_blocks([fields.get("核心资产"), new_fields.get("核心资产")]),
        "方法论": merge_bullet_blocks([fields.get("方法论"), new_fields.get("方法论")]),
        "认知演进": merge_text_block([fields.get("认知演进"), new_fields.get("认知演进")], bullet=True),
        "知识演化图谱": compact_text(new_fields.get("知识演化图谱")) or compact_text(fields.get("知识演化图谱")),
        "下一步行动": merge_bullet_blocks([fields.get("下一步行动"), new_fields.get("下一步行动")]),
        "关联资产": merge_bullet_blocks([fields.get("关联资产"), new_fields.get("关联资产")]),
        "参考案例": merge_bullet_blocks([fields.get("参考案例"), new_fields.get("参考案例")]),
        "同步时间": compact_text(new_fields.get("同步时间")) or compact_text(fields.get("同步时间")),
    }
    update_fields.update(conversation_title_update_fields(asset_document_title(canonical_title), current_fields=fields))
    graph_snapshot = tutorial_knowledge_graph_snapshot_from_fields({**fields, **update_fields})
    if graph_snapshot:
        update_fields["知识演化图谱"] = graph_snapshot
    updated = client.update_record(app_token, table_id, target["record_id"], update_fields)
    return "updated", updated


def consolidate_reading_records(
    client: FeishuClient,
    app_token: str,
    table_id: str,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        key = reading_record_key_from_fields(record.get("fields", {}))
        if not key:
            continue
        groups.setdefault(key, []).append(record)

    merged_groups = 0
    deleted_records = 0
    warnings: list[str] = []

    for group_records in groups.values():
        if len(group_records) == 1:
            record = group_records[0]
            fields = record.get("fields", {})
            current_count = parse_intish(fields.get("推荐次数"), default=1)
            update_fields: dict[str, Any] = {}
            if compact_text(fields.get("推荐次数")) != str(current_count):
                update_fields["推荐次数"] = current_count
            if compact_text(fields.get("提及频率")) != str(current_count):
                update_fields["提及频率"] = current_count
            if update_fields:
                try:
                    client.update_record(app_token, table_id, record["record_id"], update_fields)
                except FeishuError as exc:
                    warnings.append(f"{compact_text(fields.get('书名'))}: 推荐次数修正失败 - {exc}")
            continue

        merged_groups += 1
        keeper = group_records[0]
        keeper_fields = keeper.get("fields", {})
        title = compact_text(keeper_fields.get("书名"))
        merged_count = sum(parse_intish(item.get("fields", {}).get("推荐次数"), default=1) for item in group_records)
        aggregated_fields = [item.get("fields", {}) for item in group_records]

        online_value = next(
            (
                value
                for value in (fields.get("在线地址") for fields in aggregated_fields)
                if reading_online_link(value) or reading_online_text(value)
            ),
            None,
        )
        cover_value = next(
            (
                value
                for value in (fields.get("封面图") for fields in aggregated_fields)
                if has_reading_cover(value)
            ),
            None,
        )

        update_fields: dict[str, Any] = {
            "对话ID": merge_text_block([fields.get("对话ID") for fields in aggregated_fields]),
            "日期": merge_text_block([fields.get("日期") for fields in aggregated_fields]),
            "来源主题": merge_source_theme_values([fields.get("来源主题") for fields in aggregated_fields]),
            "推荐理由": merge_text_block([fields.get("推荐理由") for fields in aggregated_fields], bullet=True),
            "优先级": best_priority([fields.get("优先级") for fields in aggregated_fields]),
            "状态": best_status([fields.get("状态") for fields in aggregated_fields]),
            "推荐次数": merged_count,
            "提及频率": merged_count,
        }
        merged_tag_values = merge_tags([fields.get("精华标签") for fields in aggregated_fields])
        if merged_tag_values:
            update_fields["精华标签"] = merged_tag_values
        update_fields["在线地址"] = reading_online_field(title, reading_online_link(online_value))
        if cover_value:
            update_fields["封面图"] = cover_value

        try:
            client.update_record(app_token, table_id, keeper["record_id"], update_fields)
        except FeishuError as exc:
            warnings.append(f"{title}: 合并主记录失败 - {exc}")
            continue

        for duplicate in group_records[1:]:
            try:
                client.delete_record(app_token, table_id, duplicate["record_id"])
                deleted_records += 1
            except FeishuError as exc:
                warnings.append(f"{title}: 删除重复记录失败 - {exc}")

    refreshed_records = client.list_records(app_token, table_id, limit=max(len(records), 100))
    return {
        "records": refreshed_records,
        "merged_groups": merged_groups,
        "deleted_records": deleted_records,
        "warnings": warnings,
    }


def upsert_reading_record(
    client: FeishuClient,
    app_token: str,
    table_id: str,
    existing_records: list[dict[str, Any]],
    new_fields: dict[str, Any],
) -> tuple[str, list[dict[str, Any]]]:
    key = reading_record_key_from_fields(new_fields)
    matching = [record for record in existing_records if reading_record_key_from_fields(record.get("fields", {})) == key]

    if not matching:
        create_fields = dict(new_fields)
        create_fields.setdefault("推荐次数", 1)
        create_fields.setdefault("提及频率", parse_intish(create_fields.get("推荐次数"), default=1))
        created = client.create_record(app_token, table_id, create_fields)
        existing_records.append({"record_id": created.get("record_id"), "fields": create_fields})
        return "created", existing_records

    target = matching[0]
    fields = target.get("fields", {})
    merged_count = parse_intish(fields.get("推荐次数"), default=1) + parse_intish(new_fields.get("推荐次数"), default=1)
    update_fields: dict[str, Any] = {
        "推荐次数": merged_count,
        "提及频率": merged_count,
        "对话ID": merge_text_block([fields.get("对话ID"), new_fields.get("对话ID")]),
        "日期": merge_text_block([fields.get("日期"), new_fields.get("日期")]),
        "来源主题": merge_source_theme_values([fields.get("来源主题"), new_fields.get("来源主题")]),
        "推荐理由": merge_text_block([fields.get("推荐理由"), new_fields.get("推荐理由")], bullet=True),
        "优先级": best_priority([fields.get("优先级"), new_fields.get("优先级")]),
        "状态": best_status([fields.get("状态"), new_fields.get("状态")]),
    }
    merged_tag_values = merge_tags([fields.get("精华标签"), new_fields.get("精华标签")])
    if merged_tag_values:
        update_fields["精华标签"] = merged_tag_values

    current_online = fields.get("在线地址")
    new_online = new_fields.get("在线地址")
    if new_online and (
        not current_online
        or not reading_online_link(current_online)
    ):
        update_fields["在线地址"] = new_online

    current_cover = fields.get("封面图")
    new_cover = new_fields.get("封面图")
    if new_cover and not has_reading_cover(current_cover):
        update_fields["封面图"] = new_cover

    client.update_record(app_token, table_id, target["record_id"], update_fields)
    fields.update(update_fields)
    return "updated", existing_records


def render_gap_snapshot(gaps: list[GapItem]) -> str:
    lines = []
    for gap in gaps:
        main = gap.gap or "未命名不足"
        detail = gap.suggested_practice or gap.why_it_matters
        if detail:
            lines.append(f"{main} -> {detail}")
        else:
            lines.append(main)
    return bullet_block(lines)


def render_methodology_snapshot(methodology: MethodologyPayload) -> str:
    lines: list[str] = []
    if methodology.name:
        lines.append(f"名称：{sanitize_tutorial_text(methodology.name)}")
    for step in methodology.steps or []:
        if compact_text(step):
            lines.append(sanitize_tutorial_text(step))
    return bullet_block(lines)


def render_evolution_snapshot(evolution: EvolutionPayload) -> str:
    lines = []
    if evolution.previous_belief:
        lines.append(f"原认知：{sanitize_tutorial_text(evolution.previous_belief)}")
    if evolution.current_belief:
        lines.append(f"新认知：{sanitize_tutorial_text(evolution.current_belief)}")
    return "\n".join(lines)


def render_action_snapshot(actions: list[ActionItem]) -> str:
    lines = []
    for action in actions:
        label = sanitize_tutorial_text(action.todo) or "未命名行动"
        if action.priority:
            label = f"{label} [{action.priority}]"
        lines.append(label)
    return bullet_block(lines)


def render_reference_snapshot(references: list[ReferenceItem]) -> str:
    lines = []
    for reference in references:
        label = sanitize_tutorial_text(reference.name) or "未命名参考"
        if reference.why:
            label = f"{label} -> {sanitize_tutorial_text(reference.why)}"
        if reference.url:
            label = f"{label} -> {reference.url}"
        lines.append(label)
    return bullet_block(lines)


def render_source_snapshot(source: SourcePayload) -> str:
    lines: list[str] = []
    if source.type:
        lines.append(f"类型：{sanitize_tutorial_text(source.type)}")
    if source.name:
        lines.append(f"名称：{sanitize_tutorial_text(source.name)}")
    if source.date:
        lines.append(f"日期：{sanitize_tutorial_text(source.date)}")
    if source.url:
        lines.append(f"链接：{source.url}")
    return "\n".join(lines)


def contributor_person_entries(contributors: list[ContributorPayload]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    for contributor in contributors:
        open_id = compact_text(contributor.open_id)
        if not open_id or open_id in seen:
            continue
        seen.add(open_id)
        entries.append({"id": open_id})
    return entries


def contributor_names(contributors: list[ContributorPayload]) -> list[str]:
    names: list[str] = []
    for contributor in contributors:
        label = compact_text(contributor.name) or compact_text(contributor.open_id)
        if label:
            names.append(label)
    return unique_texts(names)


def default_contributor_person_entries() -> list[dict[str, str]]:
    return contributor_person_entries([default_contributor()])


def normalize_person_entries(value: Any) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in as_list(value):
        person_id = ""
        if isinstance(item, dict):
            person_id = compact_text(first_present(item, "id", "open_id", "user_id", "union_id", default=""))
        else:
            text = compact_text(item)
            if text.startswith("ou_"):
                person_id = text
        if not person_id or person_id in seen:
            continue
        seen.add(person_id)
        entries.append({"id": person_id})
    return entries


def merge_person_fields(values: list[Any]) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    for value in values:
        for entry in normalize_person_entries(value):
            person_id = compact_text(entry.get("id"))
            if not person_id or person_id in seen:
                continue
            seen.add(person_id)
            entries.append({"id": person_id})
    return entries


def render_related_asset_snapshot(related_assets: list[RelatedAssetItem]) -> str:
    lines = []
    for asset in related_assets:
        label = sanitize_tutorial_text(asset.title) or "未命名资产"
        if asset.relation:
            label = f"{label} -> {sanitize_tutorial_text(asset.relation)}"
        if asset.url:
            label = f"{label} -> {asset.url}"
        lines.append(label)
    return bullet_block(lines)


def compact_graph_phrase(value: Any, *, max_chars: int) -> str:
    text = first_sentence_excerpt(value, max_chars=max_chars)
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    breakpoints = [
        cut.rfind(mark)
        for mark in (" -> ", " → ", "，", ",", "；", ";", "、", " ", "）", ")")
    ]
    breakpoint = max(breakpoints)
    if breakpoint >= max_chars * 0.55:
        cut = cut[:breakpoint]
    else:
        while cut and len(text) > len(cut) and cut[-1].isascii() and cut[-1].isalnum() and text[len(cut)].isascii() and text[len(cut)].isalnum():
            cut = cut[:-1]
    if cut.count("（") > cut.count("）"):
        cut = cut[: cut.rfind("（")]
    if cut.count("(") > cut.count(")"):
        cut = cut[: cut.rfind("(")]
    return cut.rstrip(" ，,;；/-→")


def render_knowledge_graph_snapshot(
    *,
    title: str = "",
    value: str = "",
    core_outputs: list[str] | None = None,
    methodology_name: str = "",
    methodology_steps: list[str] | None = None,
    previous_belief: str = "",
    current_belief: str = "",
    next_actions: list[str] | None = None,
    related_assets: list[str] | None = None,
) -> str:
    core_outputs = reusable_asset_points(core_outputs or [])
    methodology_steps = [
        compact_graph_phrase(item, max_chars=30)
        for item in methodology_steps or []
        if compact_text(item)
    ]
    next_actions = [
        compact_graph_phrase(item, max_chars=34)
        for item in next_actions or []
        if compact_text(item)
    ]
    related_assets = [sanitize_tutorial_text(item) for item in related_assets or [] if compact_text(item)]

    lines: list[str] = []
    if title:
        lines.append(f"主题：{sanitize_tutorial_text(title)}")
    if value:
        lines.append(f"团队价值：{sanitize_tutorial_text(value)}")
    if core_outputs:
        lines.append(f"可复用资产：{'、'.join(core_outputs[:TEAM_ASSET_MAX_ITEMS])}")
    if methodology_name or methodology_steps:
        method = sanitize_tutorial_text(methodology_name) or "可照做流程"
        if methodology_steps:
            method = f"{method} -> {' -> '.join(methodology_steps[:3])}"
        lines.append(f"方法论：{method}")
    if previous_belief or current_belief:
        if previous_belief and current_belief:
            lines.append(f"认知演进：{sanitize_tutorial_text(previous_belief)} -> {sanitize_tutorial_text(current_belief)}")
        else:
            lines.append(f"认知演进：{sanitize_tutorial_text(current_belief or previous_belief)}")
    if next_actions:
        lines.append(f"下一步行动：{'、'.join(next_actions[:2])}")
    if related_assets:
        lines.append(f"关联资产：{'、'.join(related_assets[:3])}")
    if lines:
        lines.append("循环机制：沉淀 -> 复用 -> 验证 -> 回写")
    return "\n".join(lines)


def render_knowledge_graph_snapshot_from_note(note: NotePayload) -> str:
    return render_knowledge_graph_snapshot(
        title=note.tldr.topic or note.title,
        value=note.tldr.value,
        core_outputs=note.core_outputs,
        methodology_name=note.methodology.name,
        methodology_steps=note.methodology.steps or [],
        previous_belief=note.evolution.previous_belief,
        current_belief=note.evolution.current_belief,
        next_actions=[action.todo for action in note.next_actions],
        related_assets=[asset.title for asset in note.related_assets],
    )


def render_book_snapshot(books: list[BookItem]) -> str:
    lines = []
    for book in books:
        label = book.title
        if book.author:
            label = f"{label} / {book.author}"
        if book.reason:
            label = f"{label} -> {book.reason}"
        lines.append(label)
    return bullet_block(lines)


def parse_priority(value: Any) -> int:
    normalized = compact_text(value).strip().lower()
    if normalized in {"high", "高", "p0", "p1"}:
        return 3
    if normalized in {"medium", "中", "normal", "p2"}:
        return 2
    if normalized in {"low", "低", "p3"}:
        return 1
    return 0


def sort_gap_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def sort_key(record: dict[str, Any]) -> tuple[int, str, str]:
        fields = record.get("fields", {})
        review_on = compact_text(fields.get("复盘日期"))
        date = compact_text(fields.get("日期"))
        return (
            parse_priority(fields.get("优先级")),
            review_on or "9999-99-99",
            date or "0000-00-00",
        )

    pending = []
    for record in records:
        status = compact_text(record.get("fields", {}).get("状态")).strip().lower()
        if status in {"已完成", "done", "completed"}:
            continue
        pending.append(record)
    return sorted(pending, key=sort_key, reverse=True)


def sort_reading_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def sort_key(record: dict[str, Any]) -> tuple[int, str]:
        fields = record.get("fields", {})
        return parse_priority(fields.get("优先级")), compact_text(fields.get("日期"))

    pending = []
    for record in records:
        status = compact_text(record.get("fields", {}).get("状态")).strip().lower()
        if status in {"已完成", "读完", "finished", "done", "completed"}:
            continue
        pending.append(record)
    return sorted(pending, key=sort_key, reverse=True)


def build_review_message(
    conversation_records: list[dict[str, Any]],
    gap_records: list[dict[str, Any]],
    reading_records: list[dict[str, Any]],
) -> str:
    pieces = ["知识复利回顾"]

    if conversation_records:
        fields = conversation_records[0].get("fields", {})
        title = conversation_title_value(fields) or "最近一次对话"
        pieces.append(f"最近沉淀主题：{title}")

        directions = split_bullets(compact_text(fields.get("下一步行动"))) or split_bullets(
            compact_text(fields.get("后续思考方向"))
        )
        if directions:
            pieces.append("接下来优先行动：")
            pieces.extend(f"{index}. {item}" for index, item in enumerate(directions[:3], start=1))

    if gap_records:
        pieces.append("当前最该补的短板：")
        for gap in gap_records[:3]:
            fields = gap.get("fields", {})
            line = compact_text(fields.get("不足")) or compact_text(fields.get("标题"))
            action = compact_text(fields.get("弥补动作"))
            if action:
                line = f"{line} -> {action}"
            pieces.append(f"- {line}")

    if reading_records:
        pieces.append("推荐继续读：")
        for book in reading_records[:2]:
            fields = book.get("fields", {})
            label = compact_text(fields.get("书名")) or "未命名书目"
            author = compact_text(fields.get("作者"))
            reason = compact_text(fields.get("推荐理由"))
            if author:
                label = f"{label} / {author}"
            if reason:
                label = f"{label} -> {reason}"
            pieces.append(f"- {label}")

    if len(pieces) == 1:
        pieces.append("知识库里还没有可回顾的内容。先完成一次 sync，再开启提醒。")

    return "\n".join(pieces)


def render_reminder(note: NotePayload) -> str:
    reminder = note.reminder.strip()
    if reminder:
        return reminder

    pieces = [f"知识复利提醒：{note.title}"]
    if note.tldr.new_this_round:
        pieces.append(f"本次新增：{note.tldr.new_this_round}")
    if note.tldr.value:
        pieces.append(f"资产价值：{note.tldr.value}")
    if note.next_actions:
        pieces.append("下一步行动：")
        pieces.extend(f"{index}. {item.todo}" for index, item in enumerate(note.next_actions[:3], start=1))
    if note.references:
        pieces.append(f"可参考：{note.references[0].name}")
    return "\n".join(pieces)


def task_focus_from_note(note: NotePayload) -> str:
    for candidate in (note.tldr.topic, note.title, note.tldr.new_this_round):
        text = first_sentence_excerpt(candidate, max_chars=72)
        if text:
            return text
    for candidate in note.discussion_points + [note.source_context, note.summary]:
        text = first_sentence_excerpt(candidate, max_chars=72)
        if text:
            return text
    return note.title


def result_focus_from_note(note: NotePayload, task_focus: str) -> str:
    task_key = normalize_general_key(first_sentence_excerpt(task_focus, max_chars=120))
    candidates = [note.tldr.new_this_round, note.tldr.value] + note.core_outputs + note.key_insights + note.actions
    for candidate in candidates:
        text = first_sentence_excerpt(candidate, max_chars=84)
        if not text:
            continue
        if normalize_general_key(text) == task_key:
            continue
        return text
    return task_focus


def next_focus_from_note(note: NotePayload) -> str:
    candidates = (
        [action.todo for action in note.next_actions if action.todo]
        + note.next_thinking_directions
        + [gap.suggested_practice for gap in note.blind_spots if gap.suggested_practice]
        + note.actions
    )
    for candidate in candidates:
        text = first_sentence_excerpt(candidate, max_chars=72)
        if text:
            return text
    return "回看这次沉淀，并继续补足下一步最小可执行动作。"


def sync_result_url(config: dict[str, Any], tutorial_url: str) -> str:
    return compact_text(tutorial_url) or compact_text(config.get("base_url"))


def render_sync_push_message(
    note: NotePayload,
    action: str,
    *,
    result_url: str = "",
    root_url: str = "",
) -> str:
    title = note.title or "未命名主题"
    task_focus = task_focus_from_note(note)
    result_focus = result_focus_from_note(note, task_focus)
    next_focus = next_focus_from_note(note)

    if action == "created":
        lines = [
            f"你新增了一条知识资产：《{title}》",
            f"资产主题：{task_focus}",
            f"本次新增：{result_focus}",
            f"下一步行动：{next_focus}",
        ]
    else:
        lines = [
            f"你更新了一条知识资产：《{title}》",
            f"资产主题：{task_focus}",
            f"认知或产物变化：{result_focus}",
            f"下一步行动：{next_focus}",
        ]

    if result_url:
        lines.append(f"文档：{result_url}")
    if root_url and compact_text(root_url) != compact_text(result_url):
        lines.append(f"知识复利系统入口：{root_url}")
    return "\n".join(lines)


def render_upgrade_docs_push_message(
    tutorial_urls: dict[str, str],
    *,
    root_url: str = "",
) -> str:
    updated_count = len(tutorial_urls)
    lines = [
        f"能力资产文档已刷新：{updated_count} 个主题",
        "这次更新已按团队阅读口径重排为：贡献者、来源、3 秒速览、知识演化图谱、可直接复用、方法论、认知演进、下一步行动、关联资产、参考案例。",
    ]
    for title, url in list(tutorial_urls.items())[:5]:
        if url:
            lines.append(f"- {title}: {url}")
        else:
            lines.append(f"- {title}")
    if updated_count > 5:
        lines.append(f"还有 {updated_count - 5} 个主题已更新。")
    if root_url:
        lines.append(f"知识复利系统入口：{root_url}")
    return "\n".join(lines)


def split_bullets(value: str) -> list[str]:
    items: list[str] = []
    for line in compact_text(value).splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("- "):
            line = line[2:].strip()
        items.append(line)
    return items


def extract_link_url(value: Any) -> str:
    if isinstance(value, dict):
        return compact_text(value.get("link"))
    text = compact_text(value)
    if text.startswith("http://") or text.startswith("https://"):
        return text
    return ""


def summary_body_from_fields(fields: dict[str, Any]) -> str:
    body = compact_text(fields.get("摘要正文"))
    if body:
        return body
    summary_value = fields.get("摘要")
    if extract_link_url(summary_value):
        return ""
    return compact_text(summary_value)


def strip_discussion_metadata(text: Any) -> str:
    line = compact_text(text)
    if not line:
        return ""
    line = re.sub(r"^\d{4}-\d{2}-\d{2}(?:[T\s]\d{2}:\d{2}(?::\d{2})?)?\s*", "", line).strip()
    line = re.sub(r"^\[[^\]]+\]\s*", "", line).strip()
    return line


def complete_clause_excerpt(value: str, *, max_chars: int) -> str:
    value = compact_text(value)
    if not value or len(value) <= max_chars:
        return value

    # Keep whole clauses instead of chopping text and pretending the omission is a summary.
    parts = re.split(r"([，,])", value)
    selected: list[str] = []
    pending = ""
    for part in parts:
        if not part:
            continue
        pending += part
        if part in {"，", ","}:
            clause = pending.strip()
            pending = ""
            candidate = "".join(selected + [clause]).rstrip("，, ")
            if selected and len(candidate) > max_chars:
                break
            selected.append(clause)
            continue

    if pending.strip():
        clause = pending.strip()
        candidate = "".join(selected + [clause]).rstrip("，, ")
        if not selected or len(candidate) <= max_chars:
            selected.append(clause)

    result = "".join(selected).rstrip("，, ")
    return result or value


def first_sentence_excerpt(text: Any, *, max_chars: int = 80) -> str:
    value = sanitize_tutorial_text(text)
    if not value:
        return ""
    value = re.sub(r"\s+", " ", value).strip()
    value = strip_discussion_metadata(value)
    value = re.sub(r"^(?:[-=]+>|→|⇒)\s*", "", value).strip()
    value = re.sub(
        r"^(?:本次|这次|此次|这一轮|当前|目前)?\s*(?:主要)?(?:在)?(?:讨论|推进|处理|解决|梳理|聚焦|完善)\s*",
        "",
        value,
    ).strip()
    value = re.sub(r"^我们(?:主要)?(?:围绕|在)\s*", "", value).strip()
    value = re.split(r"[。！？!?；;\n]", value, maxsplit=1)[0].strip(" ，,;；。")
    return complete_clause_excerpt(value, max_chars=max_chars)


def overview_sentence_from_fields(fields: dict[str, Any]) -> str:
    title = conversation_title_value(fields) or "未命名主题"
    agent_values = normalize_multi_values(fields.get("对话Agent"))
    latest_agent = agent_values[0] if agent_values else ""
    discussion = split_bullets(compact_text(fields.get("讨论问题")))

    core = ""
    for candidate in discussion:
        core = first_sentence_excerpt(candidate)
        if core:
            break
    if not core:
        for candidate in (fields.get("原始上下文"), summary_body_from_fields(fields), title):
            core = first_sentence_excerpt(candidate)
            if core:
                break

    if not core:
        return ""

    if normalize_general_key(core) == normalize_general_key(title):
        if latest_agent:
            return f"这个主题主要记录与 {latest_agent} 围绕“{title}”这项任务的讨论与推进。"
        return f"这个主题主要围绕“{title}”这项任务展开。"

    if latest_agent:
        return f"这个主题主要记录与 {latest_agent} 围绕“{title}”这项任务的讨论，重点是：{core}。"
    return f"这个主题主要围绕“{title}”这项任务展开，重点是：{core}。"


def should_render_detailed_summary(summary: str, overview: str) -> bool:
    body = compact_text(summary)
    short = compact_text(overview)
    if not body:
        return False
    if normalize_general_key(first_sentence_excerpt(body, max_chars=200)) == normalize_general_key(
        first_sentence_excerpt(short, max_chars=200)
    ):
        return False
    return len(body) > 24 or "\n" in body


def sedimentation_topic_title(fields: dict[str, Any]) -> str:
    return conversation_title_value(fields) or compact_text(fields.get("TLDR主题")) or "未命名主题"


def asset_document_title(topic: Any) -> str:
    base = strip_theme_affixes(topic) or compact_text(topic) or "未命名主题"
    return f"{base}｜能力资产"


def tutorial_doc_title(fields: dict[str, Any]) -> str:
    return asset_document_title(sedimentation_topic_title(fields))


def tutorial_doc_url(document_info: dict[str, Any]) -> str:
    for key in ("url", "document_url", "link", "permalink"):
        url = compact_text(document_info.get(key))
        if url:
            return url
    node_token = compact_text(first_present(document_info, "node_token", default=""))
    if node_token:
        return f"{WIKI_URL_PREFIX}/{node_token}"
    document_id = compact_text(
        first_present(document_info, "document_id", "document_token", "token", "obj_token", default="")
    )
    if document_id:
        return f"{DOCX_URL_PREFIX}/{document_id}"
    return ""


def parse_docx_document_id(value: Any) -> str:
    text = compact_text(value)
    if not text:
        return ""
    if re.fullmatch(r"dox[a-zA-Z0-9]+", text):
        return text
    match = re.search(r"/docx/([a-zA-Z0-9]+)", text)
    if match:
        return match.group(1)
    return ""


def existing_tutorial_url(fields: dict[str, Any]) -> str:
    return extract_link_url(fields.get("摘要"))


def existing_tutorial_document_id(fields: dict[str, Any]) -> str:
    return parse_docx_document_id(existing_tutorial_url(fields))


def list_all_root_children(client: FeishuClient, document_id: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page_token: str | None = None
    while True:
        data = client.list_document_children(
            document_id,
            document_id,
            page_size=500,
            page_token=page_token,
            with_descendants=False,
        )
        items.extend(data.get("items", []))
        if not data.get("has_more"):
            break
        page_token = compact_text(data.get("page_token"))
        if not page_token:
            break
    return items


def replace_document_root_children(
    client: FeishuClient,
    document_id: str,
    children: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    existing_children = list_all_root_children(client, document_id)
    remaining = len(existing_children)
    while remaining > 0:
        chunk = min(remaining, 500)
        client.batch_delete_document_children(document_id, document_id, start_index=0, end_index=chunk)
        remaining -= chunk

    return append_document_children_batched(client, document_id, document_id, children)


def append_document_children_batched(
    client: FeishuClient,
    document_id: str,
    block_id: str,
    children: list[dict[str, Any]],
    *,
    batch_size: int = 50,
) -> list[dict[str, Any]]:
    created_children: list[dict[str, Any]] = []
    if not children:
        return created_children
    normalized_batch_size = min(max(batch_size, 1), 50)
    for index in range(0, len(children), normalized_batch_size):
        data = client.create_document_children(
            document_id,
            block_id,
            children[index : index + normalized_batch_size],
        )
        created_children.extend(data.get("children", []))
    return created_children


def conversation_doc_parent_target() -> str | None:
    return (
        env_nonempty("FEISHU_DOC_PARENT_URL")
        or env_nonempty("FEISHU_DOC_PARENT_TOKEN")
        or env_nonempty("FEISHU_DOC_FOLDER_TOKEN")
        or env_nonempty("FEISHU_BASE_FOLDER_TOKEN")
    )


def configured_dashboard_target(config: dict[str, Any] | None = None) -> str:
    return compact_text(
        env_nonempty("FEISHU_DASHBOARD_TARGET_URL")
        or (config or {}).get(DASHBOARD_TARGET_URL_CONFIG_KEY)
    )


def require_confirmation_before_target_fallback(config: dict[str, Any] | None = None) -> bool:
    override = env_nonempty("FEISHU_REQUIRE_TARGET_CONFIRMATION")
    if override is not None:
        return parse_boolish(override, default=True)
    return parse_boolish(
        (config or {}).get(TARGET_FALLBACK_CONFIRMATION_CONFIG_KEY),
        default=True,
    )


def target_write_confirmation_error(
    target: str,
    asset_label: str,
    exc: Exception | str,
) -> FeishuError:
    location = compact_text(target) or "当前配置的目标地址"
    message = compact_text(exc)
    return FeishuError(
        f"{asset_label} 无法写入目标位置：{location}。"
        "为了避免静默写到其他位置，本次已停止，没有自动回退。"
        "请先询问用户是否允许继续写入其他位置后，再重新执行。"
        f"{f' 原始错误：{message}' if message else ''}"
    )


def unsupported_target_write_error(target: str, asset_label: str) -> FeishuError:
    location = compact_text(target) or "当前配置的目标地址"
    return FeishuError(
        f"{asset_label} 的目标位置当前不是可直接写入的 folder/wiki/docx 地址：{location}。"
        "为了避免静默写到别处，本次已停止。"
        "请先询问用户是否允许改为写入其他可写位置，再继续执行。"
    )


def parse_feishu_doc_parent_target(value: str) -> dict[str, str]:
    raw = compact_text(value)
    if not raw:
        return {}

    if "://" not in raw:
        if raw.startswith("fld"):
            return {"kind": "folder", "token": raw}
        if raw.startswith("wik"):
            return {"kind": "wiki", "token": raw, "lookup_obj_type": "wiki"}
        if raw.startswith("dox"):
            return {"kind": "wiki", "token": raw, "lookup_obj_type": "docx"}
        return {"kind": "folder", "token": raw}

    parsed = parse.urlparse(raw)
    path = parsed.path or ""
    folder_match = re.search(r"/drive/folder/([^/?#]+)", path)
    if folder_match:
        return {"kind": "folder", "token": folder_match.group(1)}

    wiki_match = re.search(r"/wiki/([^/?#]+)", path)
    if wiki_match:
        return {"kind": "wiki", "token": wiki_match.group(1), "lookup_obj_type": "wiki"}

    docx_match = re.search(r"/docx/([^/?#]+)", path)
    if docx_match:
        return {"kind": "wiki", "token": docx_match.group(1), "lookup_obj_type": "docx"}

    return {"kind": "unknown", "value": raw}


def resolve_doc_parent_target(client: FeishuClient, raw_target: str | None) -> dict[str, str] | None:
    if not raw_target:
        return None

    target = parse_feishu_doc_parent_target(raw_target)
    kind = target.get("kind")
    if kind == "folder":
        return target
    if kind == "wiki":
        try:
            node = client.get_wiki_node(target["token"], obj_type=target.get("lookup_obj_type"))
        except FeishuError as exc:
            message = str(exc)
            if "99991672" in message or "wiki:" in message:
                raise FeishuError(WIKI_PERMISSION_HINT) from exc
            raise FeishuError(
                "当前这个文档地址没有解析成可写入的知识库父节点。"
                "普通 docx 链接只有在它本身属于知识库节点时，才能在它下面创建子文档；"
                "否则请改给知识库/wiki 地址，或给一个文件夹地址。"
            ) from exc

        space_id = compact_text(node.get("space_id"))
        node_token = compact_text(node.get("node_token"))
        if not space_id or not node_token:
            raise FeishuError(f"知识库父节点解析结果不完整: {node}")
        return {"kind": "wiki", "space_id": space_id, "node_token": node_token}

    raise FeishuError(
        "FEISHU_DOC_PARENT_URL / FEISHU_DOC_PARENT_TOKEN 不是可识别的飞书文件夹、知识库或文档地址。"
    )


def resolve_conversation_doc_parent(client: FeishuClient) -> dict[str, str] | None:
    return resolve_doc_parent_target(client, conversation_doc_parent_target())


def resolve_dashboard_doc_parent(client: FeishuClient, config: dict[str, Any]) -> dict[str, str] | None:
    raw_target = configured_dashboard_target(config)
    if raw_target:
        parsed = parse_feishu_doc_parent_target(raw_target)
        if parsed.get("kind") == "unknown":
            raise unsupported_target_write_error(raw_target, "仪表盘")
        return resolve_doc_parent_target(client, raw_target)
    return resolve_conversation_doc_parent(client)


def current_notify_member_id() -> str | None:
    return env_nonempty("FEISHU_NOTIFY_OPEN_ID") or env_nonempty("FEISHU_NOTIFY_RECEIVE_ID")


def grant_doc_access_if_possible(client: FeishuClient, document_id: str) -> None:
    member_id = current_notify_member_id()
    if not member_id:
        return
    try:
        client.add_permission_member(
            document_id,
            doc_type="docx",
            member_id=member_id,
            member_type="openid",
            perm="full_access",
            perm_type="container",
            collaborator_type="user",
            need_notification=False,
        )
    except FeishuError:
        pass


def numbered_markdown(items: list[str]) -> list[str]:
    return [f"{index}. {item}" for index, item in enumerate(items, start=1)]


def folder_url_from_token(token: str) -> str:
    cleaned = compact_text(token)
    if not cleaned:
        return ""
    return f"https://trip.larkenterprise.com/drive/folder/{cleaned}"


def configured_doc_root_url(config: dict[str, Any] | None = None) -> str:
    explicit = compact_text(env_nonempty("FEISHU_DOC_ROOT_URL") or (config or {}).get(DOC_ROOT_URL_CONFIG_KEY))
    if explicit:
        return explicit

    for candidate in (
        env_nonempty("FEISHU_DOC_PARENT_URL"),
        env_nonempty("FEISHU_DOC_PARENT_TOKEN"),
        env_nonempty("FEISHU_DOC_FOLDER_TOKEN"),
        env_nonempty("FEISHU_BASE_FOLDER_TOKEN"),
    ):
        raw = compact_text(candidate)
        if not raw:
            continue
        parsed = parse_feishu_doc_parent_target(raw)
        if parsed.get("kind") == "folder":
            return folder_url_from_token(parsed.get("token", ""))
        if parsed.get("kind") in {"wiki", "unknown"}:
            return raw
    return ""


def tutorial_fragments_from_text(value: Any, *, max_chars: int = 30) -> list[str]:
    items: list[str] = []
    for part in re.split(r"[；;]+", compact_text(value)):
        excerpt = first_sentence_excerpt(part, max_chars=max_chars)
        excerpt = re.sub(r"^(?:并|同时|以及|另外|顺带|再|再把)\s*", "", excerpt).strip()
        if excerpt:
            items.append(excerpt)
    return unique_texts(items)


def merge_tutorial_fragments(
    values: list[Any],
    *,
    max_items: int = 3,
    max_chars: int = 72,
    item_max_chars: int = 30,
) -> str:
    fragments: list[str] = []
    seen: set[str] = set()
    for value in values:
        for fragment in tutorial_fragments_from_text(value, max_chars=item_max_chars):
            key = normalize_general_key(fragment) or fragment
            if key in seen:
                continue
            seen.add(key)
            fragments.append(fragment)

    selected: list[str] = []
    for fragment in fragments:
        candidate = "；".join(selected + [fragment])
        if selected and len(candidate) > max_chars:
            break
        if len(candidate) > max_chars:
            selected.append(first_sentence_excerpt(fragment, max_chars=max_chars))
            break
        selected.append(fragment)
        if len(selected) >= max_items:
            break

    if selected:
        return "；".join(selected)
    return ""


def tutorial_summary_entries(fields: dict[str, Any]) -> list[str]:
    grouped: dict[str, list[str]] = {}
    order: list[str] = []

    for entry in discussion_entries_from_fields(fields):
        date_text = compact_text(entry.get("date_text")) or compact_text(fields.get("同步时间"))[:10] or compact_text(
            fields.get("日期")
        )
        if not date_text:
            continue
        if date_text not in grouped:
            grouped[date_text] = []
            order.append(date_text)
        grouped[date_text].append(entry.get("body"))

    if not order:
        fallback_date = compact_text(fields.get("同步时间"))[:10] or compact_text(fields.get("日期"))
        fallback_summary = summary_body_from_fields(fields) or overview_sentence_from_fields(fields) or task_focus_from_fields(fields)
        if fallback_date and compact_text(fallback_summary):
            grouped[fallback_date] = [fallback_summary]
            order.append(fallback_date)

    items: list[str] = []
    for date_text in order:
        merged = merge_tutorial_fragments(grouped.get(date_text, []), max_items=3, max_chars=72, item_max_chars=28)
        if merged:
            items.append(f"{date_text}：{merged}")
    return items


def concise_tutorial_points(
    values: list[Any],
    *,
    max_items: int = 4,
    max_chars: int = 42,
) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for value in values:
        excerpt = first_sentence_excerpt(value, max_chars=max_chars)
        if not excerpt:
            continue
        key = normalize_general_key(excerpt) or excerpt
        if key in seen:
            continue
        seen.add(key)
        items.append(excerpt)
        if len(items) >= max_items:
            break
    return items


def split_tutorial_source_fragments(value: Any) -> list[str]:
    fragments: list[str] = []
    for line in split_bullets(sanitize_tutorial_text(value)):
        for part in re.split(r"[。！？!?；;\n]+", line):
            text = sanitize_tutorial_text(part).strip(" ，,;；。")
            text = re.sub(r"^(?:[-=]+>|→|⇒)\s*", "", text).strip()
            if text:
                fragments.append(text)
    return unique_texts(fragments)


def tutorial_build_step_candidates(fields: dict[str, Any], field_names: tuple[str, ...]) -> list[str]:
    values: list[Any] = []
    for field_name in field_names:
        if field_name == "__task_focus__":
            values.append(task_focus_from_fields(fields))
        elif field_name == "__summary__":
            values.append(summary_body_from_fields(fields))
        elif field_name == "__title__":
            values.append(conversation_title_value(fields))
        else:
            values.append(fields.get(field_name))

    candidates: list[str] = []
    for value in values:
        candidates.extend(split_tutorial_source_fragments(value))
    return unique_texts(candidates)


def select_tutorial_build_step_detail(
    candidates: list[str],
    keywords: tuple[str, ...],
    used_keys: set[str],
    *,
    require_keyword: bool,
    max_chars: int = 90,
) -> str:
    keyword_keys = [normalize_general_key(keyword) for keyword in keywords if normalize_general_key(keyword)]
    scored: list[tuple[int, int, str, str]] = []

    for index, candidate in enumerate(candidates):
        excerpt = first_sentence_excerpt(candidate, max_chars=max_chars)
        if not excerpt:
            continue
        key = normalize_general_key(excerpt) or excerpt
        if key in used_keys:
            continue

        haystack = normalize_general_key(candidate)
        score = sum(1 for keyword_key in keyword_keys if keyword_key and keyword_key in haystack)
        if require_keyword and score <= 0:
            continue
        if len(excerpt) >= 12:
            score += 1
        scored.append((score, -index, excerpt, key))

    if not scored:
        return ""

    scored.sort(reverse=True)
    _, _, excerpt, key = scored[0]
    used_keys.add(key)
    return excerpt


def tutorial_build_steps(fields: dict[str, Any]) -> list[str]:
    specs: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = [
        (
            "界定目标与复用边界",
            ("目标", "边界", "任务", "问题", "场景", "用例", "主题", "主线", "验证", "压测"),
            ("__task_focus__", "TLDR主题", "本次新增", "讨论问题", "__summary__", "原始上下文", "__title__"),
        ),
        (
            "整理输入材料与约束",
            ("规范", "规则", "模板", "token", "design", "UI Kit", "模式", "资产", "schema", "字段", "约束"),
            ("核心资产", "方法论", "参考案例", "核心洞察", "心智模型", "行动建议", "__summary__", "讨论问题"),
        ),
        (
            "搭建流程或结构骨架",
            ("流程", "结构", "骨架", "页面", "组件", "布局", "状态", "链路", "闭环", "表", "框架"),
            ("方法论", "核心资产", "下一步行动", "心智模型", "行动建议", "核心洞察", "讨论问题", "__summary__"),
        ),
        (
            "填充关键内容并形成产物",
            ("内容", "数据", "文档", "教程", "HTML", "PNG", "交互", "输出", "写入", "落地", "交付", "生成"),
            ("核心资产", "参考案例", "下一步行动", "行动建议", "核心洞察", "__summary__", "讨论问题", "心智模型"),
        ),
        (
            "验证产物并回写改进",
            ("验证", "评审", "预览", "走查", "checklist", "复盘", "回写", "提醒", "下一步", "迭代", "校验"),
            ("下一步行动", "认知演进", "后续思考方向", "知识缺口", "行动建议", "核心洞察", "讨论问题"),
        ),
    ]

    steps: list[str] = []
    used_keys: set[str] = set()
    for label, keywords, field_names in specs:
        candidates = tutorial_build_step_candidates(fields, field_names)
        detail = select_tutorial_build_step_detail(candidates, keywords, used_keys, require_keyword=True)
        if not detail:
            detail = select_tutorial_build_step_detail(candidates, keywords, used_keys, require_keyword=False)
        if detail:
            steps.append(f"{label}：{detail}")

    return steps[:5]


def full_tutorial_points(values: list[Any]) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = re.sub(r"\s+", " ", sanitize_tutorial_text(value)).strip()
        if not text:
            continue
        key = normalize_general_key(text) or text
        if key in seen:
            continue
        seen.add(key)
        items.append(text)
    return items


def tutorial_theme_source_keys(fields: dict[str, Any]) -> set[str]:
    keys = {
        conversation_theme_key_from_fields(fields),
        normalize_general_key(canonical_conversation_title_from_text(conversation_title_value(fields))),
        normalize_general_key(conversation_title_value(fields)),
    }
    return {key for key in keys if key}


def reading_source_theme_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    for item in split_source_theme_values(value):
        canonical = canonical_conversation_title_from_text(item) or compact_text(item)
        key = normalize_general_key(canonical) or normalize_general_key(item)
        if key:
            keys.add(key)
    return keys


def fallback_tutorial_reading_items(fields: dict[str, Any]) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    seen: set[str] = set()
    for line in split_bullets(compact_text(fields.get("阅读建议"))):
        parts = re.split(r"\s*->\s*", line, maxsplit=1)
        title = compact_text(parts[0])
        reason = compact_text(parts[1]) if len(parts) > 1 else ""
        if not title:
            continue
        key = normalize_general_key(title) or normalize_lookup_key(title) or title
        if key in seen:
            continue
        seen.add(key)
        items.append({"title": title, "url": "", "reason": reason})
    return items


def tutorial_reading_items(
    fields: dict[str, Any],
    reading_records: list[dict[str, Any]] | None = None,
) -> list[dict[str, str]]:
    theme_keys = tutorial_theme_source_keys(fields)
    items: list[dict[str, str]] = []
    seen: set[str] = set()

    if reading_records:
        sorted_records = sorted(
            reading_records,
            key=lambda record: (
                parse_intish(record.get("fields", {}).get("推荐次数"), default=1),
                parse_priority(record.get("fields", {}).get("优先级")),
                compact_text(record.get("fields", {}).get("日期")),
            ),
            reverse=True,
        )
        for record in sorted_records:
            reading_fields = record.get("fields", {})
            source_keys = reading_source_theme_keys(reading_fields.get("来源主题"))
            if theme_keys and not theme_keys.intersection(source_keys):
                continue
            title = compact_text(reading_fields.get("书名"))
            if not title:
                continue
            key = normalize_general_key(title) or normalize_lookup_key(title) or title
            if key in seen:
                continue
            seen.add(key)
            reason = merge_tutorial_fragments(
                split_bullets(compact_text(reading_fields.get("推荐理由"))),
                max_items=2,
                max_chars=96,
                item_max_chars=48,
            )
            items.append(
                {
                    "title": title,
                    "url": reading_online_link(reading_fields.get("在线地址")),
                    "reason": reason,
                }
            )

    return items or fallback_tutorial_reading_items(fields)


def tutorial_tldr_from_fields(fields: dict[str, Any]) -> TldrPayload:
    title = conversation_title_value(fields) or "未命名主题"
    topic = compact_text(fields.get("TLDR主题")) or title
    new_this_round = reusable_asset_label(fields.get("本次新增"), max_chars=48)
    value = first_sentence_excerpt(fields.get("价值"), max_chars=72)

    if not new_this_round:
        summary = summary_body_from_fields(fields)
        new_this_round = simple_sentence_excerpt(summary, max_chars=80)
    if not value:
        candidates = split_bullets(compact_text(fields.get("核心资产"))) or split_bullets(compact_text(fields.get("核心洞察")))
        value = first_sentence_excerpt(candidates[0], max_chars=80) if candidates else ""

    return TldrPayload(topic=topic, new_this_round=new_this_round, value=value)


def tutorial_core_outputs_from_fields(fields: dict[str, Any]) -> list[str]:
    items = reusable_asset_points(split_bullets(compact_text(fields.get("核心资产"))))
    if items:
        return items
    return reusable_asset_points(split_bullets(compact_text(fields.get("核心洞察"))), max_items=TEAM_ASSET_MAX_ITEMS)


def tutorial_workflow_from_fields(fields: dict[str, Any]) -> list[str]:
    items = full_tutorial_points(split_bullets(compact_text(fields.get("工作流"))))
    if items:
        return items
    return concise_tutorial_points(split_bullets(compact_text(fields.get("心智模型"))), max_items=6, max_chars=72)


def tutorial_methodology_from_fields(fields: dict[str, Any]) -> MethodologyPayload:
    raw_lines = split_bullets(compact_text(fields.get("方法论")))
    name = ""
    steps: list[str] = []
    for line in raw_lines:
        text = sanitize_tutorial_text(line)
        if text.startswith("名称：") or text.startswith("方法名："):
            name = compact_text(text.split("：", 1)[1])
            continue
        if text:
            steps.append(text)

    workflow = tutorial_workflow_from_fields(fields)
    if not steps:
        steps = workflow or tutorial_build_steps(fields)
    if not name and steps:
        name = f"{conversation_title_value(fields) or '未命名主题'} 方法"
    return MethodologyPayload(name=name, steps=steps)


def tutorial_evolution_from_fields(fields: dict[str, Any]) -> EvolutionPayload:
    previous = ""
    current = ""
    for line in split_bullets(compact_text(fields.get("认知演进"))):
        text = sanitize_tutorial_text(line)
        if text.startswith("原认知：") or text.startswith("旧认知："):
            previous = compact_text(text.split("：", 1)[1])
        elif text.startswith("新认知：") or text.startswith("当前认知："):
            current = compact_text(text.split("：", 1)[1])
        elif "->" in text and not current:
            before, after = text.split("->", 1)
            previous = compact_text(before)
            current = compact_text(after)
        elif "→" in text and not current:
            before, after = text.split("→", 1)
            previous = compact_text(before)
            current = compact_text(after)
        elif text and not current:
            current = text
    return EvolutionPayload(previous_belief=previous, current_belief=current)


def tutorial_actions_from_fields(fields: dict[str, Any]) -> list[ActionItem]:
    source_lines = (
        split_bullets(compact_text(fields.get("下一步行动")))
        or split_bullets(compact_text(fields.get("行动建议")))
        or split_bullets(compact_text(fields.get("知识缺口")))
        or split_bullets(compact_text(fields.get("后续思考方向")))
    )
    actions: list[ActionItem] = []
    for line in source_lines:
        text = sanitize_tutorial_text(line)
        priority = "medium"
        match = re.search(r"\[(high|medium|low)\]\s*$", text, flags=re.I)
        if match:
            priority = match.group(1).lower()
            text = text[: match.start()].strip()
        text = re.sub(r"^(?:□|☐|\\[ \\])\s*", "", text).strip()
        if text:
            actions.append(ActionItem(todo=text, priority=priority))
    return actions


def tutorial_references_from_fields(fields: dict[str, Any]) -> list[ReferenceItem]:
    source_lines = split_bullets(compact_text(fields.get("参考案例"))) or split_bullets(compact_text(fields.get("阅读建议")))
    references: list[ReferenceItem] = []
    for line in source_lines:
        text = sanitize_tutorial_text(line)
        parts = [compact_text(part) for part in re.split(r"\s*->\s*", text, maxsplit=2)]
        if not parts or not parts[0]:
            continue
        name = parts[0]
        why = parts[1] if len(parts) >= 2 else ""
        url = parts[2] if len(parts) >= 3 and parts[2].startswith(("http://", "https://")) else ""
        references.append(ReferenceItem(name=name, why=why, url=url))
    return references


def tutorial_source_from_fields(fields: dict[str, Any]) -> SourcePayload:
    if not compact_text(fields.get("来源")):
        return SourcePayload()
    source_type = ""
    name = ""
    url = ""
    date = ""
    for line in split_bullets(compact_text(fields.get("来源"))):
        text = sanitize_tutorial_text(line)
        if text.startswith("类型："):
            source_type = compact_text(text.split("：", 1)[1])
        elif text.startswith("名称："):
            name = compact_text(text.split("：", 1)[1])
        elif text.startswith("日期："):
            date = compact_text(text.split("：", 1)[1])
        elif text.startswith("链接："):
            url = compact_text(text.split("：", 1)[1])
        elif text and not name:
            name = text
    if not date:
        date = compact_text(fields.get("日期")) or compact_text(fields.get("同步时间"))[:10]
    return SourcePayload(type=source_type or "conversation", name=name, url=url, date=date)


def tutorial_contributor_labels_from_fields(fields: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    for item in as_list(fields.get("贡献者")):
        if isinstance(item, dict):
            label = compact_text(
                first_present(item, "name", "en_name", "email", "id", "open_id", default="")
            )
        else:
            label = compact_text(item)
        if label:
            labels.append(label)
    if labels:
        return unique_texts(labels)
    default_item = default_contributor()
    return contributor_names([default_item])


def tutorial_related_assets_from_fields(fields: dict[str, Any]) -> list[RelatedAssetItem]:
    assets: list[RelatedAssetItem] = []
    for line in split_bullets(compact_text(fields.get("关联资产"))):
        text = sanitize_tutorial_text(line)
        parts = [compact_text(part) for part in re.split(r"\s*->\s*", text, maxsplit=2)]
        if not parts or not parts[0]:
            continue
        title = parts[0]
        relation = parts[1] if len(parts) >= 2 else ""
        url = parts[2] if len(parts) >= 3 and parts[2].startswith(("http://", "https://")) else ""
        assets.append(RelatedAssetItem(title=title, relation=relation, url=url))
    return assets


def tutorial_knowledge_graph_snapshot_from_fields(fields: dict[str, Any]) -> str:
    tldr = tutorial_tldr_from_fields(fields)
    methodology = tutorial_methodology_from_fields(fields)
    evolution = tutorial_evolution_from_fields(fields)
    actions = tutorial_actions_from_fields(fields)
    related_assets = tutorial_related_assets_from_fields(fields)
    title = tldr.topic or strip_theme_affixes(conversation_title_value(fields)) or conversation_title_value(fields)
    return render_knowledge_graph_snapshot(
        title=title,
        value=tldr.value,
        core_outputs=tutorial_core_outputs_from_fields(fields),
        methodology_name=methodology.name,
        methodology_steps=methodology.steps or [],
        previous_belief=evolution.previous_belief,
        current_belief=evolution.current_belief,
        next_actions=[action.todo for action in actions],
        related_assets=[asset.title for asset in related_assets],
    )


def graph_font(size: int, *, bold: bool = False):
    from PIL import ImageFont

    candidates = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for path in candidates:
        if not Path(path).exists():
            continue
        try:
            return ImageFont.truetype(path, size=size, index=1 if bold and path.endswith(".ttc") else 0)
        except Exception:
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def graph_text_width(draw: Any, text: str, font: Any) -> float:
    try:
        return float(draw.textlength(text, font=font))
    except Exception:
        bbox = draw.textbbox((0, 0), text, font=font)
        return float(bbox[2] - bbox[0])


def wrap_graph_text(draw: Any, text: str, font: Any, max_width: int, *, max_lines: int = 4) -> list[str]:
    text = sanitize_tutorial_text(text)
    if not text:
        return []
    lines: list[str] = []
    for paragraph in text.splitlines() or [text]:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        current = ""
        tokens = re.findall(r"[A-Za-z0-9_+./-]+|\s+|.", paragraph)
        for token in tokens:
            token = token if not token.isspace() else " "
            candidate = current + token
            if current and graph_text_width(draw, candidate, font) > max_width:
                lines.append(current.rstrip())
                current = token.lstrip()
                if len(lines) >= max_lines:
                    return lines
            else:
                current = candidate
        if current:
            lines.append(current.rstrip())
            if len(lines) >= max_lines:
                return lines
    return lines


def draw_graph_arrow(draw: Any, start: tuple[int, int], end: tuple[int, int], *, fill: str = "#64748B") -> None:
    draw.line([start, end], fill=fill, width=4)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 12
    left = (
        end[0] - size * math.cos(angle - math.pi / 6),
        end[1] - size * math.sin(angle - math.pi / 6),
    )
    right = (
        end[0] - size * math.cos(angle + math.pi / 6),
        end[1] - size * math.sin(angle + math.pi / 6),
    )
    draw.polygon([end, left, right], fill=fill)


def graph_node_texts_from_fields(fields: dict[str, Any]) -> list[tuple[str, str]]:
    tldr = tutorial_tldr_from_fields(fields)
    core_outputs = tutorial_core_outputs_from_fields(fields)
    methodology = tutorial_methodology_from_fields(fields)
    evolution = tutorial_evolution_from_fields(fields)
    actions = tutorial_actions_from_fields(fields)

    value_text = simple_sentence_excerpt(tldr.value or tldr.new_this_round, max_chars=44) or "先判断对团队有没有复用价值"
    core_text = "、".join(core_outputs[:3]) or "模板、规范、清单"
    if methodology.steps:
        method_text = " -> ".join(methodology.steps[:3])
    else:
        method_text = methodology.name or "抽取可照做步骤"
    if evolution.previous_belief and evolution.current_belief:
        evolution_text = f"{evolution.previous_belief} -> {evolution.current_belief}"
    else:
        evolution_text = evolution.current_belief or "从记录内容到沉淀能力"
    action_text = " / ".join(action.todo for action in actions[:2] if action.todo) or "下一轮验证并回写"

    return [
        ("团队价值", value_text),
        ("可直接复用", core_text),
        ("方法论", method_text),
        ("认知演进", evolution_text),
        ("下一步行动", action_text),
        ("持续更新", "Base 字段 / 文档结构 / 提醒闭环同步"),
    ]


def generate_knowledge_graph_png(fields: dict[str, Any]) -> tuple[bytes, int, int]:
    from PIL import Image, ImageDraw

    width, height = 1500, 900
    image = Image.new("RGB", (width, height), "#F8FAFC")
    draw = ImageDraw.Draw(image)
    title_font = graph_font(44, bold=True)
    subtitle_font = graph_font(24)
    node_title_font = graph_font(28, bold=True)
    node_body_font = graph_font(23)
    small_font = graph_font(20)

    title = tutorial_tldr_from_fields(fields).topic or strip_theme_affixes(conversation_title_value(fields))
    title = title or "能力资产"
    draw.text((70, 52), f"{KNOWLEDGE_GRAPH_SECTION_TITLE}：{title}", fill="#0F172A", font=title_font)
    draw.text(
        (72, 112),
        "让团队先看价值和可复用资产，再沿着方法论、认知演进和下一步行动持续回写。",
        fill="#475569",
        font=subtitle_font,
    )

    node_w, node_h = 310, 165
    nodes = [
        (70, 200),
        (430, 200),
        (790, 200),
        (1150, 200),
        (790, 560),
        (430, 560),
    ]
    colors = [
        ("#E0F2FE", "#0369A1"),
        ("#DCFCE7", "#15803D"),
        ("#FEF3C7", "#B45309"),
        ("#FCE7F3", "#BE185D"),
        ("#EDE9FE", "#6D28D9"),
        ("#F1F5F9", "#334155"),
    ]
    arrows = [
        ((70 + node_w, 282), (430, 282)),
        ((430 + node_w, 282), (790, 282)),
        ((790 + node_w, 282), (1150, 282)),
        ((1305, 365), (945, 560)),
        ((790, 642), (430 + node_w, 642)),
        ((430, 642), (225, 365)),
    ]
    for start, end in arrows:
        draw_graph_arrow(draw, start, end)

    for index, ((x, y), (label, body), (bg, accent)) in enumerate(zip(nodes, graph_node_texts_from_fields(fields), colors)):
        draw.rounded_rectangle((x, y, x + node_w, y + node_h), radius=24, fill="white", outline="#CBD5E1", width=2)
        draw.rounded_rectangle((x, y, x + node_w, y + 52), radius=24, fill=bg, outline=bg)
        draw.rectangle((x, y + 28, x + node_w, y + 52), fill=bg)
        draw.text((x + 24, y + 15), f"{index + 1}. {label}", fill=accent, font=node_title_font)
        wrapped = wrap_graph_text(draw, body, node_body_font, node_w - 48, max_lines=4)
        body_y = y + 72
        for line in wrapped:
            draw.text((x + 24, body_y), line, fill="#1E293B", font=node_body_font)
            body_y += 31

    related_assets = tutorial_related_assets_from_fields(fields)
    if related_assets:
        chip_y = 790
        draw.text((72, chip_y), "关联资产", fill="#334155", font=small_font)
        chip_x = 175
        for asset in related_assets[:4]:
            label = sanitize_tutorial_text(asset.title)
            chip_w = min(max(int(graph_text_width(draw, label, small_font)) + 38, 150), 300)
            if chip_x + chip_w > width - 70:
                break
            draw.rounded_rectangle((chip_x, chip_y - 8, chip_x + chip_w, chip_y + 34), radius=20, fill="#FFFFFF", outline="#CBD5E1")
            draw.text((chip_x + 18, chip_y), label[:18], fill="#334155", font=small_font)
            chip_x += chip_w + 16

    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue(), width, height


def render_conversation_tutorial(
    fields: dict[str, Any],
    *,
    reading_items: list[dict[str, str]] | None = None,
) -> str:
    agent_values = normalize_multi_values(fields.get("对话Agent"))
    tldr = tutorial_tldr_from_fields(fields)
    core_outputs = tutorial_core_outputs_from_fields(fields)
    methodology = tutorial_methodology_from_fields(fields)
    evolution = tutorial_evolution_from_fields(fields)
    actions = tutorial_actions_from_fields(fields)
    related_assets = tutorial_related_assets_from_fields(fields)
    references = tutorial_references_from_fields(fields)
    source = tutorial_source_from_fields(fields)
    contributor_labels = tutorial_contributor_labels_from_fields(fields)
    if not references and reading_items:
        references = [
            ReferenceItem(name=item.get("title", ""), why=item.get("reason", ""), url=item.get("url", ""))
            for item in reading_items
            if compact_text(item.get("title"))
        ]
    date_value = compact_text(fields.get("日期")) or compact_text(fields.get("同步时间"))[:10]

    lines: list[str] = []

    meta_bits = []
    if date_value:
        meta_bits.append(f"最近整理：{date_value}")
    if agent_values:
        meta_bits.append(f"适用 Agent：{' / '.join(agent_values)}")
    if contributor_labels:
        meta_bits.append(f"贡献者：{' / '.join(contributor_labels)}")
    source_bits = [source.name or source.type]
    if source.date:
        source_bits.append(source.date)
    if any(source_bits):
        meta_bits.append(f"来源：{' / '.join(bit for bit in source_bits if bit)}")
    if meta_bits:
        lines.extend(["> " + " ｜ ".join(meta_bits), ""])

    lines.extend(["## 3 秒速览", ""])
    if tldr.value:
        lines.extend([f"这份文档能帮你：{tldr.value}", ""])
    if core_outputs:
        lines.extend([f"可以直接复用：{'、'.join(core_outputs[:3])}", ""])

    graph_snapshot = tutorial_knowledge_graph_snapshot_from_fields(fields)
    if graph_snapshot:
        lines.extend([f"## {KNOWLEDGE_GRAPH_SECTION_TITLE}", ""])
        lines.extend(f"- {item}" for item in graph_snapshot.splitlines() if item)
        lines.append("")

    if core_outputs:
        lines.extend(["## 可直接复用", ""])
        lines.extend(f"- {item}" for item in core_outputs)
        lines.append("")

    if methodology.name or methodology.steps:
        lines.extend(["## 方法论", ""])
        if methodology.name:
            lines.extend([f"名称：{methodology.name}", ""])
        if methodology.steps:
            lines.extend(numbered_markdown(methodology.steps))
            lines.append("")

    if evolution.previous_belief or evolution.current_belief:
        lines.extend(["## 认知演进", ""])
        if evolution.previous_belief:
            lines.append(f"原认知：{evolution.previous_belief}")
        if evolution.current_belief:
            lines.append(f"新认知：{evolution.current_belief}")
        lines.append("")

    if actions:
        lines.extend(["## 下一步行动", ""])
        lines.extend(f"- □ {item.todo}" for item in actions if item.todo)
        lines.append("")

    if related_assets:
        lines.extend(["## 关联资产", ""])
        for item in related_assets:
            line = markdown_link(item.title, item.url) if item.url else item.title
            if item.relation:
                line = f"{line}：{item.relation}"
            lines.append(f"- {line}")
        lines.append("")

    if references:
        lines.extend(["## 参考案例", ""])
        for item in references:
            line = markdown_link(item.name, item.url) if item.url else item.name
            if item.why:
                line = f"{line}：{item.why}"
            lines.append(f"- {line}")
        lines.append("")

    return sanitize_tutorial_text("\n".join(lines).strip()) + "\n"


def text_elements(content: str, *, link: str = "") -> list[dict[str, Any]]:
    text = sanitize_tutorial_text(content)
    if not text:
        return []
    parts = [text[i : i + 1800] for i in range(0, len(text), 1800)]
    link_value = compact_text(link)
    elements: list[dict[str, Any]] = []
    for part in parts:
        if not part:
            continue
        text_run: dict[str, Any] = {"content": part}
        if link_value:
            text_run["text_element_style"] = {"link": {"url": link_value}}
        elements.append({"text_run": text_run})
    return elements


def tutorial_text_block(content: str) -> dict[str, Any] | None:
    elements = text_elements(content)
    if not elements:
        return None
    return {"block_type": 2, "text": {"elements": elements}}


def tutorial_heading_block(level: int, content: str) -> dict[str, Any] | None:
    elements = text_elements(content)
    if not elements:
        return None
    normalized_level = min(max(level, 1), 6)
    block_type = 2 + normalized_level
    return {
        "block_type": block_type,
        f"heading{normalized_level}": {"elements": elements},
    }


def tutorial_bullet_block(content: str) -> dict[str, Any] | None:
    elements = text_elements(content)
    if not elements:
        return None
    return {"block_type": 12, "bullet": {"elements": elements}}


def tutorial_bullet_elements_block(elements: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not elements:
        return None
    return {"block_type": 12, "bullet": {"elements": elements}}


def tutorial_link_bullet_block(title: str, url: str) -> dict[str, Any] | None:
    label = compact_text(title) or "未命名书目"
    link = compact_text(url)
    return tutorial_link_reason_bullet_block(label, link)


def tutorial_link_reason_bullet_block(title: str, url: str, reason: str = "") -> dict[str, Any] | None:
    label = compact_text(title) or "未命名书目"
    link = compact_text(url)
    reason_text = compact_text(reason)
    elements: list[dict[str, Any]] = []
    if link:
        elements.extend(text_elements(label, link=link))
    else:
        elements.extend(text_elements(f"{label}（暂无网络链接）"))
    if reason_text:
        elements.extend(text_elements(f"：{reason_text}"))
    return tutorial_bullet_elements_block(elements)


def tutorial_reference_bullet_block(name: str, url: str = "", why: str = "") -> dict[str, Any] | None:
    label = compact_text(name) or "未命名参考"
    link = compact_text(url)
    reason_text = compact_text(why)
    elements: list[dict[str, Any]] = []
    elements.extend(text_elements(label, link=link) if link else text_elements(label))
    if reason_text:
        elements.extend(text_elements(f"：{reason_text}"))
    return tutorial_bullet_elements_block(elements)


def tutorial_ordered_block(content: str) -> dict[str, Any] | None:
    elements = text_elements(content)
    if not elements:
        return None
    return {"block_type": 13, "ordered": {"elements": elements}}


def tutorial_image_block() -> dict[str, Any]:
    return {"block_type": 27, "image": {}}


def append_blocks(blocks: list[dict[str, Any]], new_blocks: list[dict[str, Any] | None]) -> None:
    for block in new_blocks:
        if block:
            blocks.append(block)


def build_conversation_tutorial_blocks(
    fields: dict[str, Any],
    *,
    reading_items: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    agent_values = normalize_multi_values(fields.get("对话Agent"))
    tldr = tutorial_tldr_from_fields(fields)
    core_outputs = tutorial_core_outputs_from_fields(fields)
    methodology = tutorial_methodology_from_fields(fields)
    evolution = tutorial_evolution_from_fields(fields)
    actions = tutorial_actions_from_fields(fields)
    related_assets = tutorial_related_assets_from_fields(fields)
    references = tutorial_references_from_fields(fields)
    source = tutorial_source_from_fields(fields)
    contributor_labels = tutorial_contributor_labels_from_fields(fields)
    if not references and reading_items:
        references = [
            ReferenceItem(name=item.get("title", ""), why=item.get("reason", ""), url=item.get("url", ""))
            for item in reading_items
            if compact_text(item.get("title"))
        ]
    date_value = compact_text(fields.get("日期")) or compact_text(fields.get("同步时间"))[:10]

    blocks: list[dict[str, Any]] = []

    meta_bits = []
    if date_value:
        meta_bits.append(f"最近整理：{date_value}")
    if agent_values:
        meta_bits.append(f"适用 Agent：{' / '.join(agent_values)}")
    if contributor_labels:
        meta_bits.append(f"贡献者：{' / '.join(contributor_labels)}")
    source_bits = [source.name or source.type]
    if source.date:
        source_bits.append(source.date)
    if any(source_bits):
        meta_bits.append(f"来源：{' / '.join(bit for bit in source_bits if bit)}")
    if meta_bits:
        append_blocks(blocks, [tutorial_text_block(" ｜ ".join(meta_bits))])

    append_blocks(blocks, [tutorial_heading_block(2, "3 秒速览")])
    append_blocks(
        blocks,
        [
            tutorial_text_block(f"这份文档能帮你：{tldr.value}") if tldr.value else None,
            tutorial_text_block(f"可以直接复用：{'、'.join(core_outputs[:3])}") if core_outputs else None,
        ],
    )

    graph_snapshot = tutorial_knowledge_graph_snapshot_from_fields(fields)
    if graph_snapshot:
        append_blocks(blocks, [tutorial_heading_block(2, KNOWLEDGE_GRAPH_SECTION_TITLE), tutorial_image_block()])

    if core_outputs:
        append_blocks(blocks, [tutorial_heading_block(2, "可直接复用")])
        append_blocks(blocks, [tutorial_bullet_block(item) for item in core_outputs])

    if methodology.name or methodology.steps:
        append_blocks(blocks, [tutorial_heading_block(2, "方法论")])
        if methodology.name:
            append_blocks(blocks, [tutorial_text_block(f"名称：{methodology.name}")])
        append_blocks(blocks, [tutorial_ordered_block(item) for item in methodology.steps or []])

    if evolution.previous_belief or evolution.current_belief:
        append_blocks(blocks, [tutorial_heading_block(2, "认知演进")])
        append_blocks(
            blocks,
            [
                tutorial_text_block(f"原认知：{evolution.previous_belief}") if evolution.previous_belief else None,
                tutorial_text_block(f"新认知：{evolution.current_belief}") if evolution.current_belief else None,
            ],
        )

    if actions:
        append_blocks(blocks, [tutorial_heading_block(2, "下一步行动")])
        append_blocks(blocks, [tutorial_bullet_block(f"□ {item.todo}") for item in actions if item.todo])

    if related_assets:
        append_blocks(blocks, [tutorial_heading_block(2, "关联资产")])
        append_blocks(
            blocks,
            [
                tutorial_reference_bullet_block(
                    item.title,
                    item.url,
                    item.relation,
                )
                for item in related_assets
            ],
        )

    if references:
        append_blocks(blocks, [tutorial_heading_block(2, "参考案例")])
        append_blocks(
            blocks,
            [
                tutorial_reference_bullet_block(
                    item.name,
                    item.url,
                    item.why,
                )
                for item in references
            ],
        )

    return blocks


def knowledge_graph_fallback_blocks(fields: dict[str, Any]) -> list[dict[str, Any]]:
    snapshot = tutorial_knowledge_graph_snapshot_from_fields(fields)
    return [block for block in (tutorial_bullet_block(line) for line in snapshot.splitlines() if line) if block]


def install_knowledge_graph_images(
    client: FeishuClient,
    document_id: str,
    source_blocks: list[dict[str, Any]],
    created_blocks: list[dict[str, Any]],
    fields: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []
    if not source_blocks or not created_blocks:
        return warnings

    graph_bytes: bytes | None = None
    graph_width = 0
    graph_height = 0
    graph_error = ""

    def fallback_to_text(index: int, reason: str) -> None:
        nonlocal warnings
        warnings.append(f"{KNOWLEDGE_GRAPH_SECTION_TITLE}: 图片插入失败，已改用文字图谱 - {reason}")
        fallback_blocks = knowledge_graph_fallback_blocks(fields)
        if not fallback_blocks:
            return
        try:
            client.batch_delete_document_children(document_id, document_id, start_index=index, end_index=index + 1)
            client.create_document_children(document_id, document_id, fallback_blocks, index=index)
        except FeishuError as exc:
            warnings.append(f"{KNOWLEDGE_GRAPH_SECTION_TITLE}: 文字图谱回填失败 - {exc}")

    for index, source_block in enumerate(source_blocks):
        if source_block.get("block_type") != 27:
            continue
        if index >= len(created_blocks):
            fallback_to_text(index, "未拿到图片块 ID")
            continue
        block_id = compact_text(created_blocks[index].get("block_id"))
        if not block_id:
            fallback_to_text(index, "图片块 ID 为空")
            continue

        if graph_bytes is None and not graph_error:
            try:
                graph_bytes, graph_width, graph_height = generate_knowledge_graph_png(fields)
            except Exception as exc:
                graph_error = str(exc)
        if graph_error or graph_bytes is None:
            fallback_to_text(index, graph_error or "图片生成失败")
            continue

        safe_title = normalize_lookup_key(strip_theme_affixes(conversation_title_value(fields)) or "knowledge-graph")
        file_name = f"{safe_title or 'knowledge-graph'}-evolution-map.png"
        try:
            upload = client.upload_media(
                block_id,
                file_name=file_name,
                file_bytes=graph_bytes,
                parent_type="docx_image",
            )
            file_token = compact_text(upload.get("file_token"))
            if not file_token:
                raise FeishuError(f"图片上传后未返回 file_token: {upload}")
            client.replace_document_image(
                document_id,
                block_id,
                file_token,
                width=graph_width,
                height=graph_height,
                align=2,
                caption=KNOWLEDGE_GRAPH_SECTION_TITLE,
            )
        except FeishuError as exc:
            fallback_to_text(index, str(exc))

    return warnings


def create_conversation_tutorial_doc(
    client: FeishuClient,
    fields: dict[str, Any],
    *,
    config: dict[str, Any] | None = None,
    reading_items: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    title = tutorial_doc_title(fields)
    parent_target = resolve_conversation_doc_parent(client)
    try:
        if parent_target and parent_target.get("kind") == "wiki":
            wiki_node = client.create_wiki_node(
                parent_target["space_id"],
                parent_node_token=parent_target["node_token"],
                obj_type="docx",
                title=title,
            )
            document = {
                "node_token": compact_text(wiki_node.get("node_token")),
                "obj_token": compact_text(wiki_node.get("obj_token")),
                "obj_type": compact_text(wiki_node.get("obj_type")) or "docx",
            }
        else:
            folder_token = parent_target.get("token") if parent_target else None
            document = client.create_document(title, folder_token=folder_token)
    except FeishuError as exc:
        message = str(exc)
        if parent_target and parent_target.get("kind") == "folder" and (
            "1770040" in message or "no folder permission" in message
        ):
            if require_confirmation_before_target_fallback(config):
                raise target_write_confirmation_error(conversation_doc_parent_target() or "", "教程文档", exc) from exc
            document = client.create_document(title)
        elif "99991672" in message and ("wiki:" in message or parent_target and parent_target.get("kind") == "wiki"):
            raise FeishuError(WIKI_PERMISSION_HINT) from exc
        else:
            raise
    document_id = compact_text(
        first_present(document, "document_id", "document_token", "token", "obj_token", default="")
    )
    if not document_id:
        raise FeishuError(f"创建教程文档后没有拿到 document_id: {document}")

    blocks = build_conversation_tutorial_blocks(fields, reading_items=reading_items)
    if not blocks:
        raise FeishuError("教程块生成结果为空")

    created_blocks = append_document_children_batched(client, document_id, document_id, blocks)
    warnings = install_knowledge_graph_images(client, document_id, blocks, created_blocks, fields)
    url = tutorial_doc_url(document)
    if not url:
        raise FeishuError(f"教程文档创建成功，但没有拿到文档 URL: {document}")
    return {"document_id": document_id, "url": url, "warnings": warnings}


def update_conversation_tutorial_doc(
    client: FeishuClient,
    document_id: str,
    fields: dict[str, Any],
    *,
    url: str = "",
    reading_items: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    title = tutorial_doc_title(fields)
    client.update_document_title(document_id, title)
    blocks = build_conversation_tutorial_blocks(fields, reading_items=reading_items)
    if not blocks:
        raise FeishuError("教程块生成结果为空")
    created_blocks = replace_document_root_children(client, document_id, blocks)
    warnings = install_knowledge_graph_images(client, document_id, blocks, created_blocks, fields)
    return {"document_id": document_id, "url": url or f"{DOCX_URL_PREFIX}/{document_id}", "warnings": warnings}


def refresh_conversation_tutorial_doc(
    client: FeishuClient,
    app_token: str,
    table_id: str,
    record: dict[str, Any],
    *,
    config: dict[str, Any] | None = None,
    reading_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    fields = record.get("fields", {})
    existing_url = existing_tutorial_url(fields)
    existing_document_id = existing_tutorial_document_id(fields)
    reading_items = tutorial_reading_items(fields, reading_records)
    try:
        if existing_document_id:
            document = update_conversation_tutorial_doc(
                client,
                existing_document_id,
                fields,
                url=existing_url,
                reading_items=reading_items,
            )
        elif existing_url:
            raise FeishuError(
                "当前主题已经有教程文档链接，但不是可直接编辑的 docx 地址。"
                "为了避免再次新建文档，本次没有覆盖原文档；请先把摘要里的链接换成 docx 文档链接。"
            )
        else:
            document = create_conversation_tutorial_doc(client, fields, config=config, reading_items=reading_items)
    except FeishuError as exc:
        message = str(exc)
        if "99991672" in message or "docx:document" in message or "docx:document:create" in message:
            raise FeishuError(DOC_PERMISSION_HINT) from exc
        raise

    client.update_record(
        app_token,
        table_id,
        record["record_id"],
        {
            **conversation_title_update_fields(tutorial_doc_title(fields), current_fields=fields),
            "摘要": {"text": "查看详情", "link": document["url"]},
        },
    )
    grant_doc_access_if_possible(client, document["document_id"])
    return document


def refresh_conversation_tutorial_docs(
    client: FeishuClient,
    app_token: str,
    table_id: str,
    records: list[dict[str, Any]],
    *,
    config: dict[str, Any] | None = None,
    reading_records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    updated_records = 0
    warnings: list[str] = []
    tutorial_urls: dict[str, str] = {}

    for record in records:
        fields = record.get("fields", {})
        title = conversation_title_value(fields) or record.get("record_id", "未命名主题")
        try:
            document = refresh_conversation_tutorial_doc(
                client,
                app_token,
                table_id,
                record,
                config=config,
                reading_records=reading_records,
            )
            updated_records += 1
            tutorial_urls[title] = document["url"]
            for warning in document.get("warnings", []):
                warnings.append(f"{title}: {warning}")
        except FeishuError as exc:
            warnings.append(f"{title}: 教程文档生成失败 - {exc}")

    return {
        "updated_records": updated_records,
        "tutorial_urls": tutorial_urls,
        "warnings": warnings,
    }


def dashboard_doc_title() -> str:
    return env_nonempty("FEISHU_DASHBOARD_TITLE") or DEFAULT_DASHBOARD_TITLE


def existing_dashboard_url(config: dict[str, Any]) -> str:
    return compact_text(env_nonempty("FEISHU_DASHBOARD_DOC_URL") or config.get(DASHBOARD_DOC_CONFIG_KEY))


def existing_dashboard_document_id(config: dict[str, Any]) -> str:
    return compact_text(
        env_nonempty("FEISHU_DASHBOARD_DOC_ID")
        or config.get(DASHBOARD_DOC_ID_CONFIG_KEY)
        or parse_docx_document_id(existing_dashboard_url(config))
    )


def task_focus_from_fields(fields: dict[str, Any]) -> str:
    discussion = split_bullets(compact_text(fields.get("讨论问题")))
    for candidate in discussion:
        text = first_sentence_excerpt(candidate, max_chars=72)
        if text:
            return text
    for candidate in (
        fields.get("本次新增"),
        fields.get("价值"),
        fields.get("TLDR主题"),
        fields.get("原始上下文"),
        summary_body_from_fields(fields),
        fields.get("标题"),
    ):
        text = first_sentence_excerpt(candidate, max_chars=72)
        if text:
            return text
    return conversation_title_value(fields)


def parse_discussion_entry(line: Any, *, fallback_fields: dict[str, Any] | None = None) -> dict[str, Any]:
    raw = compact_text(line)
    match = re.match(
        r"^(?P<date>\d{4}-\d{2}-\d{2})(?:[T\s]\d{2}:\d{2}(?::\d{2})?)?\s*(?:\[(?P<agent>[^\]]+)\])?\s*(?P<body>.*)$",
        raw,
    )
    fields = fallback_fields or {}
    if match:
        date_text = compact_text(match.group("date"))
        agent = compact_text(match.group("agent")) or " / ".join(normalize_multi_values(fields.get("对话Agent")))
        body = compact_text(match.group("body")) or raw
    else:
        date_text = compact_text(fields.get("日期")) or compact_text(fields.get("同步时间"))[:10]
        agent = " / ".join(normalize_multi_values(fields.get("对话Agent")))
        body = raw
    return {
        "raw": raw,
        "date_text": date_text,
        "datetime": parse_datetimeish(date_text),
        "agent": agent or "codex",
        "body": strip_discussion_metadata(body) or raw,
    }


def discussion_entries_from_fields(fields: dict[str, Any]) -> list[dict[str, Any]]:
    entries = [parse_discussion_entry(line, fallback_fields=fields) for line in split_bullets(fields.get("讨论问题"))]
    if entries:
        return entries
    fallback = task_focus_from_fields(fields)
    if not fallback:
        return []
    return [parse_discussion_entry(fallback, fallback_fields=fields)]


def design_stage_haystack(fields: dict[str, Any]) -> str:
    pieces: list[str] = []
    for field_name in (
        "标题",
        "TLDR主题",
        "本次新增",
        "价值",
        "核心资产",
        "方法论",
        "认知演进",
        "知识演化图谱",
        "下一步行动",
        "关联资产",
        "参考案例",
        "讨论问题",
        "摘要正文",
        "核心洞察",
        "心智模型",
        "行动建议",
        "后续思考方向",
        "原始上下文",
    ):
        value = compact_text(fields.get(field_name))
        if value:
            pieces.append(value)
    for field_name in ("领域", "标签", "对话Agent"):
        pieces.extend(normalize_multi_values(fields.get(field_name)))
    return normalize_general_key(" ".join(piece for piece in pieces if piece))


def infer_design_stages(fields: dict[str, Any]) -> list[str]:
    haystack = design_stage_haystack(fields)
    scored: list[tuple[int, int, str]] = []
    for index, rule in enumerate(DESIGN_STAGE_RULES):
        score = sum(1 for keyword in rule["keywords"] if normalize_general_key(keyword) in haystack)
        if score:
            scored.append((score, index, rule["name"]))

    if not scored:
        title_key = normalize_general_key(conversation_title_value(fields))
        if any(marker in title_key for marker in ("prototype", "原型", "figma", "html")):
            return ["原型验证", "方案设计"]
        if any(marker in title_key for marker in ("workflow", "工作流", "skill", "知识库", "知识复利")):
            return ["方法搭建", "复盘沉淀"]
        return ["方案设计"]

    scored.sort(key=lambda item: (item[0], -item[1]), reverse=True)
    best_score = scored[0][0]
    selected = [name for score, _, name in scored if score >= max(1, best_score - 1)]
    return unique_texts(selected)[:2]


def value_excerpt_candidates(fields: dict[str, Any]) -> list[str]:
    title_key = normalize_general_key(conversation_title_value(fields))
    items: list[str] = []
    for candidate in (
        split_bullets(compact_text(fields.get("核心资产")))
        + split_bullets(compact_text(fields.get("方法论")))
        + split_bullets(compact_text(fields.get("认知演进")))
        + split_bullets(compact_text(fields.get("知识演化图谱")))
        + split_bullets(compact_text(fields.get("下一步行动")))
        + split_bullets(compact_text(fields.get("关联资产")))
        + split_bullets(compact_text(fields.get("参考案例")))
        + split_bullets(compact_text(fields.get("核心洞察")))
        + split_bullets(compact_text(fields.get("心智模型")))
        + split_bullets(compact_text(fields.get("行动建议")))
        + split_bullets(compact_text(fields.get("后续思考方向")))
        + [fields.get("本次新增"), fields.get("价值"), summary_body_from_fields(fields), task_focus_from_fields(fields)]
    ):
        text = first_sentence_excerpt(candidate, max_chars=70)
        if not text:
            continue
        if normalize_general_key(text) == title_key:
            continue
        items.append(text)
    return unique_texts(items)


def dashboard_record_sort_key(record: dict[str, Any]) -> datetime:
    fields = record.get("fields", {})
    return (
        parse_datetimeish(fields.get("同步时间"))
        or parse_datetimeish(fields.get("日期"))
        or datetime.min
    )


def ascii_bar(value: int, max_value: int, *, width: int = 10) -> str:
    normalized_max = max(max_value, 1)
    filled = round((value / normalized_max) * width) if value > 0 else 0
    filled = min(max(filled, 0), width)
    return "█" * filled + "░" * (width - filled)


def format_duration(minutes: int) -> str:
    if minutes <= 0:
        return "0 小时"
    hours = minutes / 60
    if hours >= 1:
        return f"{hours:.1f} 小时"
    return f"{minutes} 分钟"


def markdown_link(label: str, url: str) -> str:
    text = compact_text(label) or "查看"
    link = compact_text(url)
    if not link:
        return text
    return f"[{text}]({link})"


def markdown_cell(value: Any) -> str:
    text = compact_text(value)
    return text.replace("|", "\\|").replace("\n", " / ")


def estimate_time_saved(conversation_records: list[dict[str, Any]]) -> dict[str, int]:
    context_minutes = 0
    reuse_minutes = 0
    quality_minutes = 0

    for record in conversation_records:
        fields = record.get("fields", {})
        discussion_count = max(len(discussion_entries_from_fields(fields)), 1)
        insight_count = (
            len(split_bullets(compact_text(fields.get("核心资产"))))
            + len(split_bullets(compact_text(fields.get("方法论"))))
            + len(split_bullets(compact_text(fields.get("关联资产"))))
            + len(split_bullets(compact_text(fields.get("参考案例"))))
            + len(split_bullets(compact_text(fields.get("核心洞察"))))
            + len(split_bullets(compact_text(fields.get("心智模型"))))
        )
        action_count = len(split_bullets(compact_text(fields.get("下一步行动")))) + len(
            split_bullets(compact_text(fields.get("行动建议")))
        )
        gap_count = len(split_bullets(compact_text(fields.get("知识缺口"))))
        next_count = len(split_bullets(compact_text(fields.get("认知演进")))) + len(
            split_bullets(compact_text(fields.get("后续思考方向")))
        )
        has_tutorial = bool(extract_link_url(fields.get("摘要")))

        context_minutes += min(75, 15 + max(discussion_count - 1, 0) * 6)
        reuse_minutes += min(120, insight_count * 10 + action_count * 8 + (25 if has_tutorial else 0))
        quality_minutes += min(60, gap_count * 10 + next_count * 8)

    total_minutes = context_minutes + reuse_minutes + quality_minutes
    return {
        "context_minutes": context_minutes,
        "reuse_minutes": reuse_minutes,
        "quality_minutes": quality_minutes,
        "total_minutes": total_minutes,
    }


def build_dashboard_focus_items(
    conversation_records: list[dict[str, Any]],
    gap_records: list[dict[str, Any]],
    reading_records: list[dict[str, Any]],
) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()

    def add_item(text: str) -> None:
        compact = compact_text(text)
        key = normalize_general_key(compact) or compact
        if not compact or key in seen:
            return
        seen.add(key)
        items.append(compact)

    for gap in sort_gap_records(gap_records):
        fields = gap.get("fields", {})
        name = first_sentence_excerpt(fields.get("不足") or fields.get("标题"), max_chars=30)
        action = first_sentence_excerpt(fields.get("弥补动作"), max_chars=42)
        if name:
            add_item(f"优先补足“{name}”{f'：{action}' if action else ''}")
        if len(items) >= 2:
            break

    for record in sorted(conversation_records, key=dashboard_record_sort_key, reverse=True):
        fields = record.get("fields", {})
        title = conversation_title_value(fields)
        directions = split_bullets(compact_text(fields.get("下一步行动"))) or split_bullets(
            compact_text(fields.get("后续思考方向"))
        )
        for direction in directions:
            direction_text = first_sentence_excerpt(direction, max_chars=40)
            if direction_text:
                add_item(f"继续推进“{title}”：{direction_text}")
            if len(items) >= 3:
                return items

    for record in sort_reading_records(reading_records):
        fields = record.get("fields", {})
        title = compact_text(fields.get("书名"))
        reason = first_sentence_excerpt(fields.get("推荐理由"), max_chars=36)
        if title:
            add_item(f"安排阅读《{title}》{f'：{reason}' if reason else ''}")
        if len(items) >= 3:
            return items

    if not items:
        add_item("继续把新的实践反馈合并回已有主题，让知识条目保持在“方法级”而不是“碎片级”。")
    return items[:3]


def build_dashboard_payload(
    config: dict[str, Any],
    conversation_records: list[dict[str, Any]],
    gap_records: list[dict[str, Any]],
    reading_records: list[dict[str, Any]],
) -> dict[str, Any]:
    cutoff = datetime.now() - timedelta(days=RECENT_ACTIVITY_WINDOW_DAYS)
    tutorial_count = 0
    latest_sync = ""
    total_round_count = 0
    recent_round_count = 0
    rankings: list[dict[str, Any]] = []
    stage_records: dict[str, list[dict[str, Any]]] = {rule["name"]: [] for rule in DESIGN_STAGE_RULES}
    stage_rounds: dict[str, int] = {rule["name"]: 0 for rule in DESIGN_STAGE_RULES}

    sorted_records = sorted(conversation_records, key=dashboard_record_sort_key, reverse=True)
    for record in sorted_records:
        fields = record.get("fields", {})
        entries = discussion_entries_from_fields(fields)
        round_count = max(len(entries), 1) if fields else 0
        recent_count = sum(1 for entry in entries if entry.get("datetime") and entry["datetime"] >= cutoff)
        if recent_count == 0:
            fallback_time = parse_datetimeish(fields.get("同步时间")) or parse_datetimeish(fields.get("日期"))
            if fallback_time and fallback_time >= cutoff:
                recent_count = 1

        total_round_count += round_count
        recent_round_count += recent_count
        latest_sync = latest_text_value([latest_sync, fields.get("同步时间"), fields.get("日期")])
        if existing_tutorial_url(fields):
            tutorial_count += 1

        stages = infer_design_stages(fields)
        for stage in stages:
            stage_records.setdefault(stage, []).append(record)
            stage_rounds[stage] = stage_rounds.get(stage, 0) + round_count

        rankings.append(
            {
                "title": conversation_title_value(fields) or record.get("record_id", "未命名主题"),
                "tutorial_url": existing_tutorial_url(fields),
                "round_count": round_count,
                "recent_count": recent_count,
                "latest_sync": compact_text(fields.get("同步时间")) or compact_text(fields.get("日期")),
                "focus": task_focus_from_fields(fields),
            }
        )

    use_recent_counts = any(item["recent_count"] > 0 for item in rankings)
    for item in rankings:
        item["score"] = item["recent_count"] if use_recent_counts else item["round_count"]

    rankings.sort(
        key=lambda item: (
            item["score"],
            item["round_count"],
            parse_datetimeish(item["latest_sync"]) or datetime.min,
        ),
        reverse=True,
    )

    stage_rows: list[dict[str, Any]] = []
    for rule in DESIGN_STAGE_RULES:
        matched = stage_records.get(rule["name"], [])
        if not matched:
            continue
        highlights: list[str] = []
        related_titles: list[str] = []
        for record in sorted(matched, key=dashboard_record_sort_key, reverse=True):
            fields = record.get("fields", {})
            title = conversation_title_value(fields)
            if title:
                related_titles = unique_texts(related_titles + [title])
            highlights = unique_texts(highlights + value_excerpt_candidates(fields))
            if len(highlights) >= 2 and len(related_titles) >= 2:
                break
        stage_rows.append(
            {
                "name": rule["name"],
                "theme_count": len(matched),
                "round_count": stage_rounds.get(rule["name"], len(matched)),
                "chart_type": rule["chart_type"],
                "value_summary": "；".join(highlights[:2])
                or (
                    f"围绕“{' / '.join(related_titles[:2])}”持续提炼可复用的方法资产。"
                    if related_titles
                    else "持续把分散经验整理成可以复用的结构化资产。"
                ),
            }
        )

    stage_rows.sort(key=lambda item: (item["round_count"], item["theme_count"]), reverse=True)
    pending_gaps = sort_gap_records(gap_records)
    pending_reading = sort_reading_records(reading_records)
    high_priority_reading = sum(1 for record in pending_reading if parse_priority(record.get("fields", {}).get("优先级")) >= 3)
    pending_action_count = sum(
        len(split_bullets(compact_text(record.get("fields", {}).get("下一步行动"))))
        for record in conversation_records
    )
    reference_count = sum(
        len(split_bullets(compact_text(record.get("fields", {}).get("参考案例"))))
        for record in conversation_records
    )
    related_asset_count = sum(
        len(split_bullets(compact_text(record.get("fields", {}).get("关联资产"))))
        for record in conversation_records
    )
    time_saved = estimate_time_saved(conversation_records)
    focus_items = build_dashboard_focus_items(conversation_records, gap_records, reading_records)

    if not conversation_records:
        encouragement = "当第一批主题被稳定合并成方法条目后，这里就会开始出现真正的知识复利。"
    elif tutorial_count == len(conversation_records) and recent_round_count >= len(conversation_records):
        encouragement = "你已经不只是在保存聊天记录，而是在把方法论反复打磨成可复用资产。"
    elif recent_round_count >= 5:
        encouragement = "最近的沉淀节奏很稳，继续把实践反馈合并回原主题，复利会越来越明显。"
    else:
        encouragement = "知识资产已经成形，下一步只要持续回流反馈，这套体系会越来越像你的第二大脑。"

    return {
        "title": dashboard_doc_title(),
        "refreshed_at": now_iso(),
        "latest_sync": latest_sync or now_iso(),
        "topic_count": len(conversation_records),
        "tutorial_count": tutorial_count,
        "total_round_count": total_round_count,
        "recent_round_count": recent_round_count,
        "pending_gap_count": len(pending_gaps),
        "pending_action_count": pending_action_count,
        "related_asset_count": related_asset_count,
        "reference_count": reference_count,
        "pending_reading_count": len(pending_reading),
        "high_priority_reading_count": high_priority_reading,
        "rankings": rankings[:5],
        "stage_rows": stage_rows,
        "time_saved": time_saved,
        "focus_items": focus_items,
        "encouragement": encouragement,
        "base_url": compact_text(config.get("base_url")),
        "reading_gallery_url": compact_text(config.get(READING_GALLERY_CONFIG_KEY)),
        "tutorial_links": [
            {
                "title": item["title"],
                "url": item["tutorial_url"],
            }
            for item in rankings
            if item.get("tutorial_url")
        ],
    }


def render_dashboard_markdown(
    config: dict[str, Any],
    conversation_records: list[dict[str, Any]],
    gap_records: list[dict[str, Any]],
    reading_records: list[dict[str, Any]],
) -> str:
    payload = build_dashboard_payload(config, conversation_records, gap_records, reading_records)
    rankings = payload["rankings"]
    stage_rows = payload["stage_rows"]
    time_saved = payload["time_saved"]
    max_hot = max((item["score"] for item in rankings), default=1)
    max_stage_rounds = max((item["round_count"] for item in stage_rows), default=1)
    tutorial_coverage = f"{payload['tutorial_count']} / {payload['topic_count']}"

    lines = [f"# {payload['title']}", ""]
    lines.append(
        "> "
        + " ｜ ".join(
            [
                f"最近刷新：{compact_text(payload['refreshed_at'])[:19]}",
                f"数据最近同步：{compact_text(payload['latest_sync'])[:10]}",
                f"数据窗口：近 {RECENT_ACTIVITY_WINDOW_DAYS} 天",
                f"主题数：{payload['topic_count']}",
                f"沉淀轮次：{payload['total_round_count']}",
            ]
        )
    )
    lines.extend(["", f"> {payload['encouragement']}", ""])

    lines.extend(
        [
            "## 一眼总览",
            "",
            "| 指标 | 当前值 | 说明 |",
            "| --- | --- | --- |",
            f"| 沉淀主题数 | {payload['topic_count']} | 已合并成可复用的方法主题 |",
            f"| 累计沉淀轮次 | {payload['total_round_count']} | 按主题记录的同步历史估算 |",
            f"| 近 {RECENT_ACTIVITY_WINDOW_DAYS} 天同步次数 | {payload['recent_round_count']} | 最近仍在高频推进的内容 |",
            f"| 能力文档覆盖 | {tutorial_coverage} | 每个主题都尽量对应一份能力资产文档 |",
            f"| 待行动项 | {payload['pending_action_count']} | 来自“下一步行动”字段 |",
            f"| 关联资产 | {payload['related_asset_count']} | 来自“关联资产”字段 |",
            f"| 参考案例 | {payload['reference_count']} | 来自“参考案例”字段 |",
            f"| 节省时间估计 | {format_duration(time_saved['total_minutes'])} | 保守按找回上下文 / 复用方案 / 减少试错估算 |",
            "",
        ]
    )

    lines.extend(
        [
            "## 近期高频沉淀内容",
            "",
            "| 主题 | 热度 | 最近同步 | 这段时间主要在推进什么 |",
            "| --- | --- | --- | --- |",
        ]
    )
    if rankings:
        for item in rankings:
            title = markdown_link(item["title"], item["tutorial_url"])
            heat = f"{ascii_bar(item['score'], max_hot)} {item['score']} 次"
            latest_sync = compact_text(item["latest_sync"])[:10] or "-"
            focus = markdown_cell(first_sentence_excerpt(item["focus"], max_chars=64) or item["title"])
            lines.append(f"| {title} | {heat} | {latest_sync} | {focus} |")
    else:
        lines.append("| 暂无沉淀主题 | - | - | 先完成一次 sync，这里就会出现高频主题排名。 |")
    lines.append("")

    lines.extend(
        [
            "## 不同设计节点上的价值提炼",
            "",
            "| 设计节点 | 覆盖主题 / 轮次 | 价值提炼 | 适合图表 |",
            "| --- | --- | --- | --- |",
        ]
    )
    if stage_rows:
        for row in stage_rows:
            coverage = f"{row['theme_count']} 个主题 / {row['round_count']} 次"
            value = markdown_cell(f"{ascii_bar(row['round_count'], max_stage_rounds, width=8)} {row['value_summary']}")
            lines.append(f"| {row['name']} | {coverage} | {value} | {row['chart_type']} |")
    else:
        lines.append("| 暂无阶段数据 | - | 还没有足够的主题内容可以提炼阶段价值。 | - |")
    lines.append("")

    lines.extend(
        [
            "## 帮你节省的时间估计",
            "",
            "| 节省来源 | 估算 | 说明 |",
            "| --- | --- | --- |",
            f"| 找回上下文 | {format_duration(time_saved['context_minutes'])} | 通过主题合并和能力文档快速找回背景 |",
            f"| 复用方案 | {format_duration(time_saved['reuse_minutes'])} | 直接复用核心资产、方法论、参考案例和文档 |",
            f"| 减少试错 | {format_duration(time_saved['quality_minutes'])} | 通过认知演进与下一步行动减少重复摸索 |",
            "",
            f"保守估算下来，当前知识库已经替你省下约 {format_duration(time_saved['total_minutes'])} 的重复整理时间。",
            "",
        ]
    )

    lines.extend(["## 未来需要重点关注的内容", ""])
    for item in payload["focus_items"]:
        lines.append(f"- {item}")
    lines.append("")

    lines.extend(["## 快速入口", ""])
    if payload["base_url"]:
        lines.append(f"- 对话沉淀总览：{markdown_link('打开 Base', payload['base_url'])}")
    if payload["reading_gallery_url"]:
        lines.append(f"- 阅读画册：{markdown_link('打开阅读队列画册', payload['reading_gallery_url'])}")
    if payload["tutorial_links"]:
        for item in payload["tutorial_links"][:5]:
            lines.append(f"- 主题教程：{markdown_link(item['title'], item['url'])}")
    lines.append("")

    lines.extend(
        [
            "## 可继续扩展的飞书图表类型",
            "",
            "| 图表类型 | 推荐用途 | 对应数据源 |",
            "| --- | --- | --- |",
            "| 横向条形图 | 看不同设计节点的沉淀轮次高低 | 对话沉淀 |",
            f"| 折线图 | 看近 {RECENT_ACTIVITY_WINDOW_DAYS} 天的沉淀活跃趋势 | 同步时间 |",
            "| 环形图 | 看核心资产 / 方法论 / 行动项占比 | 对话沉淀 |",
            "| 堆叠条形图 | 看每个主题下“资产 / 方法 / 行动”的结构 | 对话沉淀 |",
            "",
        ]
    )

    return "\n".join(lines).strip() + "\n"


def build_dashboard_blocks(
    config: dict[str, Any],
    conversation_records: list[dict[str, Any]],
    gap_records: list[dict[str, Any]],
    reading_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    payload = build_dashboard_payload(config, conversation_records, gap_records, reading_records)
    rankings = payload["rankings"]
    stage_rows = payload["stage_rows"]
    time_saved = payload["time_saved"]
    max_hot = max((item["score"] for item in rankings), default=1)
    max_stage_rounds = max((item["round_count"] for item in stage_rows), default=1)
    blocks: list[dict[str, Any]] = []

    append_blocks(blocks, [tutorial_heading_block(1, payload["title"])])
    append_blocks(
        blocks,
        [
            tutorial_text_block(
                " ｜ ".join(
                    [
                        f"最近刷新：{compact_text(payload['refreshed_at'])[:19]}",
                        f"数据最近同步：{compact_text(payload['latest_sync'])[:10]}",
                        f"数据窗口：近 {RECENT_ACTIVITY_WINDOW_DAYS} 天",
                        f"主题数：{payload['topic_count']}",
                        f"沉淀轮次：{payload['total_round_count']}",
                    ]
                )
            ),
            tutorial_text_block(payload["encouragement"]),
        ],
    )

    append_blocks(blocks, [tutorial_heading_block(2, "一眼总览")])
    overview_lines = [
        f"沉淀主题数：{payload['topic_count']} ｜ 已合并成可复用的方法主题",
        f"累计沉淀轮次：{payload['total_round_count']} ｜ 按主题记录的同步历史估算",
        f"近 {RECENT_ACTIVITY_WINDOW_DAYS} 天同步次数：{payload['recent_round_count']} ｜ 最近仍在高频推进的内容",
        f"能力文档覆盖：{payload['tutorial_count']} / {payload['topic_count']} ｜ 每个主题尽量对应一份能力资产文档",
        f"待行动项：{payload['pending_action_count']} ｜ 来自“下一步行动”字段",
        f"关联资产：{payload['related_asset_count']} ｜ 来自“关联资产”字段",
        f"参考案例：{payload['reference_count']} ｜ 来自“参考案例”字段",
        f"节省时间估计：{format_duration(time_saved['total_minutes'])} ｜ 保守按找回上下文 / 复用方案 / 减少试错估算",
    ]
    append_blocks(blocks, [tutorial_bullet_block(line) for line in overview_lines])

    append_blocks(blocks, [tutorial_heading_block(2, "近期高频沉淀内容")])
    if rankings:
        hot_lines = [
            (
                f"{item['title']} ｜ 热度 {ascii_bar(item['score'], max_hot)} {item['score']} 次"
                f" ｜ 最近同步 {compact_text(item['latest_sync'])[:10] or '-'}"
                f" ｜ 推进重点：{first_sentence_excerpt(item['focus'], max_chars=80) or item['title']}"
            )
            for item in rankings
        ]
        append_blocks(blocks, [tutorial_ordered_block(line) for line in hot_lines])
    else:
        append_blocks(blocks, [tutorial_text_block("先完成一次 sync，这里就会出现高频主题排名。")])

    append_blocks(blocks, [tutorial_heading_block(2, "不同设计节点上的价值提炼")])
    if stage_rows:
        stage_lines = [
            (
                f"{row['name']} ｜ {row['theme_count']} 个主题 / {row['round_count']} 次"
                f" ｜ {ascii_bar(row['round_count'], max_stage_rounds, width=8)}"
                f" ｜ 价值：{row['value_summary']}"
                f" ｜ 适合图表：{row['chart_type']}"
            )
            for row in stage_rows
        ]
        append_blocks(blocks, [tutorial_bullet_block(line) for line in stage_lines])
    else:
        append_blocks(blocks, [tutorial_text_block("还没有足够的主题内容可以提炼阶段价值。")])

    append_blocks(blocks, [tutorial_heading_block(2, "帮你节省的时间估计")])
    time_lines = [
        f"找回上下文：{format_duration(time_saved['context_minutes'])} ｜ 通过主题合并和能力文档快速找回背景",
        f"复用方案：{format_duration(time_saved['reuse_minutes'])} ｜ 直接复用核心资产、方法论、参考案例和文档",
        f"减少试错：{format_duration(time_saved['quality_minutes'])} ｜ 通过认知演进与下一步行动减少重复摸索",
    ]
    append_blocks(blocks, [tutorial_bullet_block(line) for line in time_lines])
    append_blocks(
        blocks,
        [tutorial_text_block(f"保守估算下来，当前知识库已经替你省下约 {format_duration(time_saved['total_minutes'])} 的重复整理时间。")],
    )

    append_blocks(blocks, [tutorial_heading_block(2, "未来需要重点关注的内容")])
    append_blocks(blocks, [tutorial_bullet_block(item) for item in payload["focus_items"]])

    append_blocks(blocks, [tutorial_heading_block(2, "快速入口")])
    quick_links: list[str] = []
    if payload["base_url"]:
        quick_links.append(f"对话沉淀总览：{payload['base_url']}")
    if payload["reading_gallery_url"]:
        quick_links.append(f"阅读画册：{payload['reading_gallery_url']}")
    for item in payload["tutorial_links"][:5]:
        quick_links.append(f"主题教程｜{item['title']}：{item['url']}")
    if quick_links:
        append_blocks(blocks, [tutorial_bullet_block(line) for line in quick_links])
    else:
        append_blocks(blocks, [tutorial_text_block("当前还没有可用的入口链接。")])

    append_blocks(blocks, [tutorial_heading_block(2, "可继续扩展的飞书图表类型")])
    chart_lines = [
        "横向条形图 ｜ 看不同设计节点的沉淀轮次高低 ｜ 数据源：对话沉淀",
        f"折线图 ｜ 看近 {RECENT_ACTIVITY_WINDOW_DAYS} 天的沉淀活跃趋势 ｜ 数据源：同步时间",
        "环形图 ｜ 看核心资产 / 方法论 / 行动项占比 ｜ 数据源：对话沉淀",
        "堆叠条形图 ｜ 看每个主题下“资产 / 方法 / 行动”的结构 ｜ 数据源：对话沉淀",
    ]
    append_blocks(blocks, [tutorial_bullet_block(line) for line in chart_lines])
    return blocks


def create_dashboard_doc(
    client: FeishuClient,
    config: dict[str, Any],
    conversation_records: list[dict[str, Any]],
    gap_records: list[dict[str, Any]],
    reading_records: list[dict[str, Any]],
) -> dict[str, str]:
    title = dashboard_doc_title()
    parent_target = resolve_dashboard_doc_parent(client, config)
    try:
        if parent_target and parent_target.get("kind") == "wiki":
            wiki_node = client.create_wiki_node(
                parent_target["space_id"],
                parent_node_token=parent_target["node_token"],
                obj_type="docx",
                title=title,
            )
            document = {
                "node_token": compact_text(wiki_node.get("node_token")),
                "obj_token": compact_text(wiki_node.get("obj_token")),
                "obj_type": compact_text(wiki_node.get("obj_type")) or "docx",
            }
        else:
            folder_token = parent_target.get("token") if parent_target else None
            document = client.create_document(title, folder_token=folder_token)
    except FeishuError as exc:
        message = str(exc)
        if parent_target and parent_target.get("kind") == "folder" and (
            "1770040" in message or "no folder permission" in message
        ):
            target = configured_dashboard_target(config) or conversation_doc_parent_target() or ""
            if require_confirmation_before_target_fallback(config):
                raise target_write_confirmation_error(target, "仪表盘", exc) from exc
            document = client.create_document(title)
        elif "99991672" in message and ("wiki:" in message or parent_target and parent_target.get("kind") == "wiki"):
            raise FeishuError(WIKI_PERMISSION_HINT) from exc
        else:
            raise

    document_id = compact_text(
        first_present(document, "document_id", "document_token", "token", "obj_token", default="")
    )
    if not document_id:
        raise FeishuError(f"创建仪表盘文档后没有拿到 document_id: {document}")

    blocks = build_dashboard_blocks(config, conversation_records, gap_records, reading_records)
    if not blocks:
        raise FeishuError("仪表盘文档块生成结果为空")

    append_document_children_batched(client, document_id, document_id, blocks)
    grant_doc_access_if_possible(client, document_id)
    url = tutorial_doc_url(document)
    if not url:
        url = f"{DOCX_URL_PREFIX}/{document_id}"
    return {"document_id": document_id, "url": url}


def update_dashboard_doc(
    client: FeishuClient,
    document_id: str,
    url: str,
    config: dict[str, Any],
    conversation_records: list[dict[str, Any]],
    gap_records: list[dict[str, Any]],
    reading_records: list[dict[str, Any]],
) -> dict[str, str]:
    blocks = build_dashboard_blocks(config, conversation_records, gap_records, reading_records)
    if not blocks:
        raise FeishuError("仪表盘文档块生成结果为空")
    replace_document_root_children(client, document_id, blocks)
    grant_doc_access_if_possible(client, document_id)
    return {"document_id": document_id, "url": url or f"{DOCX_URL_PREFIX}/{document_id}"}


def refresh_dashboard_doc(
    client: FeishuClient,
    config: dict[str, Any],
    conversation_records: list[dict[str, Any]],
    gap_records: list[dict[str, Any]],
    reading_records: list[dict[str, Any]],
    *,
    config_path: str | None = None,
) -> dict[str, str]:
    preferred_target = configured_dashboard_target(config)
    if preferred_target:
        parsed_target = parse_feishu_doc_parent_target(preferred_target)
        if parsed_target.get("kind") == "unknown":
            raise unsupported_target_write_error(preferred_target, "仪表盘")

    existing_url = existing_dashboard_url(config)
    existing_document_id = existing_dashboard_document_id(config)

    try:
        if existing_document_id:
            document = update_dashboard_doc(
                client,
                existing_document_id,
                existing_url,
                config,
                conversation_records,
                gap_records,
                reading_records,
            )
        elif existing_url:
            raise FeishuError(
                "当前仪表盘已经有链接，但没有可编辑的文档 ID。"
                "请补充 dashboard_doc_document_id，或清空后让脚本重新创建。"
            )
        else:
            document = create_dashboard_doc(
                client,
                config,
                conversation_records,
                gap_records,
                reading_records,
            )
    except FeishuError as exc:
        message = str(exc)
        if "99991672" in message or "docx:document" in message or "docx:document:create" in message:
            raise FeishuError(DOC_PERMISSION_HINT) from exc
        raise

    config[DASHBOARD_DOC_CONFIG_KEY] = document["url"]
    config[DASHBOARD_DOC_ID_CONFIG_KEY] = document["document_id"]
    if config_path:
        write_json(Path(config_path), config)
    return document


def load_dashboard_records(
    client: FeishuClient,
    app_token: str,
    table_ids: dict[str, str],
    *,
    limit: int = 2000,
) -> dict[str, list[dict[str, Any]]]:
    records = {
        "conversations": client.list_records(
            app_token,
            table_ids["conversations"],
            field_names=conversation_field_names(),
            limit=limit,
        ),
        "gaps": [],
        "reading": [],
    }
    if table_ids.get("gaps"):
        records["gaps"] = client.list_records(
            app_token,
            table_ids["gaps"],
            field_names=table_field_names(TABLE_SPECS["gaps"]),
            limit=limit,
        )
    if table_ids.get("reading"):
        records["reading"] = client.list_records(
            app_token,
            table_ids["reading"],
            field_names=table_field_names(TABLE_SPECS["reading"]),
            limit=limit,
        )
    return records


def build_records(note: NotePayload) -> dict[str, Any]:
    conversation_record = {
        "标题": asset_document_title(note.title),
        "对话ID": note.conversation_key,
        "日期": note.conversation_date,
        "标签": select_core_topic_tags(
            note.tags,
            topic_tag_context_from_note(note.title, note.tldr, note.core_outputs, note.methodology),
        ),
        "对话Agent": [note.agent],
        "来源": render_source_snapshot(note.source),
        "TLDR主题": sanitize_tutorial_text(note.tldr.topic),
        "本次新增": sanitize_tutorial_text(note.tldr.new_this_round),
        "价值": sanitize_tutorial_text(note.tldr.value),
        "核心资产": sanitized_bullet_block(reusable_asset_points(note.core_outputs)),
        "方法论": render_methodology_snapshot(note.methodology),
        "认知演进": render_evolution_snapshot(note.evolution),
        "知识演化图谱": render_knowledge_graph_snapshot_from_note(note),
        "下一步行动": render_action_snapshot(note.next_actions),
        "关联资产": render_related_asset_snapshot(note.related_assets),
        "参考案例": render_reference_snapshot(note.references),
        "同步时间": now_iso(),
    }
    contributor_entries = contributor_person_entries(note.contributors)
    if contributor_entries:
        conversation_record["贡献者"] = contributor_entries

    return {
        "conversation": conversation_record,
        "gaps": [],
        "reading": [],
        "reminder": render_reminder(note),
    }


def enrich_reading_records(
    client: FeishuClient,
    app_token: str,
    table_id: str,
    records: list[dict[str, Any]],
    metadata_overrides: dict[str, dict[str, Any]],
    *,
    refresh_metadata: bool = False,
    refresh_covers: bool = False,
) -> dict[str, Any]:
    upload_cache: dict[str, str] = {}
    warnings: list[str] = []
    updated_records = 0

    for record in records:
        fields = record.get("fields", {})
        title = compact_text(fields.get("书名"))
        if not title:
            continue

        title_key = normalize_lookup_key(title)
        override = metadata_overrides.get(title_key, {})
        update_fields: dict[str, Any] = {}

        normalized_source_theme = merge_source_theme_values([fields.get("来源主题")])
        if normalized_source_theme and compact_text(fields.get("来源主题")) != normalized_source_theme:
            update_fields["来源主题"] = normalized_source_theme

        current_tags = fields.get("精华标签")
        if override.get("tags") and (refresh_metadata or not current_tags):
            update_fields["精华标签"] = override["tags"]

        current_online = fields.get("在线地址")
        current_online_link = reading_online_link(current_online)
        online_url = compact_text(first_present(override, "online_url", default=""))
        desired_online = reading_online_field(title, online_url)
        if refresh_metadata or current_online_link != reading_online_link(desired_online):
            if refresh_metadata or not current_online_link:
                update_fields["在线地址"] = desired_online

        current_cover = fields.get("封面图")
        if refresh_covers or not has_reading_cover(current_cover):
            cover_url = compact_text(first_present(override, "cover_url", default=""))
            try:
                file_token = upload_reading_cover(
                    client,
                    app_token,
                    title,
                    upload_cache,
                    cover_url=cover_url,
                )
                update_fields["封面图"] = [{"file_token": file_token}]
            except FeishuError as exc:
                warnings.append(f"{title}: 封面上传失败 - {exc}")

        if not update_fields:
            continue

        try:
            client.update_record(app_token, table_id, record["record_id"], update_fields)
            updated_records += 1
        except FeishuError as exc:
            warnings.append(f"{title}: 记录更新失败 - {exc}")

    return {
        "updated_records": updated_records,
        "warnings": warnings,
    }


def ensure_tables(client: FeishuClient, app_token: str, *, include_legacy: bool | None = None) -> dict[str, str]:
    existing = {item["name"]: item["table_id"] for item in client.list_tables(app_token)}
    table_ids: dict[str, str] = {}
    for logical_name, spec in active_table_specs(include_legacy=include_legacy).items():
        table_name = spec["name"]
        if table_name in existing:
            table_ids[logical_name] = existing[table_name]
        else:
            table_ids[logical_name] = client.create_table(app_token, table_name, spec["fields"])
        ensure_table_fields(client, app_token, table_ids[logical_name], spec["fields"])
    return table_ids


def read_note_input(note_json: str | None, use_stdin: bool) -> dict[str, Any]:
    if note_json:
        return read_json(Path(note_json))
    if use_stdin or not sys.stdin.isatty():
        raw = sys.stdin.read()
        if not raw.strip():
            raise FeishuError("Expected JSON note on stdin, but stdin was empty.")
        return json.loads(raw)
    raise FeishuError("Provide --note-json PATH or pipe JSON into stdin.")


def cmd_template(_: argparse.Namespace) -> int:
    print(json.dumps(default_note_template(), ensure_ascii=False, indent=2))
    return 0


def cmd_bootstrap(args: argparse.Namespace) -> int:
    client = build_client()
    app_token = args.app_token
    base_info: dict[str, Any] = {}

    if not app_token:
        folder_token = args.folder_token or os.getenv("FEISHU_BASE_FOLDER_TOKEN")
        base_info = client.create_base(args.base_name, folder_token=folder_token)
        app_token = base_info["app_token"]

    table_ids = ensure_tables(client, app_token)
    payload = {
        "skill": "feishu-knowledge-compounder",
        "created_at": now_iso(),
        "app_token": app_token,
        "base_url": base_info.get("url", ""),
        "table_ids": table_ids,
        "table_names": {key: value["name"] for key, value in active_table_specs().items()},
    }

    if args.config_out:
        write_json(Path(args.config_out), payload)

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def maybe_send_reminder(client: FeishuClient, message: str) -> dict[str, Any] | None:
    target = resolve_notify_target()
    if not target:
        raise FeishuError(
            "No reminder target configured. Set FEISHU_NOTIFY_WEBHOOK, FEISHU_NOTIFY_OPEN_ID, FEISHU_NOTIFY_CHAT_ID, or FEISHU_NOTIFY_RECEIVE_ID."
        )
    if target["mode"] == "webhook":
        return client.send_webhook_message(target["webhook"], message, secret=target.get("secret"))
    return client.send_app_message(target["receive_id"], target["receive_id_type"], message)


def cmd_doctor(args: argparse.Namespace) -> int:
    config_path = args.config or os.getenv(DEFAULT_CONFIG_ENV)
    result: dict[str, Any] = {
        "loaded_env_files": getattr(args, "_loaded_env_files", []),
        "config_path": config_path or "",
        "has_app_id": bool(os.getenv("FEISHU_APP_ID")),
        "has_app_secret": bool(os.getenv("FEISHU_APP_SECRET")),
        "has_user_access_token": bool(env_nonempty("FEISHU_USER_ACCESS_TOKEN")),
        "has_notify_target": bool(resolve_notify_target()),
        "ready_for_bootstrap": False,
        "ready_for_sync": False,
        "ready_for_review": False,
        "missing": [],
        "checks": {},
    }

    if result["has_user_access_token"] or (result["has_app_id"] and result["has_app_secret"]):
        result["ready_for_bootstrap"] = True
    else:
        result["missing"].append("FEISHU_USER_ACCESS_TOKEN or FEISHU_APP_ID / FEISHU_APP_SECRET")

    config: dict[str, Any] = {}
    if config_path:
        try:
            config = load_runtime_config(config_path)
            result["checks"]["config_exists"] = True
        except FileNotFoundError:
            result["checks"]["config_exists"] = False
            result["missing"].append(f"Config file not found: {config_path}")
        except json.JSONDecodeError:
            result["checks"]["config_exists"] = False
            result["missing"].append(f"Config JSON is invalid: {config_path}")
    else:
        result["checks"]["config_exists"] = False
        result["missing"].append("FEISHU_COMPOUNDER_CONFIG or --config")

    if config:
        try:
            resolve_storage(config)
            result["ready_for_sync"] = True
            result["ready_for_review"] = True
        except FeishuError as exc:
            result["missing"].append(str(exc))

    if not result["has_notify_target"]:
        result["missing"].append(
            "Reminder target: FEISHU_NOTIFY_WEBHOOK, FEISHU_NOTIFY_OPEN_ID, FEISHU_NOTIFY_CHAT_ID, or FEISHU_NOTIFY_RECEIVE_ID"
        )

    if args.ping and result["ready_for_bootstrap"]:
        client = build_client()
        try:
            if client.access_token:
                result["checks"]["auth_ping"] = f"ok ({client.access_token_kind}_access_token)"
            else:
                client.tenant_access_token()
                result["checks"]["auth_ping"] = "ok (tenant_access_token)"
        except FeishuError as exc:
            result["checks"]["auth_ping"] = f"failed: {exc}"
            result["ready_for_bootstrap"] = False

        if config and result["ready_for_sync"]:
            try:
                app_token, _ = resolve_storage(config)
                tables = client.list_tables(app_token)
                result["checks"]["table_ping"] = {
                    "ok": True,
                    "table_count": len(tables),
                }
            except FeishuError as exc:
                result["checks"]["table_ping"] = {"ok": False, "error": str(exc)}
                result["ready_for_sync"] = False
                result["ready_for_review"] = False

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def cmd_grant_access(args: argparse.Namespace) -> int:
    config = load_runtime_config(args.config)
    app_token = args.app_token or resolve_base_token(config)
    member_id = (
        args.member_id
        or env_nonempty("FEISHU_NOTIFY_OPEN_ID")
        or env_nonempty("FEISHU_NOTIFY_RECEIVE_ID")
    )
    if not member_id:
        raise FeishuError(
            "Missing target member ID. Pass --member-id or set FEISHU_NOTIFY_OPEN_ID / FEISHU_NOTIFY_RECEIVE_ID."
        )

    member_type = args.member_type
    if not member_type:
        member_type = "openid" if env_nonempty("FEISHU_NOTIFY_OPEN_ID") else "openid"

    client = build_client()
    granted = client.add_permission_member(
        app_token,
        doc_type=args.doc_type,
        member_id=member_id,
        member_type=member_type,
        perm=args.perm,
        perm_type=args.perm_type,
        collaborator_type=args.collaborator_type,
        need_notification=args.need_notification,
    )

    payload = {
        "base_url": config.get("base_url", ""),
        "app_token": app_token,
        "granted_member": granted,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_migrate(args: argparse.Namespace) -> int:
    client = build_client()

    source_config = load_runtime_config(args.from_config)
    target_config = load_runtime_config(args.to_config)

    source_app_token, source_table_ids = resolve_storage(source_config)
    target_app_token = args.to_app_token or resolve_base_token(target_config)
    target_table_ids = ensure_tables(
        client,
        target_app_token,
        include_legacy=any(source_table_ids.get(key) for key in LEGACY_TABLE_KEYS),
    )

    migrated_counts: dict[str, int] = {}
    preview: dict[str, list[dict[str, str]]] = {}

    for logical_name, spec in TABLE_SPECS.items():
        if not source_table_ids.get(logical_name) or not target_table_ids.get(logical_name):
            migrated_counts[logical_name] = 0
            continue
        field_names = table_field_names(spec)
        source_records = client.list_records(
            source_app_token,
            source_table_ids[logical_name],
            field_names=field_names,
            limit=args.limit,
        )
        normalized_records = []
        for item in source_records:
            fields = item.get("fields", {})
            normalized_records.append(
                {field: fields.get(field) for field in field_names if fields.get(field) not in (None, "")}
            )

        migrated_counts[logical_name] = len(normalized_records)
        if args.dry_run:
            preview[logical_name] = normalized_records[:3]
            continue

        for fields in normalized_records:
            client.create_record(target_app_token, target_table_ids[logical_name], fields)

    payload: dict[str, Any] = {
        "source_app_token": source_app_token,
        "target_app_token": target_app_token,
        "migrated_counts": migrated_counts,
    }
    if args.dry_run:
        payload["preview"] = preview

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    raw_note = read_note_input(args.note_json, args.stdin)
    validate_no_placeholder_ellipsis(raw_note)
    note = normalize_note(raw_note)
    records = build_records(note)
    config_path = args.config or os.getenv(DEFAULT_CONFIG_ENV)

    if args.dry_run:
        print(json.dumps(records, ensure_ascii=False, indent=2))
        return 0

    config = load_runtime_config(args.config)
    app_token, table_ids = resolve_storage(config)
    client = build_client()
    conversation_field_map, conversation_schema_warnings = ensure_conversation_schema(
        client,
        app_token,
        table_ids["conversations"],
    )

    existing_conversation_records = client.list_records(
        app_token,
        table_ids["conversations"],
        field_names=conversation_field_names(),
        limit=2000,
    )
    conversation_consolidation = consolidate_conversation_records(
        client,
        app_token,
        table_ids["conversations"],
        existing_conversation_records,
    )
    mirrored_conversation_fields = {
        **records["conversation"],
        **conversation_title_update_fields(
            records["conversation"].get("标题", ""),
            current_fields=records["conversation"],
            available_fields=conversation_field_map,
        ),
    }
    conversation_action, conversation = upsert_conversation_record(
        client,
        app_token,
        table_ids["conversations"],
        conversation_consolidation["records"],
        mirrored_conversation_fields,
    )
    tutorial_result = {
        "updated_records": 0,
        "tutorial_urls": {},
        "warnings": [],
    }
    legacy_table_warnings: list[str] = []
    gap_records: list[dict[str, Any]] = []
    if records["gaps"] and table_ids.get("gaps"):
        gap_records = [
            client.create_record(app_token, table_ids["gaps"], gap_record) for gap_record in records["gaps"]
        ]
    elif records["gaps"]:
        legacy_table_warnings.append("已跳过不足追踪写入：当前配置只启用主表。")
    existing_reading_records: list[dict[str, Any]] = []
    reading_results: list[str] = []
    reading_enrichment = {"updated_records": 0, "warnings": []}
    if records["reading"] and table_ids.get("reading"):
        ensure_table_fields(client, app_token, table_ids["reading"], TABLE_SPECS["reading"]["fields"])
        existing_reading_records = client.list_records(
            app_token,
            table_ids["reading"],
            field_names=table_field_names(TABLE_SPECS["reading"]),
            limit=2000,
        )
        existing_reading_records = consolidate_reading_records(
            client,
            app_token,
            table_ids["reading"],
            existing_reading_records,
        )["records"]
        for read_record in records["reading"]:
            action, existing_reading_records = upsert_reading_record(
                client,
                app_token,
                table_ids["reading"],
                existing_reading_records,
                read_record,
            )
            reading_results.append(action)
        reading_enrichment = enrich_reading_records(
            client,
            app_token,
            table_ids["reading"],
            client.list_records(
                app_token,
                table_ids["reading"],
                field_names=table_field_names(TABLE_SPECS["reading"]),
                limit=2000,
            ),
            load_book_metadata_overrides(),
        )
    elif records["reading"]:
        legacy_table_warnings.append("已跳过阅读队列写入：当前配置只启用主表。")
    current_conversation_records = client.list_records(
        app_token,
        table_ids["conversations"],
        field_names=conversation_field_names(),
        limit=2000,
    )
    current_reading_records = (
        client.list_records(
            app_token,
            table_ids["reading"],
            field_names=table_field_names(TABLE_SPECS["reading"]),
            limit=2000,
        )
        if table_ids.get("reading")
        else []
    )
    current_record = next(
        (item for item in current_conversation_records if item.get("record_id") == conversation.get("record_id")),
        None,
    )
    if current_record:
        tutorial_result = refresh_conversation_tutorial_docs(
            client,
            app_token,
            table_ids["conversations"],
            [current_record],
            config=config,
            reading_records=current_reading_records,
        )

    dashboard_result = None
    dashboard_warning = ""
    try:
        dashboard_records = load_dashboard_records(client, app_token, table_ids)
        dashboard_result = refresh_dashboard_doc(
            client,
            config,
            dashboard_records["conversations"],
            dashboard_records["gaps"],
            dashboard_records["reading"],
            config_path=config_path,
        )
    except FeishuError as exc:
        dashboard_warning = f"仪表盘刷新失败 - {exc}"

    tutorial_url = next(iter(tutorial_result["tutorial_urls"].values()), "")
    push_result = None
    push_warning = ""
    push_message = render_sync_push_message(
        note,
        conversation_action,
        result_url=sync_result_url(config, tutorial_url),
        root_url=configured_doc_root_url(config),
    )
    try:
        if resolve_notify_target():
            push_result = maybe_send_reminder(client, push_message)
        else:
            push_warning = (
                "知识库维护已完成，但没有发送 push：未配置 FEISHU_NOTIFY_OPEN_ID / FEISHU_NOTIFY_CHAT_ID / webhook。"
            )
    except FeishuError as exc:
        push_warning = f"知识库维护完成 push 发送失败 - {exc}"

    payload = {
        "conversation_record_id": conversation.get("record_id"),
        "conversation_action": conversation_action,
        "conversation_merged_group_count": conversation_consolidation["merged_groups"],
        "conversation_tutorial_updated": bool(tutorial_result["updated_records"]),
        "conversation_tutorial_url": tutorial_url,
        "document_root_url": configured_doc_root_url(config),
        "dashboard_url": dashboard_result["url"] if dashboard_result else "",
        "gap_record_count": len(gap_records),
        "reading_record_count": len(records["reading"]),
        "reading_created_count": sum(1 for item in reading_results if item == "created"),
        "reading_updated_count": sum(1 for item in reading_results if item == "updated"),
        "reading_enriched_count": reading_enrichment["updated_records"],
        "push_sent": bool(push_result),
        "push_message": push_message,
        "conversation_key": note.conversation_key,
        "warnings": conversation_schema_warnings
        + conversation_consolidation["warnings"]
        + tutorial_result["warnings"]
        + legacy_table_warnings
        + reading_enrichment["warnings"]
        + ([dashboard_warning] if dashboard_warning else [])
        + ([push_warning] if push_warning else []),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_send_reminder(args: argparse.Namespace) -> int:
    raw_note = read_note_input(args.note_json, args.stdin)
    validate_no_placeholder_ellipsis(raw_note)
    note = normalize_note(raw_note)
    client = build_client()
    result = maybe_send_reminder(client, render_reminder(note))
    print(json.dumps({"reminder_sent": True, "result": result}, ensure_ascii=False, indent=2))
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    config = load_runtime_config(args.config)
    app_token, table_ids = resolve_storage(config)
    client = build_client()

    conversation_records = client.list_records(
        app_token,
        table_ids["conversations"],
        field_names=["标题", "下一步行动", "日期", "同步时间"],
        sort=["同步时间 DESC"],
        limit=max(args.limit, 1),
    )
    gap_records = []
    if table_ids.get("gaps"):
        gap_records = sort_gap_records(
            client.list_records(
                app_token,
                table_ids["gaps"],
                field_names=["标题", "不足", "弥补动作", "优先级", "复盘日期", "状态", "日期"],
                sort=["日期 DESC"],
                limit=max(args.limit * 2, 10),
            )
        )
    reading_records = []
    if table_ids.get("reading"):
        reading_records = sort_reading_records(
            client.list_records(
                app_token,
                table_ids["reading"],
                field_names=["书名", "作者", "推荐理由", "优先级", "状态", "日期"],
                sort=["日期 DESC"],
                limit=max(args.limit * 2, 10),
            )
        )

    message = build_review_message(conversation_records, gap_records, reading_records)
    reminder_result = None
    if args.notify:
        reminder_result = maybe_send_reminder(client, message)

    payload = {
        "latest_conversation_count": len(conversation_records),
        "gap_candidates": len(gap_records),
        "reading_candidates": len(reading_records),
        "message": message,
        "reminder_sent": bool(reminder_result),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_upgrade_reading(args: argparse.Namespace) -> int:
    config_path = args.config or os.getenv(DEFAULT_CONFIG_ENV)
    config = load_runtime_config(args.config)
    app_token, table_ids = resolve_storage(config)
    table_id = table_ids.get("reading")
    if not table_id:
        raise FeishuError("当前配置只启用主表，没有阅读队列表。需要旧版阅读队列时，请先配置 FEISHU_READING_TABLE_ID。")
    client = build_client()
    reading_spec = TABLE_SPECS["reading"]
    field_map = ensure_table_fields(client, app_token, table_id, reading_spec["fields"])
    metadata_overrides = load_book_metadata_overrides()
    records = client.list_records(
        app_token,
        table_id,
        field_names=table_field_names(reading_spec),
        limit=args.limit,
    )
    consolidate_result = consolidate_reading_records(client, app_token, table_id, records)
    records = consolidate_result["records"]

    recommendation_counts: dict[str, int] = {}
    for record in records:
        key = reading_record_key_from_fields(record.get("fields", {}))
        if key:
            recommendation_counts[key] = parse_intish(record.get("fields", {}).get("推荐次数"), default=1)

    views = client.list_views(app_token, table_id)
    gallery_view = next((view for view in views if view.get("view_name") == READING_GALLERY_VIEW_NAME), None)
    if not gallery_view:
        gallery_view = next((view for view in views if view.get("view_type") == "gallery"), None)
    if not gallery_view:
        gallery_view = client.create_view(app_token, table_id, READING_GALLERY_VIEW_NAME, "gallery")

    hidden_field_names = ["对话ID", "类型"]
    hidden_field_ids = [
        field_map[name]["field_id"] for name in hidden_field_names if name in field_map and field_map[name].get("field_id")
    ]
    try:
        client.patch_view(
            app_token,
            table_id,
            gallery_view["view_id"],
            view_name=READING_GALLERY_VIEW_NAME,
            property_payload={"hidden_fields": hidden_field_ids},
        )
    except FeishuError:
        pass

    warnings: list[str] = list(consolidate_result["warnings"])
    updated_records = 0

    for record in records:
        fields = record.get("fields", {})
        record_key = reading_record_key_from_fields(fields)
        expected_count = recommendation_counts.get(record_key, parse_intish(fields.get("推荐次数"), default=1))
        count_updates: dict[str, Any] = {}
        if compact_text(fields.get("推荐次数")) != str(expected_count):
            count_updates["推荐次数"] = expected_count
        if compact_text(fields.get("提及频率")) != str(expected_count):
            count_updates["提及频率"] = expected_count
        if count_updates:
            try:
                client.update_record(app_token, table_id, record["record_id"], count_updates)
                updated_records += 1
            except FeishuError as exc:
                warnings.append(f"{compact_text(fields.get('书名'))}: 推荐次数修正失败 - {exc}")

    enrichment_result = enrich_reading_records(
        client,
        app_token,
        table_id,
        records,
        metadata_overrides,
        refresh_metadata=args.refresh_metadata,
        refresh_covers=args.refresh_covers,
    )
    updated_records += enrichment_result["updated_records"]
    warnings.extend(enrichment_result["warnings"])

    gallery_url = build_reading_gallery_url(app_token, table_id, gallery_view["view_id"])
    if config_path:
        config[READING_GALLERY_CONFIG_KEY] = gallery_url
        write_json(Path(config_path), config)

    dashboard_result = None
    try:
        dashboard_records = load_dashboard_records(client, app_token, table_ids, limit=max(args.limit, 2000))
        dashboard_result = refresh_dashboard_doc(
            client,
            config,
            dashboard_records["conversations"],
            dashboard_records["gaps"],
            dashboard_records["reading"],
            config_path=config_path,
        )
    except FeishuError as exc:
        warnings.append(f"仪表盘刷新失败 - {exc}")

    payload = {
        "reading_table_id": table_id,
        "gallery_view_id": gallery_view["view_id"],
        "gallery_url": gallery_url,
        "dashboard_url": dashboard_result["url"] if dashboard_result else "",
        "record_count": len(records),
        "merged_group_count": consolidate_result["merged_groups"],
        "deleted_duplicate_count": consolidate_result["deleted_records"],
        "updated_record_count": updated_records,
        "recommendation_count": {
            compact_text(record.get("fields", {}).get("书名")): recommendation_counts.get(
                reading_record_key_from_fields(record.get("fields", {})),
                1,
            )
            for record in records
            if compact_text(record.get("fields", {}).get("书名"))
        },
        "warnings": warnings,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_upgrade_conversations(args: argparse.Namespace) -> int:
    config_path = args.config or os.getenv(DEFAULT_CONFIG_ENV)
    config = load_runtime_config(args.config)
    app_token, table_ids = resolve_storage(config)
    table_id = table_ids["conversations"]
    client = build_client()

    _, schema_warnings = ensure_conversation_schema(client, app_token, table_id)
    records = client.list_records(
        app_token,
        table_id,
        field_names=conversation_field_names(),
        limit=args.limit,
    )
    consolidate_result = consolidate_conversation_records(client, app_token, table_id, records)
    warnings = list(schema_warnings + consolidate_result["warnings"])
    dashboard_result = None
    try:
        dashboard_records = load_dashboard_records(client, app_token, table_ids, limit=max(args.limit, 2000))
        dashboard_result = refresh_dashboard_doc(
            client,
            config,
            dashboard_records["conversations"],
            dashboard_records["gaps"],
            dashboard_records["reading"],
            config_path=config_path,
        )
    except FeishuError as exc:
        warnings.append(f"仪表盘刷新失败 - {exc}")

    payload = {
        "conversation_table_id": table_id,
        "record_count": len(consolidate_result["records"]),
        "merged_group_count": consolidate_result["merged_groups"],
        "deleted_duplicate_count": consolidate_result["deleted_records"],
        "updated_record_count": consolidate_result["updated_records"],
        "dashboard_url": dashboard_result["url"] if dashboard_result else "",
        "warnings": warnings,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_upgrade_conversation_docs(args: argparse.Namespace) -> int:
    config_path = args.config or os.getenv(DEFAULT_CONFIG_ENV)
    config = load_runtime_config(args.config)
    app_token, table_ids = resolve_storage(config)
    table_id = table_ids["conversations"]
    client = build_client()

    _, schema_warnings = ensure_conversation_schema(client, app_token, table_id)
    records = client.list_records(
        app_token,
        table_id,
        field_names=conversation_field_names(),
        limit=args.limit,
    )
    reading_records = (
        client.list_records(
            app_token,
            table_ids["reading"],
            field_names=table_field_names(TABLE_SPECS["reading"]),
            limit=max(args.limit, 2000),
        )
        if table_ids.get("reading")
        else []
    )
    tutorial_result = refresh_conversation_tutorial_docs(
        client,
        app_token,
        table_id,
        records,
        config=config,
        reading_records=reading_records,
    )
    warnings = list(schema_warnings + tutorial_result["warnings"])
    dashboard_result = None
    try:
        dashboard_records = load_dashboard_records(client, app_token, table_ids, limit=max(args.limit, 2000))
        dashboard_result = refresh_dashboard_doc(
            client,
            config,
            dashboard_records["conversations"],
            dashboard_records["gaps"],
            dashboard_records["reading"],
            config_path=config_path,
        )
    except FeishuError as exc:
        warnings.append(f"仪表盘刷新失败 - {exc}")

    push_result = None
    push_message = ""
    if args.notify:
        push_message = render_upgrade_docs_push_message(
            tutorial_result["tutorial_urls"],
            root_url=configured_doc_root_url(config),
        )
        try:
            push_result = maybe_send_reminder(client, push_message)
        except FeishuError as exc:
            warnings.append(f"能力资产文档刷新 push 发送失败 - {exc}")

    payload = {
        "conversation_table_id": table_id,
        "record_count": len(records),
        "tutorial_updated_count": tutorial_result["updated_records"],
        "tutorial_urls": tutorial_result["tutorial_urls"],
        "dashboard_url": dashboard_result["url"] if dashboard_result else "",
        "push_sent": bool(push_result),
        "push_message": push_message,
        "warnings": warnings,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_refresh_dashboard(args: argparse.Namespace) -> int:
    config_path = args.config or os.getenv(DEFAULT_CONFIG_ENV)
    config = load_runtime_config(args.config)
    app_token, table_ids = resolve_storage(config)
    client = build_client()
    records = load_dashboard_records(client, app_token, table_ids, limit=args.limit)
    dashboard = refresh_dashboard_doc(
        client,
        config,
        records["conversations"],
        records["gaps"],
        records["reading"],
        config_path=config_path,
    )
    payload = build_dashboard_payload(config, records["conversations"], records["gaps"], records["reading"])
    print(
        json.dumps(
            {
                "dashboard_url": dashboard["url"],
                "dashboard_document_id": dashboard["document_id"],
                "topic_count": payload["topic_count"],
                "total_round_count": payload["total_round_count"],
                "recent_round_count": payload["recent_round_count"],
                "pending_action_count": payload["pending_action_count"],
                "related_asset_count": payload["related_asset_count"],
                "reference_count": payload["reference_count"],
                "pending_gap_count": payload["pending_gap_count"],
                "pending_reading_count": payload["pending_reading_count"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bootstrap a Feishu Base, sync distilled notes, and send reminders."
    )
    parser.add_argument("--env-file", help="Optional .env file to load before running the command.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap = subparsers.add_parser("bootstrap", help="Create or reuse the Base tables.")
    bootstrap.add_argument("--base-name", default="AI 知识复利系统", help="Name for a new Feishu Base.")
    bootstrap.add_argument("--folder-token", help="Optional folder token for Base creation.")
    bootstrap.add_argument("--app-token", help="Reuse an existing Base app token instead of creating one.")
    bootstrap.add_argument("--config-out", help="Write the resulting config JSON to this path.")
    bootstrap.set_defaults(func=cmd_bootstrap)

    template = subparsers.add_parser("template", help="Print a starter JSON note template.")
    template.set_defaults(func=cmd_template)

    sync = subparsers.add_parser("sync", help="Sync one distilled note into Feishu.")
    sync.add_argument("--config", help=f"Config file path. Defaults to ${DEFAULT_CONFIG_ENV}.")
    sync.add_argument("--note-json", help="Path to the distilled note JSON file.")
    sync.add_argument("--stdin", action="store_true", help="Read the note JSON from stdin.")
    sync.add_argument(
        "--notify",
        action="store_true",
        help="Deprecated: sync now sends a completion push automatically when a Feishu notify target is configured.",
    )
    sync.add_argument("--dry-run", action="store_true", help="Print payloads without calling Feishu.")
    sync.set_defaults(func=cmd_sync)

    reminder = subparsers.add_parser("send-reminder", help="Send a reminder without syncing records.")
    reminder.add_argument("--note-json", help="Path to the distilled note JSON file.")
    reminder.add_argument("--stdin", action="store_true", help="Read the note JSON from stdin.")
    reminder.set_defaults(func=cmd_send_reminder)

    review = subparsers.add_parser("review", help="Review existing Feishu knowledge rows and compose a reminder.")
    review.add_argument("--config", help=f"Config file path. Defaults to ${DEFAULT_CONFIG_ENV}.")
    review.add_argument("--limit", type=int, default=3, help="How many gaps or books to include in the summary.")
    review.add_argument("--notify", action="store_true", help="Send the review summary through Feishu.")
    review.set_defaults(func=cmd_review)

    upgrade_reading = subparsers.add_parser(
        "upgrade-reading",
        help="Upgrade the reading queue with gallery view, richer book fields, and metadata backfill.",
    )
    upgrade_reading.add_argument("--config", help=f"Config file path. Defaults to ${DEFAULT_CONFIG_ENV}.")
    upgrade_reading.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Maximum number of reading records to inspect and enrich.",
    )
    upgrade_reading.add_argument(
        "--refresh-covers",
        action="store_true",
        help="Re-upload cover images even if a record already has one.",
    )
    upgrade_reading.add_argument(
        "--refresh-metadata",
        action="store_true",
        help="Overwrite existing online links or tags with the metadata overrides.",
    )
    upgrade_reading.set_defaults(func=cmd_upgrade_reading)

    upgrade_conversations = subparsers.add_parser(
        "upgrade-conversations",
        help="Upgrade the conversation table to topic-based records with merged history and multi-select fields.",
    )
    upgrade_conversations.add_argument("--config", help=f"Config file path. Defaults to ${DEFAULT_CONFIG_ENV}.")
    upgrade_conversations.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Maximum number of conversation records to inspect and consolidate.",
    )
    upgrade_conversations.set_defaults(func=cmd_upgrade_conversations)

    upgrade_conversation_docs = subparsers.add_parser(
        "upgrade-conversation-docs",
        help="Generate tutorial documents for conversation topics and store their URLs in 摘要.",
    )
    upgrade_conversation_docs.add_argument(
        "--config",
        help=f"Config file path. Defaults to ${DEFAULT_CONFIG_ENV}.",
    )
    upgrade_conversation_docs.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Maximum number of conversation topic records to generate docs for.",
    )
    upgrade_conversation_docs.add_argument(
        "--notify",
        action="store_true",
        help="Send a Feishu completion push after asset documents are refreshed.",
    )
    upgrade_conversation_docs.set_defaults(func=cmd_upgrade_conversation_docs)

    refresh_dashboard = subparsers.add_parser(
        "refresh-dashboard",
        help="Generate or update the dynamic Feishu dashboard document from the current knowledge tables.",
    )
    refresh_dashboard.add_argument("--config", help=f"Config file path. Defaults to ${DEFAULT_CONFIG_ENV}.")
    refresh_dashboard.add_argument(
        "--limit",
        type=int,
        default=2000,
        help="Maximum number of records to scan per table when rebuilding the dashboard.",
    )
    refresh_dashboard.set_defaults(func=cmd_refresh_dashboard)

    migrate = subparsers.add_parser(
        "migrate",
        help="Copy the canonical knowledge table, plus legacy tables when present, into another Base.",
    )
    migrate.add_argument("--from-config", required=True, help="Source config file path.")
    migrate.add_argument("--to-config", required=True, help="Target config file path.")
    migrate.add_argument("--to-app-token", help="Optional target Base token override.")
    migrate.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Maximum number of rows per available table to migrate.",
    )
    migrate.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview up to three rows per table without writing to the target Base.",
    )
    migrate.set_defaults(func=cmd_migrate)

    doctor = subparsers.add_parser("doctor", help="Check local setup, config, and optional Feishu connectivity.")
    doctor.add_argument("--config", help=f"Config file path. Defaults to ${DEFAULT_CONFIG_ENV}.")
    doctor.add_argument("--ping", action="store_true", help="Attempt live Feishu auth and table checks.")
    doctor.set_defaults(func=cmd_doctor)

    grant = subparsers.add_parser(
        "grant-access",
        help="Grant the current user or another collaborator access to the Base created by the app.",
    )
    grant.add_argument("--config", help=f"Config file path. Defaults to ${DEFAULT_CONFIG_ENV}.")
    grant.add_argument("--app-token", help="Optional Base app token override.")
    grant.add_argument(
        "--member-id",
        help="Target collaborator ID. Defaults to FEISHU_NOTIFY_OPEN_ID or FEISHU_NOTIFY_RECEIVE_ID.",
    )
    grant.add_argument(
        "--member-type",
        default="openid",
        choices=["openid", "userid", "unionid", "email", "openchat", "groupid", "wikispaceid"],
        help="ID type for the collaborator.",
    )
    grant.add_argument(
        "--perm",
        default="full_access",
        choices=["view", "edit", "full_access"],
        help="Permission role to grant.",
    )
    grant.add_argument(
        "--doc-type",
        default="bitable",
        help="Document type for the token. Use bitable for Feishu Base.",
    )
    grant.add_argument(
        "--perm-type",
        default="container",
        choices=["container", "single_page"],
        help="Permission scope type. single_page is only useful for wiki nodes.",
    )
    grant.add_argument(
        "--collaborator-type",
        default="user",
        choices=[
            "user",
            "chat",
            "department",
            "group",
            "wiki_space_member",
            "wiki_space_viewer",
            "wiki_space_editor",
        ],
        help="Collaborator category.",
    )
    grant.add_argument(
        "--need-notification",
        action="store_true",
        help="Whether Feishu should notify the collaborator about the new permission.",
    )
    grant.set_defaults(func=cmd_grant_access)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args._loaded_env_files = auto_load_dotenv(args.env_file)
    try:
        return args.func(args)
    except FeishuError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"[ERROR] Invalid JSON input: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"[ERROR] Missing file: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("[ERROR] Interrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
