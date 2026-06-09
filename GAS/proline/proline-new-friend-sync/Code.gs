/**
 * 「新」公式 LINE アカウントの友だち追加 GET とフォーム回答 POST を 1 本の Web アプリで受ける。
 * 友だち追加は「新友達追加情報」シートへ upsert し、フォーム回答は「form_8：在宅ワーク面談前アンケート」へ追記する。
 * form_8 行の「新旧」列には「新」を記録する。
 */
var SETTINGS_ = {
  mainSpreadsheetId: "1BQOswkbIBjzMdya5MICAMBcMmrJWd7rXLANPbSDc5m4",
  friendSheetName: "新友達追加情報",
  formSheetName: "form_8：在宅ワーク面談前アンケート",
  masterSpreadsheetId: "1BQOswkbIBjzMdya5MICAMBcMmrJWd7rXLANPbSDc5m4",
  masterSheetName: "アフィリエイター情報",
  timezone: "Asia/Tokyo",
  friendDateFormat: "yyyy/MM/dd HH:mm:ss",
  formDateFormat: "yyyy-MM-dd HH:mm:ss",
  successText: "Success",
  noneText: "なし",
  lockTimeoutMs: 30000,
  plannedStatusText: "1S予定",
  doneStatusText: "1S済み",
  duplicateStatusText: "重複",
  ownerHeaderText: "1S担当",
  defaultOwnerText: "Sho"
};

var FRIEND_HEADERS_ = [
  "友だち追加日",
  "最終更新日時",
  "ユーザーID(uid)",
  "登録者LINE名",
  "ステータス",
  "紹介者コード",
  "紹介者名(LINE名)",
  "LINE送信メルアド",
  "パスワード",
  "ニックネーム",
  "電話番号",
  "年齢",
  "年代",
  "性別",
  "フリー項目1",
  "シナリオ位置"
];

var FRIEND_FIELDS_ = [
  "addedAt",
  "updatedAt",
  "uid",
  "lineName",
  "status",
  "refCode",
  "refName",
  "emailLine",
  "password",
  "nickname",
  "phone",
  "nenrei",
  "nendai",
  "seibetu",
  "free1",
  "scenario"
];

var FRIEND_FIELD_CANDIDATES_ = {
  addedAt:   ["友だち追加日", "初回登録日時", "送信日"],
  updatedAt: ["最終更新日時", "最終活動日"],
  uid:       ["ユーザーID(uid)", "uid"],
  lineName:  ["登録者LINE名", "snsname"],
  status:    ["ステータス", "稼働状態"],
  refCode:   ["紹介者コード"],
  refName:   ["紹介者名(LINE名)"],
  emailLine: ["LINE送信メルアド", "email-line", "email_line"],
  password:  ["パスワード", "password"],
  nickname:  ["ニックネーム", "nickname"],
  phone:     ["電話番号", "phone"],
  nenrei:    ["年齢", "nenrei"],
  nendai:    ["年代", "nendai"],
  seibetu:   ["性別", "seibetu"],
  free1:     ["フリー項目1", "free1"],
  scenario:  ["シナリオ位置", "シナリオ位置1", "scenario"]
};

var FORM_HEADERS_ = [
  "送信日",
  "新旧",
  "uid",
  "アフィリエイター",
  "LINE名",
  "氏名",
  "性別",
  "年齢",
  "電話番号",
  "応募理由",
  "年月",
  "1S",
  "1S担当",
  "1Sメモ",
  "面接",
  "契約の有無",
  "決済手段",
  "結果",
  "追いかけメモ",
  "売上",
  "着金",
  "次回予定日",
  "次回予定入金額",
  "アフィリエイター報酬チェック",
  "アフィリエイター報酬額",
  "手数料引いた報酬",
  "営業代行報酬チェック",
  "営業代行報酬額",
  "合計報酬額",
  "月野手数料チェック",
  "月野手数料",
  "列 9",
  "列 10"
];

