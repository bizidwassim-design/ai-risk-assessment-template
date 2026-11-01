# AI Risk Assessment Template (ISO/IEC 42001)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![CI](https://github.com/bizidwassim-design/ai-risk-assessment-template/actions/workflows/ci.yml/badge.svg)](https://github.com/bizidwassim-design/ai-risk-assessment-template/actions/workflows/ci.yml) [![Fictional data](https://img.shields.io/badge/sample%20data-fictional-informational)](SECURITY.md) [![No macros](https://img.shields.io/badge/office%20files-no%20macros-success)](SECURITY.md)

A free, open-source Excel workbook to inventory AI systems, assess AI-specific risks with a
**Likelihood × Severity (5×5)** method across **individuals, society and the organisation**, decide treatment with
**ISO/IEC 42001:2023 Annex A** control references, and summarise the **AI system impact assessment** per system —
with a preliminary **EU AI Act** category. Generated from a reviewable Python script; no macros; all sample data fictional.

> 🇫🇷 Résumé en français en bas de page.

## Layout

```
AI-Risk-Assessment-Template.xlsx   the workbook (generated — do not edit the binary in pull requests)
scripts/build_template.py          openpyxl script that builds it
docs/
  iso42001-mapping.md              clauses 6.1.2 / 6.1.3 / 6.1.4 and Annex A.5 / A.6 / A.7 → sheets and columns
  eu-ai-act-quick-classifier.md    plain-language decision tree for a first classification
  ai-risk-categories.md            the eight risk categories: prompts, scenarios, typical controls
```

## Quick start

1. Download `AI-Risk-Assessment-Template.xlsx` and open it in Excel, LibreOffice Calc or Google Sheets.
2. Read `01_Methodology`, then calibrate the organisational thresholds in `03_Risk_Scales`.
3. List your AI systems in `02_AI_System_Inventory` — role (provider / deployer), use case, model type, data,
   autonomy level, affected parties, and a preliminary EU AI Act category using
   [`docs/eu-ai-act-quick-classifier.md`](docs/eu-ai-act-quick-classifier.md).
4. Add risks in `04_AI_Risk_Register`: pick the System ID (the name fills in), choose one of the eight categories,
   score inherent and residual risk, reference ISO 42001 Annex A control IDs.
5. Record the conclusion per system in `05_Impact_Assessment_Summary` and report with `06_Dashboard`.

**Conventions:** blue text = input · black on grey = formula · red residual score = higher than inherent ·
red date = overdue · orange EU AI Act cell = high-risk or prohibited · red "No" = production/pilot system without an impact assessment.

## What's inside

| Sheet | Purpose |
|-------|---------|
| `01_Methodology` | Method, severity lenses, rating bands, the eight categories, step-by-step, standards alignment, conventions |
| `02_AI_System_Inventory` | 20 rows: System ID, name, organisation role, use case, model type, data, personal data, autonomy level (1–4), affected parties, owners, lifecycle, EU AI Act category, impact assessment done, last assessment |
| `03_Risk_Scales` | Likelihood 1–5 · Severity 1–5 described for individuals / society / organisation · acceptance criteria · autonomy levels |
| `04_AI_Risk_Register` | 50 rows: category, scenario, cause, affected parties, severity lens, inherent L×S → score and rating, treatment, controls, ISO 42001 Annex A reference, other references, residual L×S, owner, dates, status |
| `05_Impact_Assessment_Summary` | One row per system from the inventory: risk counts, residual counts by rating (COUNTIFS), highest residual score and rating, categories still High or Critical, conclusion, conditions, approver, next review |
| `06_Dashboard` | KPIs, counts by rating (inherent vs residual), by category, by EU AI Act category, by treatment and status; two bar charts |

### Method in one minute

```
Risk Score = Likelihood (1–5) × Severity (1–5)        → 1 to 25
Severity   = highest of: harm to individuals · harm to society · harm to the organisation
```

| Rating | Score | Typical response |
|--------|-------|------------------|
| 🟢 Low | 1–4 | Accept and monitor model metrics; review yearly |
| 🟡 Medium | 5–9 | Mitigate, or accept with justification; review every 6 months |
| 🟠 High | 10–16 | Treatment plan within 90 days; senior management and AI governance lead acceptance only |
| 🔴 Critical | 17–25 | Do not launch / pause until interim controls exist; executive decision within 30 days |

### The eight risk categories

Bias & fairness · Transparency & explainability · Robustness & drift · Privacy · Security (prompt injection, data
poisoning, model theft, excessive agency) · Safety · Accountability & oversight · Legal & regulatory (EU AI Act).
Prompts and example scenarios per category: [`docs/ai-risk-categories.md`](docs/ai-risk-categories.md).

