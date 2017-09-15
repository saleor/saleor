#!/usr/bin/env bash

HOST=$1
PORT=$2

habitus --build host=$HOST port=$PORT --host=unix:///var/run/docker.sock --binding=0.0.0.0 --secrets=true