var FORM_FIELD_LABEL_MAP_ = {
  "氏名：": "氏名",
  "性別：": "性別",
  "年齢：": "年齢",
  "電話番号：": "電話番号",
  "応募理由（任意）：": "応募理由"
};

var MASTER_CODE_HEADER_CANDIDATES_ = ["アフィリエイトコード", "紹介者コード"];
var MASTER_NAME_HEADER_CANDIDATES_ = ["LINE名", "紹介者名(LINE名)", "登録者LINE名", "アフィリエイター"];

function doGet(e) {
  var lock = LockService.getScriptLock();

  try {
    lock.waitLock(SETTINGS_.lockTimeoutMs);

    var payload = parseFriendRequest_(e);
    var spreadsheet = openMainSpreadsheet_();
    var sheet = getOrCreateNamedSheet_(spreadsheet, SETTINGS_.friendSheetName);
    var headerMap = ensureFriendHeaderMap_(sheet);
    var timestamp = formatDate_(SETTINGS_.friendDateFormat);
    var referrerName = resolveReferrerName_(payload.refCode, spreadsheet);
    var existingRow = findRowByValue_(sheet, getFriendHeaderColumn_(headerMap, "uid"), payload.uid);

    if (existingRow > 0) {
      updateExistingFriendRow_(sheet, headerMap, existingRow, payload, timestamp, referrerName);
    } else {
      appendNewFriendRow_(sheet, headerMap, payload, timestamp, referrerName);
    }

    return ContentService.createTextOutput(SETTINGS_.successText);
  } catch (error) {
    Logger.log("proline-new-friend-sync GET error: " + (error && error.stack ? error.stack : error));
    return ContentService.createTextOutput("Error: " + error.message);
  } finally {
    if (lock.hasLock()) {
      lock.releaseLock();
    }
  }
}

function doPost(e) {
  var lock = LockService.getScriptLock();

  try {
    lock.waitLock(SETTINGS_.lockTimeoutMs);

    var request = buildFormRequest_(e);
    if (!request.uid) {
      throw new Error("uid is required.");
    }

    var spreadsheet = openMainSpreadsheet_();
    var sheet = getOrCreateNamedSheet_(spreadsheet, SETTINGS_.formSheetName);
    var headerMap = ensureHeaderMap_(sheet, FORM_HEADERS_);
    var row = buildEmptyRow_(sheet.getLastColumn());
    var referrerName = resolveReferrerName_(request.refCode, spreadsheet);
    syncFriendReferralFromForm_(spreadsheet, request, referrerName);

    setRowValue_(row, headerMap, "送信日", request.sentAt);
    setRowValue_(row, headerMap, "新旧", "新");
    setRowValue_(row, headerMap, "uid", request.uid);
    setRowValue_(row, headerMap, "アフィリエイター", referrerName === SETTINGS_.noneText ? "" : referrerName);
    setRowValue_(row, headerMap, "LINE名", request.lineName);
    setRowValue_(row, headerMap, "氏名", resolveApplicantName_(request));
    setRowValue_(row, headerMap, "性別", pickFirstNonEmpty_([
      findFormValueByLabel_(request.formValuesByLabel, "性別："),
      request.userData.seibetu
    ]));
    setRowValue_(row, headerMap, "年齢", pickFirstNonEmpty_([
      findFormValueByLabel_(request.formValuesByLabel, "年齢："),
      request.userData.nenrei
    ]));
    setRowValue_(row, headerMap, "電話番号", pickFirstNonEmpty_([
      findFormValueByLabel_(request.formValuesByLabel, "電話番号："),
      request.userData.phone
    ]));
    setRowValue_(row, headerMap, "応募理由", pickFirstNonEmpty_([
      findFormValueByLabel_(request.formValuesByLabel, "応募理由（任意）："),
      ""
    ]));
    setRowValue_(row, headerMap, "年月", buildYearMonthText_(request.sentAt));

    applyFormFieldMappings_(row, headerMap, request.formValuesByLabel);
    applyFormStatusForNewRow_(sheet, headerMap, row, request.uid);

    sheet.appendRow(row);

    return ContentService.createTextOutput(SETTINGS_.successText);
  } catch (error) {
    Logger.log("proline-new-friend-sync POST error: " + (error && error.stack ? error.stack : error));
    return ContentService.createTextOutput("Error: " + error.message);
  } finally {
    if (lock.hasLock()) {
      lock.releaseLock();
    }
  }
}

