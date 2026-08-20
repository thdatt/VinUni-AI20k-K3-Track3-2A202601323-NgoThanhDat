.PHONY: install test lint format run-baseline run-multi benchmark submission clean

install:
	pip install -e ".[dev,llm]"

test:
	pytest

lint:
	ruff check src tests scripts

format:
	ruff format src tests scripts

run-baseline:
	python -m multi_agent_research_lab.cli baseline --query "When is a multi-agent research system justified over a single agent?"

run-multi:
	python -m multi_agent_research_lab.cli multi-agent --query "When is a multi-agent research system justified over a single agent?"

benchmark:
	python scripts/run_benchmark.py

submission:
	python scripts/run_submission.py

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache dist build *.egg-info
