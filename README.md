<div align="center">

# BizSage

### Financial and operational decision support for Pakistani restaurants

A Python and Streamlit expert system that investigates possible reasons a restaurant's
profit is under pressure, explains the evidence, and compares practical options.
**BizSage supports the owner's decision; it does not make the decision for them.**

[About](#about) · [Features](#features) · [Setup](#getting-started) · [How it works](#expert-system-methodology) · [Tests](#tests) · [License](#license)

</div>

## About

BizSage is an educational **expert system and decision support system (DSS)** for
small restaurants. It helps owners examine issues such as falling revenue, staffing
that does not match customer demand, food costs, wastage, cash flow, and debt.

The project uses **declarative JSON knowledge**, interpreted by a Python inference
engine. It contains **60 unique diagnostic conditions** across six categories,
plus exclusion and chained rules. The guided Streamlit interface accepts incomplete
information, shows why a finding is supported or weakened, and compares options with
pros, cons, scores, assumptions, and illustrative estimates.

Demo businesses and branch records are fictional. Findings are evidence-based
confidence scores, not statistical probabilities or professional financial advice.

## Features

- **Guided Streamlit workflow:** Start → Business information → Investigation → Findings and options.
- **60 unique diagnostic conditions:** Ten in each of six restaurant-operation categories.
- **Forward-chaining inference:** Rules can assert facts that enable further rules.
- **Explainable findings:** Review evidence for and against possible causes and see which rules fired.
- **Incomplete-data handling:** Blank or unknown inputs remain unknown; they are not silently treated as zero or “No.”
- **Uncertainty and data-quality support:** Handles approximate answers, contradictions, and overlapping evidence.
- **Decision support:** Compare alternatives using weighted criteria, visible pros and cons, and editable assumptions. The owner chooses.
- **Branch comparison:** Explore branch revenue trends, branch similarity, and closure or operating alternatives using the included fictional sample or your own data.
- **Pakistani examples and inputs:** Includes fictional Karachi, Lahore, and highway restaurant examples, plus support for common numeric formats such as `4.5 lac` and `450k`.

## Tech stack

Python · Streamlit · pandas · NumPy · Plotly · pytest

## How it works

```text
Business profile and monthly figures
                 │
                 ▼
       Derived financial facts
                 │
                 ▼
 JSON knowledge base ──> Python rule interpreter
                              │
                              ▼
               Inference and certainty factors
                              │
                              ▼
        Explained findings and missing evidence
                              │
                              ▼
      DSS compares options; owner makes the choice
```

### Expert-system methodology

1. **Knowledge base:** `knowledge_base/` stores facts, thresholds, hypotheses, diagnostic rules, exclusions, chained rules, and decision strategies as JSON.
2. **Working memory:** The system stores known facts, certainty, and their source. Missing, unknown, and disputed facts are not treated as false.
3. **Rule interpretation:** A generic Python interpreter evaluates declarative conditions without embedding restaurant-specific thresholds in SQL or in the inference algorithm.
4. **Forward chaining:** Matching rules fire; any new facts they assert can enable other rules in a later reasoning cycle.
5. **Hypothesis evaluation:** Certainty factors combine evidence for and against each possible cause. Related evidence is dampened to reduce double counting.
6. **Question selection:** The system ranks useful unanswered questions based on how much they could clarify unresolved causes.
7. **Decision support:** A separate weighted scoring process compares possible actions and their trade-offs. It informs the owner rather than choosing automatically.

## Getting started

### Requirements

- Python 3.10 or later
- Internet access is not needed to run the local app after installing dependencies.

### Install

Create and activate a virtual environment from the project root.

**Windows (PowerShell)**

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### Run the Streamlit app

```bash
streamlit run app.py
```

Open the local address printed in the terminal. Start with a fictional example or
enter your own restaurant information. Leave figures blank when you do not know them.

### Public access (WAN)

The commands above run the app locally; they do **not** make it available over the
internet. To provide WAN or mobile-data access, deploy the project to a public
Streamlit-compatible host and test the resulting URL from outside your local network,
including on mobile data. No public deployment or 3G performance is claimed by this
repository.

## Tests

Run the suite from the project root:

```bash
python -m pytest -q
```

Or use the included runner:

```bash
python -m tests.run_all
```

Tests cover knowledge-base validation and rule uniqueness, every rule's firing
behavior, inference and chaining, uncertainty, missing and contradictory data,
financial calculations, decision scoring, and branch comparisons.

## Project structure

```text
app.py                 Streamlit entry point and navigation
config.py              Project identity, reasoning bands, and editable assumptions
knowledge_base/        Declarative JSON rules, facts, thresholds, and strategies
expert_system/         Working memory, inference, certainty, questions, explanations
calculations/          Financial and operational fact derivation
decision_support/      Option scoring, estimates, and branch analysis
ui/                    Guided Streamlit pages, components, charts, and theme
demo_data/              Fictional restaurant and branch examples
tests/                  Automated regression tests
tools/                  Knowledge-base documentation utility
```

## Limitations

- Thresholds and certainty factors are educational starting values, not statistically validated industry standards.
- Support scores indicate evidence strength under the rules; they are **not probabilities**.
- Option estimates depend on user-provided figures and editable assumptions. They are illustrative, not forecasts.
- The fictional examples do not represent real businesses or financial records.
- BizSage is not professional accounting, investment, or business advice.
- Public WAN availability and performance on 3G depend on deployment and have not been verified here.

## Author

**Amna Mohsin** · Roll No: **CT-24169**

## License

The project-authored software is licensed under the MIT License; see [`LICENSE`](LICENSE).
This license does not replace the licenses of Python dependencies or other third-party
materials.

## Academic use

This project was developed for educational use. If you reuse or adapt it, credit the
author and follow your institution's academic-integrity requirements.
