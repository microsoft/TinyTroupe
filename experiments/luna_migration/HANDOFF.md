# GPT-6 Luna migration: experimental branch handoff

**Read this document before running anything. The experiments are PAUSED.**

This temporary directory preserves migration helpers and selected evidence so work
can continue on another machine. It is not production library code. Curate or
remove it before merging the branch with `main`; preserve the production repairs,
tests, and relevant user documentation separately.

## Current state and scope

- Branch: `update-gpt-6-luna`.
- Default model and reasoning model: `gpt-6-luna`.
- Reasoning effort: `xhigh`. The API rejected the originally requested `max`;
  the user approved `xhigh`. Do not silently substitute another effort or model.
- The experiment was stopped at the user's request on November 6, 2026.
- The latest production library fingerprint is
  `3f5b80697765c367766a8291cc4a9a27aa8db7b9889ecb058bb2dede96c9d501`.
- That source passed **450 core tests**, with 440 deselected and 7 warnings, in
  1,407.24 seconds. Three focused live planner cases also passed.
- **The quantitative-quality objective is NOT complete.** Gazpacho purchase
  responses remain compressed. This branch is not a validated drop-in replacement
  for the empirical survey examples.

The user asked for a committed current state and a detailed, portable handoff.
Packaging this directory does not authorize restarting the paused experiment,
changing scientific methodology, merging, or pushing.

## What the session was about

The original request was to move from GPT-5 Mini to GPT-6 Luna on a separate branch,
then rerun notebook examples, starting with quicker ones, and carefully classify
outputs as better, worse, essentially unchanged, or errors.

The user subsequently requested prompt optimization based on observed failures,
comparisons involving both models, more mined cases than the initial approximately
20 examples, repeated iterations on failures, integration into TinyTroupe, and
real end-to-end notebook checks.

Across the session, 25 active notebooks were executed. The evidence corpus expanded
to 8,839 completed observations and 8,811 normalized requests. These are recorded
execution observations, not independent scientific replications or independent
human data points. The full bulk corpus is not in this compact Git handoff.

The central principle was to fix interpretable defects rather than manufacture
desired survey outcomes. Successful execution, a higher mean, more varied numbers,
and faithful extraction are different claims. Do not conflate them.

## Integrated production work

The commit preserves the accumulated library changes, tests, configurations, and
notebook changes. This is a development snapshot, not a declaration that every
modified example is empirically validated.

### Model configuration and transport

The configuration migration covers root, example, library, and relevant CI
surfaces. OpenAI client changes accommodate the new model's reasoning parameters.
Actor system instructions and turn cues remain plain text; structured stimuli and
image handling retain their established contracts.

### Interpretation, action behavior, and continuity

Prompt/runtime repairs cover action contracts, story continuation, literal
interpretation of capabilities versus obligations, developmental realism,
conversation closure, and document/memory grounding. A permission such as "needs
no supervision" must not be interpreted as a requirement for adults to be absent.
Agents must not invent inaccessible document contents or completed work.

Memory repairs distinguish real omission from a false gap warning. The Investment
notebook has a local 100-event lookback for its finite meeting; this is not a
blanket expansion of global retention defaults.

### Extraction fidelity

The interaction-results extractor distinguishes public speech from THINK, DONE,
and other private/internal content. Reasons, qualifications, rankings, and choices
must remain causally connected. A missing answer stays missing.

The final extraction repair was exercised on 100 actual survey histories without
changing their ratings/rankings or types. Ninety justifications were verbatim public
substrings or null; the remaining ten were manually reviewed as faithful summaries,
quotation wrappers, or public nonanswer explanations.

This repair corrected reporting fidelity. It did not cure low or narrow ratings
already present in actual TALK actions.

### Population construction and planning

The original population description survives dimension generation and planning.
Selected characteristics and eligibility carry through into individual biography
generation. Population instructions, alternative-trait catalogs, and population
distributions must not become an individual's personality.

The sampling planner now uses closed-vocabulary categorical option identifiers:
nonempty arrays of unique in-range integers. Deterministic reconstruction restores
the exact original names and strings. Invalid structure raises errors rather than
silently repairing selections.

