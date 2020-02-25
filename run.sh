#!/bin/bash

# shellcheck disable=SC2164
SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

cd "$SCRIPTPATH"
if [[ -f "./venv/bin/activate" ]]
then
	source ./venv/bin/activate
fi
cd python/
python3 main.py
