#!/bin/bash
# Annotate test failures with metadata for tracking

# This script should be called when a test fails in CI
# Usage: ./annotate-test-failure.sh <test-name> <context>

TEST_NAME="$1"
CONTEXT="$2"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Create failures log if it doesn't exist
mkdir -p .metrics
FAILURE_LOG=".metrics/test-failures.jsonl"

# Add failure record
cat >> "$FAILURE_LOG" << EOF
{"test": "$TEST_NAME", "context": "$CONTEXT", "timestamp": "$TIMESTAMP", "commit": "$GITHUB_SHA", "pr": "$GITHUB_PR_NUMBER", "branch": "$GITHUB_REF_NAME"}
EOF

# Also add as GitHub annotation if in CI
if [ -n "$GITHUB_ACTIONS" ]; then
    echo "::warning title=Test Failure::$TEST_NAME failed in $CONTEXT"
fi