For explicitly requested behavioral contrasts, compatible singleton allocations
preserve the opposing ends in a realized small sample. An extreme allowed only in
a mixture is not guaranteed to appear. These allocations are illustrative coverage,
not an estimate of behavioral prevalence and not quotas for survey ratings.

Opposing behaviors must also be different vocabulary options. An option saying
"rejects novelty OR buys impulsively" cannot guarantee either behavior.

### Comprehension versus demanded format

Three actor instructions clarify that demanded numbers or deep reasoning cannot
grant an infant or toddler understanding of a household purchase-propensity scale.
Concrete reactions can remain unscored. No invented caregiver answers for the child.

This is task-specific, not an age cutoff: children's counting and capable adults'
numerical preferences remain available.

### Weighted demographic alternatives

The final planner paragraph preserves compatible weighted demographic alternatives
inside behavioral directives rather than fixing a race, gender, or region to make
a profile distinctive. Redundant optional descriptions can remain unconstrained
when independent draws would conflict. Credential-dependent jobs cannot be drawn
independently of incompatible qualification alternatives.

It preserves expected marginals, not exact realized quotas, demographic correlations,
or a validated joint population model. The new live regression uses explicit
synthetic region/settlement/medical-qualification weights and culinary endpoints.

## Completed full notebook findings

For the later follow-up request, only the most complete gazpacho variation was used:
`Bottled Gazpacho Market Research 5 (with behavior correction).ipynb`.
Do not rerun all its variations merely because several are modified in the branch.

| Study | Completed execution | Finding |
|---|---|---|
| Investment Firm, CF5 | 20 steps; 1,215.22 seconds | Better financial-fact retention; 23 public utterances. Still repetitive and defers some unavailable valuation inputs. |
| Children's storytelling study 2, CF5 | 50 parents; 4,054.67 seconds | First choices A0/B31/C10/D0/E9. Better differentiation than original unanimity, but repetitive and not empirically validated. |
| Gazpacho 5, CF5 | 50 people; 3,814.48 seconds | Ratings 1:4 / 2:37 / 3:6 / 4:0 / 5:0 / N/A:3. Numerical mean 2.042553. |
| Gazpacho 5, CF6 | Fresh 50 people; 6,404.86 seconds | Ratings 1:5 / 2:31 / 3:13 / 4:0 / 5:0 / N/A:1. Numerical mean 2.163265; sample SD 0.589736. |

CF6 adult-only numerical responses were 1:3 / 2:22 / 3:13 / 4:0 / 5:0,
mean 2.263158. All 49 numerical extractions matched public speech. All 50 public
responses and explanations were manually reviewed. Forty-nine explanations were
verbatim/null; one added quotation marks around an exact public substring.

CF6 is a different cohort from CF5, so the higher mean is not a paired demonstration
of improvement. Warm/familiar-food objections and regular-purchase qualifications
remain repetitive.

The human gazpacho control reports 50 US respondents, mean 2.86, sample SD about
1.3554, completed July 5, 2025. Exact recruitment eligibility and representativeness
are unknown. No assumed age-25 filter or national representativeness claim is valid.
Respondent-level human tables and private report links are deliberately excluded
from this handoff; aggregate facts do not supply the missing recruitment protocol.

## Failed or withheld hypotheses: do not repeat blindly

- Twenty-one bounded framing, transport, season, prompt, and effort conditions did
  not establish a calibration cure. An independent eight-person holdout remained
  compressed. Situated trial-versus-regular-purchase framing was not adopted as a
  cure merely because some scores changed.
- A genuinely minimal actor template did not solve compression.
- A low-effort diagnostic reduced reasoning tokens but still produced only 2/3
  responses. Production remains `xhigh`.
- Removing unrelated worked biography examples did not establish calibration:
  corrected JSON-mode comparisons were Diego 3/3, Marco 2/2, Gabriel 1/2.
- Coverage alone did not fix the survey: the six-person adult screen still returned
  only 2/3. Do not identify guaranteed traits with guaranteed purchase ratings.
