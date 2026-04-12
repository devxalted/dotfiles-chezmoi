#!/bin/bash
if [[ "$(uname)" == "Darwin" ]]; then
    # macOS uptime: "10:30  up 5 days,  3:45, 2 users, load averages: ..."
    uptime | sed 's/.*up //;s/,[^,]*user.*//;s/ *$//'
else
    uptime -p | sed 's/up //'
fi
