#!/bin/bash
cd `dirname $0`
screen -S `cat pid.txt` -X quit
rm pid.txt