#!/bin/sh

if [ $# -lt 1 ]; then
    uiFiles=`ls *.ui`
else
    uiFiles=$@
fi

for uiFile in $uiFiles; do
    echo "Processing $uiFile"
    filename=`basename $uiFile .ui`
    echo "Writing as ../src/lib/qtui/$filename.py"
    pykdeuic4 -o ../src/lib/qtui/$filename.py $uiFile
done

exit 0