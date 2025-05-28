import os
import requests
from datetime import datetime, timezone, timedelta
#from dotenv import load_dotenv, find_dotenv

# 로컬 테스트용 .env 로드
#load_dotenv(find_dotenv(), override=True)

def send_weekly_meeting_message():
    discord_webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst).strftime("%Y-%m-%d %H:%M")

    embed = {
        "title": "📢 주간 회의 알림",
        "color": 0xFFA500,
        "description": (
            f"현재 시간은 **{now}** 입니다.\n\n"
            "잠시후 오후 3시 30분에 주간 회의가 시작됩니다.\n"
            "모두 참석 부탁드립니다! :spiral_calendar_pad:"
        ),
    }

    payload = {"embeds": [embed]}
    response = requests.post(discord_webhook_url, json=payload)

    if response.status_code != 204:
        raise RuntimeError(f"Discord 전송 실패: {response.status_code} {response.text}")


def main():
    send_weekly_meeting_message()

if __name__ == "__main__":
    main()