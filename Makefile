.DEFAULT_GOAL := test

.PHONY: clean help requirements test validate quality production-requirements

# Generates a help message. Borrowed from https://github.com/pydanny/cookiecutter-djangopackage.
help: ## Display this help message
	@echo "Please use \`make <target>\` where <target> is one of"
	@perl -nle'print $& if m{^[\.a-zA-Z_-]+:.*?## .*$$}' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-25s\033[0m %s\n", $$1, $$2}'

clean: ## Delete generated byte code and coverage reports
	find . -name '*.pyc' -delete
	coverage erase

requirements: ## Install requirements for local development
	pipenv install --dev

production-requirements: ## Install requirements for production
	pipenv install

test: clean ## Run tests and generate coverage report
	coverage run -m pytest --durations=25 -v
	coverage report -m

quality: ## Run isort, pycodestyle, and Pylint
	isort --check-only --recursive .
	pycodestyle .
	pylint --rcfile=pylintrc pipeline
	mypy .

validate: quality test ## Run tests and quality checks
