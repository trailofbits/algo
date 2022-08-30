# Algo web app UI

## Abstract

[A short description of what project does]

## Background

VUE docs,
asyncio docs

## Rationale

Why A not B
(vue is modern and doesn't require build system and depoendency)
asyncio - same
PBEX is patched because shell access considered insecure

## Implementation

app/server.py management, threading
config yaml writer
generic approach to provider UI (set required fields, validation, inherit ENV, try to detect)
how progress displayed

## testing
testing js: vue-test-library + loader
testing python: pytests
testing pbex compatibility: demo yaml

## Compatibility (if applicable)

[A discussion of the change with regard to the compatibility.]
Due to ansible doesn't have API, have to manually check if custom PBEX would still work

## Open issues (if applicable)

Still requires pip install, consider py2exe, pyinstaller
No task progress displayed, require callback module
