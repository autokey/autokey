#!/bin/bash

MD="*.md"

for f in $MD;
do
    /usr/bin/pandoc -o "${f:0:-3}.rst" -t rst -f markdown "$f"
done
