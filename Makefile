#!/usr/bin/make
lint:
	uv run pre-commit run --all-files

dev:
	APP_COMPONENT=web APP_DEV_MODE=true APP_HTTP_PORT=8000 scripts/run_web.sh
