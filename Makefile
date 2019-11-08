#
# Makefile
# Malcolm Ramsay, 2019-08-13 10:13
#

#
# Notebook rules
#

all_notebooks = $(wildcard notebooks/*.md)

.PHONY: notebooks
notebooks: $(all_notebooks:.md=.ipynb)

.PHONY: sync
sync:
	jupytext --set-formats ipynb,md notebooks/*.md
	jupytext --set-formats ipynb,md notebooks/*.ipynb
	jupytext --sync --pipe black notebooks/*.ipynb

%.ipynb: %.md
	cd $(dir $<) && jupytext --to notebook --execute $(notdir $<)

.PHONY: figures
figures: notebooks ## Generate all the figures in the figures directory

#
# Report Targets
#

report_targets := $(wildcard reports/*.md)
all_figures := $(wildcard figures/*.svg)

convert_figures: $(all_figures:.svg=.pdf)

reports: $(report_targets:.md=.pdf) ## Generate reports
	echo $<

%.pdf: %.md $(all_figures:.svg=.pdf)
	cd $(dir $<); pandoc $(notdir $<) --filter pandoc-crossref -o $(notdir $@)

%.pdf: %.svg
	cairosvg $< -o $@

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# vim:ft=make
#
