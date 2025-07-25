#!/bin/bash

PID_FILE="/root/Development/magicLB/magiclb.pid"

start() {
    if [ -f "$PID_FILE" ]; then
        echo "magicLB is already running (PID: $(cat $PID_FILE))."
        exit 1
    fi

    echo "Starting magicLB..."
    # Run in background and capture PID
    python3 -m src.main server_mode > /dev/null 2>&1 &
    echo $! > "$PID_FILE"
    echo "magicLB started with PID: $(cat $PID_FILE)"
}

stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "magicLB is not running (PID file not found)."
        return 0 # Exit successfully, as there's nothing to stop
    fi

    PID=$(cat "$PID_FILE")
    echo "Stopping magicLB (PID: $PID)..."
    kill "$PID" 2>/dev/null # Suppress error if process is already gone
    rm "$PID_FILE"
    echo "magicLB stopped."
}

launch_dialog() {
    echo "Launching magicLB dialog interface..."
    python3 -m src.main dialog_mode
}

restart() {
    stop
    start
}

case "$1" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    launch_dialog)
        launch_dialog
        ;;
    restart)
        restart
        ;;
    *)
        echo "Usage: $0 {start|stop|launch_dialog|restart}"
        exit 1
        ;;
esac
