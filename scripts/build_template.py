#!/usr/bin/env python3
"""
Build AI-Risk-Assessment-Template.xlsx

An open-source AI risk assessment workbook aligned with ISO/IEC 42001:2023
(clauses 6.1.2 AI risk assessment and 6.1.4 AI system impact assessment; Annex A.5, A.6, A.7)
with an EU AI Act category column.

Usage:
    pip install openpyxl
    python scripts/build_template.py            # writes ../AI-Risk-Assessment-Template.xlsx

No macros, no personal data. All sample entries are fictional. MIT License (see LICENSE).
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.comments import Comment
from openpyxl.formatting.rule import FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

# --------------------------------------------------------------------------- #
# Design tokens
# --------------------------------------------------------------------------- #
FONT = "Arial"
NAVY = "1F3864"
MID_BLUE = "2F5597"
LIGHT_BLUE = "D9E2F3"
PALE = "F2F2F2"
INPUT_BLUE = "0000FF"
GRID = "BFBFBF"

BANDS = [  # (label, min, max, fill, text colour)
    ("Low", 1, 4, "C6E0B4", "1E4620"),
    ("Medium", 5, 9, "FFE699", "7F6000"),
    ("High", 10, 16, "F4B183", "7F3200"),
    ("Critical", 17, 25, "C00000", "FFFFFF"),
]

S_METH = "01_Methodology"
S_INV = "02_AI_System_Inventory"
S_SCALES = "03_Risk_Scales"
S_REG = "04_AI_Risk_Register"
S_IMPACT = "05_Impact_Assessment_Summary"
S_DASH = "06_Dashboard"

INV_FIRST, INV_LAST = 5, 24      # 20 AI systems
REG_FIRST, REG_LAST = 5, 54      # 50 risks

thin = Side(style="thin", color=GRID)
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)

# Lists
ROLES = ["Provider (we develop it)", "Deployer / user (we use it)", "Both (develop and use)", "Distributor / importer"]
MODEL_TYPES = ["Rule-based / expert system", "Classical ML (regression, trees, clustering)", "Deep learning (vision, speech, time series)",
               "LLM / generative AI – third-party API", "LLM / generative AI – self-hosted or fine-tuned", "Hybrid / agentic (model + tools)"]
AUTONOMY = ["1 – Informs (human decides)", "2 – Recommends (human chooses among options)",
            "3 – Acts with human approval", "4 – Acts autonomously (human monitors)"]
EU_CAT = ["Not assessed", "Out of scope", "Minimal risk", "Limited risk (transparency duties)", "High-risk (Annex III area)",
          "High-risk (Annex I product safety)", "Prohibited practice", "GPAI model obligations"]
LIFECYCLE = ["Idea", "Development", "Pilot", "Production", "Retired"]
YESNO = ["Yes", "No"]
CATEGORIES = ["Bias & fairness", "Transparency & explainability", "Robustness & drift", "Privacy", "Security",
              "Safety", "Accountability & oversight", "Legal & regulatory (EU AI Act)"]
TREATMENT = ["Mitigate", "Accept", "Transfer", "Avoid"]
STATUS = ["Open", "In progress", "Mitigated", "Accepted", "Closed"]
CONCLUSION = ["Not assessed", "Proceed", "Proceed with conditions", "Do not proceed / redesign"]


# --------------------------------------------------------------------------- #
# Style helpers
# --------------------------------------------------------------------------- #
def f(bold: bool = False, color: str = "000000", size: int = 10, italic: bool = False) -> Font:
    return Font(name=FONT, bold=bold, color=color, size=size, italic=italic)


def fill(hex_color: str) -> PatternFill:
    return PatternFill("solid", start_color=hex_color, end_color=hex_color)


def put(ws, ref, value=None, *, font=None, bg=None, align=None, border=False, fmt=None):
    cell = ws[ref]
    if value is not None:
        cell.value = value
    cell.font = font or f()
    if bg:
        cell.fill = fill(bg)
    cell.alignment = align or Alignment(vertical="top", wrap_text=True)
    if border:
        cell.border = BORDER
    if fmt:
        cell.number_format = fmt
    return cell


def header(ws, row, labels, *, start_col=1, height=34, bg=NAVY):
    for i, label in enumerate(labels):
        c = ws.cell(row=row, column=start_col + i, value=label)
        c.font = f(bold=True, color="FFFFFF")
        c.fill = fill(bg)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = BORDER
    ws.row_dimensions[row].height = height


def title(ws, text, subtitle=None, width_cols=8):
    ws["A1"].value = text
    ws["A1"].font = f(bold=True, color="FFFFFF", size=16)
    ws["A1"].alignment = Alignment(vertical="center")
    for col in range(1, width_cols + 1):
        ws.cell(row=1, column=col).fill = fill(NAVY)
    ws.row_dimensions[1].height = 34
    if subtitle:
        ws["A2"].value = subtitle
        ws["A2"].font = f(italic=True, color="404040")
        ws["A2"].alignment = Alignment(vertical="center")
        ws.row_dimensions[2].height = 22


def widths(ws, mapping):
    for col, w in mapping.items():
        ws.column_dimensions[col].width = w


def page_setup(ws, landscape=True):
    ws.page_setup.orientation = "landscape" if landscape else "portrait"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True


def list_dv(options, *, warn=False):
    dv = DataValidation(type="list", formula1='"' + ",".join(options) + '"', allow_blank=True)
    dv.showErrorMessage = True
    dv.errorStyle = "warning" if warn else "stop"
    dv.errorTitle = "Invalid entry"
    dv.error = "Please choose a value from the list."
    return dv


def date_dv():
    dv = DataValidation(type="date", operator="greaterThanOrEqual", formula1="36526", allow_blank=True)
    dv.errorStyle = "warning"
    dv.showErrorMessage = True
    dv.error = "Enter a valid date (yyyy-mm-dd)."
    return dv


def rating_formula(score_cell: str) -> str:
    return (f'=IF({score_cell}="","",IF({score_cell}>=17,"Critical",IF({score_cell}>=10,"High",'
            f'IF({score_cell}>=5,"Medium","Low"))))')


def band_rules(ws, col, first, last, *, text_based):
    rng = f"{col}{first}:{col}{last}"
    for name, lo, hi, bg, fg in BANDS:
        formula = f'${col}{first}="{name}"' if text_based else \
            f"AND(ISNUMBER(${col}{first}),${col}{first}>={lo},${col}{first}<={hi})"
        ws.conditional_formatting.add(
            rng, FormulaRule(formula=[formula], fill=fill(bg), font=Font(name=FONT, bold=True, color=fg), stopIfTrue=True))


# --------------------------------------------------------------------------- #
# 01_Methodology
# --------------------------------------------------------------------------- #
def build_methodology(wb: Workbook):
    ws = wb.active
    ws.title = S_METH
    ws.sheet_properties.tabColor = NAVY
    ws.sheet_view.showGridLines = False
    title(ws, "AI Risk Assessment Template",
          "ISO/IEC 42001:2023 cl. 6.1.2 (AI risk assessment) · cl. 6.1.4 (AI system impact assessment) · Annex A.5 / A.6 / A.7 · EU AI Act category",
          width_cols=2)
    widths(ws, {"A": 32, "B": 120})
    ws["A1"].comment = Comment(
        "OPEN SOURCE: released under the MIT License. Free to use, copy, modify and redistribute. "
        "Provided 'as is' without warranty. All sample data is fictional.", "Template", width=360, height=100)

    row = 3
    ws["A3"].value = "Version 1.0  ·  Open source (MIT)  ·  No macros  ·  All sample data is fictional"
    ws["A3"].font = f(italic=True, color="595959")

    def section(text):
        nonlocal row
        row += 1
        c = ws.cell(row=row, column=1, value=text)
        c.font = f(bold=True, color="FFFFFF", size=11)
        for col in (1, 2):
            ws.cell(row=row, column=col).fill = fill(MID_BLUE)
        ws.row_dimensions[row].height = 22
        c.alignment = Alignment(vertical="center")
        row += 1

    def line(label, text, *, height=None, label_font=None):
        nonlocal row
        a = ws.cell(row=row, column=1, value=label)
        a.font = label_font or f(bold=True)
        a.alignment = Alignment(vertical="top", wrap_text=True)
        b = ws.cell(row=row, column=2, value=text)
        b.font = f()
        b.alignment = Alignment(vertical="top", wrap_text=True)
        if height:
            ws.row_dimensions[row].height = height
        row += 1

    section("1. Purpose")
    line("What it is",
         "A workbook to inventory AI systems, identify and score AI-specific risks, decide treatment, and summarise the impact "
         "assessment per system — the artefacts an AI management system (ISO/IEC 42001) expects for clauses 6.1.2 and 6.1.4.", height=34)
    line("Who it is for",
         "AI governance leads, CISOs, GRC and product teams in organisations that build or deploy AI — from a single chatbot to "
         "a portfolio of models — without buying a GRC platform.", height=34)
    line("What it is not",
         "A legal opinion on the EU AI Act, a model evaluation tool, or a replacement for a DPIA. It organises the questions and the evidence.", height=22)

    section("2. The method")
    line("Formula", "Risk Score = Likelihood (1–5) × Severity (1–5)   →   1 to 25", height=18)
    line("Severity across three lenses",
         "Severity is scored once, as the highest of three lenses described in 03_Risk_Scales: harm to INDIVIDUALS (rights, "
         "safety, discrimination, privacy), harm to SOCIETY (groups, public trust, environment, democracy) and harm to the "
         "ORGANISATION (legal, financial, operational, reputational). An AI risk is rarely 'only' a company problem.", height=48)
    line("Inherent and residual",
         "Score each risk twice: INHERENT (before treatment, with only unavoidable controls) and RESIDUAL (after existing and "
         "planned controls). Residual must not exceed inherent — the cell turns red if it does.", height=34)
    for name, lo, hi, bg, fg in BANDS:
        meaning = {
            "Low": "Acceptable within normal management. Monitor and review annually.",
            "Medium": "Treat, or accept with documented justification by the system owner. Review every 6 months.",
            "High": "Treatment plan with owner and date. Acceptance needs senior management and the AI governance lead.",
            "Critical": "Stop or do not launch until interim controls are in place. Executive decision within 30 days.",
        }[name]
        a = ws.cell(row=row, column=1, value=f"{name}  ({lo}–{hi})")
        a.font = f(bold=True, color=fg)
        a.fill = fill(bg)
        a.alignment = Alignment(horizontal="center", vertical="center")
        a.border = BORDER
        b = ws.cell(row=row, column=2, value=meaning)
        b.font = f()
        b.alignment = Alignment(vertical="center", wrap_text=True)
        b.border = BORDER
        ws.row_dimensions[row].height = 22
        row += 1

    section("3. Risk categories")
    cats = {
        "Bias & fairness": "Outputs systematically disadvantage people or groups; proxies for protected characteristics; unequal error rates.",
        "Transparency & explainability": "People do not know AI is involved, cannot understand or contest an outcome; decisions cannot be explained to a regulator.",
        "Robustness & drift": "Performance degrades with new data, edge cases or adversarial inputs; silent model or data drift; hallucination.",
        "Privacy": "Personal data in training, prompts, retrieval or outputs; memorisation; purpose creep; missing legal basis.",
        "Security": "Prompt injection, data poisoning, model theft or extraction, supply-chain compromise of models and datasets, excessive agency.",
        "Safety": "Physical, psychological or financial harm from acting on outputs; unsafe automation; missing fallback.",
        "Accountability & oversight": "No owner, no approval gate for model changes, no human oversight that can actually intervene, no incident process.",
        "Legal & regulatory (EU AI Act)": "Wrong or missing risk classification; obligations of providers or deployers not met; sector rules; IP and contracts.",
    }
    for k, v in cats.items():
        line(k, v, height=30)

    section("4. Step-by-step")
    steps = [
        ("Step 1 — Inventory", f"List every AI system in {S_INV}: your role (provider / deployer), use case, model type, data, autonomy level, affected parties, lifecycle status and a preliminary EU AI Act category (see docs/eu-ai-act-quick-classifier.md)."),
        ("Step 2 — Calibrate", f"Read {S_SCALES}. Adjust the organisational thresholds (money, downtime) to your size. Keep the individual and societal descriptors."),
        ("Step 3 — Identify risks", f"In {S_REG}, add at least one row per category per system that is in Pilot or Production. Pick the System ID from the drop-down — the name fills in."),
        ("Step 4 — Score inherent", "Choose Likelihood and Severity (1–5). Score and Rating are calculated. Note which lens drove the severity."),
        ("Step 5 — Treat", "Decide Mitigate / Accept / Transfer / Avoid. Record controls and reference the ISO/IEC 42001 Annex A control IDs they implement (and ISO 27001 / NIST AI RMF where useful)."),
        ("Step 6 — Score residual", "Re-score assuming the controls work. Residual should be lower than inherent."),
        ("Step 7 — Impact summary", f"{S_IMPACT} rolls up the register per system. Record the impact-assessment conclusion (Proceed / with conditions / Do not proceed) and the next review date."),
        ("Step 8 — Report", f"Use {S_DASH} in AI governance committee and management review (ISO/IEC 42001 clause 9.3)."),
    ]
    for label, text in steps:
        line(label, text, height=34)

    section("5. Alignment with standards")
    line("ISO/IEC 42001:2023",
         "Cl. 6.1.2 AI risk assessment (criteria, identification, analysis, evaluation) → 03_Risk_Scales and 04_AI_Risk_Register. "
         "Cl. 6.1.3 AI risk treatment → treatment, controls and Annex A references in the register. "
         "Cl. 6.1.4 AI system impact assessment → affected parties in the inventory, severity lenses, 05_Impact_Assessment_Summary. "
         "Annex A.5 impact assessment, A.6 life cycle, A.7 data → control reference column. Details in docs/iso42001-mapping.md.", height=62)
    line("EU AI Act",
         "The inventory carries a preliminary category per system; the register has a dedicated 'Legal & regulatory' risk category to "
         "track obligations. The classifier in docs/ is plain-language guidance, not legal advice.", height=34)
    line("ISO/IEC 27001:2022 · NIST AI RMF 1.0",
         "Security and privacy risks map to ISO 27001 Annex A controls; the 'Other references' column accepts NIST AI RMF function IDs (GOVERN, MAP, MEASURE, MANAGE).", height=34)

    section("6. Conventions")
    line("Blue text", "Input cells — type here.", label_font=f(bold=True, color=INPUT_BLUE), height=18)
    line("Black text, grey fill", "Formulas — do not overwrite (System Name, Scores, Ratings, summary counts).", height=18)
    line("Red score / red date", "Red residual score = higher than inherent. Red target date = overdue and not closed.", height=18)
    line("Roles, not names", "Use roles ('Head of Data Science'), never personal names or contact details. No client names, credentials or confidential incident details.", height=30)

    section("7. Disclaimer")
    line("Not legal advice", "This template supports professional judgement; it does not replace legal advice, a conformity assessment or a certification audit.", height=30)
    page_setup(ws)


# --------------------------------------------------------------------------- #
# 02_AI_System_Inventory
# --------------------------------------------------------------------------- #
INV_HEADERS = [
    "System ID", "AI System Name", "Organisation Role", "Use Case / Purpose", "Model Type", "Data Used",
    "Personal Data?", "Autonomy Level", "Affected Parties", "Business Owner (role)", "Technical Owner (role)",
    "Lifecycle Status", "EU AI Act Category (preliminary)", "Impact Assessment Done?", "Last Assessment", "Notes",
]

INV_SAMPLES = [
    ("AIS-001", "RouteMind — delivery ETA and route optimisation", ROLES[0],
     "Predicts delivery time windows and re-sequences driver routes during the day from telematics and order data.",
     MODEL_TYPES[1], "Telematics (GPS, speed), order and address data, historical delivery times, weather feed",
     "Yes", AUTONOMY[2], "Drivers (schedules, workload), customers (promised slots), dispatch team",
     "Head of Operations", "Head of Data Science", "Production", EU_CAT[2], "Yes", date(2026, 9, 12),
     "In-house model retrained monthly. Drivers can reject a re-route from the app."),
    ("AIS-002", "Support assistant (chat) — built on a third-party LLM", ROLES[1],
     "Answers customer questions on shipment status and invoices; drafts replies for agents; retrieves order data.",
     MODEL_TYPES[3], "Customer questions, order and shipment records (retrieval), support-ticket history, knowledge-base articles",
     "Yes", AUTONOMY[1], "Customers (information, decisions based on answers), support agents, model provider as processor",
     "Head of Customer Experience", "Digital Platform Lead", "Pilot", EU_CAT[3], "No", date(2026, 10, 3),
     "Model API hosted by a third-party provider (contract with Contoso AI Services, fictional). Pilot with 5 % of traffic."),
    ("AIS-003", "Candidate screening — SaaS ranking of applications", ROLES[1],
     "Ranks incoming applications for warehouse and driver roles and suggests a shortlist to recruiters.",
     MODEL_TYPES[2], "CVs, application forms, interview notes, historical hiring outcomes (vendor-trained model)",
     "Yes", AUTONOMY[1], "Job applicants (access to employment), recruiters, works council",
     "Head of Human Resources", "HR Systems Manager", "Production", EU_CAT[4], "No", None,
     "Provided by Fabrikam Talent (fictional vendor). Employment use case — high-risk area. Impact assessment overdue."),
]


def build_inventory(wb: Workbook):
    ws = wb.create_sheet(S_INV)
    ws.sheet_properties.tabColor = "548235"
    title(ws, "AI System Inventory", "One row per AI system (rows 5–24). Blue = input. Sample rows are fictional — overwrite or delete them.", width_cols=16)
    widths(ws, {"A": 10, "B": 34, "C": 22, "D": 44, "E": 30, "F": 40, "G": 10, "H": 26, "I": 38, "J": 20, "K": 20,
                "L": 12, "M": 28, "N": 12, "O": 13, "P": 48})
    header(ws, 4, INV_HEADERS, height=40)
    for r in range(INV_FIRST, INV_LAST + 1):
        idx = r - INV_FIRST
        sample = INV_SAMPLES[idx] if idx < len(INV_SAMPLES) else None
        for ci in range(1, len(INV_HEADERS) + 1):
            c = ws.cell(row=r, column=ci)
            if sample and sample[ci - 1] is not None:
                c.value = sample[ci - 1]
            c.font = f(color=INPUT_BLUE, bold=(ci == 1))
            c.border = BORDER
            c.alignment = Alignment(vertical="top", wrap_text=True,
                                    horizontal="center" if ci in (1, 7, 12, 14, 15) else "left")
        ws.cell(row=r, column=15).number_format = "yyyy-mm-dd"
        if sample:
            ws.row_dimensions[r].height = 70

    rng = lambda col: f"{col}{INV_FIRST}:{col}{INV_LAST}"
    for col, opts in (("C", ROLES), ("E", MODEL_TYPES), ("G", YESNO), ("H", AUTONOMY), ("L", LIFECYCLE), ("M", EU_CAT), ("N", YESNO)):
        dv = list_dv(opts)
        ws.add_data_validation(dv)
        dv.add(rng(col))
    dvd = date_dv()
    ws.add_data_validation(dvd)
    dvd.add(rng("O"))

    # High-risk / prohibited categories highlighted; production without impact assessment flagged
    ws.conditional_formatting.add(rng("M"), FormulaRule(
        formula=[f'OR(LEFT($M{INV_FIRST},9)="High-risk",$M{INV_FIRST}="Prohibited practice")'],
        fill=fill("F4B183"), font=Font(name=FONT, bold=True, color="7F3200")))
    ws.conditional_formatting.add(rng("N"), FormulaRule(
        formula=[f'AND($N{INV_FIRST}="No",OR($L{INV_FIRST}="Production",$L{INV_FIRST}="Pilot"))'],
        fill=fill("FFD9D9"), font=Font(name=FONT, bold=True, color="C00000")))

    ws.freeze_panes = "C5"
    ws.auto_filter.ref = f"A4:P{INV_LAST}"
    page_setup(ws)


# --------------------------------------------------------------------------- #
# 03_Risk_Scales
# --------------------------------------------------------------------------- #
def build_scales(wb: Workbook):
    ws = wb.create_sheet(S_SCALES)
    ws.sheet_properties.tabColor = MID_BLUE
    ws.sheet_view.showGridLines = False
    title(ws, "Risk Scales and Acceptance Criteria", "Calibrate the organisational thresholds before first use. Severity = highest of the three lenses.", width_cols=6)
    widths(ws, {"A": 12, "B": 18, "C": 44, "D": 44, "E": 44, "F": 44})

    put(ws, "A3", "LIKELIHOOD  (how likely is the scenario within the next 12 months, given how the system is used?)", font=f(bold=True, color=NAVY, size=11))
    header(ws, 4, ["Score", "Level", "Description", "Indicative frequency / probability", "Example (AI context)"])
    likelihood = [
        (1, "Rare", "Would need an unusual combination of conditions.", "Less than once in 10 years · < 5 %",
         "A well-tested rule-based system with a human check on every output produces a harmful recommendation."),
        (2, "Unlikely", "Could happen, not expected.", "Once in 3–10 years · 5–20 %",
         "A monitored classical model drifts past its alert threshold without anyone noticing for a quarter."),
        (3, "Possible", "Has happened to similar systems or organisations.", "Once in 1–3 years · 20–50 %",
         "A chatbot gives an incorrect answer that a customer acts on, with no AI disclosure."),
        (4, "Likely", "Will probably happen in the current set-up.", "About yearly · 50–80 %",
         "A third-party LLM receives personal data in prompts because no redaction exists."),
        (5, "Almost certain", "Already happening or structurally unavoidable.", "Several times a year · > 80 %",
         "An unreviewed vendor model is used for hiring decisions without bias testing or applicant information."),
    ]
    for i, rowdata in enumerate(likelihood):
        r = 5 + i
        for j, v in enumerate(rowdata):
            c = ws.cell(row=r, column=1 + j, value=v)
            c.font = f(bold=(j < 2))
            c.alignment = Alignment(horizontal="center" if j in (0, 1) else "left", vertical="top", wrap_text=True)
            c.border = BORDER
        ws.row_dimensions[r].height = 44

    put(ws, "A11", "SEVERITY  (worst credible consequence — score the HIGHEST of the three lenses)", font=f(bold=True, color=NAVY, size=11))
    header(ws, 12, ["Score", "Level", "Individuals (rights, safety, discrimination, privacy)", "Society (groups, public trust, environment, democracy)", "Organisation (legal, financial, operational, reputational)"])
    severity = [
        (1, "Negligible", "Inconvenience, easily reversed; no effect on rights or access to services.",
         "No measurable effect beyond the individuals involved.",
         "Loss under 5,000; disruption under 1 hour; no regulatory interest."),
        (2, "Minor", "Short-term disadvantage or annoyance; reversible with a request; limited personal data exposed.",
         "Small group affected; local, short-lived loss of trust.",
         "Loss 5,000–50,000; degraded process up to 4 hours; internal embarrassment."),
        (3, "Moderate", "Material disadvantage (denied a service, financial loss, distress) that can be corrected; sensitive data of a limited number of people exposed.",
         "A defined group is treated unfairly; local media or community concern; measurable environmental cost.",
         "Loss 50,000–250,000; critical process down up to a day; regulator enquiry; contract penalties."),
        (4, "Major", "Serious, hard-to-reverse harm: lost job or housing opportunity, wrongful denial of benefits, injury, large-scale exposure of personal data.",
         "Systematic discrimination against a protected group; manipulation of many people; national media; erosion of trust in a public service.",
         "Loss 250,000–1,000,000; critical process down 1–3 days; mandatory notifications; regulatory sanction; loss of a major customer."),
        (5, "Severe", "Threat to life, liberty or livelihood; irreversible harm; exposure of special-category data at scale.",
         "Harm to vulnerable populations at scale; interference with democratic processes or safety-critical infrastructure.",
         "Loss above 1,000,000 or viability threatened; prohibition of the system; criminal liability; sustained national coverage."),
    ]
    for i, rowdata in enumerate(severity):
        r = 13 + i
        for j, v in enumerate(rowdata):
            c = ws.cell(row=r, column=1 + j, value=v)
            c.font = f(bold=(j < 2))
            c.alignment = Alignment(horizontal="center" if j in (0, 1) else "left", vertical="top", wrap_text=True)
            c.border = BORDER
        ws.row_dimensions[r].height = 74

    put(ws, "A19", "RISK ACCEPTANCE CRITERIA  (suggested — align with your AI policy and risk appetite)", font=f(bold=True, color=NAVY, size=11))
    header(ws, 20, ["Rating", "Score range", "Required response", "Who may accept", "Treatment deadline", "Review frequency"])
    accept = {
        "Low": ("Accept by default; monitor model performance metrics.", "System owner", "None required", "Annually"),
        "Medium": ("Mitigate, or accept with documented justification.", "System owner, informed to AI governance lead", "Within 6 months", "Every 6 months"),
        "High": ("Treatment plan mandatory with owner, budget and date. Acceptance is exceptional.", "Senior management + AI governance lead", "Within 90 days", "Quarterly"),
        "Critical": ("Do not launch / pause the system until interim controls are in place.", "Executive management, with written rationale", "Within 30 days (interim controls now)", "Monthly until below High"),
    }
    for i, (name, lo, hi, bg, fg) in enumerate(reversed(BANDS)):
        r = 21 + i
        vals = [name, f"{lo} – {hi}", *accept[name]]
        for j, v in enumerate(vals):
            c = ws.cell(row=r, column=1 + j, value=v)
            c.border = BORDER
            c.alignment = Alignment(horizontal="center" if j < 2 else "left", vertical="top", wrap_text=True)
            c.font = f(bold=(j < 2), color=fg if j == 0 else "000000")
            if j == 0:
                c.fill = fill(bg)
        ws.row_dimensions[r].height = 44

    put(ws, "A26", "AUTONOMY LEVEL  (used in the inventory — higher autonomy usually raises likelihood of harm reaching people before a human notices)", font=f(bold=True, color=NAVY, size=11))
    header(ws, 27, ["Level", "Name", "Meaning", "Typical oversight expectation"])
    autonomy_rows = [
        ("1", "Informs", "Produces information a human reads before deciding.", "Human decides; AI output is one input among others."),
        ("2", "Recommends", "Proposes options or a ranking; a human chooses.", "Human can see alternatives and override without friction."),
        ("3", "Acts with approval", "Prepares an action that executes after a human approves.", "Approval is meaningful (time, information, competence) — not a rubber stamp."),
        ("4", "Acts autonomously", "Executes actions; humans monitor and can stop it.", "Monitoring, thresholds, kill switch and rollback are tested."),
    ]
    for i, vals in enumerate(autonomy_rows):
        r = 28 + i
        for j, v in enumerate(vals):
            c = ws.cell(row=r, column=1 + j, value=v)
            c.border = BORDER
            c.font = f(bold=(j < 2))
            c.alignment = Alignment(horizontal="center" if j == 0 else "left", vertical="top", wrap_text=True)
        ws.row_dimensions[r].height = 30
    put(ws, "A33", "Rating thresholds (1–4 / 5–9 / 10–16 / 17–25) are built into the register, the summary and the dashboard formulas. "
        "Change them consistently if you need different bands.", font=f(italic=True, color="595959"))
    ws.merge_cells("A33:F33")
    page_setup(ws)


# --------------------------------------------------------------------------- #
# 04_AI_Risk_Register
# --------------------------------------------------------------------------- #
REG_HEADERS = [
    "Risk ID", "System ID", "AI System Name", "Risk Category", "Risk Scenario / Description", "Cause / Source",
    "Affected Parties", "Severity Lens (driver)",
    "Inherent Likelihood (1-5)", "Inherent Severity (1-5)", "Inherent Score", "Inherent Rating",
    "Treatment", "Existing / Planned Controls", "ISO 42001 Annex A Reference", "Other References (ISO 27001 / NIST AI RMF)",
    "Residual Likelihood (1-5)", "Residual Severity (1-5)", "Residual Score", "Residual Rating",
    "Risk Owner (role)", "Target Date", "Status", "Last Review", "Comments",
]
LENS = ["Individuals", "Society", "Organisation"]

COLS = {name: get_column_letter(i + 1) for i, name in enumerate([
    "id", "sys", "sysname", "cat", "scenario", "cause", "parties", "lens", "iL", "iS", "iScore", "iR",
    "treat", "controls", "a42001", "other", "rL", "rS", "rScore", "rR", "owner", "target", "status", "review", "comments",
])}

# (id, system, category, scenario, cause, parties, lens, iL, iS, treatment, controls, a42001, other,
#  rL, rS, owner, target, status, review, comments)
REG_SAMPLES = [
    ("AIR-001", "AIS-003", CATEGORIES[0],
     "The screening model ranks applicants with employment gaps or non-local education lower, indirectly disadvantaging carers, migrants and older candidates.",
     "Vendor model trained on historical hiring outcomes; no disparate-impact testing on our applicant population; proxies for protected characteristics in features.",
     "Job applicants; works council; the organisation (discrimination claims)", "Individuals",
     4, 5, "Mitigate",
     "Planned: quarterly disparate-impact test per role family (selection-rate ratios); remove gap-length and school features; recruiter review of every shortlist; applicant notice.",
     "A.5.4, A.6.2.4, A.7.4, A.9.4", "ISO 27001: A.5.34 | NIST AI RMF: MEASURE 2.11, MANAGE 2.2",
     2, 4, "Head of Human Resources", date(2027, 1, 31), "In progress", date(2026, 10, 15),
     "First fairness test run on 3,000 historical applications; results under review with the vendor."),
    ("AIR-002", "AIS-003", CATEGORIES[7],
     "Use of AI to rank applicants for employment falls in a high-risk area of the EU AI Act; deployer obligations (human oversight, logging, informing workers' representatives and applicants) are not demonstrably met.",
     "System adopted as a SaaS feature without a regulatory classification; contract silent on provider obligations and documentation.",
     "Job applicants; the organisation (fines, suspension of use); the vendor", "Organisation",
     4, 4, "Mitigate",
     "Formal classification with legal counsel; obtain provider's technical documentation and instructions for use; log retention; trained reviewers; information to applicants and employee representatives; register use if required.",
     "A.2.2, A.3.2, A.6.2.3, A.8.2, A.10.3", "ISO 27001: A.5.31, A.5.19 | NIST AI RMF: GOVERN 1.1, MAP 1.1",
     2, 4, "Head of Human Resources", date(2027, 3, 31), "Open", date(2026, 10, 15),
     "Vendor documentation requested. Applicable dates to be confirmed by counsel."),
    ("AIR-003", "AIS-002", CATEGORIES[4],
     "A customer writes instructions inside a support message or a referenced document; the assistant follows them and reveals another customer's shipment details or drafts a refund it should not.",
     "Prompt injection through user content and retrieved tickets; retrieval not filtered by customer; tool actions run with the service account's permissions.",
     "Customers (data exposure); the organisation (breach notification, fraud)", "Individuals",
     4, 4, "Mitigate",
     "Retrieval filtered by customer ID before prompting; user content passed as data not instructions; tools limited to read-only in the pilot; adversarial prompt test set before each release; output logged with retrieved document IDs.",
     "A.6.2.4, A.6.2.6, A.6.2.8, A.7.4", "ISO 27001: A.8.3, A.8.26, A.8.28, A.8.29 | NIST AI RMF: MEASURE 2.7",
     2, 3, "Digital Platform Lead", date(2026, 12, 15), "In progress", date(2026, 10, 20),
     "Red-team prompt set (120 cases) written; 3 leaks found and fixed in pilot."),
    ("AIR-004", "AIS-002", CATEGORIES[3],
     "Names, addresses and free-text complaints are sent to the third-party model provider in prompts; retention and training-use terms were not confirmed; no legal basis documented for the new purpose.",
     "No redaction layer; standard provider terms accepted at sign-up; privacy notice does not mention AI-assisted support.",
     "Customers and their contacts; the organisation (data-protection enforcement)", "Individuals",
     4, 4, "Mitigate",
     "Pseudonymise identifiers before prompting; contract with zero-retention and no-training clauses and EU processing; update privacy notice; DPIA; prompt logs redacted and retained 30 days.",
     "A.7.3, A.7.5, A.8.2, A.10.3", "ISO 27001: A.5.19, A.5.20, A.5.34, A.8.12 | NIST AI RMF: MAP 4.1",
     2, 3, "Head of Customer Experience", date(2026, 12, 31), "Open", date(2026, 10, 3),
     "DPIA opened. Provider has confirmed zero-retention option is available in the enterprise tier."),
    ("AIR-005", "AIS-002", CATEGORIES[1],
     "Customers are not told they are chatting with an AI; the assistant invents delivery promises and policy details that customers rely on and later dispute.",
     "No disclosure in the chat UI; model allowed to answer outside the knowledge base; no confidence or citation shown.",
     "Customers (misinformation, financial decisions); support agents; the organisation (claims)", "Individuals",
     4, 3, "Mitigate",
     "Clear AI disclosure at the start of each chat and on drafts; answers restricted to retrieved sources with citations; 'I don't know' path to a human; disclaimer on commitments; weekly accuracy sampling.",
     "A.6.2.4, A.8.2, A.9.3, A.9.4", "NIST AI RMF: GOVERN 4.2, MEASURE 2.5",
     1, 3, "Head of Customer Experience", date(2026, 11, 30), "In progress", date(2026, 10, 20),
     "Disclosure banner live in pilot; citation feature in development."),
    ("AIR-006", "AIS-001", CATEGORIES[2],
     "After opening a new regional depot and changing delivery zones, the ETA model systematically under-estimates travel time; promised slots are missed and drivers accumulate overtime before anyone links it to the model.",
     "Monthly retraining cadence; no drift monitoring on input distributions; no business-metric alert tied to model version.",
     "Customers (missed slots); drivers (overtime); dispatch; the organisation (SLA penalties)", "Organisation",
     3, 3, "Mitigate",
     "Input and prediction drift monitoring with alerts; retrain trigger on network changes; model version recorded on every ETA; weekly dashboard comparing promised versus actual; rollback procedure tested.",
     "A.6.2.6, A.6.2.8, A.7.4, A.7.6", "ISO 27001: A.8.16, A.8.32 | NIST AI RMF: MEASURE 2.4, MANAGE 4.1",
     2, 2, "Head of Data Science", date(2027, 1, 15), "Open", date(2026, 9, 12),
     "Drift monitoring proof of concept scheduled for next sprint."),
    ("AIR-007", "AIS-001", CATEGORIES[5],
     "Automatic re-sequencing of routes during the day compresses breaks and pushes drivers towards legal driving-time limits; a fatigued driver is involved in a road accident.",
     "Optimiser objective rewards on-time rate only; break and driving-time rules are not hard constraints; drivers feel pressured to accept re-routes.",
     "Drivers and the public (safety); the organisation (liability, licence)", "Individuals",
     2, 5, "Mitigate",
     "Driving-time and break rules as hard constraints in the optimiser; re-routes within 2 hours of a limit blocked; driver can reject without penalty; monthly review of near-limit events with the safety officer.",
     "A.5.4, A.6.1.2, A.6.2.2, A.6.2.6, A.9.4", "NIST AI RMF: MAP 1.5, MANAGE 1.3",
     1, 4, "Head of Operations", date(2026, 12, 31), "In progress", date(2026, 10, 1),
     "Hard constraints implemented; reject-without-penalty policy agreed with the works council."),
    ("AIR-008", "AIS-001", CATEGORIES[6],
     "Retrained models are promoted to production by the data team without an approval gate, documented tests or a named accountable owner; after an incident nobody can say which model version produced a given route.",
     "No model release process; ownership split between operations and data science; event logs do not record model version.",
     "The organisation (accountability, audit findings); drivers and customers indirectly", "Organisation",
     3, 3, "Mitigate",
     "Named AI system owner; release checklist with sign-off (tests, fairness and safety checks, rollback plan); model registry with versions; version stamped in route events; quarterly review by the AI governance committee.",
     "A.3.2, A.4.2, A.6.2.3, A.6.2.5, A.6.2.8", "ISO 27001: A.5.2, A.8.32 | NIST AI RMF: GOVERN 2.1, MANAGE 2.3",
     1, 3, "Head of Operations", date(2027, 2, 28), "Open", date(2026, 9, 12),
     "Owner assigned; release checklist drafted."),
]


def build_register(wb: Workbook):
    ws = wb.create_sheet(S_REG)
    ws.sheet_properties.tabColor = "C55A11"
    title(ws, "AI Risk Register", "Likelihood × Severity. Blue = input; grey = formula. Rows 5–54. Sample risks are fictional — overwrite or delete them.", width_cols=25)
    groups = [("IDENTIFICATION", "A", "H", "2F5597"), ("INHERENT RISK", "I", "L", "C55A11"), ("TREATMENT", "M", "P", "548235"),
              ("RESIDUAL RISK", "Q", "T", "7030A0"), ("GOVERNANCE", "U", "Y", "595959")]
    for label, c1, c2, color in groups:
        ws.merge_cells(f"{c1}3:{c2}3")
        cell = ws[f"{c1}3"]
        cell.value = label
        cell.font = f(bold=True, color="FFFFFF")
        cell.fill = fill(color)
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[3].height = 20
    header(ws, 4, REG_HEADERS, height=52)
    widths(ws, {"A": 10, "B": 10, "C": 28, "D": 22, "E": 50, "F": 40, "G": 30, "H": 13, "I": 11, "J": 11, "K": 10, "L": 11,
                "M": 12, "N": 50, "O": 24, "P": 34, "Q": 11, "R": 11, "S": 10, "T": 11, "U": 22, "V": 12, "W": 12, "X": 12, "Y": 40})

    C = COLS
    formula_cols = {C["sysname"], C["iScore"], C["iR"], C["rScore"], C["rR"]}
    center_cols = {C["id"], C["sys"], C["lens"], C["iL"], C["iS"], C["iScore"], C["iR"], C["treat"], C["rL"], C["rS"],
                   C["rScore"], C["rR"], C["target"], C["status"], C["review"]}

    for r in range(REG_FIRST, REG_LAST + 1):
        sample = REG_SAMPLES[r - REG_FIRST] if r - REG_FIRST < len(REG_SAMPLES) else None
        values: dict[str, object] = {}
        if sample:
            (rid, sysid, cat, scenario, cause, parties, lens, iL, iS, treat, controls, a42001, other,
             rL, rS, owner, target, status, review, comments) = sample
            values = {C["id"]: rid, C["sys"]: sysid, C["cat"]: cat, C["scenario"]: scenario, C["cause"]: cause,
                      C["parties"]: parties, C["lens"]: lens, C["iL"]: iL, C["iS"]: iS, C["treat"]: treat,
                      C["controls"]: controls, C["a42001"]: a42001, C["other"]: other, C["rL"]: rL, C["rS"]: rS,
                      C["owner"]: owner, C["target"]: target, C["status"]: status, C["review"]: review, C["comments"]: comments}
        values[C["sysname"]] = (
            f'=IF(${C["sys"]}{r}="","",IFERROR(INDEX(\'{S_INV}\'!$B${INV_FIRST}:$B${INV_LAST},'
            f'MATCH(${C["sys"]}{r},\'{S_INV}\'!$A${INV_FIRST}:$A${INV_LAST},0)),"ID not found in inventory"))')
        values[C["iScore"]] = f'=IF(AND(ISNUMBER({C["iL"]}{r}),ISNUMBER({C["iS"]}{r})),{C["iL"]}{r}*{C["iS"]}{r},"")'
        values[C["iR"]] = rating_formula(f'{C["iScore"]}{r}')
        values[C["rScore"]] = f'=IF(AND(ISNUMBER({C["rL"]}{r}),ISNUMBER({C["rS"]}{r})),{C["rL"]}{r}*{C["rS"]}{r},"")'
        values[C["rR"]] = rating_formula(f'{C["rScore"]}{r}')

        for ci in range(1, len(REG_HEADERS) + 1):
            col = get_column_letter(ci)
            c = ws[f"{col}{r}"]
            if col in values:
                c.value = values[col]
            is_formula = col in formula_cols
            c.font = f(color="000000" if is_formula else INPUT_BLUE,
                       bold=(col in {C["iScore"], C["iR"], C["rScore"], C["rR"]}))
            if is_formula:
                c.fill = fill(PALE)
            c.border = BORDER
            c.alignment = Alignment(vertical="top", wrap_text=True, horizontal="center" if col in center_cols else "left")
        ws[f"{C['target']}{r}"].number_format = "yyyy-mm-dd"
        ws[f"{C['review']}{r}"].number_format = "yyyy-mm-dd"
        if sample:
            ws.row_dimensions[r].height = 118

    first, last = REG_FIRST, REG_LAST
    dv_sys = DataValidation(type="list", formula1=f"='{S_INV}'!$A${INV_FIRST}:$A${INV_LAST}", allow_blank=True)
    dv_sys.showErrorMessage = True
    dv_sys.errorStyle = "warning"
    dv_sys.errorTitle = "Unknown system"
    dv_sys.error = "This ID is not in the AI System Inventory. Add the system there first."
    ws.add_data_validation(dv_sys)
    dv_sys.add(f"{C['sys']}{first}:{C['sys']}{last}")

    dv_score = list_dv(["1", "2", "3", "4", "5"])
    dv_score.errorTitle = "Score must be 1–5"
    dv_score.error = "Enter a whole number from 1 to 5 (see 03_Risk_Scales)."
    ws.add_data_validation(dv_score)
    for key in ("iL", "iS", "rL", "rS"):
        dv_score.add(f"{C[key]}{first}:{C[key]}{last}")
    for key, opts in (("cat", CATEGORIES), ("lens", LENS), ("treat", TREATMENT), ("status", STATUS)):
        dv = list_dv(opts)
        ws.add_data_validation(dv)
        dv.add(f"{C[key]}{first}:{C[key]}{last}")
    dvd = date_dv()
    ws.add_data_validation(dvd)
    dvd.add(f"{C['target']}{first}:{C['target']}{last}")
    dvd.add(f"{C['review']}{first}:{C['review']}{last}")

    for key in ("iR", "rR"):
        band_rules(ws, C[key], first, last, text_based=True)
    for key in ("iScore", "rScore"):
        band_rules(ws, C[key], first, last, text_based=False)
    ws.conditional_formatting.add(
        f"{C['rScore']}{first}:{C['rScore']}{last}",
        FormulaRule(formula=[f"AND(ISNUMBER({C['rScore']}{first}),ISNUMBER({C['iScore']}{first}),{C['rScore']}{first}>{C['iScore']}{first})"],
                    font=Font(name=FONT, bold=True, color="FF0000"), fill=fill("FFD9D9")))
    ws.conditional_formatting.add(
        f"{C['target']}{first}:{C['target']}{last}",
        FormulaRule(formula=[f'AND(ISNUMBER({C["target"]}{first}),{C["target"]}{first}<TODAY(),'
                             f'{C["status"]}{first}<>"Closed",{C["status"]}{first}<>"Mitigated",{C["status"]}{first}<>"Accepted")'],
                    font=Font(name=FONT, bold=True, color="FF0000")))

    ws.freeze_panes = "D5"
    ws.auto_filter.ref = f"A4:Y{last}"
    page_setup(ws)
    ws.print_title_rows = "3:4"


# --------------------------------------------------------------------------- #
# 05_Impact_Assessment_Summary
# --------------------------------------------------------------------------- #
IMPACT_HEADERS = [
    "System ID", "AI System Name", "Organisation Role", "Autonomy Level", "EU AI Act Category", "Lifecycle Status",
    "Risks Recorded", "Open Risks", "Residual Critical", "Residual High", "Residual Medium", "Residual Low",
    "Highest Residual Score", "Highest Residual Rating", "Categories with High/Critical Residual",
    "Impact Assessment Conclusion", "Conditions / Required Actions", "Approved by (role)", "Next Review",
]

IMPACT_SAMPLES = {
    "AIS-001": ("Proceed with conditions", "Hard constraints on driving time (AIR-007) verified before next optimiser release; drift monitoring live by Q1.", "AI Governance Lead", date(2027, 3, 31)),
    "AIS-002": ("Proceed with conditions", "Pilot stays read-only and capped at 5 % of traffic until AIR-003 and AIR-004 are mitigated; DPIA completed.", "AI Governance Lead", date(2027, 1, 31)),
    "AIS-003": ("Do not proceed / redesign", "Suspend automated ranking; recruiters review all applications until fairness testing and the legal classification (AIR-001, AIR-002) are complete.", "Executive Committee", date(2026, 12, 15)),
}


def build_impact(wb: Workbook):
    ws = wb.create_sheet(S_IMPACT)
    ws.sheet_properties.tabColor = "7030A0"
    title(ws, "AI System Impact Assessment Summary",
          f"One row per system, pulled from {S_INV}; counts come from {S_REG}. Blue = input (conclusion, conditions, approval, review).", width_cols=19)
    widths(ws, {"A": 10, "B": 34, "C": 22, "D": 24, "E": 26, "F": 12, "G": 10, "H": 10, "I": 10, "J": 10, "K": 10, "L": 10,
                "M": 11, "N": 12, "O": 30, "P": 22, "Q": 52, "R": 20, "S": 12})
    header(ws, 4, IMPACT_HEADERS, height=44)

    I = f"'{S_INV}'!"
    R = f"'{S_REG}'!"
    C = COLS
    reg = lambda key: f"{R}${C[key]}${REG_FIRST}:${C[key]}${REG_LAST}"
    for i in range(INV_LAST - INV_FIRST + 1):
        r = 5 + i
        ir = INV_FIRST + i
        sysid = f"$A{r}"
        formulas = {
            "A": f'=IF({I}$A${ir}="","",{I}$A${ir})',
            "B": f'=IF({sysid}="","",{I}$B${ir})',
            "C": f'=IF({sysid}="","",{I}$C${ir})',
            "D": f'=IF({sysid}="","",{I}$H${ir})',
            "E": f'=IF({sysid}="","",{I}$M${ir})',
            "F": f'=IF({sysid}="","",{I}$L${ir})',
            "G": f'=IF({sysid}="","",COUNTIF({reg("sys")},{sysid}))',
            "H": f'=IF({sysid}="","",COUNTIFS({reg("sys")},{sysid},{reg("status")},"<>Closed"))',
            "I": f'=IF({sysid}="","",COUNTIFS({reg("sys")},{sysid},{reg("rR")},"Critical"))',
            "J": f'=IF({sysid}="","",COUNTIFS({reg("sys")},{sysid},{reg("rR")},"High"))',
            "K": f'=IF({sysid}="","",COUNTIFS({reg("sys")},{sysid},{reg("rR")},"Medium"))',
            "L": f'=IF({sysid}="","",COUNTIFS({reg("sys")},{sysid},{reg("rR")},"Low"))',
            "M": f'=IF({sysid}="","",IF(G{r}=0,"",_xlfn.MAXIFS({reg("rScore")},{reg("sys")},{sysid})))',
            "N": f'=IF(M{r}="","",IF(M{r}>=17,"Critical",IF(M{r}>=10,"High",IF(M{r}>=5,"Medium","Low"))))',
            "O": f'=IF({sysid}="","",IF(I{r}+J{r}=0,"–",TEXTJOIN(", ",TRUE,'
                 + ",".join(f'IF(COUNTIFS({reg("sys")},{sysid},{reg("cat")},"{cat}",{reg("rScore")},">=10")>0,"{cat}","")'
                            for cat in CATEGORIES) + ")))",
        }
        for col, formula in formulas.items():
            put(ws, f"{col}{r}", formula, font=f(bold=(col in "AIMN")), bg=PALE, border=True,
                align=Alignment(vertical="top", wrap_text=True, horizontal="center" if col in "ADFGHIJKLMN" else "left"))
        sample_id = INV_SAMPLES[i][0] if i < len(INV_SAMPLES) else None
        sample = IMPACT_SAMPLES.get(sample_id) if sample_id else None
        for j, col in enumerate("PQRS"):
            c = put(ws, f"{col}{r}", sample[j] if sample else None, font=f(color=INPUT_BLUE), border=True,
                    align=Alignment(vertical="top", wrap_text=True, horizontal="center" if col in "PS" else "left"))
            if col == "S":
                c.number_format = "yyyy-mm-dd"
        ws.row_dimensions[r].height = 58 if sample else 18

    # "O" column uses TEXTJOIN (Excel 2019+); mark with prefix for compatibility
    for i in range(INV_LAST - INV_FIRST + 1):
        c = ws[f"O{5 + i}"]
        c.value = c.value.replace("TEXTJOIN(", "_xlfn.TEXTJOIN(")

    dv_conc = list_dv(CONCLUSION)
    ws.add_data_validation(dv_conc)
    dv_conc.add(f"P5:P{4 + INV_LAST - INV_FIRST + 1}")
    dvd = date_dv()
    ws.add_data_validation(dvd)
    dvd.add(f"S5:S{4 + INV_LAST - INV_FIRST + 1}")

    last = 4 + INV_LAST - INV_FIRST + 1
    band_rules(ws, "N", 5, last, text_based=True)
    band_rules(ws, "M", 5, last, text_based=False)
    ws.conditional_formatting.add(f"P5:P{last}", FormulaRule(formula=['$P5="Do not proceed / redesign"'], fill=fill("C00000"), font=Font(name=FONT, bold=True, color="FFFFFF")))
    ws.conditional_formatting.add(f"P5:P{last}", FormulaRule(formula=['$P5="Proceed with conditions"'], fill=fill("FFE699"), font=Font(name=FONT, bold=True, color="7F6000")))
    ws.conditional_formatting.add(f"P5:P{last}", FormulaRule(formula=['$P5="Proceed"'], fill=fill("C6E0B4"), font=Font(name=FONT, bold=True, color="1E4620")))
    ws.conditional_formatting.add(f"S5:S{last}", FormulaRule(formula=['AND(ISNUMBER($S5),$S5<TODAY())'], font=Font(name=FONT, bold=True, color="FF0000")))

    r = last + 2
    put(ws, f"A{r}", "HOW TO READ THIS SHEET", font=f(bold=True, color=NAVY, size=11))
    notes = [
        "Each row is the roll-up required for an AI system impact assessment (ISO/IEC 42001 clause 6.1.4, Annex A.5): who is affected, how autonomous the system is, and what the residual risk looks like after treatment.",
        "'Categories with High/Critical Residual' lists the risk categories that still score 10 or more after treatment — those are the conditions to write down before approving.",
        "The conclusion is a human decision: Proceed · Proceed with conditions · Do not proceed / redesign. A system with any Critical residual risk should not be 'Proceed'.",
        "Record the approving role and the next review date (at least yearly, or on significant change, incident or new regulation).",
    ]
    for i, t in enumerate(notes):
        ws.merge_cells(f"A{r + 1 + i}:S{r + 1 + i}")
        put(ws, f"A{r + 1 + i}", t, align=Alignment(vertical="center", wrap_text=True))
        ws.row_dimensions[r + 1 + i].height = 30
    ws.freeze_panes = "C5"
    page_setup(ws)


# --------------------------------------------------------------------------- #
# 06_Dashboard
# --------------------------------------------------------------------------- #
def build_dashboard(wb: Workbook):
    ws = wb.create_sheet(S_DASH)
    ws.sheet_properties.tabColor = "C00000"
    ws.sheet_view.showGridLines = False
    title(ws, "AI Risk Dashboard", f"Figures update automatically from {S_REG} and {S_INV}.", width_cols=14)
    widths(ws, {"A": 32, "B": 14, "C": 14, "D": 14, "E": 14, "F": 4, "G": 14, "H": 14, "I": 14, "J": 14, "K": 14, "L": 14, "M": 14, "N": 14})
    R = f"'{S_REG}'!"
    I = f"'{S_INV}'!"
    C = COLS
    reg = lambda key: f"{R}${C[key]}${REG_FIRST}:${C[key]}${REG_LAST}"
    inv = lambda col: f"{I}${col}${INV_FIRST}:${col}${INV_LAST}"

    kpis = [
        ("AI systems inventoried", f"=COUNTA({inv('A')})", "0"),
        ("Systems in production or pilot without impact assessment", f'=COUNTIFS({inv("L")},"Production",{inv("N")},"No")+COUNTIFS({inv("L")},"Pilot",{inv("N")},"No")', "0"),
        ("Risks recorded", f"=COUNTA({reg('id')})", "0"),
        ("Open risks (not Closed)", f'=COUNTA({reg("id")})-COUNTIF({reg("status")},"Closed")', "0"),
        ("Highest residual score", f'=IF(COUNT({reg("rScore")})=0,"–",MAX({reg("rScore")}))', "0"),
        ("Overdue actions", f'=COUNTIFS({reg("target")},"<"&TODAY(),{reg("status")},"<>Closed",{reg("status")},"<>Mitigated",{reg("status")},"<>Accepted")', "0"),
    ]
    positions = [("A", "A"), ("B", "C"), ("D", "E"), ("G", "H"), ("I", "J"), ("K", "L")]
    for (label, formula, fmt), (c1, c2) in zip(kpis, positions):
        if c1 != c2:
            ws.merge_cells(f"{c1}4:{c2}4")
            ws.merge_cells(f"{c1}5:{c2}5")
        put(ws, f"{c1}4", label, font=f(bold=True, color="FFFFFF"), bg=MID_BLUE, align=Alignment(horizontal="center", vertical="center", wrap_text=True))
        put(ws, f"{c1}5", formula, font=f(bold=True, size=18, color=NAVY), bg=LIGHT_BLUE, align=Alignment(horizontal="center", vertical="center"), fmt=fmt)
        for cc in {c1, c2}:
            ws[f"{cc}4"].fill = fill(MID_BLUE)
            ws[f"{cc}5"].fill = fill(LIGHT_BLUE)
    ws.row_dimensions[4].height = 40
    ws.row_dimensions[5].height = 40

    # ---- by rating
    put(ws, "A7", "RISKS BY RATING", font=f(bold=True, color=NAVY, size=11))
    header(ws, 8, ["Rating", "Score range", "Inherent", "Residual", "Reduction"], height=28)
    order = list(reversed(BANDS))
    for i, (name, lo, hi, bg, fg) in enumerate(order):
        r = 9 + i
        put(ws, f"A{r}", name, font=f(bold=True, color=fg), bg=bg, align=Alignment(horizontal="center", vertical="center"), border=True)
        put(ws, f"B{r}", f"{lo} – {hi}", align=Alignment(horizontal="center", vertical="center"), border=True)
        put(ws, f"C{r}", f'=COUNTIF({reg("iR")},$A{r})', font=f(bold=True), align=Alignment(horizontal="center", vertical="center"), border=True)
        put(ws, f"D{r}", f'=COUNTIF({reg("rR")},$A{r})', font=f(bold=True), align=Alignment(horizontal="center", vertical="center"), border=True)
        put(ws, f"E{r}", f"=C{r}-D{r}", align=Alignment(horizontal="center", vertical="center"), border=True, fmt="+0;-0;0")
        ws.row_dimensions[r].height = 22
    put(ws, "A13", "Total rated", font=f(bold=True), bg=PALE, align=Alignment(horizontal="center", vertical="center"), border=True)
    put(ws, "B13", "", bg=PALE, border=True)
    put(ws, "C13", "=SUM(C9:C12)", font=f(bold=True), bg=PALE, align=Alignment(horizontal="center", vertical="center"), border=True)
    put(ws, "D13", "=SUM(D9:D12)", font=f(bold=True), bg=PALE, align=Alignment(horizontal="center", vertical="center"), border=True)
    put(ws, "E13", "", bg=PALE, border=True)

    # ---- by category
    put(ws, "A15", "RISKS BY CATEGORY", font=f(bold=True, color=NAVY, size=11))
    header(ws, 16, ["Category", "Risks", "Inherent High+", "Residual High+", "Open"], height=28)
    for i, cat in enumerate(CATEGORIES):
        r = 17 + i
        put(ws, f"A{r}", cat, align=Alignment(horizontal="left", vertical="center"), border=True)
        put(ws, f"B{r}", f'=COUNTIF({reg("cat")},$A{r})', font=f(bold=True), align=Alignment(horizontal="center", vertical="center"), border=True)
        put(ws, f"C{r}", f'=COUNTIFS({reg("cat")},$A{r},{reg("iScore")},">=10")', align=Alignment(horizontal="center", vertical="center"), border=True)
        put(ws, f"D{r}", f'=COUNTIFS({reg("cat")},$A{r},{reg("rScore")},">=10")', align=Alignment(horizontal="center", vertical="center"), border=True)
        put(ws, f"E{r}", f'=COUNTIFS({reg("cat")},$A{r},{reg("status")},"<>Closed")', align=Alignment(horizontal="center", vertical="center"), border=True)
        ws.row_dimensions[r].height = 20
    r_tot = 17 + len(CATEGORIES)
    put(ws, f"A{r_tot}", "Total", font=f(bold=True), bg=PALE, align=Alignment(horizontal="left", vertical="center"), border=True)
    for col in "BCDE":
        put(ws, f"{col}{r_tot}", f"=SUM({col}17:{col}{r_tot - 1})", font=f(bold=True), bg=PALE, align=Alignment(horizontal="center", vertical="center"), border=True)

    # ---- by EU AI Act category (inventory) and by treatment / status
    put(ws, "A27", "SYSTEMS BY EU AI ACT CATEGORY", font=f(bold=True, color=NAVY, size=11))
    header(ws, 28, ["Category", "Systems"], height=24)
    for i, cat in enumerate(EU_CAT):
        r = 29 + i
        put(ws, f"A{r}", cat, align=Alignment(horizontal="left", vertical="center"), border=True)
        put(ws, f"B{r}", f'=COUNTIF({inv("M")},$A{r})', font=f(bold=True), align=Alignment(horizontal="center", vertical="center"), border=True)

    put(ws, "G27", "BY TREATMENT", font=f(bold=True, color=NAVY, size=11))
    header(ws, 28, ["Decision", "Count"], start_col=7, height=24)
    for i, t in enumerate(TREATMENT):
        r = 29 + i
        put(ws, f"G{r}", t, align=Alignment(horizontal="left", vertical="center"), border=True)
        put(ws, f"H{r}", f'=COUNTIF({reg("treat")},$G{r})', font=f(bold=True), align=Alignment(horizontal="center", vertical="center"), border=True)
    put(ws, "J27", "BY STATUS", font=f(bold=True, color=NAVY, size=11))
    header(ws, 28, ["Status", "Count"], start_col=10, height=24)
    for i, s in enumerate(STATUS):
        r = 29 + i
        put(ws, f"J{r}", s, align=Alignment(horizontal="left", vertical="center"), border=True)
        put(ws, f"K{r}", f'=COUNTIF({reg("status")},$J{r})', font=f(bold=True), align=Alignment(horizontal="center", vertical="center"), border=True)

    # ---- charts
    chart = BarChart()
    chart.type = "col"
    chart.grouping = "clustered"
    chart.title = "Inherent vs residual risks by rating"
    chart.y_axis.title = "Number of risks"
    chart.y_axis.majorGridlines = None
    data = Reference(ws, min_col=3, max_col=4, min_row=8, max_row=12)
    cats = Reference(ws, min_col=1, min_row=9, max_row=12)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    chart.height = 7.5
    chart.width = 16
    chart.series[0].graphicalProperties.solidFill = "C55A11"
    chart.series[1].graphicalProperties.solidFill = "2F5597"
    ws.add_chart(chart, "G7")

    chart2 = BarChart()
    chart2.type = "bar"
    chart2.grouping = "clustered"
    chart2.title = "Risks by category (inherent vs residual at High or above)"
    chart2.x_axis.title = None
    chart2.y_axis.majorGridlines = None
    data2 = Reference(ws, min_col=3, max_col=4, min_row=16, max_row=16 + len(CATEGORIES))
    cats2 = Reference(ws, min_col=1, min_row=17, max_row=16 + len(CATEGORIES))
    chart2.add_data(data2, titles_from_data=True)
    chart2.set_categories(cats2)
    chart2.height = 9
    chart2.width = 16
    chart2.series[0].graphicalProperties.solidFill = "C55A11"
    chart2.series[1].graphicalProperties.solidFill = "2F5597"
    ws.add_chart(chart2, "G38")

    put(ws, "A38", "HOW TO USE IN THE AI GOVERNANCE COMMITTEE", font=f(bold=True, color=NAVY, size=11))
    tips = [
        "1. Start with systems in production or pilot that have no impact assessment — they are the unknown risk.",
        "2. Review every Critical and High residual risk: is the treatment on track, is the interim control in place?",
        "3. Look at the category chart: several systems with the same weak category (e.g. transparency) point to a missing organisational control, not a project issue.",
        "4. Check the EU AI Act table: any High-risk or Prohibited entry needs a documented legal position.",
        "5. Record decisions in 05_Impact_Assessment_Summary (conclusion, conditions, approver, next review).",
    ]
    for i, t in enumerate(tips):
        r = 39 + i
        ws.merge_cells(f"A{r}:E{r}")
        put(ws, f"A{r}", t, align=Alignment(vertical="center", wrap_text=True))
        ws.row_dimensions[r].height = 34
    page_setup(ws)


# --------------------------------------------------------------------------- #
def main(out: Path) -> None:
    wb = Workbook()
    build_methodology(wb)
    build_inventory(wb)
    build_scales(wb)
    build_register(wb)
    build_impact(wb)
    build_dashboard(wb)
    wb.properties.title = "AI Risk Assessment Template"
    wb.properties.subject = "AI risk assessment and impact assessment workbook (ISO/IEC 42001, EU AI Act)"
    wb.properties.creator = "Open-source contributors"
    wb.properties.description = "MIT-licensed template. All sample data is fictional."
    wb.calculation.fullCalcOnLoad = True
    wb.active = 0
    wb.save(out)
    print(f"Wrote {out}")


if __name__ == "__main__":
    default = Path(__file__).resolve().parent.parent / "AI-Risk-Assessment-Template.xlsx"
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else default)
