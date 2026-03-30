#!/bin/bash
# bot_runner.sh — start the Telegram bot
# Kills ALL stale telegram_bot.py processes before starting a new one.

PROJECT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$PROJECT/.bot.pid"
SCRIPT="telegram_bot/telegram_bot.py"

cd "$PROJECT"

# Kill any running instance by script name (catches stale processes the PID file misses)
STALE_PIDS=$(powershell.exe -NoProfile -Command \
  "Get-WmiObject Win32_Process -Filter \"name='python.exe'\" | Where-Object { \$_.CommandLine -like '*telegram_bot.py*' } | Select-Object -ExpandProperty ProcessId" \
  2>/dev/null | tr -d '\r')

if [ -n "$STALE_PIDS" ]; then
    for PID in $STALE_PIDS; do
        echo "Stopping stale bot instance (PID $PID)…"
        taskkill //PID "$PID" //F 2>/dev/null
    done
    sleep 1
fi
rm -f "$PID_FILE"

source venv/Scripts/activate

# Start bot, capture PID
python "$SCRIPT" "$@" &
BOT_PID=$!
echo "$BOT_PID" > "$PID_FILE"
echo "Bot started (PID $BOT_PID). PID saved to .bot.pid"

# Wait so the script stays alive and the process is tracked
wait "$BOT_PID"
rm -f "$PID_FILE"
