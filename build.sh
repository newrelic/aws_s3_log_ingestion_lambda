#!/bin/bash

export WRKDIR=$(pwd)
export LYR_PDS_DIR="layers-python38-requirements"
        
mkdir -p packages/
        
# Building Python-pandas layer
cd ${WRKDIR}/${LYR_PDS_DIR}/
${WRKDIR}/${LYR_PDS_DIR}/build_layer.sh
zip -r ${WRKDIR}/packages/python38-requirements.zip .
rm -rf ${WRKDIR}/${LYR_PDS_DIR}/python/