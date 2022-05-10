#!/bin/bash

export WRKDIR=$(pwd)
export LAYER_FIRST="layer-python38-requirements"
export LAYER_SECOND="layer-python38-requirements-other"
        
mkdir -p packages/
        
cd ${WRKDIR}/${LAYER_FIRST}/
${WRKDIR}/${LAYER_FIRST}/build_layer.sh
zip -r ${WRKDIR}/packages/python38-requirements-first.zip .
rm -rf ${WRKDIR}/${LAYER_FIRST}/python/

cd ${WRKDIR}/${LAYER_SECOND}/
${WRKDIR}/${LAYER_FIRST}/build_layer.sh
zip -r ${WRKDIR}/packages/python38-requirements-second.zip .
rm -rf ${WRKDIR}/${LAYER_FIRST}/python/