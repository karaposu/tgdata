# Revision 8 product verification

PASS. See ../verification.md for counts, commands, limits and evidence. All source
hashes remained unchanged during verification. Product files match the prebuild;
the product-only PR tree matches all111 tested sources and the complete product diff.
No test failure or behavioral correction occurred. Logs use synthetic fixtures.

The larger test48 outer allowance is240 seconds; native case deadlines are retained.
Timeout/kill is a failure, never a passing observation. The install probe runs the
actual generated command against installed modules and an installed permanent helper.
