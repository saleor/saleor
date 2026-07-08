# Worktree-safe dev container

A drop-in alternative to `.devcontainer/` for running **multiple git worktrees of this
repo at the same time** without the stacks colliding.

It differs from `.devcontainer/` in two ways:

1. **Ephemeral host ports.** Services publish only their container port, so Docker assigns a
   random free host port to each stack. Two stacks never fight over `5432`/`6379`/etc.
2. **Per-worktree Compose project name.** The `compose.sh` wrapper derives the project name
   from the worktree's root directory, so containers, networks, and volumes are namespaced per
   worktree automatically — each worktree gets its own isolated data with no setup.

It reuses `.devcontainer/`'s `Dockerfile`, `common.env`, and `backend.env` (referenced by
relative path from `docker-compose.yml`) rather than copying them, so `.devcontainer/` must
remain present.

## Using it with the Compose CLI

Use the `compose.sh` wrapper instead of `docker compose` — it sets a per-worktree project name
for you, so there is nothing to configure per worktree:

```sh
.worktree-container/compose.sh up -d
.worktree-container/compose.sh ps
.worktree-container/compose.sh down      # add -v to also drop the volumes
```

Because host ports are ephemeral, look up the assigned host port when connecting from host machine:

```sh
.worktree-container/compose.sh port db 5432       # -> 127.0.0.1:<random>
.worktree-container/compose.sh port cache 6379
.worktree-container/compose.sh port mailpit 8025
.worktree-container/compose.sh port dashboard 80
```