- Demographic-budget revisions 1 and 2 failed the unchanged expected race-marginal
  error limit of one person: errors 1.592430 and 1.819665 people. Neither was adopted.
- Revision 3 changed approach to preserving weighted alternatives. It passed all
  unchanged numerical criteria, but was withheld for qualification/job compatibility.
- Revision 4 added that generic guard. It passed the same numerical criteria, was
  manually reviewed across all 25 directives, and was integrated exactly as tested.

For revisions 3/4, race, gender, region, and settlement expected counts match source
weights to floating-point precision; age totals stay 9/7/20/6/8; all four predefined
singletons survive; both older bands permit educational variation. The 100-seed
checks are deterministic draw checks, **not 100 independent model replications**.

Some earlier exploration used the wrong request shape or omitted production JSON
mode. Corrected audits distinguish those exploratory content checks from exact
production replays. Do not label the earlier harness mismatches production passes.

## Bounded checks and their caveats

The final comprehension check exercised all CF6 people under five plus two adult
controls, using exact saved biographies and original questionnaire/correction/
extraction settings:

- Age 0: N/A, retained.
- Ages 2/3: unsupported purchase digits became unscored concrete reactions.
- Age 4: still scored 2; not claimed repaired or validated as adult propensity.
- Adults 66/69: retained 2/3.

That command failed its final whole-library hash assertion because the unrelated
dimension docstring was edited while it ran. A separate audit proves the sole
four-line delta, confirms actor instructions were unchanged, and recovers the
receipt without repeating calls. Do not call the original command an unqualified
pass. See `cf6-comprehension-screen/receipt.json`.

The coherent-dimension check repeats the original full population input through the
actual production method and JSON mode. The audit proves only the four instruction
lines changed; impulsive buying and strong rejection are separately selectable.

The final weighted-alternatives integration check replays the accepted original-input
response through `TinyPersonFactory._compute_sample_plan` with identical messages
and schema, producing no new saved API response. This is integration evidence,
not another independent model trial.

## Source and validation lineage

Fingerprints hash sorted package `.py`/`.mustache` files using NUL-separated relative
path components, a NUL, exact bytes, and a NUL. Package path separators are normalized
by that convention, but CRLF/LF byte changes can still alter historical hashes.

| Stage | Library SHA256 | Validation |
|---|---|---|
| Full CF5 rollouts | `fca0c6b13bdbfb88a0856955384530f42bed3f2b8bee350bb23dccbe5d8375cd` | 429 core cases |
| Extraction repair | `88c05fcfc6d336a487c57b1bca665eccf983c073ab8fec035507ed88f3dbf97d` | 432 core cases; 100-history extraction |
| Generator boundary | `000fcfb488ab982f259f778def4269a13e6972f0113eb5046d7c0f45a6b6fbd8` | 434 core cases |
| Compact identifiers/coverage; full CF6 | `8c6a0a640111c4c219a1dfa06e8bcee99621fd03c1d45a0bf3871c50f28b8333` | 444 core cases |
| Comprehension/coherent options | `ca9b09398b9dab603bc54a6fa729d7b27ce386dc80eeb3cff6e5117d51fa16f9` | 449 core cases |
| Weighted alternatives, current | `3f5b80697765c367766a8291cc4a9a27aa8db7b9889ecb058bb2dede96c9d501` | 450 core cases |

Historical validators intentionally fail against newer library stages. Do not
rerun a CF6 live-source audit against the final planner source and mistake the
expected mismatch for a failed historical execution.

Wire-message audits must apply the production `utils.dedent` preprocessing.
Decorator input may contain JSON followed by suffix text: use
`JSONDecoder.raw_decode`, not `json.loads` of the entire suffix. Generated biographies
may acquire the documented `country_of_residence=None` default; do not generalize
that into arbitrary missing/null equivalence.

## Crash, retry, and precise paused state

The first final-source CF7 notebook started November 3, 2026. It completed population
generation and interaction, then stopped during extraction at cell 36. Its last
saved elapsed time was 10,080.09 seconds. It did not complete the notebook.

