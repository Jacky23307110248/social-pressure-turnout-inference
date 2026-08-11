.PHONY: analysis assets report test all

analysis:
	python scripts/run_primary_analysis.py
	python scripts/run_robustness_analysis.py
	python scripts/run_secondary_analysis.py

assets: analysis
	python scripts/generate_report_assets.py

report: assets
	python scripts/build_report.py

test:
	pytest

all: report test

