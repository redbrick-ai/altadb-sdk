clean:
	rm -rf altadb*.egg-info altadb*.whl

install:
	python -m pip install --upgrade pip && \
	python -m pip install -e .[dev]

lint:
	black --check altadb && \
	flake8 --benchmark --count altadb && \
	pycodestyle --benchmark --count --statistics altadb && \
	pydocstyle --count altadb && \
	mypy altadb && \
	pylint --rcfile=setup.cfg -j=3 --recursive=y altadb

unit:
	pytest -n 12 -x tests

test: lint unit


build: clean install
	python -m build -w -n -o .

docker: build
	docker build -t redbrickai/altadb:latest -t redbrickai/altadb:`python -c 'import altadb;print(altadb.__version__)'` .
