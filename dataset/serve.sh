datasette /mnt/data/text.db -p 8211 \
    --reload \
    --template-dir=templates/ \
    --plugins-dir=plugins/ \
    --static images:/mnt/data/appledaily \
    --static static:/home/jimmywu/sinica/venv/codes/museums/static \
    -m metadata.yaml
