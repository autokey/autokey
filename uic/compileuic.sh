#!/bin/sh

for uiFile in `ls *.ui`; do
    echo "Processing $uiFile"
    filename=`basename $uiFile .ui`
    echo "Writing as ../src/lib/qtui/$filename.py"
    pykdeuic4 -o ../src/lib/qtui/$filename.py $uiFile
done

exit 0