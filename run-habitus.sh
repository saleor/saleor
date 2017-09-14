#!/usr/bin/env bash

HOST=$1
habitus --build host=$HOST --host=unix:///var/run/docker.sock --binding=0.0.0.0 --secrets=true
