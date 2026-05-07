#!/usr/bin/env bash
set -euo pipefail

# Basic security scan replacement for Snyk: run Bandit locally
# Requires: pip install bandit

bandit -r app -q -f txt
