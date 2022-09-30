#!/bin/bash
echo -e "\n---------- $(date) ----------\n" >> log.txt
screen -dmS $$ bash -c "pipenv run authbind python . 2>&1 | tee log.txt"
echo $$ > pid.txt
./attach.sh