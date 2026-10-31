# How the workbook supports ISO/IEC 42001:2023

ISO/IEC 42001 is the management-system standard for AI. Clause 6 asks you to assess and treat AI risks and to assess
the impact of each AI system on people and society; Annex A lists the controls you choose from. This page maps the
workbook to the clauses and controls **by identifier and in our own words** — read the standard for the requirements.

## Clause 6.1.2 — AI risk assessment

What the clause expects, in plain terms: a repeatable process with defined criteria, that identifies AI risks, analyses
them (likelihood and consequence), evaluates them against the criteria and keeps the results.

| Expectation | Where in the workbook |
|-------------|-----------------------|
| Risk criteria defined and kept consistent | `03_Risk_Scales` — likelihood 1–5, severity 1–5 across individuals / society / organisation, rating bands, acceptance criteria |
| Risks identified for each AI system | `04_AI_Risk_Register` — one row per risk, linked to a System ID from the inventory, eight risk categories |
| Analysis: likelihood and consequence | Inherent Likelihood × Severity → Score and Rating (formulas) |
| Evaluation against criteria | Rating bands (Low / Medium / High / Critical) and the acceptance table |
| Repeatable, documented process | `01_Methodology` steps 1–8; dated reviews (Last Review column) |
| Results retained | The register itself; keep versions under change control |

## Clause 6.1.3 — AI risk treatment

| Expectation | Where in the workbook |
|-------------|-----------------------|
| Treatment option chosen per risk | Treatment column (Mitigate / Accept / Transfer / Avoid) |
| Controls determined and compared with Annex A | Existing / Planned Controls and ISO 42001 Annex A Reference columns |
| Residual risk evaluated and accepted by the owner | Residual Likelihood × Severity, Risk Owner, Status |
| Treatment plan | Target Date, Status, Comments; overdue dates turn red |

## Clause 6.1.4 — AI system impact assessment

What the clause expects: for each AI system, an assessment of the potential consequences for individuals, groups and
society, considering the system's intended use, context, data, autonomy and the parties affected; documented and
available to interested parties as appropriate.

| Expectation | Where in the workbook |
|-------------|-----------------------|
| Which systems, what they do, who is affected | `02_AI_System_Inventory` — use case, model type, data, autonomy level, affected parties, lifecycle status |
| Consequences for individuals and society, not only the organisation | Severity scale has three lenses; the register records which lens drove the score (Severity Lens column) |
| Assessment per system, with a conclusion | `05_Impact_Assessment_Summary` — roll-up per system (counts by residual rating, highest residual, categories still High+), conclusion, conditions, approver, next review |
| Triggered on change | Last Assessment date in the inventory; Next Review in the summary; the dashboard flags production or pilot systems with no assessment |

The summary sheet is deliberately short. If you need a narrative impact assessment, use the Markdown template in the
[iso27001-iso42001-toolkit](https://github.com/bizidwassim-design/iso27001-iso42001-toolkit) and reference the
System ID and Risk IDs from this workbook.

## Annex A controls referenced in the sample register

The ISO 42001 Annex A Reference column accepts any control ID. The three control groups the brief of this template
focuses on are described below in our own words; the sample risks reference them.

### A.5 — AI system impact assessment

| Control ID | What it is about (our wording) | Sample risks |
|------------|--------------------------------|--------------|
| A.5.2 | Having a process for assessing the impact of AI systems | all — the process is this workbook plus your narrative template |
| A.5.3 | Writing the assessment down and keeping it | `05_Impact_Assessment_Summary` |
| A.5.4 | Looking at the effect on individuals and groups | AIR-001, AIR-007 |
| A.5.5 | Looking at the effect on society | severity lens "Society" |

### A.6 — AI system life cycle

| Control ID | What it is about (our wording) | Sample risks |
|------------|--------------------------------|--------------|
| A.6.1.2 | Stating what "responsible development" means for you, as objectives | AIR-007 |
| A.6.1.3 | Having a design and development process that embeds those objectives | — |
| A.6.2.2 | Writing requirements and specifications for the system, including safety and oversight | AIR-007 |
| A.6.2.3 | Documenting design and development decisions | AIR-002, AIR-008 |
| A.6.2.4 | Verifying and validating the system before and after release (testing, fairness and robustness checks) | AIR-001, AIR-003, AIR-005 |
| A.6.2.5 | Deploying in a controlled way, with approval | AIR-008 |
| A.6.2.6 | Operating and monitoring the system (performance, drift, incidents) | AIR-003, AIR-006, AIR-007 |
| A.6.2.7 | Keeping technical documentation up to date | — |
| A.6.2.8 | Recording event logs so behaviour can be reconstructed | AIR-003, AIR-006, AIR-008 |

### A.7 — Data for AI systems

| Control ID | What it is about (our wording) | Sample risks |
|------------|--------------------------------|--------------|
| A.7.2 | Managing the data used to build and improve the system | — |
| A.7.3 | Knowing where data comes from and that you may use it | AIR-004 |
| A.7.4 | Making sure data is good enough for the purpose (quality, representativeness) | AIR-001, AIR-003, AIR-006 |
| A.7.5 | Keeping data provenance | AIR-004 |
| A.7.6 | Preparing data in a controlled, documented way | AIR-006 |

Other Annex A areas you will reference often: A.2 (AI policy), A.3 (roles and reporting concerns), A.4 (resources),
A.8 (information for interested parties — transparency), A.9 (responsible use), A.10 (third parties and customers).
The sample risks AIR-002, AIR-005 and AIR-008 use several of them.

## Clause 9.3 — management review

`06_Dashboard` gives the counts by rating, by category, by EU AI Act category, by treatment and by status, plus
two charts. Export it or screenshot it for the AI governance committee and the management review.

## What the workbook does not do

* It does not prove conformity. An auditor will want the process (policy, roles, criteria), evidence that it ran
  (dated assessments, approvals) and evidence that controls work.
* It does not replace a Statement of Applicability. Use the one in the sibling toolkit and reference the Risk IDs.
* It is not a legal classification under the EU AI Act — see [`eu-ai-act-quick-classifier.md`](eu-ai-act-quick-classifier.md)
  for a first orientation only.
