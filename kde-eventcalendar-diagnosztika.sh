#!/usr/bin/env bash
# Florum – az Event Calendar widget diagnózisa (a Python-szkript burka).
#   bash kde-eventcalendar-diagnosztika.sh
#   bash kde-eventcalendar-diagnosztika.sh --javitas --restart
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$DIR/eventcalendar-diagnosztika.py" "$@"
