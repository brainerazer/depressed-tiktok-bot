#!/usr/bin/env bash

set -e

PYTHON="python -O"
APP="exec ${PYTHON} -m aiogram_bot"

${PYTHON} -m depressed_tiktok_bot.main