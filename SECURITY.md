# Security policy

## Supported versions

The latest GitHub Release is supported with security fixes.

## Reporting

Please use GitHub's private vulnerability reporting for `KanadeK/markerwalk`. Do not open a public
issue for path-containment bypasses, arbitrary file reads/writes, markup injection, dependency
compromise, or accidental disclosure of real survey data.

Include the affected version, operating system, minimal synthetic manifest, expected/actual result,
and whether an output file was created. Never include real cemetery records, credentials, or private
photos in the report.

## Security boundaries

MarkerWalk validates external JSON once, contains resolved input paths under the manifest
directory, escapes generated HTML/SVG, invokes no shell commands at runtime, performs no network
requests, and stores no credentials. Its geometric route is not a safety or accessibility claim.

