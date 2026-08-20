#!/usr/bin/env bash
set -euo pipefail
grep -R "TODO(student)" -n src tests || true
