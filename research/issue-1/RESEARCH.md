# Issue #1 research: CUC-aligned Text-Fabric materializers

## Question

How should this repository expose the Burns Workbooks as a local Text-Fabric materializer that Agora can discover/install and that the Context-Fabric/cfabric-mcp stack can load, while preserving the semantics and licensing boundary of the source?

## Repositories inspected

- `alexsosn/ugarit-context-parsing` (`master` at `d4d1b5c9967ab8549003b8fa2a672a6ed200abdf`)
- `DT-UCPH/cuc` (`main` at `ad69400f5446e1c8217af01659c7c10ab00c015b` during research)
- `alexsosn/Agora` (`main`; materializer contract/installer and Context-Fabric registry)
- `alexsosn/Pseudepigrapha-TF` (reference third-party Agora materializer)

## Current Burns source model

`parse_workbooks_to_csv.py` already performs the source-sensitive work:

- 45 worksheet PDFs are parsed into one CSV per worksheet;
- merged cells are forward-filled so each output row stands alone;
- wrapped cells and section/root grouping are preserved;
- legacy-font Ugaritic transliteration is repaired to Unicode;
- known source slips are corrected explicitly;
- every emitted row carries `source_page`, `section`, `root`, `headword`, `ktu`, `references`, `locus`, `room`, `point`, `depth`, `disputed`, and `comments`.

The generated CSV corpus is 13,857 rows. It is deliberately not committed because the Burns/White Rose source is CC BY-NC-ND 2.5 and the CSV is a derived reformatting.

The Appendix parser has a different 11-column KTU catalogue model (`ktu`, `rs_number`, `genre`, findspot fields, bibliography page references, comments). Combining it with Workbook rows would produce an artificial schema, so Appendix materialization is deferred to a separate design.

## CUC interoperability surface

The current CUC Text-Fabric corpus uses:

- slot type: `sign`;
- non-slot types including `word`, `column`, `line`, `tablet`;
- section hierarchy: `tablet,column,line`;
- `tablet` feature values such as `KTU 1.14`;
- `g_cons` as the consonantal transliteration of a CUC word;
- `language` for language identity;
- diplomatic/editorial sign features such as `sign`, `usign`, `emen`, `cert`, `cont`, `alt`, and trailers.

Burns Workbooks do not contain a diplomatic sign stream, word segmentation, columns, or line nodes equivalent to CUC. Reconstructing CUC `sign`/`word` nodes from Burns headwords or references would fabricate textual structure and would make downstream queries misleading.

Therefore “CUC-compatible” in this converter means **interoperable identifiers and conventions where the underlying semantics match**, not graph-shape identity:

1. preserve the literal Burns `ktu` value;
2. expose a normalized `cuc_tablet` feature using CUC's `KTU <number>` spelling for real KTU identifiers;
3. expose `language=Ugaritic` on Workbook record slots;
4. preserve the parser's Unicode Ugaritic transliteration unchanged;
5. do not create CUC `sign`, `word`, `line`, or `column` nodes from data that do not encode them;
6. identify the generated dataset as Burns Workbooks, not as Copenhagen Ugaritic Corpus.

This gives consumers a stable join key to the CUC tablet namespace without collapsing two different datasets into one ontology.

## Text-Fabric graph design

### Slot model

One Workbook CSV row becomes one TF slot of type `record`.

Reasons:

- the row is the smallest lossless unit produced by the source parser;
- every source field can be represented directly as a node feature on that slot;
- row order preserves the worksheet's reading/table order;
- no synthetic tokenization is required.

### Structural nodes

Create non-slot nodes in contiguous type blocks:

- `worksheet`: one per source CSV/PDF, spanning all records from that worksheet;
- `section`: one per contiguous section occurrence inside a worksheet;
- `entry`: one per contiguous `(section, root, headword)` occurrence, spanning its rows.

Contiguous per-type node-id blocks are deliberate: Text-Fabric derives type ranges from `otype`, and the reference Pseudepigrapha converter already guards this invariant.

The Text-Fabric section hierarchy is `worksheet,section,entry`. The corresponding section features are `worksheet`, `section`, and `entry`. Empty section/root/headword values must receive deterministic technical labels for section navigation while the literal source fields remain separately preserved.

### Record features

Preserve all Workbook CSV columns verbatim, with the source KTU value named `ktu` and a separate normalized join feature:

- `source_page` (int)
- `section_source`
- `root`
- `headword`
- `ktu`
- `cuc_tablet`
- `references`
- `locus`
- `room`
- `point`
- `depth`
- `disputed`
- `comments`
- `language` = `Ugaritic`
- `source_file` = relative CSV/PDF path, never an absolute user path
- `source_row` = 1-based data-row index within the generated/loaded CSV

Structural node labels use separate features (`worksheet`, `section`, `entry`) so source strings are not overloaded with navigation semantics.

### Determinism

- source files sorted by POSIX relative path;
- rows preserved in source order;
- structural occurrences numbered by first appearance;
- no timestamps in TF feature metadata or conversion report;
- no absolute local paths in features/report;
- JSON report written with stable key ordering;
- identical source trees produce byte-equivalent semantic payloads (Text-Fabric may add its own generated support metadata, so tests compare graph/report semantics and stable source hashes rather than wall-clock metadata).

## Source validation and failure policy

CSV input is fail-closed:

