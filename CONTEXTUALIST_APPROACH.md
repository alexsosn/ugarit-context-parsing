# Texts in Place: The Contextualist Approach to the Ugaritic Archives

Duncan Coe Burns's dissertation, *Contents, Texts and Contexts: A Contextualist
Approach to the Ugaritic Texts and Their Cultic Vocabulary*, proposes that
Ugaritic texts should be read not as a collection of isolated works, but as
objects found in particular buildings, rooms, and excavation points. Its central
claim is simple: a tablet's findspot is not secondary metadata appended to the
text. It is part of the evidence and potentially part of the text's meaning.

## The Approach

Burns begins by criticizing three habits in Ugaritic scholarship: privileging
texts over archaeological evidence, concentrating on sources already classified
as "religious" or "literary," and reducing diverse evidence to a single coherent
picture of Ugaritic religion. The first habit is especially problematic. A
traditional reading may transliterate, translate, and compare a tablet with
similar texts while almost completely detaching it from the place where it was
found.

The contextualist approach restores this material dimension. Its starting
hypothesis is that the placement of tablets in an ancient archive was at least
partly deliberate: the physical grouping of texts may express an intellectual
classification by content or function. The proximity of tablets, their presence
in the same room, and differences between archives may therefore help us
understand individual words and documents, as well as the people and institutions
that used them.

The method proceeds in five stages:

1. Select a starting corpus (*prime texts*) by findspot rather than by a modern
   genre label. In the dissertation, these are texts from the "House of the High
   Priest" (GP) and the "House of the Hurrian Priest" (PH).
2. Identify the units to be studied within them (*prime content*). To test the
   method, Burns uses cultic vocabulary: divine, personal, and geographical
   names; cultic jargon; cultic commodities, locations, times and events,
   personnel, and actions.
3. Find every occurrence of that vocabulary in the rest of the Ugaritic corpus.
   The resulting *derived texts* are included because of a specific lexical link,
   not because of a pre-existing genre classification.
4. "Recontextualize" each occurrence by joining its text and line references to
   its locus, room, excavation point, depth, and the reliability of its recorded
   location.
5. Compare the distribution at lexical, textual, intertextual, and spatial
   levels. Shared vocabulary can reveal connections between archives, while
   exclusive vocabulary may indicate specialization.

This is not an attempt to replace philology with an excavation map. Translation
and the analysis of formulas, genre, and textual structure remain essential.
Archaeological records are not treated as infallible either: they are incomplete,
sometimes contradictory, and the tablets' original arrangement may have been
disturbed. The method brings together two imperfect bodies of evidence and
requires uncertainty to be recorded explicitly.

## Why the Annotation Matters

The database is valuable for more than its inventory of cultic words. Its
fundamental unit is the relationship "lexeme - place in a text - findspot."
Without that relationship, it is impossible to test the dissertation's central
question: whether the distribution of terms forms meaningful spatial patterns.

The annotation matters because it:

- preserves the path from interpretation back to evidence by recording the KTU
  number, line, and excavation data for every item;
- retains ambiguity by distinguishing homographs, probable cultic usage, usage
  without a securely identified cultic function, and disputed locations;
- permits GP and PH to be compared across the complete body of shared and
  exclusive vocabulary rather than through a few prominent texts;
- includes administrative lists and other documents that genre-based selection
  can easily marginalize as "non-religious";
- turns conclusions into reproducible queries: attestations can be recounted,
  classification rules revised, or new findspot evidence introduced to see
  whether the pattern persists.

This structure keeps together three dimensions that are normally dispersed
across different publications: word, document, and archaeological context.

## Why These Scripts Exist

The dissertation's appendix survives as 45 PDF tables organized into nine
thematic workbooks with five worksheets each. This is readable by a person, but
awkward for reproducible analysis: the tables are difficult to combine, search,
filter, and validate automatically. The legacy transliteration font creates an
additional problem because text extracted from the PDFs contains characters that
do not correspond to the intended Unicode symbols.

The [`scripts/parse_workbooks_to_csv.py`](scripts/parse_workbooks_to_csv.py)
script turns this printed representation back into structured rows. It:

- reconstructs the nine original columns and adds the source page, section, and
  root group;
- expands merged cells so that each row is self-contained;
- rejoins wrapped cell contents and discards only repeated headers and page
  numbers;
- converts the extracted legacy Ugaritic transliteration to standard Unicode;
- repairs the effects of an erroneous global `pn → P.N.` replacement: it
  restores `pn` inside Ugaritic words (`ṣP.N. → ṣpn`, `ḫrP.N.t → ḫrpnt`) and
  restores the Northern Palace findspot code `PN`, while leaving genuine
  personal-name annotations such as `(P.N.)` and `Broken P.N.?` unchanged;
- preserves the KTU number, line references, locus, room, point, depth,
  disputed-location flag, and comments.

The script therefore does not "prove" Burns's hypothesis or replace philological
classification. It makes the empirical basis of the method machine-readable and
the workflow reproducible. A researcher can generate the same tables from
lawfully obtained source PDFs, inspect the transformation, and then construct
their own searches, summaries, maps, and network models.

The generated CSV files are a derivative representation of material licensed
under CC BY-NC-ND 2.5. They are therefore not published in this repository and
remain local-only. The public repository contains the transformation code, schema
documentation, and rules that allow researchers to process source files they have
obtained themselves.

## Source

Duncan Coe Burns, *Contents, Texts and Contexts: A Contextualist Approach to the
Ugaritic Texts and Their Cultic Vocabulary*, PhD dissertation, University of
Sheffield. See especially Chapters 2-5 and the conclusion.