function parseFriendRequest_(e) {
  var params = e && e.parameter ? e.parameter : {};
  var uid = normalizeString_(params.uid);

  if (!uid) {
    throw new Error("uid is required.");
  }

  return {
    uid:      uid,
    name:     normalizeString_(pickFirstNonEmpty_([params.name, params.snsname])),
    status:   normalizeString_(params.status),
    refCode:  normalizeString_(pickFirstNonEmpty_([params.ref_code, params.free2])),
    emailLine: normalizeString_(pickFirstNonEmpty_([params.email_line, params["email-line"]])),
    password:  normalizeString_(params.password),
    nickname:  normalizeString_(params.nickname),
    phone:     normalizeString_(params.phone),
    nenrei:    normalizeString_(params.nenrei),
    nendai:    normalizeString_(params.nendai),
    seibetu:   normalizeString_(params.seibetu),
    free1:     normalizeString_(params.free1),
    scenario:  normalizeString_(pickFirstNonEmpty_([params.scenario, params["シナリオ位置1"]]))
  };
}

function buildFormRequest_(e) {
  var raw = e && e.postData && e.postData.contents ? e.postData.contents : "";
  var params = e && e.parameter ? e.parameter : {};
  var payload = parseRequestPayload_(raw);
  var userData = getNestedObject_(payload, "user_data");

  return {
    raw: raw,
    params: params,
    payload: payload,
    userData: userData,
    formData: getNestedObject_(payload, "form_data"),
    formValuesByLabel: extractFormValuesByLabel_(raw, payload),
    uid: normalizeString_(pickFirstNonEmpty_([params.uid, payload.uid, userData.uid])),
    lineName: normalizeString_(pickFirstNonEmpty_([
      params["user_data[snsname]"],
      params["user_data[linename]"],
      params.snsname,
      params.name,
      userData.snsname,
      userData.linename
    ])),
    sentAt: resolveFormSentAt_(params, payload, userData),
    refCode: extractRefCode_(params, payload, userData)
  };
}

function openMainSpreadsheet_() {
  if (SETTINGS_.mainSpreadsheetId) {
    return SpreadsheetApp.openById(SETTINGS_.mainSpreadsheetId);
  }

  return SpreadsheetApp.getActiveSpreadsheet();
}

function getOrCreateNamedSheet_(spreadsheet, sheetName) {
  var sheet = spreadsheet.getSheetByName(sheetName);

  if (!sheet) {
    sheet = spreadsheet.insertSheet(sheetName);
  }

  return sheet;
}

function ensureHeaderMap_(sheet, requiredHeaders) {
  var lastColumn = sheet.getLastColumn();
  var headerValues = lastColumn > 0 ? sheet.getRange(1, 1, 1, lastColumn).getDisplayValues()[0] : [];
  var headerMap = buildHeaderMap_(headerValues);
  var headerChanged = false;

  if (isHeaderRowBlank_(headerValues)) {
    headerValues = requiredHeaders.slice();
    headerMap = buildHeaderMap_(headerValues);
    headerChanged = true;
  } else {
    for (var i = 0; i < requiredHeaders.length; i++) {
      var headerName = requiredHeaders[i];
      var normalizedHeaderName = normalizeString_(headerName);

      if (!headerMap[normalizedHeaderName]) {
        headerValues.push(headerName);
        headerMap[normalizedHeaderName] = headerValues.length;
        headerChanged = true;
      }
    }
  }

  if (headerChanged) {
    sheet.getRange(1, 1, 1, headerValues.length).setValues([headerValues]);
    sheet.setFrozenRows(1);
  }

  return headerMap;
}

