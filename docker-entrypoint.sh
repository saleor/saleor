#!/usr/bin/env bash

set -e

exec gosu "$APP_USER" "$@"
