#!/usr/bin/env bash
set -o errexit

FROM_USER=tatsh
FROM_HOST=limelight
LOCAL_DIR="${HOME}/Music/import"
REMOTE_DIR="/home/tatsh/temp/import"
PYTHON='/home/tatsh/.virtualenvs/clem2itunes/bin/python'
CREATE_LIB='/home/tatsh/dev/clem2itunes/clem2itunes-create-lib'

ssh "${FROM_USER}@${FROM_HOST}" "${PYTHON} ${CREATE_LIB} -m 32 --split-dir /home/tatsh/.splitcue-cache/ ${REMOTE_DIR}"
rsync --force --delete-before -rtdLqc "${FROM_USER}@${FROM_HOST}:${REMOTE_DIR}/" "$LOCAL_DIR"
coffee -p update-itunes.coffee | osascript -l JavaScript
