#!/bin/bash

sudo python3 -m pip install \
  --trusted-host nexus.303net.net \
  --index-url https://nexus.303net.net/repository/pypi-public/simple \
  boto3==1.17.27 \
  etl-pm-pipeline-common==1.0.21
