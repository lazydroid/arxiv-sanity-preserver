#!/bin/bash

tar -cz *.p pdf txt templates | split -db 3G - ../sanity_2017-01-06.tgz.
