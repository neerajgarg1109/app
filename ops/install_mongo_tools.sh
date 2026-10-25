#!/usr/bin/env bash
set -euo pipefail
# Versioned official vendor package. This installer is for ubuntu-24.04 x86_64 runners.
version=100.18.0
name="mongodb-database-tools-ubuntu2404-x86_64-${version}"
curl --fail --silent --show-error --location "https://fastdl.mongodb.org/tools/db/${name}.tgz" -o "${RUNNER_TEMP}/${name}.tgz"
tar -xzf "${RUNNER_TEMP}/${name}.tgz" -C "${RUNNER_TEMP}"
printf '%s\n' "${RUNNER_TEMP}/${name}/bin" >> "$GITHUB_PATH"
