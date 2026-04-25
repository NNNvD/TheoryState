# Codex task brief: incorporate latest dashboard feedback only

## Scope
Implement only the changes listed below. Everything else in the dashboard should stay the same.

Do not redesign unrelated pages, charts, filters, data processing, colors, or layout unless a change is explicitly required by one of the tasks below.

---

# Task 1 — Rename sidebar/page labels

## Change
The current page labels `Table 1` and `Table 2` are too vague for visitors who do not already know the statement.

## Required implementation
In the sidebar/navigation, use:

1. **Overview**
2. **Diagnoses**
3. **Consequences**

## Page titles
Use more informative page titles:

- **Diagnoses: Problems in Theory Development**
- **Consequences: Effects of Weak Theory Development**

Do not use `Table 1` or `Table 2` as standalone navigation labels or page titles. It is fine to mention Table 1/Table 2 in explanatory text where useful.

---

# Task 2 — Make the intro expander open only on the Overview page

## Change
The “About this dashboard and survey” expander should orient first-time visitors on the Overview page, but it should not take up space by default on the Diagnoses and Consequences pages.

## Required implementation
Use the same expander title on all pages:

**About this dashboard and survey**

Default state:
- **Overview**: expanded by default
- **Diagnoses**: collapsed by default
- **Consequences**: collapsed by default

Everything else about the intro placement should stay the same unless required by Task 3.

---

# Task 3 — Add a survey goal/invitation to intro text

## Change
The intro should not become a long explanation of the paper. It should remain short and only add 1–2 sentences about the survey and its goal.

## Required visible sentence
Keep the visible sentence:

**This dashboard presents results from the survey accompanying the statement *The state and status of theory in psychological science*.**

Requirements:
- The statement title must be italicized.
- The statement title must link to: `https://doi.org/10.31234/osf.io/2fjx4_v2`

## Required expander text
Inside the **About this dashboard and survey** expander, keep the current text as is and add details about the survey. Use wording close to:

> This survey asks psychological scientists to evaluate possible problems in the current state of theory development and possible consequences for psychological science. The goal is to collect broad perspectives on which issues are seen as common, harmful, or consequential, and to track how these perspectives change over time.

Then add a warm invitation with the survey link:

> You are warmly invited to participate in the survey here: [survey link]

## Requirements
- Keep the survey invitation clearly visible and clickable.
- Do not use the wording “You can also complete the survey here.”
- Do not add a long summary of the full statement.
- Do not add detailed descriptions of all diagnoses/consequences in the intro.
- Keep the intro short enough that results remain the focus.

---

# Task 4 — Improve Overview section headings and descriptions

## Change
The Overview section headings and descriptions should be clearer for first-time visitors.

## Diagnoses section
Replace the current heading with:

**Overall assessment of problems in theory development**

Use concise description text close to:

> This section covers overall survey questions related to possible problems in the current state of theory development in psychology. These questions concern the diagnoses listed in Table 1 of the statement, such as **weakly specified theories**, **limited derivation of hypotheses from theory**, and **weak feedback from empirical results into theory improvement.**

## Consequences section
Replace the current heading with:

**Overall assessment of consequences of weak theory development**

Use concise description text close to:

> This section covers overall survey questions related to possible consequences of weak theory development. These questions concern the consequences listed in Table 2 of the statement, such as **low replication rates** and **overproduction of isolated effects.**

## Requirements
- Keep descriptions short and readable.
- Avoid overly technical wording.
- Avoid implying anything inaccurate about aggregation. If the values are means across items, it is acceptable to add a short sentence such as: “The bars summarize mean responses across the relevant survey items.”
- Everything else in these sections should remain unchanged unless required by another task.

---

# Task 5 — Make it explicit that bars show means

## Change
It should be clear whether the bar values show means or medians.

## Required implementation
For all bars affected by this dashboard feedback:
- label values as means;
- use `Mean: X.X / 7` where there is enough space;
- if space inside a bar is limited, use `X.X / 7` inside the bar but provide a nearby label/caption/tooltip that clearly states these values are means.

