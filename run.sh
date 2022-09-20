#!/bin/bash
./stop.sh 2>/dev/null || true
echo -e "\n---------- $(date) ----------\n" >> log.txt
nohup pipenv run authbind python prod 2>&1 >> log.txt &
echo $! > pid.txt