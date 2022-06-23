#!/bin/bash
WORKERS=$(grep -c ^processor /proc/cpuinfo)
export WORKERS=$((WORKERS-2))
export CLEAR=1
uvicorn main:app --log-level warning