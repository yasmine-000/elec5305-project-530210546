# Submission checklist

Source: the student-supplied **Project Submission Details** and marking rubric.
This is a planning checklist, not a declaration that the submission is complete.
The instructor's codec/STFT feedback defines the technical project direction;
the submission document defines the deliverables and assessment criteria.

## Required hand-in package

| Requirement | Current status | Remaining action |
| --- | --- | --- |
| Working code downloadable from GitHub | Initial implementation pushed; Python codec path tested, MATLAB analysis unexecuted | Run `run_project_tests` in MATLAB Online; fix failures; verify real speech reports and reproduction instructions |
| Written research report | Template supplied, no completed report | Literature analysis, actual experiments, results, interpretation, references, final document |
| Brief video showing code in action | Not recorded | Record actual execution and explain accomplishments and limitations |
| Upload report and video to Canvas | Not submitted | Student uploads both final artefacts |
| GitHub Site containing report and working code | Repository exists; website/Pages not prepared or published | Prepare the site with the final report, code download and reproduction instructions; configure/publish it |
| Clickable GitHub Site link in report | Pending site URL | Add the real, tested URL before final export |
| Video link in both report and GitHub Site | Pending video | Add accessible links and test them without the owner's login |
| Example results available with GitHub code | Synthetic demo generator only; no generated MATLAB examples | Add a small verified example report/figures with provenance and usage rights |

The exact wording asks for a **GitHub Site** as well as downloadable GitHub
code. Keep website publication as a distinct item; a repository alone should
not be assumed to satisfy the site requirement. GitHub Pages is a practical
implementation option, not a separately specified course platform.

## Report content

- [ ] One clearly identified, motivated research question, linked to relevant work.
- [ ] Literature review analyses key publications, not just a reference list:
  current understanding, candidate methods, their advantages/disadvantages,
  the selection rationale and concepts/unknowns learned during the project.
- [ ] Methods describe the **full intended approach**, why it can answer the
  question, reproducible materials/settings and newly learned tools/techniques.
- [ ] Clearly distinguish intended work from work actually completed.
- [ ] Results use reliable tests with sufficient coverage, clear figures/tables,
  captions and accompanying explanation. Unit-test success is software evidence,
  not evidence of comparative speech-codec quality.
- [ ] Discussion/conclusion states how far the question has been answered,
  explains successes/failures, relates findings to published work, anticipates
  criticism, identifies limitations and proposes specific further work.
- [ ] Include clear sections/subsections, a contents page and consistent citations.
- [ ] Identify borrowed code, models and other assistance; explain the student's
  actual contribution accurately. Check course policy before making declarations
  about permitted AI assistance. Do not claim assistant-generated code was
  independently authored or unrun tests were completed.
- [ ] Provide clickable site/code and video links; test the final exported report.

## Mark allocation

| Criterion | Weight |
| --- | ---: |
| Originality and personal contribution | 10% |
| Command of subject | 10% |
| Introduction | 5% |
| Literature review | 15% |
| Methodology | 15% |
| Results | 10% |
| Discussion/conclusion | 25% |
| Presentation, format and references | 10% |
| Total | 100% |

The rubric expects an existing relevant approach to be reproduced and a small
modification/change explored. It does not require a new neural codec or major
research breakthrough. A suitable planned experiment is **medium-window-only
diagnostics versus three-resolution diagnostics** on the same paired codec
outputs. Test whether the extra resolutions reveal transient/harmonic errors
that the medium scale or global metrics obscure. This is an application/analysis
contribution; do not describe standard STFT measures as a novel perceptual metric.
Whether it produces a useful finding must be established by actual data.

## Recommended project completion order

1. Run MATLAB tests and the synthetic demo; preserve logs and inspect all figures.
2. Select permitted clean speech and record corpus/speaker IDs and annotations.
3. Run paired Opus/EnCodec 6/12 kb/s on the same prepared references; inspect
   actual rates, length/delay, clipping flags, runtime scope and provenance.
4. Generate and inspect MATLAB reports, including optional STOI availability.
5. Analyse representative regions and cross-utterance variation; perform the
   medium-only versus multi-resolution comparison without assuming a winner.
6. Read and analyse the primary literature; finish report methods, results and
   discussion using only observed evidence. Drafting literature/methods can
   proceed alongside experiments.
7. Export the final report, record the real demonstration, prepare the GitHub
   Site with a small verified example, and check every cross-link.
8. Publish the site and submit the report/video to Canvas through the student's
   course account. No Canvas submission has been performed by this project.

## Dates and unspecified constraints

The supplied instructions say **end of Week 13**. They do not give an absolute
date/time, report page/word limit, exact video duration, mandatory report file
format or a named citation style. Verify these in Canvas/current course guidance;
do not infer a calendar deadline from the cloud environment's current date.

The instructor's suggested 10–20 utterances and 6/12 kb/s codec conditions are
project-specific guidance, not additional universal hand-in rules in this rubric.
