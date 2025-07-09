# Makefile for Python and MkDocs commands

.PHONY: run deploy build serve all

run:
	python main.py

deploy:
	mkdocs gh-deploy

build:
	mkdocs build

serve:
	mkdocs serve

all: run build serve
