load-env:
	direnv allow .

run-dev-app: load-env
	uv run textual run --dev app.py

start-textual-console:
	uv run textual console
