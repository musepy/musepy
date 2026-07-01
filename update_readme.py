import base64
import json
import os
import urllib.parse
import urllib.request
from typing import Any


README_PATH = os.environ.get("README_PATH", "README.md")
WAKATIME_STATS_URL = "https://wakatime.com/api/v1/users/current/stats/last_7_days"
WAKATIME_TIMEZONE = os.environ.get("WAKATIME_TIMEZONE", "Asia/Shanghai")
START_FLAG = "<!-- WAKATIME:START -->"
END_FLAG = "<!-- WAKATIME:END -->"


def trim(value: str, width: int) -> str:
    if len(value) <= width:
        return value
    if width <= 3:
        return value[:width]
    return value[: width - 3] + "..."


def bar(percent: float, width: int = 20) -> str:
    percent = max(0.0, min(100.0, percent))
    filled = round(width * percent / 100)
    return "[" + "#" * filled + "." * (width - filled) + "]"


def rows(items: list[dict[str, Any]], label_width: int = 14, limit: int = 6) -> list[str]:
    output: list[str] = []
    for item in items[:limit]:
        name = trim(str(item.get("name", "Unknown")), label_width).ljust(label_width)
        time = str(item.get("text", "0 secs")).ljust(13)
        percent = float(item.get("percent", 0))
        output.append(f"{name} {time} {bar(percent)} {percent:5.1f}%")
    return output


def build_wakatime_section(stats: dict[str, Any]) -> str:
    data = stats.get("data", {})
    total = str(data.get("human_readable_total", "0 secs"))
    languages = data.get("languages") if isinstance(data.get("languages"), list) else []
    projects = data.get("projects") if isinstance(data.get("projects"), list) else []

    lines = [
        "```text",
        f"Last 7 days: {total}",
        "",
        "Languages",
    ]
    lines.extend(rows(languages) or ["No language data."])
    lines.extend(["", "Projects"])
    lines.extend(rows(projects) or ["No project data."])
    lines.append("```")
    return "\n".join(lines)


def replace_section(readme: str, section: str) -> str:
    start = readme.find(START_FLAG)
    end = readme.find(END_FLAG)
    if start == -1 or end == -1 or end < start:
        raise ValueError("README missing WakaTime markers")

    before = readme[: start + len(START_FLAG)]
    after = readme[end:]
    return f"{before}\n{section}\n{after}"


def fetch_wakatime_stats(api_key: str) -> dict[str, Any]:
    token = base64.b64encode(api_key.encode()).decode()
    url = WAKATIME_STATS_URL + "?" + urllib.parse.urlencode({"timezone": WAKATIME_TIMEZONE})
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Basic {token}"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode())


def main() -> None:
    api_key = os.environ.get("WAKATIME_API_KEY")
    if not api_key:
        raise RuntimeError("WAKATIME_API_KEY is required")

    with open(README_PATH, encoding="utf-8") as file:
        readme = file.read()

    section = build_wakatime_section(fetch_wakatime_stats(api_key))

    with open(README_PATH, "w", encoding="utf-8") as file:
        file.write(replace_section(readme, section))


if __name__ == "__main__":
    main()
