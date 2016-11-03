SHELL:=/bin/bash

install-conda: ## Download and install miniconda
	@curl -o miniconda.sh https://repo.continuum.io/miniconda/Miniconda2-latest-Linux-x86_64.sh
	@bash miniconda.sh
	@rm miniconda.sh

dev-scripts: ## Create scripts that are useful while developing (with) sp.fem
	@printf "#!/bin/bash\ntmux -2 new-session -d 'TERM=screen-256color vim spfem/*'\ntmux split-window -h \ntmux split-window -v\ntmux -2 attach-session -d" > dev-tmux
	@chmod 744 dev-tmux

dev-install-yml: ## Create a development environment from environment.yml
	@conda env create -f environment.yml

dev-install: ## Create a development environment
	@conda create -q -n spfemenv python numpy scipy matplotlib sympy ipython pyqt=4.11.4 mayavi

activate: ## Type ". activate spfemenv" to start the conda environment
	@echo "Activate the development environment by typing: \". activate spfemenv\""

deactivate: ## Type ". deactivate" to quit the conda environment
	@echo "Deactivate the development environment by typing: \". deactivate\""

run-tests: ## Run the unit tests
	@ipython -m unittest discover ./spfem

run-perf: ## Run the performance tests
	@ipython ./spfem/test_perf.py

run-coverage: ## Run the unit tests with coverage.py
	@coverage run -m unittest discover ./spfem

build-docs: ## Run Sphinx to build the documentation
	@make -C docs html

help: ## Show this help (default)
	@echo "                     _____               "
	@echo "   ____________    _/ ____\\____   _____  "
	@echo "  /  ___/\\____ \\   \\   __\\/ __ \\ /     \\ "
	@echo "  \\___ \\ |  |_> >   |  | \\  ___/|  Y Y  \\"
	@echo " /____  >|   __/ /\ |__|  \\___  >__|_|  /"
	@echo "      \\/ |__|    \\/           \\/      \\/ "
	@echo "                                         "
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
