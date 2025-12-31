.PHONY: load-env run-app run-app-in-dev-mode start-textual-console

load-env:
	@if command -v direnv >/dev/null 2>&1; then \
		direnv allow .; \
	fi

run-app-in-dev-mode: load-env
	uv run textual run --dev app.py

run-app: load-env
	uv run textual run app.py

start-textual-console:
	uv run textual console
