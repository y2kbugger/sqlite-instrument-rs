.PHONY: help build test bench release

help:	## Show this help.
	@sed -ne 's/^\([^[:space:]]*\):.*##/\1:\t/p' $(MAKEFILE_LIST) | column -t -s $$'\t'

build: ## Build debug version of the extension
	cargo build --features testing-logs

test: build ## Run pytest test suite
	cd test && uv run -- pytest

bench: release	## Run performance benchmarks
	python ./test/benchmark.py

release: ## Build release version of the extension
	cargo build --release
