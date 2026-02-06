#!/usr/bin/env bash

set -euxo pipefail
# see https://gist.github.com/mohanpedala/1e2ff5661761d3abd0385e8223e16425

# Run pytest with a temporary XDG_CONFIG_HOME so tests don't touch your real config.
tmp_config_dir="$(mktemp -d)"
cleanup() {
	rm -rf "$tmp_config_dir"
}
trap cleanup EXIT

XDG_CONFIG_HOME="$tmp_config_dir" PYTHONPATH="lib" /bin/python -m pytest "$@"

echo "Script ended"
read x