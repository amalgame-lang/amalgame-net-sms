#!/usr/bin/env bash
# Build + run every tests/*.am against the working tree.
#
# Usage : ./tests/run_am_tests.sh [amc-binary]
#
# The working tree is staged in the amc package cache as a dev version
# (tag v0.0.0-dev, rev localdev) and a scratch project pins it in its
# amalgame.lock ; net-http and crypto come from packages-index. A fake
# SMS gateway (tests/fake_gateway.py, python3) runs on a free port,
# passed to each test as argument 1. A test fails if it prints a
# [FAIL] line, exits non-zero or runs longer than 60 s.
#
# Env : ONLY=<test name> runs one test ; KEEP=1 keeps the scratch project.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AMC="${1:-$(command -v amc)}"
if [ ! -x "$AMC" ]; then
    echo "no amc binary (pass it as the first argument)" >&2
    exit 1
fi

DEV_TAG="v0.0.0-dev"
DEV_REV="localdev"
PKG_ROOT="$HOME/.amalgame/packages/github.com/amalgame-lang/amalgame-net-sms"
DEV_DIR="$PKG_ROOT/${DEV_TAG}_${DEV_REV}"

rm -rf "$DEV_DIR" /tmp/amc-pkg-Sms*
for L in c d e f g h; do [ -d "/$L/tmp" ] && rm -rf "/$L/tmp"/amc-pkg-Sms*; done
mkdir -p "$DEV_DIR"
cp "$ROOT/facade.am" "$ROOT/facade-stub.h" "$ROOT/amalgame.toml" "$DEV_DIR/"

WORK="$(mktemp -d)"
PORT=$(( 20000 + RANDOM % 20000 ))
python3 "$ROOT/tests/fake_gateway.py" "$PORT" "$WORK/sent.jsonl" &
GW=$!
if [ -n "${KEEP:-}" ]; then
    trap 'kill $GW 2>/dev/null' EXIT
    echo "work dir : $WORK"
else
    trap 'kill $GW 2>/dev/null; rm -rf "$WORK" "$DEV_DIR"' EXIT
fi
cd "$WORK"
: > amalgame.toml
"$AMC" package add net-http@v0.29.6 crypto@v0.8.0 >/dev/null 2>&1 || { echo "cannot install net-http / crypto" >&2; exit 1; }
cat >> amalgame.toml <<TOML

[dependencies.sms]
git = "github.com/amalgame-lang/amalgame-net-sms"
tag = "${DEV_TAG}"
TOML
cat >> amalgame.lock <<LOCK

[[package]]
name = "sms"
git  = "github.com/amalgame-lang/amalgame-net-sms"
tag  = "${DEV_TAG}"
rev  = "${DEV_REV}"
LOCK

fail=0
for src in "$ROOT"/tests/${ONLY:-*}.am; do
    name="$(basename "$src" .am)"
    cp "$src" .
    echo "== $name"
    if ! "$AMC" build "$name.am" -o "$name" > "$name.build.log" 2>&1; then
        grep -iE "error|undefined" "$name.build.log" | head -20 || true
        echo "FAIL $name (build)"; fail=1; continue
    fi
    if ! timeout 60 "./$name" "$PORT" > "$name.log" 2>&1; then
        tail -20 "$name.log"; echo "FAIL $name (exit)"; fail=1; continue
    fi
    if grep -qE '^\[FAIL\]' "$name.log"; then
        grep -E '^\[FAIL\]' "$name.log"; echo "FAIL $name"; fail=1; continue
    fi
    echo "ok   $name ($(grep -c '^\[PASS\]' "$name.log") checks)"
done
# What the gateway received : exactly the accepted message, as sent.
if [ "$fail" = 0 ]; then
    if [ "$(cat "$WORK/sent.jsonl" 2>/dev/null)" = '{"text": "Kairos : P2 en défaut", "to": ["+33612345678"]}' ]; then
        echo "ok   the gateway received the message as sent (UTF-8, number)"
    else
        echo "FAIL gateway log : $(cat "$WORK/sent.jsonl" 2>/dev/null)"; fail=1
    fi
fi
exit $fail
