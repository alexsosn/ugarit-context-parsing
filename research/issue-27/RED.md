# Preserved RED: feature-only Burns TF module (#27)

RED head: `7425e12555fe6863b6e705213eadf0f7faf3ef78`

The branch contains research + plan + `tests/test_burns_tf_module.py`, while production `src/ugarit_context_parsing/module.py` does not exist.

Expected failure mode: the full suite reaches import of the new test module and fails only with `ModuleNotFoundError: No module named 'ugarit_context_parsing.module'`. Existing tests must remain healthy. No production implementation is permitted until this is attested by CI.
