#!/bin/bash

export PKG_DIR="python"
rm -rf ${PKG_DIR} && mkdir -p ${PKG_DIR}
docker run --rm -v $(pwd):/data -w /data lambci/lambda:build-python3.8 \
pip3 install -r requirements.txt --no-deps -t ${PKG_DIR}