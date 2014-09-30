#!/bin/bash

PYTHON_BIN='python'

for var in "$@"
do
	case $var in
		run) PYTHONIOENCODING=utf-8 $PYTHON_BIN main.py;;
	esac
done