On restart November 6, the client logged an unreadable JSON API cache at line 1,
column 1 and zero loaded entries. The existing runner archived the interrupted
notebook and started a fresh retry. It was **not a successful cached continuation**
or a paired continuation of the original population.

The user then explicitly stopped the experiment. The fresh retry was stopped in
generation cell 17. A valid snapshot of **75 returned responses**, approximately
2.78 MB, was saved in `cf7-gaz/recovery-response-snapshot.json`. This is partial
evidence, not a completed cohort, interaction, extraction, or quality result.

See `cf7-crash-recovery.json`. Unknown interrupted-attempt charges must not be
folded into the fresh retry's known returned usage.

The existing cache writer rewrites its JSON file non-atomically, and the loader
starts empty after a parsing failure. This was observed, not repaired in this
snapshot. Before any future recovery, validate and copy a cache to a distinct file
**before** a client can overwrite it. Do not restart the stopped run in place.

## Costs: estimates, not invoices

| Recorded scope | Returned-usage estimate USD |
|---|---:|
| Three completed CF5 notebooks | 1.414845445 |
| Full CF6 gazpacho | 0.921991735 |
| Six-person comprehension screen | 0.032120345 |
| Original-input coherent dimensions | 0.011725340 |
| Failed budget revisions 1/2 | 0.075077975 |
| Structural revisions 3/4 | 0.063865225 |

These are selected scopes, not a project/session total. Core tests and unreturned
timeout charges are excluded. Interrupted CF7 total cost is unknown.

Historical saved Luna rates were input $0.10/M, cache read $0.01/M, cache write
$0.125/M, output $0.50/M. Use `model-study/study-prices.json` for the historical
ledger, not as a claim that prices remain current. Cache writes replace ordinary
input billing for those tokens. Earlier Mini comparisons were not uniformly
effort-controlled because the client did not forward `xhigh` to Mini.

## Portable tooling and evidence map

Helper scripts live directly in this directory, retaining their original filenames.
`model-study/` contains the mining/replay/optimization utilities and offline tests.
Historical absolute checkout constants in executable helpers are changed to
repository-relative discovery. Evidence files retain historical content and hashes;
absolute paths inside protocols/records describe the original machine, not required
runtime paths.

Start with:

- `cf5-quality-report.html`: detailed quality comparison and rejected hypotheses.
- `cf4-final-followup-ledger.json`: historical experiment ledger. Its old running
  entries are superseded by this paused handoff and `cf7-crash-recovery.json`.
- `marginal-choices-validation.json`: latest production source and 450-case result.
- `demographic-coverage-budget-r3/` and `-r4/`: prospective criteria, responses,
  numerical screens, reviews, and selected caches.
- `cf6-gaz-manual-quality-review.json`, `cf6-gaz-public-evidence.json`, and
  `cf6-gaz-population-evidence.json`: complete reviewed synthetic survey evidence.
- `cf6-gaz/`: saved synthetic biographies, histories, factory, run record, and API
  cache. Do not assume an executed notebook or mixed human table is bundled.
- `cf6-comprehension-screen/`, `cf6-coherent-dimensions/`,
  `marginal-choices-integration/`: bounded repair evidence.
- `handoff-manifest.json`: exact bundled hashes, portability changes, and omissions.
- `STATUS.json`: authoritative paused state; supersedes historical running entries.

The bundle's `.gitattributes` disables newline conversion so evidence byte hashes
survive transfer. Do not reformat the captured evidence or regenerate its historical
protocols merely to satisfy a later-source validator.

The repository already stores `*.cache.json` with **Git LFS**, and this handoff
preserves that convention. Install Git LFS and fetch its objects on the receiving
machine. A Git commit or ordinary Git bundle contains cache pointers, not the cache
payloads; transferring only a bundle without the LFS objects is insufficient.
After the branch is pushed by an authorized user, the receiving checkout can run:

```powershell
git lfs install
git lfs pull
```

The handoff verifier checks actual cache bytes in the checkout. Its `--staged`
mode also verifies LFS pointer object IDs and sizes against the evidence manifest.

