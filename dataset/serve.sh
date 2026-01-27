#!/bin/bash

datasette /mnt/data/text.db \
    -h 0.0.0.0 -p 8081 --cors --reload \
    --template-dir=templates/ \
    --plugins-dir=plugins/ \
    --static images:/mnt/data/appledaily \
    --static static:/home/jimmywu/sinica/venv/gitspace/dataset/static \
    -m metadata.yaml

