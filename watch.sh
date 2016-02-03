#!/usr/bin/env bash

# ./watch.sh game sdcard

while true; do
    inotifywait -e close_write *.py
    cp -a * $2
    cp $2/$1 $2/main.py
done
