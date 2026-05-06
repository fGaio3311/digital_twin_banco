import json
from typing import Any, Iterable


def _parse_json_lines(text: str) -> Iterable[dict[str, Any]]:
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            yield payload
        elif isinstance(payload, list):
            for item in payload:
                if isinstance(item, dict):
                    yield item


def process_logs_file(content: bytes | str) -> list[dict[str, Any]]:
    if isinstance(content, bytes):
        text = content.decode("utf-8", errors="ignore")
    else:
        text = content
    return list(_parse_json_lines(text))
