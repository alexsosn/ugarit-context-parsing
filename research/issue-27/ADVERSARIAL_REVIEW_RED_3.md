# Third adversarial review RED: Burns TF module (#27)

Reviewed exact GREEN head: `df967fed4b61247cf3a65b9e37e769bf079f714a`.

All Python, installed-package, Agora, pinned Context-Fabric, and exact reviewed-CUC composition gates are green. The fresh frozen-head review found one remaining class of local consistency failures that the public writer can and should reject without access to the original Burns source or CUC index.

## Finding — report and authoritative module can disagree while each passes its own checks

`write_burns_module()` now validates authoritative placement/copies, projections, exact metadata, report source-record partition, selected/touched/anchor counts, and CUC identity. However a manually assembled `(module, report)` pair can still pass when:

1. `report.counts.annotations` disagrees with the embedded alignment annotation inventory;
2. the embedded alignment report assigns a selected occurrence to different anchor nodes than the authoritative module carrying the same stable `(annotation_id, occurrence_id)`;
3. authoritative node payload copies are mutually identical but their embedded `source_records` content differs from the top-level report `source_records` object with the same stable `record_id`.

Publishing any of these pairs would make `burns_annotations` and `burns-module-report.json` disagree about the same stable scholarly entities.

## Required local validation

Before Fabric construction:

- require module report annotation count and alignment-report annotation count to equal the actual embedded annotation inventory;
- recompute annotation disposition counts from embedded alignment annotations and require both report count summaries to agree;
- collect every selected occurrence from the embedded alignment report and require its stable ID set, anchor kind, and ordered anchor tuple to equal the authoritative module occurrence inventory;
- require every authoritative payload's ordered `record_ids` / `source_records` to match the top-level full source-record inventory exactly by stable record ID;
- require shared annotation fields exposed in a node payload (worksheet/workbook/section/root/headword/KTU/reference and semantic taxonomy) to agree with each referenced full source record.

This is self-consistency validation only. It does not attempt to prove arbitrary hand-built data is scholarly-correct against CUC; that remains the job of `build_burns_module()` and #26.

## Preserved RED

Before production changes, add synthetic tests proving the writer rejects before Fabric construction:

- forged module annotation count;
- forged alignment-report selected anchor for an otherwise valid occurrence;
- identically forged source-row content in every node copy while the top-level report retains the original row.

After GREEN, rerun every exact-head gate and restart the frozen-head adversarial review.