function ensureFriendHeaderMap_(sheet) {
  var lastColumn = sheet.getLastColumn();
  var headerValues = lastColumn > 0 ? sheet.getRange(1, 1, 1, lastColumn).getDisplayValues()[0] : [];
  var headerMap = buildHeaderMap_(headerValues);
  var headerChanged = false;

  if (isHeaderRowBlank_(headerValues)) {
    headerValues = FRIEND_HEADERS_.slice();
    headerChanged = true;
  } else {
    for (var i = 0; i < FRIEND_HEADERS_.length; i++) {
      var canonicalHeader = FRIEND_HEADERS_[i];
      var fieldKey = FRIEND_FIELDS_[i];

      if (getHeaderColumn_(headerMap, canonicalHeader)) {
        continue;
      }

      var aliasColumn = getFriendHeaderColumn_(headerMap, fieldKey);
      if (aliasColumn) {
        headerValues[aliasColumn - 1] = canonicalHeader;
      } else {
        headerValues.push(canonicalHeader);
      }

      headerMap = buildHeaderMap_(headerValues);
      headerChanged = true;
    }
  }

  if (headerChanged) {
    sheet.getRange(1, 1, 1, headerValues.length).setValues([headerValues]);
    sheet.setFrozenRows(1);
  }

  return buildHeaderMap_(headerValues);
}

function updateExistingFriendRow_(sheet, headerMap, rowNumber, payload, timestamp, referrerName) {
  setSheetValueByColumn_(sheet, rowNumber, getFriendHeaderColumn_(headerMap, "updatedAt"), timestamp);
  setSheetValueByColumn_(sheet, rowNumber, getFriendHeaderColumn_(headerMap, "lineName"), payload.name);
  setSheetValueByColumn_(sheet, rowNumber, getFriendHeaderColumn_(headerMap, "status"), payload.status);
  if (payload.refCode) {
    setSheetValueByColumn_(sheet, rowNumber, getFriendHeaderColumn_(headerMap, "refCode"), payload.refCode);
    setSheetValueByColumn_(sheet, rowNumber, getFriendHeaderColumn_(headerMap, "refName"), referrerName);
  }
  setSheetValueByColumn_(sheet, rowNumber, getFriendHeaderColumn_(headerMap, "emailLine"), payload.emailLine);
  setSheetValueByColumn_(sheet, rowNumber, getFriendHeaderColumn_(headerMap, "password"),  payload.password);
  setSheetValueByColumn_(sheet, rowNumber, getFriendHeaderColumn_(headerMap, "nickname"),  payload.nickname);
  setSheetValueByColumn_(sheet, rowNumber, getFriendHeaderColumn_(headerMap, "phone"),     payload.phone);
  setSheetValueByColumn_(sheet, rowNumber, getFriendHeaderColumn_(headerMap, "nenrei"),    payload.nenrei);
  setSheetValueByColumn_(sheet, rowNumber, getFriendHeaderColumn_(headerMap, "nendai"),    payload.nendai);
  setSheetValueByColumn_(sheet, rowNumber, getFriendHeaderColumn_(headerMap, "seibetu"),   payload.seibetu);
  setSheetValueByColumn_(sheet, rowNumber, getFriendHeaderColumn_(headerMap, "free1"),     payload.free1);
  setSheetValueByColumn_(sheet, rowNumber, getFriendHeaderColumn_(headerMap, "scenario"),  payload.scenario);
}

