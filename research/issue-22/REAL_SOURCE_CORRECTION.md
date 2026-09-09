# Issue #22 real-source evidence correction

Parent research PR #25 has merged. Its independent adversarial audit superseded the earlier global-dedup grouping numbers used as scale evidence in the initial #22 research.

The checksum-pinned 45 Workbooks PDFs contain:

- **13,857** parser rows;
- **10,419** contiguous authored semantic groups under the corrected source grouping contract;
- **4** scholarly keys that occur in two non-contiguous authored runs and would be wrongly merged by global value deduplication.

Corrected semantic-status counts under contiguous grouping are:

- `positive_fixed`: **2,675**;
- `probable_cultic`: **1,018**;
- `no_secure_cultic`: **2,091**;
- `homograph_excluded`: **4,635**.

This evidence does not turn aggregate counts into product golden files. #22 must derive annotations from source provenance and explicit row continuity, not try to force a total of 10,419. The count is a regression/audit expectation for the currently checksum-pinned real source and parser only.

The earlier 10,415 grouping in `RESEARCH.md` remains useful as the documented failure mode of global deduplication, not as a production semantic count.

The production rule remains:

- equal worksheet/textual key + consecutive source rows may form one annotation;
- a source-row gap splits the annotation;
- a later identical key after another authored group is distinct;
- backwards/non-monotonic source rows in the same worksheet fail closed;
- every raw source record remains losslessly represented regardless of semantic grouping.
