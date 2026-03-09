function processShifts(ssParam?: any, sheetParam?: any, loggerParam?: any) {
  // logger helper: accept function or object with .log; fallback Logger.log
  var log = (function (lg: any) {
    if (!lg) return function (msg: string) { Logger.log(msg); };
    if (typeof lg === "function") return lg;
    if (typeof lg.log === "function") return function (msg: string) { lg.log(msg); };
    return function (msg: string) { Logger.log(msg); };
  })(loggerParam);

  // REQUIRE ssParam: if not supplied, log and stop
  if (!ssParam) {
    log("No spreadsheet (ss) supplied. Aborting.");
    return;
  }

  // resolve spreadsheet (use supplied ssParam)
  var ss: any = ssParam;

  // resolve sheet (accept Sheet object or name) using the provided ss
  var sheet: any = sheetParam;
  if (sheet && typeof sheet.getRange === "function") {
    // sheet is a Sheet object — keep it as-is
  } else {
    if (typeof sheet === "string") sheet = ss.getSheetByName(sheet);
    if (!sheet) sheet = ss.getSheetByName("Form responses 1");
  }

  if (!sheet) {
    log("Sheet 'Form responses 1' not found.");
    return;
  }

  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var rows = data.slice(1);

  // Helper to get a value by column name
  function getValue(row: any[], colName: string) {
    var idx = headers.indexOf(colName);
    return idx >= 0 ? row[idx] : "";
  }

  // Helper to parse a shift timestamp
  function parseShiftTimestamp(row: any) {
    var timeVal = getValue(row, "Time");
    var timestampVal = getValue(row, "Timestamp");

    if (timeVal) {
      var dt = new Date(timeVal as any);
      if (!isNaN(dt.getTime())) return dt;
    }

    if (timeVal && timestampVal) {
      var datePart = new Date(timestampVal as any);
      var timeParts = (timeVal as string).split(":");
      if (timeParts.length >= 2) {
        datePart.setHours(parseInt(timeParts[0], 10), parseInt(timeParts[1], 10), 0, 0);
        return datePart;
      }
    }
    return null;
  }

  // Group shifts by staff
  var staffGroups: { [key: string]: any[] } = {};
  rows.forEach(function (row) {
    var staff = getValue(row, "Staff Name") as string;
    if (!staffGroups[staff]) staffGroups[staff] = [];
    (row as any).shiftTimestamp = parseShiftTimestamp(row);
    staffGroups[staff].push(row);
  });

  var errors: any[] = [];

  // Process each staff
  Object.keys(staffGroups).forEach(function (staff) {
    var staffRows = staffGroups[staff];
    var starts = staffRows.filter(r => getValue(r, "Log type") === "Start" && r.shiftTimestamp);
    var finishes = staffRows.filter(r => getValue(r, "Log type") === "Finish" && r.shiftTimestamp);
    var nights = staffRows.filter(r => ["Night Shift", "Sleep"].includes(getValue(r, "Log type") as string));

    var cleanedShifts: any[] = [];

    // Get all unique dates
    var allDates: { [key: string]: boolean } = {};
    starts.forEach(r => allDates[(r.shiftTimestamp as Date).toDateString()] = true);
    finishes.forEach(r => allDates[(r.shiftTimestamp as Date).toDateString()] = true);

    Object.keys(allDates).forEach(function (dateStr) {
      var dayStarts = starts.filter(r => (r.shiftTimestamp as Date).toDateString() === dateStr);
      var dayFinishes = finishes.filter(r => (r.shiftTimestamp as Date).toDateString() === dateStr);
      var minLen = Math.min(dayStarts.length, dayFinishes.length);

      for (var i = 0; i < minLen; i++) {
        var startTime = dayStarts[i].shiftTimestamp as Date;
        var finishTime = dayFinishes[i].shiftTimestamp as Date;
        var shiftLength = (finishTime.getTime() - startTime.getTime()) / 3600000; // hours
        var location = getValue(dayStarts[i], "Location");
        var comments = getValue(dayStarts[i], "Comments");

        if (shiftLength > 24) {
          errors.push([staff, startTime, finishTime, "Shift exceeds 24 hours"]);
        }

        cleanedShifts.push([staff, startTime, finishTime, shiftLength.toFixed(2), "Day", location, comments]);
      }

      for (var i = minLen; i < dayStarts.length; i++) errors.push([staff, dayStarts[i].shiftTimestamp, "No finish for start"]);
      for (var i = minLen; i < dayFinishes.length; i++) errors.push([staff, dayFinishes[i].shiftTimestamp, "No start for finish"]);
    });

    // Handle Night/Sleep shifts
    nights.forEach(function (r) {
      var sleepStart = r.shiftTimestamp as Date;
      var location = getValue(r, "Location");
      var comments = getValue(r, "Comments");

      if (!sleepStart) {
        var tsStr = getValue(r, "Timestamp") as string;
        if (tsStr) sleepStart = new Date(tsStr as any);
        if (!sleepStart) sleepStart = new Date();
        sleepStart.setHours(22, 0, 0, 0);
      }

      var sleepFinish = new Date(sleepStart.getTime() + 9 * 60 * 60 * 1000); // +9 hours
      var shiftLength = (sleepFinish.getTime() - sleepStart.getTime()) / 3600000;

      cleanedShifts.push([staff, sleepStart, sleepFinish, shiftLength.toFixed(2), "Sleep", location, comments]);
    });

    // Write shifts to staff sheet
    var safeName = staff.replace(/[/\\?*[\]]/g, "-").substr(0, 30);
    var staffSheet = ss.getSheetByName(safeName);
    if (!staffSheet) staffSheet = ss.insertSheet(safeName);
    else staffSheet.clear();

    var outHeaders = ["Staff Name", "Shift Start", "Shift Finish", "Shift Length (hours)", "Shift Type", "Location", "Comments"];
    staffSheet.appendRow(outHeaders);
    cleanedShifts.forEach(function (shift) {
      staffSheet.appendRow(shift);
    });
  });

  // Write errors to Errors sheet
  var errorSheet = ss.getSheetByName("Errors");
  if (!errorSheet) errorSheet = ss.insertSheet("Errors");
  else errorSheet.clear();

  errorSheet.appendRow(["Staff Name", "Shift Timestamp", "Shift Finish/Info", "Issue"]);
  errors.forEach(function (err) {
    errorSheet.appendRow(err);
  });

  log("Shift processing complete!");
}

