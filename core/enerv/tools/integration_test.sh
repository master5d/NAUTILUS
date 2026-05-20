#!/bin/bash
set -e

TMPDIR=$(mktemp -d)
echo "Testing in $TMPDIR"

# Create and init tech root
mkdir -p "$TMPDIR/tech"
echo "Testing: facet init --root"
facet init --root "$TMPDIR/tech" --type tech
echo "OK: Init tech"

# Create project
echo "Testing: facet new project"
facet new project ai active demo --root "$TMPDIR/tech" --apply
echo "OK: New project"

# Audit
echo "Testing: facet audit"
facet audit --root "$TMPDIR/tech"
echo "OK: Audit"

# Validate
echo "Testing: facet validate"
facet validate --root "$TMPDIR/tech"
echo "OK: Validate"

# Index
echo "Testing: facet index"
facet index --root "$TMPDIR/tech"
echo "OK: Index"

rm -rf "$TMPDIR"
echo "Integration test passed"