- at least one `*.csv` recursively;
- every selected CSV must have the exact Workbook header set;
- unexpected/missing columns are an error rather than silently ignored;
- `source_page` must be an integer >= 1;
- blank data rows are rejected/ignored only if they are truly empty across all columns (decision encoded in tests);
- symlinks are disallowed by the Agora manifest and the converter must not follow them independently.

PDF input is also fail-closed:

- at least one `*/*.pdf`/recursive PDF found;
- each PDF is passed through the existing Workbook parser;
- generated rows feed the same graph builder used by CSV conversion;
- converter execution itself performs no network access.

The existing source downloader remains a user-facing convenience outside the materializer sandbox. Agora materialization uses only `user-local` acquisition because the White Rose source is not an immutable Git input and the materializer execution declares `network: deny`.

## Agora materializer contract

Agora materializer-plugin schema v1 accepts directory inputs only and `required_globs` are conjunctive validation requirements; it has no input alternatives. A single manifest entry cannot safely mean “CSV or PDF”.

Expose two materializers with the same output contract:

- `burns-workbooks-csv-text-fabric`
  - user-local directory
  - required glob `**/*.csv`
  - Python module execution with `--input-format csv`
- `burns-workbooks-pdf-text-fabric`
  - user-local directory
  - required glob matching Workbook PDFs
  - Python module execution with `--input-format pdf`

Both:

- execute the installed project as a Python module;
- deny network access;
- emit `otype.tf`, `oslots.tf`, `otext.tf`, and `conversion-report.json`;
- carry no `{source_revision}` argument because user-local input has no Git revision identity.

Agora's installer requires an ordinary Python project and explicit code-execution approval. The current repo's `pyproject.toml` (`requires-python >=3.14`, no build backend, placeholder metadata) is not suitable. The converter should follow the reference materializer baseline:

- normal build backend;
- Python >=3.10 (matching the existing parsers and Agora CI runtimes);
- `text-fabric>=13.1,<14`;
- `pdfplumber>=0.11` for PDF materialization;
- keep the Intel-macOS cryptography compatibility bound already documented by the parser.

## Transactionality

Agora already publishes the final artifact transactionally at its host boundary, but the converter should also avoid leaving a semantically half-written local output when run standalone.

Selected implementation pattern, based on Pseudepigrapha-TF:

1. parse/validate the entire source;
2. build and validate an in-memory TF graph;
3. build a semantic conversion report and require status `ok`;
4. serialize TF into a sibling temporary directory using `tf.fabric.Fabric.save`;
5. write the report into the staged directory;
6. replace the target TF files/report only after the staged save succeeds;
7. remove stale `.tf` files from prior converter versions during successful publication.

## Conversion report

The report must provide enough evidence for Agora/integration smoke tests without embedding licensed source rows:

- schema/converter version;
- source format (`csv`/`pdf`);
- deterministic source-tree SHA-256 over relative paths + file bytes;
- source file count;
- record count;
- worksheet/section/entry counts;
- count of real KTU rows and normalized `cuc_tablet` values;
- count of `Not attested` rows;
- node/slot/oslots counts;
- checks: exact row preservation, source feature coverage, graph validity, CUC identifier normalization;
- status and warnings/errors.

No source row bodies are copied into the report.

## License/provenance policy

Generated TF is derived from the Burns source and must retain the CC BY-NC-ND 2.5 provenance warning. The repository's software license must be stated separately from source/data rights. Tests use only synthetic data authored for the test suite; no real Burns CSV/TF fixture is committed.

The converter metadata must not copy CUC's CC BY-NC 4.0 licence onto Burns-derived data. CUC is a compatibility/reference corpus, not the licensing source for this artifact.

## Context-Fabric / cfabric-mcp boundary

Agora already registers the public CUC repository as resource `cuc` for ordinary repository acquisition. This new materializer is a different path for locally derived Burns data.

Current Agora architecture can discover/fetch/install a third-party materializer and execute an explicit manifest under the materialization host. Automatic resource → installed materializer → Context-Fabric consumer composition remains deferred in Agora's own architecture. This issue should therefore deliver:

- a standalone loadable TF artifact;
- an Agora-compatible/installable materializer manifest;
- enough deterministic output metadata for Agora registration and install/materialization smoke tests.

The follow-up Agora change can register/pin this repository and verify installation/materialization. It should not implement hidden automatic composition as part of the upstream converter.

## Alternatives rejected

### Emit CUC-shaped sign slots

Rejected because the Burns Workbooks do not encode the CUC diplomatic text layer. It would turn contextual headword/reference data into invented textual structure.

### One mixed CSV/PDF materializer entry

Rejected because Agora v1 has no alternative-input contract; weakening `required_globs` would make source validation ambiguous.

### Mix Appendix rows into the Workbook TF graph

Rejected because Appendix and Workbooks have different source semantics and schemas. A separate materializer can later join on the same normalized KTU namespace.

### Download White Rose sources from inside materialization

Rejected because Agora's sandboxed materializer execution is network-denied, local licensed input should remain an explicit user choice, and the existing downloader already covers standalone acquisition.

## Research gate outcome

Proceed with a Workbooks-only, row-slot Text-Fabric converter; two user-local Agora materializer IDs; CUC alignment through normalized KTU identity and language/transliteration conventions; synthetic-only test fixtures; official Text-Fabric serialization and load smoke; separate Agora registration after the upstream converter passes its own TDD/review gate.
