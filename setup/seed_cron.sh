#!/usr/bin/env bash
# Ставит три cron-задания для скилла «Планировщик учёбы».
# Запустить один раз ПОСЛЕ первого `picoclaw gateway` (когда workspace проинициализирован).
#
# Каждый job триггерит turn агента — Гриша сам читает state и формулирует ответ.
# Не используем deliver=true, чтобы сообщение проходило через персону, а не шло сырым.

set -euo pipefail

picoclaw cron add \
  --name "study_morning" \
  --cron "0 9 * * *" \
  --message "Утренний дайджест по учёбе. Прочитай study/deadlines.json (today + overdue), сформулируй коротко (≤3 предложения), отправь пользователю. Не уговаривай и не сюсюкай."

picoclaw cron add \
  --name "study_evening" \
  --cron "0 21 * * *" \
  --message "Вечерний пинг. Один вопрос пользователю — что закрыл за день. Без давления."

picoclaw cron add \
  --name "study_weekly" \
  --cron "0 18 * * 0" \
  --message "Воскресенье 18:00. Подведи неделю: вызови progress_log.py weekly, на основе результата напиши короткое резюме (что закрыл, что висит, сколько часов где сидел). 4-6 строк максимум."

echo "Готово. Текущие jobs:"
picoclaw cron list
