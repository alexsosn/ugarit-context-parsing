# The contextualist approach to the Ugaritic archives

Duncan Coe Burns's 2003 dissertation, *Contents, Texts and Contexts: A
Contextualist Approach to the Ugaritic Texts and Their Cultic Vocabulary*,
argues that Ugaritic texts should be read as objects recovered from particular
buildings, rooms, and excavation points, rather than as a collection of isolated
works. A tablet's findspot is itself evidence, and may be part of what the text
means.

## The approach

Burns criticizes three habits in Ugaritic scholarship: privileging texts over
archaeological evidence, concentrating on sources already classified as
"religious" or "literary," and reducing diverse evidence to a single coherent
picture of Ugaritic religion. The first is the most consequential of the three.
A traditional reading may transliterate a tablet, translate it, and compare it
with similar texts while barely registering where it was found.

The contextualist approach puts that material dimension back. Its starting
hypothesis is that the placement of tablets in an archive was at least partly
deliberate, so that the physical grouping of texts may express a classification
by content or function. Proximity between tablets, their presence in the same
room, and differences between archives can then bear on how we read individual
words and documents, and on what we can say about the people and institutions
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

None of this replaces philology with an excavation map. Translation and the
analysis of formulas, genre, and textual structure remain essential. The
archaeological record gets no more deference: it is incomplete, sometimes
contradictory, and the tablets' original arrangement may have been disturbed.
The method combines two imperfect bodies of evidence and asks the researcher to
record uncertainty explicitly.

## Why the annotation matters

The database is worth more than its inventory of cultic words. Its basic unit is
the relationship "lexeme - place in a text - findspot," and without that
relationship there is no way to test the dissertation's central question:
whether the distribution of terms forms meaningful spatial patterns.

Recording it that way has consequences:

- Every item carries its KTU number, line, and excavation data, so an
  interpretation can always be walked back to the evidence under it.
- Ambiguity survives the encoding. The scheme separates homographs, probable
  cultic usage, usage with no securely identified cultic function, and disputed
  locations.
- GP and PH can be compared across the whole of their shared and exclusive
  vocabulary, not through a few prominent texts.
- Administrative lists and similar documents stay in the corpus, where selection
  by genre would have set them aside as "non-religious."
- Conclusions become queries that can be re-run: recount the attestations,
  revise a classification rule, or add new findspot evidence and see whether the
  pattern holds.

It also keeps word, document, and archaeological context in one place, where
publication normally splits them apart.

## Why these scripts exist

The dissertation's appendix survives as 45 PDF tables, organized into nine
thematic workbooks of five worksheets each. A person can read them. Software can
do little with them: the tables resist combining, searching, filtering, and
automatic validation. The legacy transliteration font adds a second problem,
since text extracted from the PDFs comes out as characters that do not match the
intended Unicode symbols.

The [`scripts/parse_workbooks_to_csv.py`](scripts/parse_workbooks_to_csv.py)
script turns the printed tables back into structured rows. It:

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

The script proves nothing about Burns's hypothesis and does not replace
philological classification. It makes the method's empirical basis machine
readable and the workflow repeatable. Given lawfully obtained source PDFs, a
researcher can regenerate the same tables, inspect the transformation, and build
their own searches, summaries, maps, and network models.

The generated CSV files are a derivative representation of material licensed
under CC BY-NC-ND 2.5, so this repository does not publish them; they stay
local. What it does publish is the transformation code, the schema
documentation, and the rules needed to process source files a researcher has
obtained independently.

## Source

Duncan Coe Burns, *Contents, Texts and Contexts: A Contextualist Approach to the
Ugaritic Texts and Their Cultic Vocabulary*, PhD dissertation, University of
Sheffield, 2003. See especially Chapters 2-5 and the conclusion.
