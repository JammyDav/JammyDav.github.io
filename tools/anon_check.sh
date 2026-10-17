#!/bin/sh
# anon_check.sh - fail if any real name, ID, mailbox, URL or client reference appears outside _source/.
#
# The patterns live in _source/anon_patterns.txt, which is never committed: a public list of
# forbidden names would publish the very names it protects. Keep that file next to your
# clone (it travels with _source/) and run this before every push:
#
#     sh tools/anon_check.sh
#
# Exit code 0 = clean, 1 = a real reference was found, 2 = the pattern file is missing.
cd "$(dirname "$0")/.." || exit 2
PATTERNS=_source/anon_patterns.txt
if [ ! -s "$PATTERNS" ]; then
  echo "FAIL: $PATTERNS not found, so nothing was checked" >&2
  exit 2
fi
hits=$(grep -rIl -i -E -f "$PATTERNS" --exclude-dir=_source --exclude-dir=.git --exclude-dir=node_modules .)
if [ -n "$hits" ]; then
  echo "FAIL: real reference found in:"
  echo "$hits"
  grep -rIn -o -i -E -f "$PATTERNS" --exclude-dir=_source --exclude-dir=.git --exclude-dir=node_modules . | head -20
  exit 1
fi
echo "clean"
