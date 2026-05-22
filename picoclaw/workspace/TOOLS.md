# TOOLS — Что включено и зачем

## Встроенные tools PicoClaw (используются)

| Tool | Зачем | Ограничения |
|------|------|-------------|
| `read_file` | Читать `study/deadlines.json`, `study/progress.md` | Только внутри workspace (`restrict_to_workspace: true`) |
| `write_file` | Инициализация study-файлов, не для регулярных правок | Не используется для `deadlines.json` после первой инициализации — только через скрипт |
| `edit_file` | Точечные правки `progress.md` если нужно поправить опечатку | Редко |
| `append_file` | Каждое изменение state → строка в `progress.md` | Основной способ логирования |
| `list_dir` | Проверить что есть в `study/` | — |
| `exec` | Запуск `deadlines.py` и `progress_log.py` | Только эти два скрипта; через стандартные deny-patterns режется shell-инъекция |
| `cron` | Утренний/вечерний/недельный дайджесты | См. `setup/seed_cron.sh` |
| `message` | Доставка ответа в активный канал (Telegram) | — |
| `web` | Подтянуть контекст по курсу, если попросят | Provider — `sogou` по умолчанию (бесплатный, без ключа). Можно заменить на Brave/Tavily в `config.json` |

## Не используются (выключены или просто не нужны)

- `subagent`, `spawn` — пока скилл один, мульти-агент не нужен. Включён `subagent` на случай будущих сложных потоков, но AGENT.md его не упоминает.
- `mcp` — выключен. См. `HSE_INTEGRATION_IDEAS.md` про потенциальный HSE-MCP в будущем.
- `i2c`, `spi`, `serial`, `send_tts`, `voice` — железо/аудио, не релевантно.

## Скрипты

- `scripts/deadlines.py` — единственный мутатор `deadlines.json`. Атомарная запись (через tmp + rename). Возвращает структурированный JSON в stdout, чтобы агент мог распарсить результат.
- `scripts/progress_log.py` — append в `progress.md` + недельная статистика.

## Секреты

Всё чувствительное — в `~/.picoclaw/.security.yml` (chmod 600). `config.json` ссылается на провайдеров, но реальные ключи живут в security.yml. См. `setup/security.yml.example`.
