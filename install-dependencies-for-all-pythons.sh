#!/usr/bin/env bash

set -e

while IFS= read -r line; do
    pyenv local "$line"
    python --version
    pip install -r requirements.txt
    pyenv local --unset
done <<< "$(pyenv versions --bare)"
