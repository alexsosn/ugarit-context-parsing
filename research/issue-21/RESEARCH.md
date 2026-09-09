# Research: Burns as a CUC-aligned Text-Fabric annotation module (#21)

## Correction of the product model

Burns does **not** own the Ugaritic text. The Copenhagen Ugaritic Corpus (CUC) owns the diplomatic text and the Text-Fabric warp. Burns supplies scholarly classifications and contextual/topographical metadata about occurrences in that text.

The target therefore follows the ETCBC/BHSA module pattern: Burns is an optional Text-Fabric module (wefts around CUC's warp), not a second corpus. The current standalone `record`-slot graph in `src/ugarit_context_parsing/graph.py` is provisional scaffolding and must not define the product model.

A Burns module must not emit its own `otype.tf` or `oslots.tf` and must not duplicate CUC text.

## Primary sources reviewed

The semantic model below is based on Burns's thesis itself, especially:

- vol. I, ch. 3, pp. 136-146: contextualist framework;
- vol. I, ch. 4, pp. 147-183: definition, selection, and identification of cultic vocabulary;
- vol. I, ch. 5, pp. 184-200: database construction, workbook/worksheet/section semantics;
- vol. I, ch. 6: how the database is interpreted and what distinctions Burns preserves;
- vol. II, Annexe 1, pp. 1-5: visual classification rules, unclassified terms, compounds, and uncertain classifications;
- the distributed Workbooks and current extraction code only as implementation evidence, not as the authority for semantics.

Source: Duncan Coe Burns, *Contents, Texts and Contexts: A Contextualist Approach to the Ugaritic Texts and their Cultic Vocabulary* (University of Sheffield, 2003), White Rose eTheses 15038.

## What Burns is actually annotating

Burns defines cultic vocabulary functionally as words or phrases that prescribe or describe human service of deities: what is done, by whom, when, where, for which deity, and with what. The project deliberately focuses on tangible expressions of cult/ritual rather than theological belief as such.

Nine workbook categories result:

1. Divine Names (DN)
2. Personal Names (PN)
3. Geographical Names (GN)
4. Cultic Jargon
5. Cultic Commodities
6. Cultic Locations
7. Cultic Times and Events
8. Cultic Personnel
9. Cultic Actions

These are **not nine equivalent entity types**.

### Workbooks I-IV: mono-referential

DN, PN, GN, and Cultic Jargon are treated as fixed-reference classifications after homographic alternatives are excluded.

- DN: proper names of individual deities or divine collectives. Epithets/appellatives count only when individualised as a particular deity/collective. Burns explicitly excludes theophoric components inside PNs from the DN survey: the PN's primary reference is the person, so the embedded divine element is incidental for this study.
- PN: names of persons, commonly identifiable from administrative/list/letter formulae, patronymics (`X bn Y`), family/fratronymic markers, and associated gentilics.
- GN: geographical names, identified through gentilics, locational syntax, and geographical/topographical terms as well as established usage across text types.
- Cultic Jargon: technical ritual nomenclature treated as a fixed semantic reference for databasing despite greater interpretive dependence than proper names. It includes offering/rite terminology, religio-magical procedure terms, abstract ritual states/results, and some opaque but apparently cultic technical vocabulary.

For these workbooks:

- Section alpha = the intended DN/PN/GN/jargon reading;
- Section beta = graphologically identical **homographic forms with another meaning**.

**Implication:** beta occurrences are evidence about a searched string, but they are not positive Burns category annotations. They belong in alignment/provenance output and, if useful, an explicit negative/homograph disposition; they must not set a positive `burns_divine_name`, `burns_personal_name`, etc. feature.

### Workbooks V-IX: multi-referential

Commodities, locations, times/events, personnel, and actions are contextual **functions of an occurrence**, not stable lexical identities. The same lexeme can be cultic in one passage and non-cultic in another.

Burns therefore divides Section alpha:

- alpha1 = probable cultic function;
- alpha2 = same lexeme/phrase, but no secure cultic application can be established.

Homographic alternative meanings remain a separate problem and must not be conflated with alpha2. Alpha2 means uncertain/non-secure *function of the intended lexeme*, not a different homographic lexeme.

Examples from Burns's identification discussion reinforce the distinction:

- a commodity can be cultic when supported by ritual syntax or internal cultic evidence, yet the same commodity in an administrative text is deliberately not assigned cultic significance when no internal evidence supports that reading;
- `mlk` can denote cultic personnel in ritual contexts but has abundant non-cultic royal/economic uses;
- action verbs are admitted only when their contextual use is cultic; Burns explicitly compares cultic and non-cultic applications rather than treating the verb lemma as inherently ritual;
- cultic locations/times likewise depend on syntactic and textual function, not string identity alone.

**Implication:** convenience features for V-IX must be occurrence-level and must distinguish at least `probable_cultic` from `no_secure_cultic_application`. A lexicon-wide lemma flag would materially misrepresent Burns.

## Prime vs derived content is provenance, not a semantic category collapse

The nine workbooks each contain five worksheets:

1. prime content found in GP;
2. prime content found in PH;
3. other locations of prime content found in both GP and PH;
4. other locations of prime content found only in GP;
5. other locations of prime content found only in PH.

Worksheets 1-2 are primary in the database hierarchy. Entries there trigger the corpus-wide search. Worksheets 3-5 are secondary/derived and can contain only terms first found in worksheet 1 and/or 2.

Worksheet 3 holds derived occurrences of vocabulary common to GP and PH; worksheet 4 holds derived occurrences initiated only by GP; worksheet 5 those initiated only by PH.

**Implication:** worksheet number/role and prime-vs-derived provenance must survive in the module, but a derived occurrence is not semantically weaker merely because it is derived. Its cultic/homograph/function classification is determined separately.

## Overlap is first-class data

Burns explicitly allows compound forms whose components participate in different workbook classifications. In Annexe 1 he uses `bt bʿl ugrt` as the example:

- `bʿl` is a DN;
- `ugrt` is a GN;
- the whole phrase `bt bʿl ugrt` is a cultic location.

Thus Burns annotations can be nested/overlapping spans. A single CUC word may participate in multiple annotations, and a multi-word Burns annotation may overlap shorter annotations of other categories.

**Implication:** scalar one-category-per-node features are insufficient as the lossless representation. The module needs stable annotation identities plus a lossless multi-valued occurrence representation, with query-friendly derived convenience features. The exact representation remains a design decision after real alignment statistics are collected.

## Unclassified and uncertain material

Annexe 1 states:

- ordinary unhighlighted terms are *unclassified* and do not enter the cultic-vocabulary database;
- compound forms preserve all component classifications;
- where classification is ambiguous, the displayed text shows Burns's preferred interpretation, while alternate interpretations are documented at the relevant database entry/comments.

**Implications:**

1. Do not turn every token in prime texts into a Burns annotation. Unclassified material is CUC text only.
2. Do not silently discard alternate classifications/comments. Preferred and alternative readings must remain distinguishable in normalized source records/provenance.
3. `uncertain` is not the same thing as `homograph` or alpha2. The normalized model needs separate axes for lexical identity, functional/cultic status, and interpretive certainty/alternatives.

## What should and should not become TF features

### Positive queryable annotation candidates

Only after exact alignment to CUC:

- Burns category on the **specific occurrence/span**;
- normalized Burns headword/root where Burns actually assigns it;
- cultic-function status (`positive/fixed`, `probable_cultic`, `no_secure_cultic_application`) rather than an undifferentiated boolean;
- workbook identity and semantic category;
- worksheet number/role and prime/derived provenance;
- GP/PH/common/exclusive source relationship where encoded by workbook structure;
- section code plus its semantic interpretation;
- Burns source provenance (workbook/worksheet/page/entry/row or equivalent stable source locator);
- contextual/topographical metadata from the same Burns database record when it applies to the aligned textual occurrence;
- disputed/uncertain/alternative-reading indicators where Burns records them.

### Not positive category features

- beta-section homographs with a different lexical meaning;
- unclassified words in Annexe 1;
- theophoric DN components inside PNs merely because a deity name string occurs there (Burns explicitly excluded these from the DN survey);
- alpha2 occurrences as if they were confirmed cultic uses;
- commodities/personnel/actions/etc. inferred cultic solely from lemma identity when Burns withheld cultic interpretation in that context;
- Burns rows whose cited KTU text is absent from the pinned CUC base: retain them in the alignment report, but do not fabricate CUC anchors;
- any inferred sign/word/line structure that CUC does not supply.

## CUC base-corpus contract

CUC 0.2.8 currently defines:

- `sign` slots: nodes 1-146017;
- `column`: 146018-146351;
- `line`: 146352-153967;
- `tablet`: 153968-154246;
- `word`: 154247-182016.

Its section types/features are `tablet,column,line`; `tablet.tf` supplies canonical labels such as `KTU 1.14`, `column.tf` supplies column identifiers, `line.tf` line numbers, and `g_cons.tf` consonantal word forms.

Burns should align to existing CUC tablet/column/line/word nodes. It must never copy these warp files into its module.

The module must bind itself to an exact/reviewed CUC compatibility target or warp fingerprint because TF modules rely on stable node numbering.

## BHSA/ETCBC module reference

The ETCBC ecosystem confirms the intended architecture:

- `ETCBC/phono` ships node features (`phono.tf`, `phono_trailer.tf`) plus `otext@phono.tf` metadata with `@coreData=BHSA`; no warp files.
- `ETCBC/valence` ships multiple node features attached to existing BHSA nodes.
- `ETCBC/parallels` demonstrates that a module can also ship valued edge features between existing base-corpus nodes (`crossref.tf`).

Therefore Burns has two legitimate TF primitives without owning a warp:

1. node features on existing CUC nodes;
2. node-to-node edge features (optionally valued) between existing CUC nodes.

Whether rich Burns span multiplicity should use canonical structured node values, edge-assisted spans, or a combination must be decided from real alignment/multiplicity statistics before implementation.

## Parser implications

The existing PDF parser performs useful extraction work but currently flattens authored merged-cell hierarchy into self-contained CSV rows. That interchange remains useful, but the normalized Burns annotation model must reconstruct/preserve the semantic distinctions above instead of treating rows as corpus nodes.

Known parser issues that research must cover include the documented `Times and Events, Worksheet 1` wrapped headword tail that currently lands in `root`, plus all existing geometry fallback, merged-cell, wrapped-reference/comment, legacy-transliteration, ayin, PN-repair, and editorial-correction behavior.

## Alignment engine requirements

Every normalized Burns annotation must end in one explicit disposition:

- `aligned_word` / `aligned_words`;
- `aligned_line`;
- `aligned_tablet` when the source assertion is genuinely whole-text level;
- `ambiguous_multiple_matches`;
- `reference_parse_ambiguous`;
- `headword_mismatch`;
- `out_of_cuc`;
- `homograph_excluded`;
- `unclassified_excluded` where relevant;
- `non_textual` / no CUC anchor where the source information is contextual metadata without an occurrence target.

No heuristic mismatch may silently become a successful alignment.

## Open research questions before PLAN.md

1. Enumerate the real grammar of Burns's `references` cells (single line, ranges, multiple references, columns, damaged/uncertain forms, `passim`, cross-references, etc.).
2. Quantify current CUC coverage of all Burns KTU references.
3. Measure word-level alignment success using CUC `g_cons` inside the parsed tablet/column/line targets.
4. Measure annotation multiplicity and overlap on CUC words/lines.
5. Inspect Burns Column I/comments systematically for alternate classifications that the current CSV parser may not make structurally explicit.
6. Decide the lossless TF representation for overlapping/multi-valued annotations after (3)-(4), rather than choosing it from synthetic examples.
7. Decide whether Appendix findspot data is independent contextual metadata for CUC tablets or redundant with workbook-expanded rows; do not merge it blindly.
8. Define a compatibility fingerprint for the exact CUC warp and tests proving Burns loading leaves CUC node counts/warp unchanged.

Production TF changes and Agora work remain blocked until these questions are answered and a concrete PLAN.md is committed.
