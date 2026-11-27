.PHONY: install test oracle baseline phoenix

install:            ## install dependencies into .venv
	uv sync --python 3.15 --extra dev

test:               ## check the factory and the benchmark (no LLM calls)
	.venv/bin/pytest -q

oracle:             ## grade the right answers for every station (must all be 1.0)
	for s in intake implement review; do .venv/bin/factory bench run $$s --oracle; done

baseline:           ## run every baseline agent 3x (costs API credits)
	for s in intake implement review; do .venv/bin/factory bench run $$s --repeat 3 --label baseline; done

phoenix:            ## trace viewer at http://localhost:6006 (leave it running; agent runs show up there)
	bash .devcontainer/start-phoenix.sh