Do not run old one-shot scripts indiscriminately. Many intentionally refuse existing
output directories, assume a particular historical fingerprint, or require inputs
not bundled here. Preserving them is not a claim that every historical invocation
can run unchanged against today's production source.

The approximately 914 MB expanded execution corpus, multi-gigabyte copied workspaces,
images, zip exports, most full-run caches, private report links, and respondent-level
human tables are not committed. Their absence is explicit in the manifest. Use the
mining utilities on a new authorized execution collection if broader prompt mining
is needed; do not pretend the old 8,811-request corpus is present.

## Setup on another machine

Use Python 3.10 with the repository's dependencies. On the original Windows machine
the environment was `py310`; the environment name itself is not portable.
The model-study requirements are separately recorded.

From the repository root, in PowerShell:

```powershell
# Original Windows conda setup, if that installation/environment exists:
$PSNativeCommandArgumentPassing = 'Legacy'
. "$env:LOCALAPPDATA\anaconda3\shell\condabin\conda-hook.ps1"
conda activate py310

# For an already active compatible environment:
python -m pip install -e .

# Supply credentials through the environment/account setup, never source files.
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUNBUFFERED = '1'
$env:PYTHONPATH = (Join-Path $PWD 'experiments\luna_migration')
python experiments\luna_migration\verify_handoff.py
```

Do not install dependencies automatically if the target environment already has
them. `model-study/requirements.txt` is only for missing study-tool dependencies.
No credentials or private human reports are supplied by the handoff.

Offline helper checks, with no model calls:

```powershell
$env:PYTHONPATH = (Join-Path $PWD 'experiments\luna_migration\model-study')
python -m pytest experiments\luna_migration\model-study -q -o addopts=
$env:PYTHONPATH = (Join-Path $PWD 'experiments\luna_migration')
python -m pytest experiments\luna_migration\test_notebook_audit.py `
    experiments\luna_migration\test_model_case_study.py -q -o addopts=
```

Production regression (makes real LLM calls where not cached; run only when resuming):

```powershell
python -m pytest -s --use_cache -m "core and not slow"
```

An isolated future full run, **only after the user resumes the experiment**, should
use a new output directory rather than overwrite `cf7-gaz`:

```powershell
python experiments\luna_migration\run_notebook_comparison.py `
    --source-dir .\examples `
    --output-dir .\experiments\luna_migration\future-gaz-run `
    --model gpt-6-luna --reasoning-model gpt-6-luna --effort xhigh `
    --api-timeout 600 --timeout 7200 --use-cache `
    'Bottled Gazpacho Market Research 5 (with behavior correction).ipynb'
```

API timeout and cell timeout are explicit execution settings, not changes to model
effort or scientific acceptance. Record source hashes and start/end times. Do not
edit library source during a run. Review every public response and confirm
draw/biography/actor/extractor correspondence before claiming quality.

## Pending work and decisions

1. Keep the experiment paused until the user requests continuation. No completed
   final-source full survey is available; recoverable partial data is not a pass.
2. On continuation, use a fresh, separately named run or a validated explicit
   recovery. Preserve partial records and unknown-cost disclosures.
3. Check the new vocabulary, plan, drawn people, biography, actual actor context,
   public answers, and extraction. Successful structure is only one gate.
4. If compression persists, broader calibration needs matched human recruitment
   criteria and unseen-product holdouts. Do not tune to this one gazpacho distribution.
5. A different rating-elicitation/embedding protocol would be a separate methodology,
   not a transparent repair of the current extraction contract. Do not replace
   a spoken 2 with an embedding-derived higher score.
6. A scientifically justified within-band age model needs actual input data; do not
   invent a cutoff to conceal extreme drawn ages. The observed age 117 in CF6 was
   inside its fresh 0-120 vocabulary; a frozen 0-110 vocabulary belongs to another
   request.
7. Before merging, curate the snapshot's notebook outputs and experimental bundle,
   review accumulated changes, and retain the directly related tests/documentation.

The useful conclusion is bounded: many concrete defects have been repaired and
verified, but empirical purchase-intent simulation has not been validated. Continue
from that honest distinction, not from a claim that every prompt now works.
