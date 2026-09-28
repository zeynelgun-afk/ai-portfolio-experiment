#!/usr/bin/env python3
"""Send an Actions failure to Telegram, falling back to the owner's DM."""

import json
import os
import urllib.parse
import urllib.request


def notify(environ=None, opener=None, message=None):
    environ = os.environ if environ is None else environ
    opener = urllib.request.urlopen if opener is None else opener
    token = environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chats = list(dict.fromkeys(chat.strip() for chat in (
        environ.get("TELEGRAM_CHAT_ID", ""),
        environ.get("TELEGRAM_CHAT_ID_DM", "")) if chat.strip()))
    if not token or not chats:
        raise RuntimeError("Telegram failure alert unavailable: missing bot token or chat ID")
    failed = []
    if environ.get("FAILED_STEPS_FILE"):
        try:
            with open(environ["FAILED_STEPS_FILE"], encoding="utf-8") as handle:
                failed = json.load(handle)
            if not isinstance(failed, list):
                failed = []
        except (OSError, ValueError):
            pass  # The alert must still be sent when fetching step names fails.
    run_url = environ.get("SOURCE_RUN_URL") or (f"{environ.get('GITHUB_SERVER_URL', 'https://github.com')}/"
               f"{environ.get('GITHUB_REPOSITORY', '')}/actions/runs/"
               f"{environ.get('GITHUB_RUN_ID', '')}")
    workflow = environ.get('SOURCE_WORKFLOW') or environ.get('GITHUB_WORKFLOW', 'unknown')
    message = message or ("🚨 AI Portföy — otomasyon hatası\n"
               f"İş akışı: {workflow}\n"
               f"Başarısız adımlar: {', '.join(str(name) for name in failed)[:2500] or 'GitHub kaydına bakın'}\n"
               "Çalışma tamamlanamadı. Ayrıntılar ve işlem durumu:\n" + run_url)
    if environ.get("ALERT_TEST") == "true":
        message = ("✅ AI Portföy — hata bildirimi TESTİ\n"
                   "Bu bir test mesajıdır; yeni bir otomasyon hatası bildirmiyor.\n"
                   "Telegram hata bildirim kanalı doğrulandı.\n" + run_url)
    for index, chat in enumerate(chats):
        request = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data=urllib.parse.urlencode({"chat_id": chat, "text": message}).encode(),
        )
        # Retry transient failures, then try the alternate destination. Never log
        # exception URLs: Telegram embeds the bot token in the URL.
        for attempt in range(2):
            try:
                with opener(request, timeout=15) as response:
                    body = json.loads(response.read())
                    if response.status == 200 and body.get("ok") is True:
                        print(f"Telegram failure alert delivered (destination {index + 1})")
                        return
            except Exception:
                pass
        print(f"::warning::Telegram alert destination {index + 1} could not be reached")
    raise RuntimeError("Telegram failure alert reached no destination; check bot and chat configuration")


if __name__ == "__main__":
    notify()
