# Как собрать архив `lastname_firstname_ai.zip`

## Что должно быть внутри (по ТЗ)

```
lastname_firstname/
  report.md          # этот шаблон, заполненный
  SOUL.md            # из picoclaw/workspace/
  AGENT.md           # из picoclaw/workspace/
  USER.md            # из picoclaw/workspace/
  config.json        # из picoclaw/ — БЕЗ токенов
```

> На API-пути Modelfile НЕ кладём — он только для Ollama. В ТЗ это явно разрешено.

## Команда для сборки (из корня репо)

```bash
LAST="fida"        # подставь свою фамилию латиницей
FIRST="aleksandr"  # имя

DIR="${LAST}_${FIRST}"
rm -rf "$DIR" "${DIR}_ai.zip"
mkdir "$DIR"

cp picoclaw/workspace/SOUL.md   "$DIR/"
cp picoclaw/workspace/AGENT.md  "$DIR/"
cp picoclaw/workspace/USER.md   "$DIR/"
cp picoclaw/config.json         "$DIR/"
cp submission/report.md         "$DIR/"

# Проверь, что в config.json нет токенов
grep -E '"token"|"api_key"' "$DIR/config.json" && echo "!!! NUKE SECRETS BEFORE ZIPPING !!!" || echo "ok, no obvious secrets"

# Чистим мусор macOS
find "$DIR" -name ".DS_Store" -delete

zip -r "${DIR}_ai.zip" "$DIR"
unzip -l "${DIR}_ai.zip"
```

## Что НЕ должно попасть в архив

- `.security.yml` (никаких реальных ключей)
- `config.json` с заполненным `token`
- `picoclaw/workspace/study/*` — это твой реальный state, в архиве он не нужен
- `__pycache__/`, `.DS_Store`, `venv/`
- `setup/seed_cron.sh` — опционально можно положить, но не обязательно
