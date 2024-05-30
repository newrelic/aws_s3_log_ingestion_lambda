#!/bin/bash

echo 'Creating python 3.11 layer...'
python -m venv python
source python/bin/activate
python/bin/pip install -r src/requirements.txt
zip -r packages/python311-requirements.zip python/lib
rm -rf python
echo 'Layer creation complete.'
