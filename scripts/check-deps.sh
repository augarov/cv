#!/usr/bin/env bash
# Checks that the tools a build stage needs are installed and new enough, so a
# build fails up front with an install hint instead of deep inside a tool.
#
# Usage: scripts/check-deps.sh python|node...
#   python  stage 1 (the renderer): git, uv
#   node    stage 2 (the website): git, git-lfs, Node.js, pnpm
#
# The minimum versions come from the project files, not from this script: uv's
# from cv_renderer/pyproject.toml (tool.uv.required-version), Node.js' and
# pnpm's from gh-pages/package.json (engines). Python itself is installed by uv.
# Runs with macOS's bash 3.2.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYPROJECT_TOML="cv_renderer/pyproject.toml"
PACKAGE_JSON="gh-pages/package.json"

problems=0

problem() {
  echo "check-deps: $*" >&2
  problems=$((problems + 1))
}

# version_at_least VERSION MINIMUM: compares dot-separated numbers
version_at_least() {
  local -a have want
  local i
  IFS=. read -r -a have <<<"$1"
  IFS=. read -r -a want <<<"$2"
  for i in 0 1 2; do
    if ((10#${have[i]:-0} > 10#${want[i]:-0})); then return 0; fi
    if ((10#${have[i]:-0} < 10#${want[i]:-0})); then return 1; fi
  done
}

# check_tool COMMAND RANGE SOURCE HINT [VERSION_COMMAND...]: COMMAND is on PATH
# and, when RANGE (">=X.Y.Z", from SOURCE) is set, VERSION_COMMAND reports at
# least that version
check_tool() {
  local name=$1 range=$2 source=$3 hint=$4
  shift 4
  local output minimum version
  if ! command -v "$name" >/dev/null 2>&1; then
    problem "$name not found; install it: $hint"
    return
  fi
  [[ -n $range ]] || return 0
  if [[ ! $range =~ ^\>=[[:space:]]*([0-9]+(\.[0-9]+)*)$ ]]; then
    problem "can't read the $name version \"$range\" in $source (only \">=X.Y.Z\" is supported)"
    return
  fi
  minimum=${BASH_REMATCH[1]}
  if ! output=$("$@" 2>&1); then
    problem "\`$*\` failed: $output"
    return
  fi
  if [[ ! $output =~ ([0-9]+(\.[0-9]+)+) ]]; then
    problem "can't read the version of $name from \`$*\`: $output"
    return
  fi
  version=${BASH_REMATCH[1]}
  if ! version_at_least "$version" "$minimum"; then
    problem "$name $version is too old: $source needs $range; upgrade it: $hint"
  fi
}

# engine NAME: gh-pages/package.json's engines.NAME, empty if unset
engine() {
  node -p "require(process.argv[1]).engines?.[process.argv[2]] ?? ''" \
    "$ROOT_DIR/$PACKAGE_JSON" "$1"
}

check_python() {
  check_tool uv \
    "$(sed -n 's/^required-version = "\(.*\)"$/\1/p' "$ROOT_DIR/$PYPROJECT_TOML")" \
    "$PYPROJECT_TOML" \
    "https://docs.astral.sh/uv/getting-started/installation/ (macOS: brew install uv)" \
    uv --version
}

check_node() {
  check_tool git-lfs "" "" \
    "https://git-lfs.com (macOS: brew install git-lfs), then git lfs install"
  check_tool node "$(command -v node >/dev/null 2>&1 && engine node)" \
    "$PACKAGE_JSON" "https://nodejs.org (macOS: brew install node)" \
    node --version
  # pnpm's own minimum is read with Node.js, so without it only its presence
  check_tool pnpm "$(command -v node >/dev/null 2>&1 && engine pnpm)" \
    "$PACKAGE_JSON" "https://pnpm.io/installation (macOS: brew install pnpm)" \
    pnpm --version
}

if (($# == 0)); then
  echo "usage: $0 python|node..." >&2
  exit 2
fi

# Both stages: the Makefile reads the build date and the source files from git
check_tool git "" "" "https://git-scm.com (macOS: xcode-select --install)"
for group in "$@"; do
  case $group in
    python) check_python ;;
    node) check_node ;;
    *)
      echo "check-deps: unknown group \"$group\" (python, node)" >&2
      exit 2
      ;;
  esac
done

if ((problems > 0)); then
  exit 1
fi
