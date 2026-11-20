var SHEET_KANVAS = "DataKanvasAksara";
var SHEET_SURVEY = "SurveyKonsumen";

var KANVAS_HEADERS = [
  "id",
  "tanggal",
  "nama_promotor",
  "zona",
  "brand",
  "canvas_plan",
  "outlet_beli_ada",
  "outlet_ks_tb",
  "outlet_ks_b",
  "outlet_tb_ada_a",
  "outlet_tb_ada_p",
  "outlet_tb_ks",
  "omset_bungkus",
  "promsus_10_1",
  "promsus_3_1",
  "promsus_2_1",
  "promsus_1_1",
  "promsus_n_mie_instan",
  "outlet_buka_ecer",
  "jumlah_rokok_sampling",
  "jumlah_konsumen_trial",
  "direct_selling",
  "waktu_submit"
];

var SURVEY_HEADERS = [
  "id",
  "waktu_survey",
  "nama_promotor",
  "sektor_survey",
  "nama_konsumen",
  "range_usia_konsumen",
  "pekerjaan_konsumen",
  "bumo_rokok_konsumen",
  "tahu_76_aksara",
  "sumber_info_76_aksara",
  "komentar_positif_rasa",
  "komentar_positif_aroma",
  "komentar_positif_hisapan",
  "komentar_positif_harga",
  "komentar_positif_kemasan",
  "komentar_positif_lainnya",
  "komentar_negatif_rasa",
  "komentar_negatif_aroma",
  "komentar_negatif_hisapan",
  "komentar_negatif_harga",
  "komentar_negatif_kemasan",
  "komentar_negatif_lainnya"
];

function sendJson(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function formatCellValue(val, isDateOnly) {
  if (val === null || val === undefined) return "";
  if (Object.prototype.toString.call(val) === "[object Date]" && !isNaN(val.getTime())) {
    var tz = Session.getScriptTimeZone() || "Asia/Jakarta";
    return Utilities.formatDate(val, tz, isDateOnly ? "yyyy-MM-dd" : "yyyy-MM-dd HH:mm:ss");
  }
  return val;
}

function ensureSheetWithHeaders(sheetName, headers) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    sheet = ss.insertSheet(sheetName);
  }
  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  }
  return sheet;
}

function readSheetAsObjects(sheetName, expectedHeaders) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(sheetName);
  if (!sheet || sheet.getLastRow() < 2) {
    return [];
  }

  var lastCol = Math.max(sheet.getLastColumn(), expectedHeaders.length);
  var rawHeaders = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  var headerMap = {};
  for (var c = 0; c < rawHeaders.length; c++) {
    var h = String(rawHeaders[c] || "").trim();
    if (h) {
      headerMap[h] = c;
    }
  }

  var numRows = sheet.getLastRow() - 1;
  var dataGrid = sheet.getRange(2, 1, numRows, lastCol).getValues();
  var results = [];

  for (var r = 0; r < dataGrid.length; r++) {
    var rowVals = dataGrid[r];
    var isAllEmpty = rowVals.every(function (cell) {
      return cell === "" || cell === null || cell === undefined;
    });
    if (isAllEmpty) continue;

    var item = {};
    for (var k = 0; k < expectedHeaders.length; k++) {
      var key = expectedHeaders[k];
      var colIdx = headerMap.hasOwnProperty(key) ? headerMap[key] : k;
      var rawVal = colIdx < rowVals.length ? rowVals[colIdx] : "";
      item[key] = formatCellValue(rawVal, key === "tanggal");
    }
    results.push(item);
  }

  return results;
}

function doGet(e) {
  try {
    var params = (e && e.parameter) ? e.parameter : {};
    var action = params.action ? String(params.action).trim().toLowerCase() : "";
    var mode = params.mode ? String(params.mode).trim().toLowerCase() : "";

    if (action === "restore" || mode === "restore") {
      var kanvasData = readSheetAsObjects(SHEET_KANVAS, KANVAS_HEADERS);
      var surveyData = readSheetAsObjects(SHEET_SURVEY, SURVEY_HEADERS);

      return sendJson({
        status: "success",
        survey_sync_version: 1,
        debug_params: params,
        kanvas: kanvasData,
        survey_konsumen: surveyData
      });
    }

    return sendJson({
      status: "success",
      survey_sync_version: 1,
      debug_params: params,
      message: "Webhook Google Apps Script aktif."
    });
  } catch (err) {
    return sendJson({
      status: "error",
      message: "Error di doGet: " + err.message
    });
  }
}

function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return sendJson({
        status: "error",
        message: "Body request kosong."
      });
    }

    var payload = JSON.parse(e.postData.contents);
    if (payload.type === "survey_konsumen") {
      return processSurveyPost(payload);
    }

    var kanvasSheet = ensureSheetWithHeaders(SHEET_KANVAS, KANVAS_HEADERS);
    var newRow = KANVAS_HEADERS.map(function (col) {
      return (payload[col] === undefined || payload[col] === null) ? "" : payload[col];
    });
    kanvasSheet.appendRow(newRow);

    return sendJson({
      status: "success",
      message: "Data kanvas tersimpan ke " + SHEET_KANVAS + "."
    });
  } catch (err) {
    return sendJson({
      status: "error",
      message: "Error di doPost: " + err.message
    });
  }
}

function processSurveyPost(payload) {
  var surveySheet = ensureSheetWithHeaders(SHEET_SURVEY, SURVEY_HEADERS);

  if (payload.id === undefined || payload.id === null || String(payload.id).trim() === "") {
    return sendJson({
      status: "error",
      type: "survey_konsumen",
      action: payload.action || "",
      message: "ID survey wajib diisi."
    });
  }

  var targetId = String(payload.id).trim();
  var foundRowIndex = -1;
  var lastRow = surveySheet.getLastRow();

  if (lastRow > 1) {
    var idCells = surveySheet.getRange(2, 1, lastRow - 1, 1).getDisplayValues();
    for (var i = 0; i < idCells.length; i++) {
      if (String(idCells[i][0]).trim() === targetId) {
        foundRowIndex = i + 2;
        break;
      }
    }
  }

  if (payload.action === "delete") {
    if (foundRowIndex !== -1) {
      surveySheet.deleteRow(foundRowIndex);
    }
    return sendJson({
      status: "success",
      type: "survey_konsumen",
      action: "delete",
      message: "Data survey dihapus."
    });
  }

  if (payload.action !== "upsert") {
    return sendJson({
      status: "error",
      type: "survey_konsumen",
      action: payload.action || "",
      message: "Aksi survey tidak dikenal."
    });
  }

  var rowValues = SURVEY_HEADERS.map(function (col) {
    return (payload[col] === undefined || payload[col] === null) ? "" : payload[col];
  });
  var writeRow = (foundRowIndex === -1) ? (surveySheet.getLastRow() + 1) : foundRowIndex;
  surveySheet.getRange(writeRow, 1, 1, SURVEY_HEADERS.length).setValues([rowValues]);

  return sendJson({
    status: "success",
    type: "survey_konsumen",
    action: "upsert",
    message: "Data survey tersimpan."
  });
}
