/**
 * Google Apps Script backend for SurveyJS -> Google Sheets.
 *
 * 1) Create a Google Sheet (e.g., "Theory Survey Responses")
 * 2) Extensions -> Apps Script -> paste this whole file into Code.gs
 * 3) Fill in SPREADSHEET_ID and SHEET_NAME
 * 4) Deploy -> New deployment -> Web app
 *    - Execute as: Me
 *    - Who has access: Anyone
 * 5) Copy the Web app URL and paste it into app.js (APPS_SCRIPT_WEBAPP_URL)
 */

const SPREADSHEET_ID = "PASTE_YOUR_SPREADSHEET_ID_HERE";
const SHEET_NAME = "responses";

function doGet() {
  return ContentService.createTextOutput("ok");
}

function doPost(e) {
  const sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(SHEET_NAME)
    || SpreadsheetApp.openById(SPREADSHEET_ID).insertSheet(SHEET_NAME);

  const raw = (e && e.postData && e.postData.contents) ? e.postData.contents : "{}";
  let payload;
  try {
    payload = JSON.parse(raw);
  } catch (err) {
    // Store malformed payload for debugging
    payload = { submitted_at: new Date().toISOString(), parse_error: String(err), raw_payload: raw };
  }

  // Expect: { submitted_at, response_id, meta_year, meta_version, data: { ...questionName: value... } }
  const meta = Object.assign({}, payload);
  const data = (payload && typeof payload.data === "object" && payload.data !== null) ? payload.data : {};
  delete meta.data;

  const record = Object.assign({}, meta, data);

  // Ensure a header row that includes all keys seen so far
  const headerRange = sheet.getRange(1, 1, 1, Math.max(sheet.getLastColumn(), 1));
  const headerValues = headerRange.getValues()[0];
  const hasHeader = headerValues.some(v => String(v || "").trim().length > 0);

  let headers = hasHeader ? headerValues.filter(h => String(h || "").trim().length > 0) : [];
  const keys = Object.keys(record);

  // Add any new keys to the header
  const missing = keys.filter(k => !headers.includes(k));
  if (!hasHeader) {
    headers = keys;
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  } else if (missing.length > 0) {
    headers = headers.concat(missing);
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  }

  // Build row in the correct column order
  const row = headers.map(h => {
    const v = record[h];
    if (v === undefined || v === null) return "";
    if (typeof v === "object") return JSON.stringify(v);
    return v;
  });

  sheet.appendRow(row);

  return ContentService
    .createTextOutput(JSON.stringify({ status: "ok" }))
    .setMimeType(ContentService.MimeType.JSON);
}
