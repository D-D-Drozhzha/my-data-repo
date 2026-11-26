# Garmin MCP для Claude

Подключает ваши данные Garmin Connect к Claude Desktop: сон, HRV, Body Battery, стресс, пульс,
Training Readiness / Status, VO2max, тренировки со сплитами и пульсовыми зонами, форма/усталость
(CTL / ATL / TSB). Умеет создавать тренировки и отправлять их на часы, а также собирать локальный дашборд.

Работает локально на вашем Mac. Пароль Garmin нигде не хранится — только токены сессии
в `~/.garminconnect` (доступ только у вашего пользователя).

## Установка (≈3 минуты)

1. Распакуйте архив в «Загрузки».
2. Откройте Терминал и выполните:
   ```
   bash ~/Downloads/garmin-mcp/install.sh
   ```
   Скрипт поставит `uv` (если его нет), попросит войти в Garmin Connect (email, пароль, код 2FA),
   и пропишет сервер `garmin` в конфиг Claude Desktop (старый конфиг сохраняется копией).
3. Полностью закройте Claude Desktop (Cmd+Q) и откройте снова. В настройках → Developer
   должен появиться сервер **garmin**.

## Что спрашивать

- «Как я восстановилась сегодня? Делать интервалы или лёгкий бег?»
- «Сравни HRV и сон за последние 4 недели — есть тренд?»
- «Разбери мою последнюю пробежку по кругам: где упал темп, что с пульсом?»
- «Какой у меня TSB и как распределить нагрузку на неделю с падел во вторник и залом в четверг?»
- «Создай интервальную 6×800 м на субботу и отправь на часы»
- «Обнови дашборд»

## Инструменты

| Восстановление | Тренировки | Запись | Прочее |
|---|---|---|---|
| get_daily_overview, get_sleep, get_trends, get_hrv, get_body_battery, get_stress, get_heart_rate, get_daily_activity, get_training_readiness, get_training_status | list_activities, get_activity (круги, зоны, погода), get_training_load (CTL/ATL/TSB), get_performance_metrics (VO2max, прогнозы забегов, endurance/hill score), get_personal_records, get_devices | create_workout, schedule_workout, list_workouts, get_calendar, delete_workout | list_garmin_methods + call_garmin_method — доступ к любым read-only данным Garmin (SpO2, дыхание, вес, питание, цикл, ЭКГ…), build_dashboard |

**TSB** считается по Garmin training load (EPOC), а не по TSS из TrainingPeaks:
абсолютные числа отличаются, но тренды и знак читаются так же.

## Дашборд

`build_dashboard` (или `~/.local/bin/uv run --script ~/garmin-mcp/garmin_dashboard.py 30`) создаёт
`~/garmin-mcp/dashboard.html` и открывает в браузере: плитки дня, сон, sleep score, HRV с вашим
коридором нормы, пульс покоя, Body Battery, стресс, шаги, CTL/ATL, TSB, таблица тренировок.
Поддерживает тёмную тему.

## Если что-то не так

- «Нет действующего входа» → `~/.local/bin/uv run --script ~/garmin-mcp/garmin_login.py --force`
- «Too many login attempts» → Garmin временно ограничил вход, подождите 15–30 минут.
- Сервер не появился → проверьте `~/Library/Application Support/Claude/claude_desktop_config.json`
  и логи в `~/Library/Logs/Claude/mcp-server-garmin.log`.
- Кэш прошлых дней: `~/.garminconnect/cache` (можно удалить, соберётся заново).

Используется неофициальная библиотека [python-garminconnect](https://github.com/cyberjunky/python-garminconnect):
у Garmin нет публичного API для частных пользователей, поэтому при изменениях на стороне Garmin
может понадобиться обновление (`uv` подтягивает свежую версию библиотеки автоматически при пересборке кэша).
