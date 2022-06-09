# Directory for PUMI test dataset for development purposes

PUMI is shipped with two datasets:
### pumi-minitest
A lightweight test dataset (9M) with down-sampled data of one example subject.
This dataset is part of the repository and serves for unit testing.

### pumi_test_data
This is a larger test dataset, for more elaborated testing during development.
This dataset is not part of this git repository.
Get them with datalad, by running the following commands in this directory.

```
export WEBDAV_USERNAME=XXXX
export WEBDAV_PASSWORD=XXXX-XXXX-XXXX-XXXX
datalad install -s git@github.com:pni-data/pumi_test_data.git pumi_test_data
datalad siblings -d pumi_test_data enable -s sciebo.sfb289
datalad get pumi_test_data/*
```