## Requirements
- Do not change the underlying statistic unless explicitly requested.
- If the current app uses means, continue using means.
- Do not label anything “Median” unless the computation actually uses medians.

---

# Task 6 — Add item-level overview figure to Diagnoses page

## Change
The Diagnoses page should include a compact overview figure before the detailed item-by-item blocks.

## Placement
Add the new figure near the top of the Diagnoses page, before the detailed item blocks.

## Section title
**Item-level overview**

## Short description
Use:

> Use the selector below to compare diagnosis items on one survey question at a time. Detailed item results are shown further down the page.

## Selector
Add a selector labeled:

**Select question**

Options:
1. **Common in respondents’ own subfield**
2. **Common in psychology overall**
3. **Harmful if present**

## Figure
Create a horizontal bar chart:
- y-axis: all 13 diagnosis item names
- x-axis: original 1–7 score
- value labels: `Mean: X.X / 7`
- sorted descending by the selected question
- color changes according to selected question:
  - blue = Common in respondents’ own subfield
  - orange = Common in psychology overall
  - green = Harmful if present

## Scale anchors
Show endpoint meanings:
- For commonness questions:
  - **1 = Not common at all**
  - **7 = Very common**
- For harmfulness:
  - **1 = Not harmful at all**
  - **7 = Extremely harmful**

## Requirements
- Do not remove the detailed item blocks below.
- Do not replace the existing detailed item-level displays.
- Keep the figure compact and readable.

---

# Task 7 — Add item-level overview figure to Consequences page

## Change
The Consequences page should include a compact overview figure before the detailed item-by-item blocks.

## Placement
Add the new figure near the top of the Consequences page, before the detailed item blocks.

## Section title
**Item-level overview**

## Short description
Use:

> Use the selector below to compare consequences on one survey question at a time. Detailed item results are shown further down the page.

## Selector
Add a selector labeled:

**Select question**

Options:
1. **Agreement that limited theory development contributes**
2. **Magnitude of that contribution**

## Figure
Create a horizontal bar chart:
- y-axis: all 5 consequence item names
- x-axis: original 1–7 score
- value labels: `Mean: X.X / 7`
- sorted descending by selected question
- color changes according to selected question:
  - purple = Agreement that limited theory development contributes
  - red = Magnitude of that contribution

## Scale anchors
Show endpoint meanings:
- For agreement:
  - **1 = Strongly disagree**
  - **7 = Strongly agree**
- For magnitude:
  - **1 = Negligible cause**
  - **7 = Major cause**

## Requirements
- Do not remove the detailed item blocks below.
- Do not replace the existing detailed item-level displays.
- Keep the figure compact and readable.

---

# Task 8 — Acceptance checklist

Before finishing, check the work against this list:

## Navigation and titles
- [ ] Sidebar labels are Overview, Diagnoses, Consequences.
- [ ] Diagnoses page title is not merely “Table 1.”
- [ ] Consequences page title is not merely “Table 2.”

## Intro
- [ ] Overview intro expander is open by default.
- [ ] Diagnoses intro expander is collapsed by default.
- [ ] Consequences intro expander is collapsed by default.
- [ ] Intro remains short.
- [ ] Intro includes a clear survey goal.
- [ ] Intro includes a warm clickable survey invitation.
- [ ] The linked statement title is italicized and links to `https://doi.org/10.31234/osf.io/2fjx4_v2`.

## Overview wording
- [ ] Overview section headings are updated.
- [ ] Overview descriptions are concise and less technical.
- [ ] The wording does not misleadingly describe what is being aggregated.

## Means
- [ ] Bar values are clearly labeled as means wherever this feedback applies.

## New item-level overview figures
- [ ] Diagnoses page has a selector-based item-level overview figure above the detailed item blocks.
- [ ] Consequences page has a selector-based item-level overview figure above the detailed item blocks.
- [ ] Detailed item blocks remain in place.
- [ ] Existing filters still work.

## Scope check
- [ ] No unrelated dashboard functionality was changed.
- [ ] Everything not explicitly listed in this task brief remains the same.