function appendNewFriendRow_(sheet, headerMap, payload, timestamp, referrerName) {
  var row = buildEmptyRow_(sheet.getLastColumn());

  setFriendRowValue_(row, headerMap, "addedAt",   timestamp);
  setFriendRowValue_(row, headerMap, "updatedAt",  timestamp);
  setFriendRowValue_(row, headerMap, "uid",        payload.uid);
  setFriendRowValue_(row, headerMap, "lineName",   payload.name);
  setFriendRowValue_(row, headerMap, "status",     payload.status);
  setFriendRowValue_(row, headerMap, "refCode",    payload.refCode);
  setFriendRowValue_(row, headerMap, "refName",    referrerName);
  setFriendRowValue_(row, headerMap, "emailLine",  payload.emailLine);
  setFriendRowValue_(row, headerMap, "password",   payload.password);
  setFriendRowValue_(row, headerMap, "nickname",   payload.nickname);
  setFriendRowValue_(row, headerMap, "phone",      payload.phone);
  setFriendRowValue_(row, headerMap, "nenrei",     payload.nenrei);
  setFriendRowValue_(row, headerMap, "nendai",     payload.nendai);
  setFriendRowValue_(row, headerMap, "seibetu",    payload.seibetu);
  setFriendRowValue_(row, headerMap, "free1",      payload.free1);
  setFriendRowValue_(row, headerMap, "scenario",   payload.scenario);

  sheet.appendRow(row);
}

function syncFriendReferralFromForm_(spreadsheet, request, referrerName) {
  if (!request.uid || !request.refCode) {
    return;
  }

  var sheet = getOrCreateNamedSheet_(spreadsheet, SETTINGS_.friendSheetName);
  var headerMap = ensureFriendHeaderMap_(sheet);
  var rowNumber = findRowByValue_(sheet, getFriendHeaderColumn_(headerMap, "uid"), request.uid);
  var timestamp = request.sentAt || formatDate_(SETTINGS_.friendDateFormat);

  if (rowNumber > 0) {
    setSheetValueByColumn_(sheet, rowNumber, getFriendHeaderColumn_(headerMap, "updatedAt"), timestamp);
    if (request.lineName) {
      setSheetValueByColumn_(sheet, rowNumber, getFriendHeaderColumn_(headerMap, "lineName"), request.lineName);
    }
    setSheetValueByColumn_(sheet, rowNumber, getFriendHeaderColumn_(headerMap, "refCode"), request.refCode);
    setSheetValueByColumn_(sheet, rowNumber, getFriendHeaderColumn_(headerMap, "refName"), referrerName);
    return;
  }

  appendNewFriendRow_(
    sheet,
    headerMap,
    {
      uid: request.uid,
      name: request.lineName,
      status: "",
      refCode: request.refCode,
      emailLine: "",
      password: "",
      nickname: "",
      phone: "",
      nenrei: "",
      nendai: "",
      seibetu: "",
      free1: "",
      scenario: ""
    },
    timestamp,
    referrerName
  );
}

function applyFormFieldMappings_(row, headerMap, formValuesByLabel) {
  for (var formLabel in FORM_FIELD_LABEL_MAP_) {
    if (!FORM_FIELD_LABEL_MAP_.hasOwnProperty(formLabel)) continue;
    var headerName = FORM_FIELD_LABEL_MAP_[formLabel];
    var value = findFormValueByLabel_(formValuesByLabel, formLabel);
    if (value) {
      setRowValue_(row, headerMap, headerName, value);
    }
  }
}

function applyFormStatusForNewRow_(sheet, headerMap, row, uid) {
  var state = getDuplicateStateByUid_(sheet, headerMap, uid);
  var shouldUsePlanned = !state.hasMatch || !state.hasActiveExisting;

  setRowValue_(
    row,
    headerMap,
    "1S",
    shouldUsePlanned ? SETTINGS_.plannedStatusText : SETTINGS_.duplicateStatusText
  );

  if (shouldUsePlanned) {
    setRowValue_(row, headerMap, SETTINGS_.ownerHeaderText, SETTINGS_.defaultOwnerText);
  }
}

function resolveApplicantName_(request) {
  var directName = findFormValueByLabel_(request.formValuesByLabel, "氏名：");
  if (directName) {
    return directName;
  }

  var familyName = normalizeString_(request.userData.sei);
  var givenName = normalizeString_(request.userData.mei);
  var joined = normalizeString_((familyName + " " + givenName).trim());

  return pickFirstNonEmpty_([joined, request.userData.nickname]);
}

