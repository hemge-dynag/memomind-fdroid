#!/bin/sh
# Mirror the freshly signed indexes into .well-known/fdroid/repo so the
# repository also works when added by fingerprint only.
set -e
cd "$(dirname "$0")/.."
mkdir -p .well-known/fdroid/repo
cp -f repo/entry.jar repo/index-v1.jar repo/index-v2.json .well-known/fdroid/repo/
echo "well-known synced"
