#!/bin/sh
abspath=$(cd ${0%/*} && echo $PWD/${0##*/})
path_only=`dirname "$abspath"`

cd $path_only/src/lib && python autokey.py
