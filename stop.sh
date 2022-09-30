#!/bin/bash
cd `dirname $0`
pid=`cat pid.txt | xargs`
[[ ! -z $pid ]] && screen -S $pid -X quit
rm pid.txt