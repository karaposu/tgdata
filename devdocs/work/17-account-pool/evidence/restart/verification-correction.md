# Verification collector correction

The first full run completed every suite and example with exit0. The collector
incorrectly marked test34/35/36 failed because it recognized only `Passed: N/N`.
Their actual output is `49 passed; 0 failed`, unittest `Ran35 tests ... OK`, and
`44 passed; 0 failed`. Added recognition of these actual runner formats; product
and test expectations are unchanged. Original full logs/collector result remain.
Re-run only those three suites with the corrected collector, then combine their
results with the already-passing complete run. No need to repeat unchanged suites.
