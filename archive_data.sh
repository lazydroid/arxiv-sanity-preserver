#!/bin/bash

tar -cz *.p pdf txt templates | split -db 3G - ../sanity_`date +%Y-%m-%d`.tgz.