function resolveFormSentAt_(params, payload, userData) {
  var explicitDate = pickFirstNonEmpty_([
    params.date,
    payload.date,
    userData.date
  ]);

  if (explicitDate) {
    return normalizeString_(explicitDate);
  }

  var unixtime = pickFirstNonEmpty_([
    params.unixtime,
    payload.unixtime,
    userData.unixtime
  ]);

  if (unixtime) {
    return formatDate_(SETTINGS_.formDateFormat, new Date(Number(unixtime) * 1000));
  }

  return formatDate_(SETTINGS_.formDateFormat);
}

function extractRefCode_(params, payload, userData) {
  return normalizeString_(pickFirstNonEmpty_([
    params.ref_code,
    params.free2,
    params["user_data[ref_code]"],
    params["user_data[free2]"],
    params["form_data[ref_code]"],
    params["form_data[free2]"],
    payload.ref_code,
    payload.free2,
    userData.ref_code,
    userData.free2,
    getNestedValue_(payload, ["form_data", "ref_code"]),
    getNestedValue_(payload, ["form_data", "free2"])
  ]));
}

function resolveReferrerName_(refCode, mainSpreadsheet) {
  if (!refCode) {
    return SETTINGS_.noneText;
  }

  var masterSpreadsheet = SETTINGS_.masterSpreadsheetId === SETTINGS_.mainSpreadsheetId
    ? mainSpreadsheet
    : SpreadsheetApp.openById(SETTINGS_.masterSpreadsheetId);
  var masterSheet = masterSpreadsheet.getSheetByName(SETTINGS_.masterSheetName);

  if (!masterSheet) {
    throw new Error("Master sheet not found: " + SETTINGS_.masterSheetName);
  }

  var lastRow = masterSheet.getLastRow();
  var lastColumn = masterSheet.getLastColumn();
  if (lastRow < 2 || lastColumn < 1) {
    return SETTINGS_.noneText;
  }

  var values = masterSheet.getRange(1, 1, lastRow, lastColumn).getDisplayValues();
  var headerMap = buildHeaderMap_(values[0] || []);
  var codeColumn = findHeaderColumnByCandidates_(headerMap, MASTER_CODE_HEADER_CANDIDATES_, 3);
  var nameColumn = findHeaderColumnByCandidates_(headerMap, MASTER_NAME_HEADER_CANDIDATES_, 2);

  for (var i = 1; i < values.length; i++) {
    if (normalizeString_(values[i][codeColumn - 1]) === refCode) {
      return normalizeString_(values[i][nameColumn - 1]) || SETTINGS_.noneText;
    }
  }

  return SETTINGS_.noneText;
}

function getDuplicateStateByUid_(sheet, headerMap, uid) {
  var uidColumn = getHeaderColumn_(headerMap, "uid");
  var statusColumn = getHeaderColumn_(headerMap, "1S");
  var normalizedUid = normalizeString_(uid);

  if (!uidColumn || !statusColumn || !normalizedUid) {
    return {
      hasMatch: false,
      hasActiveExisting: false
    };
  }

  var lastRow = sheet.getLastRow();
  if (lastRow <= 1) {
    return {
      hasMatch: false,
      hasActiveExisting: false
    };
  }

  var values = sheet.getRange(2, 1, lastRow - 1, Math.max(uidColumn, statusColumn)).getDisplayValues();
  var hasMatch = false;
  var hasActiveExisting = false;

  for (var i = 0; i < values.length; i++) {
    if (normalizeString_(values[i][uidColumn - 1]) === normalizedUid) {
      hasMatch = true;
      if (isActiveFirstStepStatus_(values[i][statusColumn - 1])) {
        hasActiveExisting = true;
        break;
      }
    }
  }

  return {
    hasMatch: hasMatch,
    hasActiveExisting: hasActiveExisting
  };
}

function isActiveFirstStepStatus_(value) {
  var status = normalizeString_(value);
  return status === SETTINGS_.plannedStatusText || status === SETTINGS_.doneStatusText;
}

