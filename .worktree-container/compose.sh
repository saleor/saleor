#!/usr/bin/env sh
# Wrapper around `docker compose` that gives each git worktree its own isolated
# stack automatically — no per-worktree setup.
#
# The Compose project name is derived from the worktree's root directory, so
# containers, networks, and volumes are namespaced per worktree. Run this instead
# of `docker compose`, e.g.:
#
#   .worktree-container/compose.sh up -d
#   .worktree-container/compose.sh port db 5432
#   .worktree-container/compose.sh down
set -eu

dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
root="$(git -C "$dir" rev-parse --show-toplevel)"

# Sanitize the worktree dir name into a valid Compose project name
# (lowercase; anything outside [a-z0-9_-] becomes "-").
name="$(printf '%s' "$(basename "$root")" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9_-' '-')"

exec docker compose -p "saleor-${name}" -f "${dir}/docker-compose.yml" "$@"
