#!/usr/bin/env bash
set -euo pipefail

UA="Mozilla/5.0 (docsiphon/0.1)"
BASE="https://developerdocs.instructure.com"

print_header() {
  echo "==== $1 ===="
}

print_header "Check Markdown twin for /services/canvas"
curl -I -L -A "$UA" "$BASE/services/canvas.md"

echo
print_header "Check Markdown twin for a subpage"
curl -I -L -A "$UA" "$BASE/services/canvas/outcomes/file.outcomes_csv.md"

echo
print_header "robots.txt and sitemap.xml"
curl -s -A "$UA" "$BASE/robots.txt"

echo
curl -s -A "$UA" "$BASE/sitemap.xml"

echo
print_header "Count URLs in sitemap-pages.xml"
curl -s -A "$UA" "$BASE/sitemap-pages.xml" | grep -c '<loc>'
