#!/bin/bash

pip install pipreqs
pipreqs --force --print --ignore repo ../itomsmasher | uniq > requirements.txt
