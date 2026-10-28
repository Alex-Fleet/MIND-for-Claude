#!/bin/bash
cd "$(dirname "$0")"; pytest tests/test_regress.py -q