function extractFormValuesByLabel_(raw, payload) {
  var valuesByLabel = {};
  mergeFormValuesFromObject_(valuesByLabel, getNestedObject_(payload, "form_data"));

  var parsed = parseOrderedFormData_(raw);
  for (var key in parsed.valuesMap) {
    if (!parsed.valuesMap.hasOwnProperty(key)) continue;
    valuesByLabel[key] = parsed.valuesMap[key].join("\n");
  }

  return valuesByLabel;
}

function mergeFormValuesFromObject_(target, source) {
  for (var key in source) {
    if (!source.hasOwnProperty(key)) continue;

    var value = source[key];
    if (Array.isArray(value)) {
      target[key] = value.map(function(item) {
        return stringifyFormValue_(item);
      }).join("\n");
      continue;
    }

    target[key] = stringifyFormValue_(value);
  }
}

function findFormValueByLabel_(valuesByLabel, label) {
  var normalizedLabel = normalizeFormLabel_(label);

  for (var key in valuesByLabel) {
    if (!valuesByLabel.hasOwnProperty(key)) continue;
    if (normalizeFormLabel_(key) === normalizedLabel) {
      return normalizeString_(valuesByLabel[key]);
    }
  }

  return "";
}

function parseRequestPayload_(raw) {
  if (!raw) {
    return {};
  }

  try {
    return JSON.parse(raw);
  } catch (error) {
    return parseNestedBody_(raw);
  }
}

function parseNestedBody_(raw) {
  var payload = {};
  var parts = String(raw || "").split("&");

  for (var i = 0; i < parts.length; i++) {
    var part = parts[i];
    if (!part) continue;

    var eq = part.indexOf("=");
    var rawKey = eq >= 0 ? part.slice(0, eq) : part;
    var rawValue = eq >= 0 ? part.slice(eq + 1) : "";
    var key = safeDecodeURIComponent_(rawKey.replace(/\+/g, " "));
    var value = safeDecodeURIComponent_(rawValue.replace(/\+/g, " "));

    assignNestedValue_(payload, key, value);
  }

  return payload;
}

function parseOrderedFormData_(raw) {
  var valuesMap = {};
  if (!raw) {
    return { valuesMap: valuesMap };
  }

  var parts = raw.split("&");
  for (var i = 0; i < parts.length; i++) {
    var part = parts[i];
    if (!part) continue;

    var eq = part.indexOf("=");
    var rawKey = eq >= 0 ? part.slice(0, eq) : part;
    var rawValue = eq >= 0 ? part.slice(eq + 1) : "";
    var decodedKey = safeDecodeURIComponent_(rawKey.replace(/\+/g, " "));
    var decodedValue = safeDecodeURIComponent_(rawValue.replace(/\+/g, " "));
    var matched = decodedKey.match(/^form_data\[(.+)\]$/);

    if (!matched) continue;

    var innerKey = matched[1].replace(/\]\[\d+\]?$/g, "");
    if (!valuesMap[innerKey]) {
      valuesMap[innerKey] = [];
    }

    if (decodedValue !== "") {
      valuesMap[innerKey].push(decodedValue);
    }
  }

  return { valuesMap: valuesMap };
}

function assignNestedValue_(target, key, value) {
  var normalizedKey = String(key || "").replace(/\]/g, "");
  var segments = normalizedKey.split("[").filter(Boolean);

  if (!segments.length) {
    return;
  }

  var current = target;
  for (var i = 0; i < segments.length - 1; i++) {
    var segment = segments[i];
    if (!current[segment] || typeof current[segment] !== "object") {
      current[segment] = {};
    }
    current = current[segment];
  }

  current[segments[segments.length - 1]] = value;
}

function getNestedObject_(target, key) {
  var value = target && target[key];
  return value && typeof value === "object" ? value : {};
}

function getNestedValue_(target, pathSegments) {
  var current = target;

  for (var i = 0; i < pathSegments.length; i++) {
    if (!current || typeof current !== "object") {
      return "";
    }

    current = current[pathSegments[i]];
  }

  return current == null ? "" : current;
}

