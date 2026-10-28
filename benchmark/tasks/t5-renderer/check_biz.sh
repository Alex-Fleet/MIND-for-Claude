#!/bin/bash
cd "$(dirname "$0")"; pytest tests/test_biz.py -q
