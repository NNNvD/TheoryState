/* Theory-in-Psychology Sentiment Survey (SurveyJS + Google Sheets backend)
 *
 * Setup steps:
 * 1) Deploy the Google Apps Script web app (see README.md) and paste its URL below.
 * 2) (Optional) Update SURVEY_YEAR and INSTRUMENT_VERSION annually.
 */

const APPS_SCRIPT_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxFyvSXpJZXtVfsLcxcLte8Yo7GXdG8nM7PQVTQIYZm2S-qAoqPFwtPSdAH9LL18C8m/exec";
const SURVEY_YEAR = 2026;
const INSTRUMENT_VERSION = "2026.1";

// 7-point scales + N/A (as a last option)
const RATE_VALUES = [
  { value: 1, text: "1" },
  { value: 2, text: "2" },
  { value: 3, text: "3" },
  { value: 4, text: "4" },
  { value: 5, text: "5" },
  { value: 6, text: "6" },
  { value: 7, text: "7" },
  { value: "NA", text: "N/A" }
];

function slugify(str) {
  return String(str)
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function uuid() {
  if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
  // Fallback
  return "id_" + Math.random().toString(16).slice(2) + "_" + Date.now().toString(16);
}

function itemPanel(item) {
  const slug = item.slug || slugify(item.name);
  const prefix = (item.table === 1 ? "t1" : "t2") + "_" + slug;

  const severityEndpoints =
    item.table === 1
      ? { min: "Minor problem", max: "Major problem" }
      : { min: "Minor cause", max: "Major cause" };

  return {
    type: "panel",
    name: prefix + "_panel",
    elements: [
      {
        type: "html",
        html:
          `<div style="padding: 8px 0 2px 0;">
             <div style="font-weight:700; font-size:1.05rem;">${item.name}</div>
             <div style="margin-top:4px; color:#555;">${item.description}</div>
           </div>`
      },
      {
        type: "rating",
        name: prefix + "_agreement",
        title: "Agreement",
        isRequired: true,
        rateValues: RATE_VALUES,
        minRateDescription: "Strongly disagree",
        maxRateDescription: "Strongly agree"
      },
      {
        type: "rating",
        name: prefix + "_severity",
        title: "Severity",
        isRequired: true,
        rateValues: RATE_VALUES,
        minRateDescription: severityEndpoints.min,
        maxRateDescription: severityEndpoints.max
      }
    ]
  };
}

function buildSurvey(items) {
  const table1 = items.filter(i => i.table === 1);
  const table2 = items.filter(i => i.table === 2);

  return {
    title: `Perspectives on Theory in Psychological Science (${SURVEY_YEAR})`,
    showQuestionNumbers: "off",
    showProgressBar: "top",
    progressBarType: "pages",
    completedHtml:
      "<h3>Thanks — your responses have been recorded.</h3>" +
      "<p>You may now close this window.</p>",
    pages: [
      {
        name: "table1",
        title: "Table 1 — Diagnoses",
        description:
          "For each diagnostic item, rate agreement (is it the case?) and severity (how big of a problem?).",
        elements: table1.map(itemPanel)
      },
      {
        name: "table2",
        title: "Table 2 — Consequences",
        description:
          "For each consequence item, rate agreement (is it the case?) and severity (how big of a cause is lack of theory development?).",
        elements: table2.map(itemPanel)
      }
    ]
  };
}

async function main() {
  // Load item bank
  const items = await fetch("./items.json", { cache: "no-store" }).then(r => r.json());

  const surveyJson = buildSurvey(items);
  const survey = new Survey.Model(surveyJson);

  // Submit to Google Apps Script -> Google Sheet
  survey.onComplete.add((sender) => {
    const payload = {
      submitted_at: new Date().toISOString(),
      response_id: uuid(),
      meta_year: SURVEY_YEAR,
      meta_version: INSTRUMENT_VERSION,
      data: sender.data
    };

    // NOTE: Google Apps Script web apps don't reliably return CORS headers.
    // We therefore post as text/plain with mode:no-cors (fire-and-forget).
    fetch(APPS_SCRIPT_WEBAPP_URL, {
      method: "POST",
      mode: "no-cors",
      headers: { "Content-Type": "text/plain;charset=utf-8" },
      body: JSON.stringify(payload)
    }).catch((err) => console.error("Submission failed:", err));
  });

  document.addEventListener("DOMContentLoaded", function() {
    survey.render(document.getElementById("surveyContainer"));
  });
}

main().catch(err => {
  console.error(err);
  const el = document.getElementById("surveyContainer");
  if (el) el.innerHTML = "<p><b>Error:</b> Failed to load survey resources.</p>";
});
