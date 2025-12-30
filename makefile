.PHONY: load-env run-dev-app start-textual-console

load-env:
	@if command -v direnv >/dev/null 2>&1; then \
		direnv allow .; \
	fi

run-dev-app: load-env
	uv run textual run --dev app.py

run-app: load-env
	uv run textual run app.py

start-textual-console:
	uv run textual console
