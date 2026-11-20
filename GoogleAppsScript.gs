function jsonResponse(payload) {
  return ContentService.createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return jsonResponse({
        status: "error",
        message: "Permintaan tidak valid atau postData kosong."
      });
    }

    var data = JSON.parse(e.postData.contents);
    if (data.type === "survey_konsumen") {
      return handleSurveyRequest(data);
    }

    var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("DataKanvas");
    if (!sheet) {
      return jsonResponse({
        status: "error",
        message: "Tab 'DataKanvas' tidak ditemukan di Google Sheets."
      });
    }

    sheet.appendRow([
      data.id,
      data.tanggal,
      data.nama_promotor,
      data.zona,
      data.brand,
      data.canvas_plan,
      data.outlet_beli_ada,
      data.outlet_ks_tb,
      data.outlet_ks_b,
      data.outlet_tb_ada_a,
      data.outlet_tb_ada_p,
      data.outlet_tb_ks,
      data.omset_bungkus,
      data.promsus_10_1,
      data.promsus_3_1,
      data.promsus_2_1,
      data.promsus_1_1,
      data.promsus_n_mie_instan,
      data.outlet_buka_ecer,
      data.jumlah_rokok_sampling,
      data.jumlah_konsumen_trial,
      data.direct_selling,
      data.waktu_submit
    ]);

    return jsonResponse({ status: "success", message: "Data berhasil disimpan." });
  } catch (error) {
    return jsonResponse({ status: "error", message: error.toString() });
  }
}

function handleSurveyRequest(data) {
  var headers = [
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
  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = spreadsheet.getSheetByName("SurveyKonsumen");
  if (!sheet) {
    sheet = spreadsheet.insertSheet("SurveyKonsumen");
  }

  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
  } else {
    var existingHeaders = sheet.getRange(1, 1, 1, headers.length).getValues()[0];
    if (existingHeaders.every(function (header) { return header === ""; })) {
      sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
    } else if (headers.some(function (header, index) {
      return existingHeaders[index] !== header;
    })) {
      throw new Error("Header tab 'SurveyKonsumen' tidak sesuai.");
    }
  }

  if (data.id === undefined || data.id === null || String(data.id).trim() === "") {
    throw new Error("ID survey wajib diisi.");
  }
  var surveyId = String(data.id);
  var lastRow = sheet.getLastRow();
  var matchingRow = -1;
  if (lastRow > 1) {
    var ids = sheet.getRange(2, 1, lastRow - 1, 1).getDisplayValues();
    matchingRow = ids.findIndex(function (row) {
      return String(row[0]).trim() === surveyId;
    });
  }

  if (data.action === "delete") {
    if (matchingRow !== -1) {
      sheet.deleteRow(matchingRow + 2);
    }
    return jsonResponse({
      status: "success",
      type: "survey_konsumen",
      action: "delete",
      message: "Survey berhasil dihapus."
    });
  }
  if (data.action !== "upsert") {
    throw new Error("Aksi survey tidak dikenal.");
  }

  var row = headers.map(function (header) {
    return data[header] === undefined || data[header] === null ? "" : data[header];
  });
  var targetRow = matchingRow === -1 ? sheet.getLastRow() + 1 : matchingRow + 2;
  sheet.getRange(targetRow, 1, 1, headers.length).setValues([row]);
  return jsonResponse({
    status: "success",
    type: "survey_konsumen",
    action: "upsert",
    message: "Survey berhasil disimpan."
  });
}

function doGet(e) {
  return jsonResponse({
    status: "success",
    survey_sync_version: 1,
    message: "Webhook Google Apps Script aktif."
  });
}
