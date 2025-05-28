import os
import requests
from notion_client import Client
from datetime import datetime, timezone, timedelta
from dateutil.parser import isoparse
# from dotenv import load_dotenv, find_dotenv

# 로컬 테스트용 .env 로드
# load_dotenv(find_dotenv(), override=True)

STATUS_EMOJI = {
    "제안됨": "💡",
    "진행중": "🚧",
    "분류됨": "🗂️",
    "완료됨": "✅"
}

def fetch_notion_data():
    notion_api_key = os.getenv("NOTION_API_KEY")
    notion_database_id = os.getenv("NOTION_DATABASE_ID")
    notion = Client(auth=notion_api_key)

    return notion.databases.query(database_id=notion_database_id)

def format_notion_data(pages: list[dict]):
    tasks = []

    for pg in pages:
        p = pg["properties"]
        title = p["Task name"]["title"][0]["plain_text"] if p["Task name"]["title"] else "제목 없음"
        status = p["Status"]["status"]["name"] if p["Status"]["status"] else "미지정"
        people = p["Assignee"]["people"]
        assignee = people[0]["name"] if people else "없음"
        date_prop = p["Due date"]["date"]
        due_str = date_prop["start"] if date_prop and date_prop.get("start") else None

        # 마감날짜가 없으면 먼 미래로 밀어버리기
        due_dt = isoparse(due_str).date() if due_str else datetime.max.date()

        tasks.append({
            "title": title,
            "status": status,
            "assignee": assignee,
            "due_str": due_str or "없음",
            "due_dt": due_dt
        })

    return tasks    

def sort_tasks(tasks):
    return sorted(
        tasks,
        key=lambda t: (t["status"] == "완료됨", t["due_dt"])
    )

def create_discord_message(tasks: list[dict]):
    kst   = timezone(timedelta(hours=9))
    today = datetime.now(kst).strftime("%Y-%m-%d")

    order = ["진행중", "제안됨", "분류됨", "완료됨"]

    embed = {
        "title": f"📋 오늘의 작업 목록 {today}",
        "color": 0x00aaff,
        "fields": []
    }

    for status in order:
        group = [t for t in tasks if t["status"] == status]
        if not group:
            continue

        emoji = STATUS_EMOJI.get(status, "")

        # 빈 줄 추가
        embed["fields"].append({
            "name": "",
            "value": "\u200B",
            "inline": False
        })

        embed["fields"].append({
            "name": f"{emoji} {status} ({len(group)})",
            "value": "\n".join(
                f"- {t['title']} **→** 마감: **{t['due_str']}**, 담당: **{t['assignee']}**"
                for t in group
            ),
            "inline": False
        })

    return embed

def send_discord_message(message: dict):
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    payload = {"embeds": [message]}
    response = requests.post(discord_webhook_url, json=payload)

    if response.status_code != 204:
        raise RuntimeError(f"Discord 전송 실패: {response.status_code} {response.text}")

def main():
    data = fetch_notion_data()
    formatted_data = format_notion_data(data["results"])
    sorted_tasks = sort_tasks(formatted_data)
    send_message = create_discord_message(sorted_tasks)
    send_discord_message(send_message)

if __name__ == "__main__":
    main()
