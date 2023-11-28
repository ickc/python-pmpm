---
fontsize:	11pt
documentclass:	memoir
classoption: article
geometry:	inner=1in, outer=1in, top=1in, bottom=1.25in
title:	Python manual package manager—a package manager written in Python for manually installing a compiled stack
...

``` {.table}
---
header: false
markdown: true
include: badges.csv
...
```

# Introduction

Python manual package manager is a package manager written in Python for manually installing a compiled stack.

# One-step install

```sh
git clone https://github.com/ickc/python-pmpm.git
cd python-pmpm
conda activate
mamba env create -f environment.yml
conda activate pmpm
pip install .
pmpm conda_install "$HOME/pmpm-test"
```
