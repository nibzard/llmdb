.PHONY: test bench typecheck

typecheck:
mypy .

test:
ruff --fix .
black .
mypy .
pytest -q

bench:
pytest -q tests/benchmarks
