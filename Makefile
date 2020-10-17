PYTHON=python3
SRC=./e2e/api/
TEST_SRC=./tests/

#=#=#=#=#=#=#=#=#=#=#=#
# Development         #
#=#=#=#=#=#=#=#+#=#=#=#

.PHONY: tox
tox: venv
	. ./venv/bin/activate && tox -- $(TEST_SRC)

.PHONY: test
test: venv
	. ./venv/bin/activate && pytest -vv $(TEST_SRC)

.PHONY: lint
lint: venv
	. ./venv/bin/activate && mypy $(SRC) $(TEST_SRC)
	. ./venv/bin/activate && flake8 $(SRC) $(TEST_SRC)
	. ./venv/bin/activate && pylint $(SRC) $(TEST_SRC)

.PHONY: format
format: venv
	. ./venv/bin/activate && isort -rc $(SRC) $(TEST_SRC)
	. ./venv/bin/activate && black $(SRC) $(TEST_SRC)

#=#=#=#=#=#=#=#=#=#=#=#
# Packaging           #
#=#=#=#=#=#=#=#+#=#=#=#

.PHONY: sdist
sdist: build-venv
	. ./build-venv/bin/activate && python setup.py sdist

.PHONY: wheel
wheel: build-venv
	. ./build-venv/bin/activate && python setup.py bdist_wheel

#=#=#=#=#=#=#=#=#=#=#=#
# Virtual Envs        #
#=#=#=#=#=#=#=#+#=#=#=#

venv: setup.py
	$(PYTHON) -m venv $@
	. ./$@/bin/activate && pip install -U "setuptools>=40.6.0" "wheel"
	. ./$@/bin/activate && pip install -e .[dev]
	touch $@

build-venv: setup.py
	$(PYTHON) -m venv $@
	. ./$@/bin/activate && pip install -U "setuptools>=40.6.0" "wheel"
	touch $@

#=#=#=#=#=#=#=#=#=#=#=#
# Cleaning            #
#=#=#=#=#=#=#=#+#=#=#=#

.PHONY: clean
clean: clean-build clean-venv clean-build-venv clean-py

.PHONY: clean-build
clean-build:
	rm -rf ./dist
	rm -rf ./build
	rm -rf ./*.egg-info

.PHONY: clean-venv
clean-venv:
	rm -rf ./venv

.PHONY: clean-build-venv
clean-build-venv:
	rm -rf ./build-venv

.PHONY: clean-py
clean-py:
	find ./ -name "*.pyc" -delete
	find ./ -name "__pychache__" -delete
	rm -rf ./.mypy_cache
	rm -rf ./.pytest_cache
