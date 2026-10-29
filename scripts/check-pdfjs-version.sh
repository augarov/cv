#!/usr/bin/env bash
# Checks that the installed pdfjs-dist, the library that public/pdfjs/build
# links to, is the version of the pdf.js viewer copied into public/pdfjs/web/
# (its viewer.mjs names it in a "pdfjsVersion = X.Y.Z" comment). Upgrading one
# without the other breaks the viewer; see .claude/skills/pdfjs-customization.
#
# Usage: scripts/check-pdfjs-version.sh PDFJS_DIST_PACKAGE_JSON VIEWER_MJS
# Runs with macOS's bash 3.2.
set -euo pipefail

if (($# != 2)); then
  echo "usage: $0 PDFJS_DIST_PACKAGE_JSON VIEWER_MJS" >&2
  exit 2
fi
package_json=$1
viewer=$2

fail() {
  echo "check-pdfjs-version: $*" >&2
  exit 1
}

[[ -f $package_json ]] || fail "$package_json not found; run make install-deps-node"
[[ -f $viewer ]] || fail "$viewer not found"

# Read as a file: require() would take a relative path for a module name
if ! library=$(node -e '
  try {
    const { version } = JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"));
    if (typeof version !== "string") throw new Error("no version field");
    console.log(version);
  } catch (error) {
    console.error(error.message);
    process.exit(1);
  }' "$package_json" 2>&1); then
  fail "can't read the version in $package_json: $library"
fi
viewer_version=$(sed -n '/pdfjsVersion = /{s/.*pdfjsVersion = \([^[:space:]]*\).*/\1/p;q;}' "$viewer")
[[ -n $viewer_version ]] || fail "no \"pdfjsVersion = X.Y.Z\" line in $viewer"

if [[ $library != "$viewer_version" ]]; then
  fail "pdfjs-dist $library doesn't match the viewer's pdf.js $viewer_version" \
    "($viewer); see .claude/skills/pdfjs-customization"
fi
