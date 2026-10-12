# Authoritative syllabus source and initial mapping

The project owner selected the Biology syllabus on JAMB's website as the curriculum authority. Third-party syllabus summaries are not the authority.

- Publisher: Joint Admissions and Matriculation Board (JAMB).
- Entry point: https://ibass.jamb.gov.ng/e-syllabus
- Official document address: https://ibass.jamb.gov.ng/assets/uploads/Biology.pdf
- Mapping established from official-domain indexed text during this session. Direct retrieval of the PDF address returned the site's JavaScript HTML shell; no local PDF, checksum, edition/year, or page number is claimed verified.
- Refresh the source before pilot publication; record a dated PDF/version or checksum when a working download is available. Do not attach an exam-year label based on third-party websites.

## Initial demo mapping

| Item | Mapping |
| --- | --- |
| Subject | Biology |
| Section | A — Variety of organisms |
| Topic | 1 — Living organisms |
| Content locator | 1(b), cell structure/functions |
| Primary objective | iv — compare plant and animal cell structure |

Official objective excerpt: “compare and contrast the structure of plant and animal cells.”

Both demo units address this one objective. Identifying structures and explaining selected functions support that comparison; the samples do not establish full coverage of this topic or the syllabus. The other two pilot topics remain undecided.

## Applying the source

New seed drafts use the official topic/objective. To align untouched legacy demo metadata in an existing local database:

    .\.venv\Scripts\python.exe manage.py seed_demo --align-syllabus

This updates only the exact old generated mapping on unreviewed drafts without reference/review notes or checked confirmations. It preserves card/question content and never publishes. Normal seed_demo remains non-overwriting. Edited, reviewed, or published records are skipped; manually review their mapping, or create a replacement draft for published history.

A syllabus defines what to learn. It is not a teaching reference proving every factual claim or media script. Keep scientific source references and all six human-review confirmations required for publication. Syllabus alignment does not approve content automatically.
