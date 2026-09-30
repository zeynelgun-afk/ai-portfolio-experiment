#!/usr/bin/env python3
"""Send an Actions failure to Telegram, falling back to the owner's DM."""

import json
import os
import urllib.parse
import urllib.request


def decision_notification(state, trade="none"):
    """Format only a validated decision; return None when there is nothing to report."""
    changes = state.get("decision_changes") if isinstance(state, dict) else None
    if not isinstance(changes, list) or not changes:
        return None
    lines = ["AI Portföy — karar yeniden değerlendirildi"]
    for change in changes:
        symbol = str(change.get("symbol", "?"))
        lines += [symbol + " → " + str(change.get("action", "?")),
                  "Ne değişti: " + str(change.get("trigger", ""))[:400],
                  "Kararın gerekçesi: " + str(change.get("reasoning", ""))[:600],
                  "Yanlışlanma koşulu: " + str(change.get("falsifier", ""))[:400],
                  "Sonraki inceleme: " + str(change.get("after", {}).get(
                      "monitoring", {}).get("next_review_at", "weekly round"))]
    lines += ["İşlem sonucu: " + str(trade or "none"),
              "https://github.com/zeynelgun-afk/ai-portfolio-experiment/blob/main/DECISION_LOG.md"]
    return "\n".join(lines)[:3500]


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
    partial_assessment = any(name in {'Reassessment health', 'News assessment health'}
                             for name in failed)
    if message is None:
        title = ('⚠️ AI Portföy — kısmi değerlendirme hatası' if partial_assessment
                 else '🚨 AI Portföy — otomasyon hatası')
        context = ("Bazı geçerli değerlendirme ve kayıtlar tamamlanmış olabilir; başarısız kalanlar "
                   "eksik/pending durumunda ve yeniden denenebilir. Bu bildirim, tüm işlemlerin "
                   "başarısız olduğu anlamına gelmez. Yeniden çalıştırmadan önce karar günlüğü ile "
                   "çalışma özetini kontrol edin. " if partial_assessment else
                   "Bazı incelemeler eksik kalmış olabilir; önceki karar veya bildirim adımları "
                   "tamamlanmış olabilir. İşlem durumunu DECISION_LOG ve GitHub kaydından doğrulayın: ")
        message = (f"{title}\n"
                   f"İş akışı: {workflow}\n"
                   f"Başarısız adımlar: {', '.join(str(name) for name in failed)[:2500] or 'GitHub kaydına bakın'}\n"
                   + context + run_url)
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
    notify(message=os.environ.get("WATCHDOG_MESSAGE", "")[:3500] or None)
