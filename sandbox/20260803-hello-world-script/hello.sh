#!/usr/bin/env bash

timestamp="$(date +%Y%m%d%H%M%S)"
log_file="$(dirname "$0")/hello_${timestamp}.log"

{
  echo "hello world"
  i=1
  for arg in "$@"; do
    echo "argument ${i}: ${arg}"
    i=$((i + 1))
  done
} | tee "$log_file"
