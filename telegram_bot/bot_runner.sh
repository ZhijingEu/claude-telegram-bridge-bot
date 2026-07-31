#!/bin/bash
# bot_runner.sh — start / stop / check the Telegram bot (Windows, Git Bash)
#
# Usage:
#   bot_runner.sh [start]   # kill stale instances, then start (default)
#   bot_runner.sh stop      # stop all running instances
#   bot_runner.sh status    # report what's running
#
# Windows notes, both of which are easy to get wrong:
#
#  1. Bash's `$!` returns a bash-internal job ID that the Windows process table
#     knows nothing about. A PID file written from `$!` is useless — taskkill
#     against it always fails. PIDs are therefore discovered by matching the
#     script path in the Windows process list.
#
#  2. Launching `venv/Scripts/python.exe` always produces TWO processes: a
#     launcher shim and its child interpreter, sharing one command line. That
#     is normal, not a stale instance, and killing only the shim does not
#     reliably take the child with it — so every match is killed.
#
# On macOS/Linux, start the bot manually instead (see README).

PROJECT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$PROJECT/.bot.pid"
SCRIPT="telegram_bot/telegram_bot.py"

cd "$PROJECT" || exit 1

if ! command -v powershell.exe >/dev/null 2>&1; then
    echo "ERROR: this script requires Windows (Git Bash) — powershell.exe not found." >&2
    echo "On macOS/Linux start the bot manually:" >&2
    echo "  source venv/bin/activate && python $SCRIPT" >&2
    exit 1
fi

# Windows PIDs of every python.exe running $SCRIPT (one per line, may be empty)
find_pids() {
    powershell.exe -NoProfile -Command \
      "Get-CimInstance Win32_Process -Filter \"name='python.exe'\" | Where-Object { \$_.CommandLine -like '*$SCRIPT*' } | Select-Object -ExpandProperty ProcessId" \
      2>/dev/null | tr -d '\r' | grep -E '^[0-9]+$'
}

# Kill every matching process; retries once because killing the launcher shim
# does not always take its child with it.
stop_all() {
    local pids attempt
    for attempt in 1 2; do
        pids=$(find_pids)
        [ -z "$pids" ] && break
        for pid in $pids; do
            echo "Stopping bot instance (PID $pid)…"
            taskkill //PID "$pid" //F >/dev/null 2>&1
        done
        sleep 1
    done
    rm -f "$PID_FILE"

    if [ -n "$(find_pids)" ]; then
        echo "WARNING: bot processes still running after stop: $(find_pids | tr '\n' ' ')" >&2
        return 1
    fi
    return 0
}

case "${1:-start}" in
    stop)
        if [ -z "$(find_pids)" ]; then
            echo "No bot instance running."
            rm -f "$PID_FILE"
            exit 0
        fi
        stop_all
        exit $?
        ;;

    status)
        pids=$(find_pids)
        if [ -z "$pids" ]; then
            echo "bot: not running"
        else
            echo "bot: running (PIDs $(echo "$pids" | tr '\n' ' '))"
        fi
        exit 0
        ;;

    start)
        shift
        ;;
esac

stop_all || exit 1

source venv/Scripts/activate

python "$SCRIPT" "$@" &
BASH_JOB=$!

# Wait for the Windows process(es) to appear, then record the real PIDs
for _ in 1 2 3 4 5 6 7 8 9 10; do
    REAL_PIDS=$(find_pids)
    [ -n "$REAL_PIDS" ] && break
    sleep 0.5
done

if [ -z "$REAL_PIDS" ]; then
    echo "ERROR: bot did not start — no matching process found." >&2
    rm -f "$PID_FILE"
    exit 1
fi

echo "$REAL_PIDS" > "$PID_FILE"
echo "Bot started (Windows PIDs $(echo "$REAL_PIDS" | tr '\n' ' ')). Saved to .bot.pid"
echo "Stop with: bash $0 stop"

# Stay alive so the job is tracked; clean up the PID file on exit
wait "$BASH_JOB"
rm -f "$PID_FILE"
