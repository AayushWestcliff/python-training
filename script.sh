#!/bin/bash

# Convert all Jupyter notebooks in the 'notebooks' directory to Markdown
# and save them in the 'docs/lectures/' directory

for nb in notebooks/*.ipynb; do
    jupyter nbconvert --to markdown "$nb" --output-dir=docs/lectures/
done
