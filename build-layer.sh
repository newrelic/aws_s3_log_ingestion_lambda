#!/bin/bash

IMG=mi-lambda/py-layer
podman build --format docker -t $IMG .
podman run -v .:/tmp $IMG
