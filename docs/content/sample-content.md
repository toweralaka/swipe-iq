# Five humorous Biology sample units

Run from backend/:

    .\.venv\Scripts\python.exe manage.py seed_sample_content

The command creates five original AI-assisted text-based units, each with three cards and three four-choice questions with answer explanations. Existing content is preserved on reruns. They are additional sample drafts, not an expansion of the approved six-unit pilot scope; the reviewer may select/refine suitable units later.

| Concept | Memory aid |
| --- | --- |
| Cell membrane | Club Cell's bouncer manages entry and exit. |
| Plant cell wall | A compound fence provides support; it does not replace the gatekeeper. |
| Chloroplast | A solar chef makes sugars; not every plant cell has this kitchen. |
| Mitochondria | Cells need ATP, not a borrowed phone charger. |
| Nucleus | Head office stores instructions; ribosomes do the protein assembly. |

All remain UNREVIEWED drafts with review boxes unset, no attached media, and no publication. Analogies are explicitly separated from scientific explanations and common misconceptions are addressed. Reviewer must check scientific accuracy, humour, and audience suitability before publishing.

Curriculum: official JAMB Biology, Section A / topic 1(b), supporting cell identification/function/comparison objectives ii–iv. See [source provenance](syllabus-source.md). Candidate teaching reference: [OpenStax Biology 2e, 4.3](https://openstax.org/books/biology-2e/pages/4-3-eukaryotic-cells); not a claim of JAMB textbook endorsement or human review. Record checked teaching references in the admin during review.

Source data: backend/editorial/data/biology_samples.json. Text cards can later supply scripts or storyboards for separately prepared and reviewed media. This command does not generate image/audio/video files.
