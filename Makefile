.PHONY: install setup test oracle baseline

install:            ## install dependencies into .venv
	uv sync --extra dev

setup:              ## generate the warehouse + build the dbt project
	.venv/bin/factory setup

test:               ## check the benchmark itself (no LLM calls)
	.venv/bin/pytest -q

oracle:             ## grade the golden answers for every station (must all be 1.0)
	for s in intake implement review governance bi line_manager; do .venv/bin/factory bench run $$s --oracle --parallel 3; done

baseline:           ## run every baseline agent 3x (costs API credits!)
	for s in intake implement review governance bi line_manager; do .venv/bin/factory bench run $$s --repeat 3 --label baseline; done
