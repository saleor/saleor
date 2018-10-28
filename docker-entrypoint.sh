#!/usr/bin/env bash

set -e

exec gosu "$HOST_UID" "$@"
