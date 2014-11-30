#!/usr/bin/env bash
set -o errexit

FROM_USER=tatsh
FROM_HOST=tat.sh
LOCAL_DIR="${HOME}/Music/import"
REMOTE_DIR="/mnt/tatsh/temp/import"

ssh "${FROM_USER}@${FROM_HOST}" "/home/tatsh/.virtualenvs/clem2itunes/bin/python /home/tatsh/dev/clem2itunes/clem2itunes-create-lib -m 32 --split-dir /mnt/tatsh4t-2/splitcue-cache/ ${REMOTE_DIR}"
rsync --force --delete-before -rtdLqc "${FROM_USER}@${FROM_HOST}:${REMOTE_DIR}/" "$LOCAL_DIR"
coffee -p update-itunes.coffee | osascript -l JavaScript
