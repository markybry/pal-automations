function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("Payroll")
    .addItem("Generate Shifts", "generateShifts")
    .addToUi();
}

function generateShifts() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("Form responses 1");

  if (!sheet) {
    SpreadsheetApp.getUi().alert("Sheet 'Form responses 1' not found.");
    return;
  }
  deleteAllExceptFormResponses();
  StaffShiftsLib.processShifts(ss, sheet, Logger)
}

function onFormSubmit(e) {
  var sheet = e.range.getSheet();       // the sheet that got a new row
  var ss = sheet.getParent();  // safer than getActiveSpreadsheet()

  var newRow = e.range.getRow();        // row number of the new submission
  var values = sheet.getRange(newRow, 1, 1, sheet.getLastColumn()).getValues()[0];

  Logger.log("New form submission: %s", values);
  deleteAllExceptFormResponses();
  StaffShiftsLib.processShifts(ss, sheet, Logger)
}

function deleteAllExceptFormResponses() {
  const ss = SpreadsheetApp.getActive();
  const keepName = 'Form responses 1';

  ss.getSheets().forEach(sheet => {
    if (sheet.getName() !== keepName) {
      ss.deleteSheet(sheet);
    }
  });
}

