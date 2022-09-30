#!/bin/bash
cd `dirname $0`
echo -e "\n---------- $(date) ----------\n" >> log.txt
screen -dmS $$ bash -c "cd .. && pipenv run authbind python . | tee log.txt"
echo $$ > pid.txt
./attach.sh