function findRowByValue_(sheet, columnNumber, expectedValue) {
  if (!columnNumber) {
    return 0;
  }

  var lastRow = sheet.getLastRow();
  if (lastRow < 2) {
    return 0;
  }

  var values = sheet.getRange(2, columnNumber, lastRow - 1, 1).getDisplayValues();
  for (var i = 0; i < values.length; i++) {
    if (normalizeString_(values[i][0]) === expectedValue) {
      return i + 2;
    }
  }

  return 0;
}

function buildHeaderMap_(headerValues) {
  var headerMap = {};

  for (var i = 0; i < headerValues.length; i++) {
    var normalizedHeader = normalizeString_(headerValues[i]);
    if (normalizedHeader && !headerMap[normalizedHeader]) {
      headerMap[normalizedHeader] = i + 1;
    }
  }

  return headerMap;
}

function getHeaderColumn_(headerMap, headerName) {
  return headerMap[normalizeString_(headerName)] || 0;
}

function getFriendHeaderColumn_(headerMap, fieldKey) {
  return findHeaderColumnByCandidates_(headerMap, FRIEND_FIELD_CANDIDATES_[fieldKey] || [], 0);
}

function findHeaderColumnByCandidates_(headerMap, candidates, fallbackColumn) {
  for (var i = 0; i < candidates.length; i++) {
    var column = getHeaderColumn_(headerMap, candidates[i]);
    if (column) {
      return column;
    }
  }

  return fallbackColumn;
}

function setFriendRowValue_(row, headerMap, fieldKey, value) {
  var column = getFriendHeaderColumn_(headerMap, fieldKey);
  if (!column) {
    return false;
  }

  row[column - 1] = normalizeString_(value);
  return true;
}

function setSheetValueByColumn_(sheet, rowNumber, columnNumber, value) {
  if (!columnNumber) {
    return false;
  }

  sheet.getRange(rowNumber, columnNumber).setValue(normalizeString_(value));
  return true;
}

function setRowValue_(row, headerMap, headerName, value) {
  var column = getHeaderColumn_(headerMap, headerName);
  if (!column) {
    return false;
  }

  row[column - 1] = normalizeString_(value);
  return true;
}

function buildEmptyRow_(width) {
  var row = [];
  for (var i = 0; i < width; i++) {
    row.push("");
  }
  return row;
}

function buildYearMonthText_(value) {
  var raw = normalizeString_(value);
  var matched = raw.match(/^(\d{4})[\/-](\d{1,2})/);

  if (matched) {
    return matched[1] + "/" + padTwoDigits_(matched[2]);
  }

  return Utilities.formatDate(new Date(), SETTINGS_.timezone, "yyyy/MM");
}

function formatDate_(format, date) {
  return Utilities.formatDate(date || new Date(), SETTINGS_.timezone, format);
}

function normalizeString_(value) {
  return value == null ? "" : String(value).trim();
}

function normalizeFormLabel_(value) {
  return String(value || "").replace(/\s+/g, "").trim();
}

function stringifyFormValue_(value) {
  if (value == null) {
    return "";
  }

  if (typeof value === "string") {
    return value;
  }

  if (typeof value === "object") {
    return JSON.stringify(value);
  }

  return String(value);
}

function pickFirstNonEmpty_(candidates) {
  for (var i = 0; i < candidates.length; i++) {
    var value = candidates[i];
    if (value !== null && value !== undefined && normalizeString_(value) !== "") {
      return value;
    }
  }

  return "";
}

function safeDecodeURIComponent_(value) {
  try {
    return decodeURIComponent(value);
  } catch (error) {
    return value;
  }
}

function padTwoDigits_(value) {
  var raw = String(value || "");
  return raw.length < 2 ? "0" + raw : raw;
}

function isHeaderRowBlank_(headerValues) {
  if (headerValues.length === 0) {
    return true;
  }

  for (var i = 0; i < headerValues.length; i++) {
    if (normalizeString_(headerValues[i])) {
      return false;
    }
  }

  return true;
}
