#!/usr/bin/env bash
set -o errexit

FROM_USER="${FROM_USER:-${USER}}"
FROM_HOST="${FROM_HOST:-limelight}"
LOCAL_DIR="${LOCAL_DIR:-${HOME}/Music/import}"
REMOTE_DIR="${REMOTE_DIR:-/home/${USER}/temp/import}"
REMOTE_PYTHON="${REMOTE_PYTHON:-/home/${USER}/.virtualenvs/clem2itunes/bin/python}"
REMOTE_CREATE_LIB="${REMOTE_CREATE_LIB:-/home/${USER}/dev/clem2itunes/clem2itunes-create-lib}"
REMOTE_SPLITCUE_CACHE_DIR="${REMOTE_SPLITCUE_CACHE_DIR:-/home/${USER}/.splitcue-cache/}"
SIZE_LIMIT_IN_GB="${SIZE_LIMIT_IN_GB:-32}"
THRESHOLD="${THRESHOLD:-0.8}"

# shellcheck disable=SC2029
ssh "${FROM_USER}@${FROM_HOST}" \
    "${REMOTE_PYTHON} \
     "${REMOTE_CREATE_LIB}" \
        -m "${SIZE_LIMIT_IN_GB}" \
        -t "${THRESHOLD}" \
        --split-dir "${REMOTE_SPLITCUE_CACHE_DIR}" \
        ${REMOTE_DIR}"
rsync --force --delete-before -rtdLqc "${FROM_USER}@${FROM_HOST}:${REMOTE_DIR}/" "$LOCAL_DIR"
rm -f update-itunes.js
coffee -bcs update-itunes.coffee | osascript -l JavaScript
