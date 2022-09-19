#!/bin/bash
echo -e "\n---------- $(date) ----------\n" >> log.txt
authbind pipenv run python prod 2>&1 | tee --append log.txt