### Sample data

Three fictional AI systems at Northwind Logistics — an in-house route optimiser (provider), a support assistant built
on a third-party LLM (deployer, pilot) and a SaaS candidate-screening tool (deployer, high-risk area) — and eight
fictional risks, one per category, with inherent and residual scores, Annex A references and treatment plans. The
summary sheet shows one system approved with conditions, one pilot continuing with conditions and one system paused
for redesign. Overwrite or delete the samples before real use.

## Design choices

* **Three severity lenses, one score.** ISO/IEC 42001 asks for consequences to individuals and society, not only to the
  business. The scale describes all three; you score the highest and record which lens drove it.
* **Inventory first.** Risks reference a System ID; the summary and dashboard roll up per system, so the impact
  assessment conclusion is tied to evidence in the register.
* **Autonomy level as a first-class attribute.** The more a system acts on its own, the earlier harm reaches people.
* **Same bands as the sibling workbooks** (1–4 / 5–9 / 10–16 / 17–25), so AI risks can be merged into an enterprise register.
* **Standards by ID only.** Annex A control IDs, clause numbers and EU AI Act notions are referenced, never reproduced.
* **Reproducible.** `scripts/build_template.py` rebuilds the workbook; CI checks sheet names, sample counts, formula shape and the absence of macros.

### Rebuilding the workbook from source

```bash
pip install openpyxl
python scripts/build_template.py
```

## Compatibility

* Verified by opening and fully recalculating in **Microsoft Excel (16.0)** — zero formula errors.
* Uses standard functions (`IF`, `AND`, `ISNUMBER`, `INDEX/MATCH`, `IFERROR`, `COUNTIF(S)`, `MAXIFS`, `TEXTJOIN`,
  `SUM`, `MAX`, `TODAY`), standard data validation and conditional formatting — no macros. `MAXIFS` and `TEXTJOIN`
  need Excel 2019 / Microsoft 365, LibreOffice 5.2+ or Google Sheets.

## Related repositories

| Repository | How it connects |
|------------|-----------------|
| [application-risk-assessment-template](https://github.com/bizidwassim-design/application-risk-assessment-template) | Same 5×5 method for any application; use both side by side or merge AI risks into it |
| [threat-modeling-toolkit](https://github.com/bizidwassim-design/threat-modeling-toolkit) | STRIDE with AI extras (prompt injection, poisoning, leakage) — feeds the Security category |
| [iso27001-iso42001-toolkit](https://github.com/bizidwassim-design/iso27001-iso42001-toolkit) | ISO 42001 Statement of Applicability, AI policy and narrative impact-assessment template |
| [grc-control-crosswalk](https://github.com/bizidwassim-design/grc-control-crosswalk) | Translate control references across ISO 27001, NIST CSF and others |
| [soc-detection-playbooks](https://github.com/bizidwassim-design/soc-detection-playbooks) | Detections for the security risks that cannot be prevented |
| [ciso-executive-dashboard](https://github.com/bizidwassim-design/ciso-executive-dashboard) | Executive reporting that can take the dashboard counts as input |
| [public-scripts](https://github.com/bizidwassim-design/public-scripts) | Other small, reviewable security scripts |

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md).

## Disclaimer

This template supports, but does not replace, professional judgement, legal advice on the EU AI Act, a conformity
assessment or a certification audit. Scores are only as good as the evidence behind them. Use roles, not personal names,
and keep client names, credentials and confidential incident details out of the file.

## AI assistance

Built with Claude Code as a coding and writing assistant, which is why it appears as a co-author on some commits.
**Editor and reviewer: Wassim Bizid**, who set the scope, the frameworks and the GRC approach, edited the content
and decided what was published. Automated tests in CI check the published outputs. This is a maintainer review,
not an independent one.

## License

[MIT](LICENSE) — free to use, copy, modify and redistribute.

---

## 🇫🇷 Résumé

Classeur Excel **open source** d'évaluation des risques liés à l'IA, aligné sur **ISO/IEC 42001:2023** (clauses 6.1.2 et
6.1.4, Annexe A.5 / A.6 / A.7) avec une catégorie préliminaire **AI Act européen**. Méthode **Probabilité × Gravité (5×5)**,
la gravité étant évaluée pour les **personnes, la société et l'organisation**. Six feuilles : méthodologie, inventaire des
systèmes d'IA, échelles, registre des risques IA (huit catégories : biais, transparence, robustesse, vie privée, sécurité,
sûreté, responsabilité, conformité), synthèse de l'analyse d'impact par système, tableau de bord. Sans macro ; données
d'exemple fictives ; généré par `scripts/build_template.py` (`pip install openpyxl`). Licence MIT.
