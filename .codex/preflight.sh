#!/usr/bin/env bash
set -e
for h in hooks/*.sh; do
  [ -x "$h" ] && bash "$h"
done
