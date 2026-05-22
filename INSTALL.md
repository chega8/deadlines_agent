# Установка и запуск Гриши

Пошагово. Всё, что нужно сделать руками — отмечено `[TODO]`.

## 0. Что у тебя должно быть готово
- Установлен PicoClaw (`picoclaw --version` работает). См. https://github.com/sipeed/picoclaw
- Создан Telegram-бот через **@BotFather** → получен `BOT_TOKEN` `[TODO]`
- Получен Telegram user ID через **@userinfobot** `[TODO]`
- Yandex Cloud: создан сервисный аккаунт с ролью `ai.languageModels.user`, есть `API_KEY` и `FOLDER_ID` `[TODO]`

## 1. Раскатать файлы

Из корня этого репо:

```bash
mkdir -p ~/.picoclaw
cp picoclaw/config.json ~/.picoclaw/config.json
cp -r picoclaw/workspace ~/.picoclaw/workspace
cp picoclaw/security.yml.example ~/.picoclaw/.security.yml
chmod 600 ~/.picoclaw/.security.yml
chmod +x ~/.picoclaw/workspace/scripts/*.py
```

## 2. Заполнить секреты

`~/.picoclaw/.security.yml` — подставить:
- `YANDEX_API_KEY` и `YANDEX_FOLDER_ID`
- `TELEGRAM_BOT_TOKEN`

`~/.picoclaw/config.json` — заменить `YOUR_TELEGRAM_USER_ID` в `channel_list.telegram.allow_from` на свой реальный id (число в виде строки, например `"123456789"`).

## 3. Yandex: важный нюанс

PicoClaw из коробки **не знает про YandexGPT** — в `model_list` он указан как `openai/yandexgpt` через OpenAI-совместимый endpoint `https://llm.api.cloud.yandex.net/v1`.

Yandex Cloud действительно отдаёт OpenAI-совместимый API, но требует:
1. Заголовок `Authorization: Api-Key <key>` (PicoClaw посылает `Bearer <key>` — для Yandex обычно тоже ок, но проверь логи `~/.picoclaw/logs/`).
2. Модель в формате `gpt://<FOLDER_ID>/yandexgpt/latest` — это значение нужно подставлять в поле `model`. Если в логах PicoClaw увидишь 404/400 от Yandex — отредактируй `config.json`, заменив `"model": "openai/yandexgpt"` на `"model": "openai/gpt://<твой-folder-id>/yandexgpt/latest"`.

**Если Yandex упрётся** — переключись на запасную модель одной строкой в `config.json`:

```jsonc
"agents": { "defaults": { "model_name": "deepseek-fallback", ... } }
```

(в `.security.yml` нужен соответствующий DeepSeek-ключ.)

## 4. Запустить

```bash
picoclaw gateway
```

В Telegram открой своего бота → `/start` → напиши «привет». Должен ответить Гриша в своей манере.

## 5. Поставить cron-задания

После первого успешного `gateway`:

```bash
bash setup/seed_cron.sh
```

Это поставит три повторяющихся задачи (утро 9:00, вечер 21:00, воскресенье 18:00).

## 6. Проверить скиллы вручную

В Telegram попробуй:
- «запиши: статвывод, дедлайн 30 мая»
- «что у меня сегодня?»
- «закрыл d1»
- «час сидел за теорвером»
- «итоги недели»

Параллельно смотри файлы: `~/.picoclaw/workspace/study/deadlines.json` и `progress.md` — каждое действие должно отражаться там.

## Если что-то сломалось

- Бот не отвечает → `picoclaw gateway` в форграунде, смотри stderr
- Модель ругается на схему tools → в `model_list` для `yandex-gpt` уже стоит `"tool_schema_transform": "simple"`, оставь
- Cron не срабатывает → `picoclaw cron list` покажет состояние, `picoclaw cron logs <name>` — историю

## Что положить в архив ДЗ

См. `submission/README.md`. Кратко: `SOUL.md`, `AGENT.md`, `USER.md`, `config.json`, `report.md`. **Без** `.security.yml` и без реальных токенов в `config.json`.
