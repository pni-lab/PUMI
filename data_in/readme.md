# Directory for PUMI test dataset for development purposes

The test dataset(s) is(are) not part of this git repository.
Get them with datalad, by running the following commands in this directory.

```
export WEBDAV_USERNAME=XXXX
export WEBDAV_PASSWORD=XXXX-XXXX-XXXX-XXXX
datalad install -s git@github.com:pni-data/pumi_test_data.git pumi_test_data
datalad siblings -d pumi_test_data enable -s sciebo.sfb289
datalad get pumi_test_data/*
```

