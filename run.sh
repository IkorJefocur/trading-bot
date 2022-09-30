#!/bin/bash
cd `dirname $0`
./stop.sh || true
echo -e "\n---------- $(date) ----------\n" >> log.txt
screen -dmS $$ bash -c "pipenv run authbind python . | tee --append log.txt"
echo $$ > pid.txt
./attach.sh