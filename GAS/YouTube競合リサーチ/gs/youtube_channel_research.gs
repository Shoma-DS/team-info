// =============================================================================
// チャンネル情報取得機能
// 「Youtubeチャンネル」シートのチャンネルURLから各種情報を取得して記入する
// =============================================================================

var CHANNEL_HEADERS = [
  "チャンネルID", "チャンネルURL", "チャンネル名", "チャンネルのバナー",
  "チャンネル詳細", "チャンネルのアイコン", "チャンネル登録者数",
  "投稿本数", "チャンネル開設日", "リンク", "累計再生回数"
];

/**
 * onOpen に追加するメニュー項目（既存の onOpen に統合してください）
 * 既存メニューに「④ チャンネル情報を取得」を追加する場合:
 *   .addItem("④ チャンネル情報を取得", "runChannelInfoFetch")
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("YouTubeリサーチ")
    .addItem("① 競合リサーチを実行", "runCompetitorYouTubeResearch")
    .addItem("② 検索キーワードリサーチを実行", "runKeywordResearch")
    .addItem("③ 再生数ランキングを実行", "runKeywordViewRanking")
    .addItem("④ チャンネル情報を取得", "runChannelInfoFetch")
    .addToUi();
}

/**
 * メイン: チャンネル情報取得
 */
function runChannelInfoFetch() {
  var ss = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  var sheet = ss.getSheetByName(CONFIG.SHEET_CHANNELS);
  if (!sheet) {
    SpreadsheetApp.getUi().alert("「" + CONFIG.SHEET_CHANNELS + "」シートが見つかりません。");
    return;
  }

  // ヘッダーが無ければ作成
  var headerMap = buildHeaderMap_(sheet);
  if (Object.keys(headerMap).length === 0) {
    sheet.getRange(1, 1, 1, CHANNEL_HEADERS.length).setValues([CHANNEL_HEADERS]);
    headerMap = buildHeaderMap_(sheet);
  } else {
    ensureChannelHeaders_(sheet, headerMap);
    headerMap = buildHeaderMap_(sheet);
  }

  // チャンネルURL列を特定
  var urlKey = findFirstExistingKey_(headerMap, CONFIG.CHANNEL_URL_KEYS);
  if (!urlKey) {
    SpreadsheetApp.getUi().alert("チャンネルURL列が見つかりません。");
    return;
  }

  var lastRow = sheet.getLastRow();
  if (lastRow < 2) {
    SpreadsheetApp.getUi().alert("チャンネルURLが入力されていません。");
    return;
  }

  var urlCol = headerMap[urlKey];
  var urls = sheet.getRange(2, urlCol, lastRow - 1, 1).getValues().map(function(r) {
    return String(r[0]).trim();
  });

  // チャンネルIDを解決
  var channelIds = resolveChannelIds_(urls);

  // 50件ずつ YouTube Channels API で詳細を取得
  var channelDataMap = fetchChannelDetails_(channelIds);

  // シートに書き込み
  for (var i = 0; i < urls.length; i++) {
    var row = i + 2;
    var chId = channelIds[i];
    if (!chId || !channelDataMap[chId]) continue;

    var info = channelDataMap[chId];
    var headerMap_ = headerMap; // 参照用

    setCellIfHeaderExists_(sheet, row, headerMap_, "チャンネルID", info.channelId);
    setCellIfHeaderExists_(sheet, row, headerMap_, "チャンネル名", info.title);
    setCellIfHeaderExists_(sheet, row, headerMap_, "チャンネルのバナー", info.bannerFormula);
    setCellIfHeaderExists_(sheet, row, headerMap_, "チャンネル詳細", info.description);
    setCellIfHeaderExists_(sheet, row, headerMap_, "チャンネルのアイコン", info.iconFormula);
    setCellIfHeaderExists_(sheet, row, headerMap_, "チャンネル登録者数", info.subscriberCount);
    setCellIfHeaderExists_(sheet, row, headerMap_, "投稿本数", info.videoCount);
    setCellIfHeaderExists_(sheet, row, headerMap_, "チャンネル開設日", info.publishedAt);
    setCellIfHeaderExists_(sheet, row, headerMap_, "リンク", info.links);
    setCellIfHeaderExists_(sheet, row, headerMap_, "累計再生回数", info.viewCount);
  }

  // バナー・アイコン列のサイズ調整
  applyChannelImageSizing_(sheet, headerMap);

  SpreadsheetApp.getUi().alert("チャンネル情報の取得が完了しました。（" + Object.keys(channelDataMap).length + " チャンネル）");
}

// -----------------------------------------------------------------------------
// チャンネルID解決
// -----------------------------------------------------------------------------

/**
 * URL配列からチャンネルIDを解決する
 * 対応形式:
 *   - https://www.youtube.com/channel/UC...
 *   - https://www.youtube.com/@handle
 *   - https://www.youtube.com/c/customname
 *   - https://www.youtube.com/user/username
 *   - チャンネルID直接入力 (UC...)
 */
function resolveChannelIds_(urls) {
  var results = [];
  for (var i = 0; i < urls.length; i++) {
    var url = urls[i];
    if (!url) { results.push(""); continue; }

    // UC... で始まるならそのままチャンネルID
    if (/^UC[\w-]{22}$/.test(url)) {
      results.push(url);
      continue;
    }

    // /channel/UC... 形式
    var channelMatch = url.match(/\/channel\/(UC[\w-]+)/);
    if (channelMatch) {
      results.push(channelMatch[1]);
      continue;
    }

    // /@handle 形式
    var handleMatch = url.match(/\/@([^\/\?]+)/);
    if (handleMatch) {
      var chId = resolveChannelIdByHandle_(handleMatch[1]);
      results.push(chId || "");
      continue;
    }

    // /c/customname または /user/username 形式
    var customMatch = url.match(/\/(?:c|user)\/([^\/\?]+)/);
    if (customMatch) {
      var chId2 = resolveChannelIdByCustomUrl_(customMatch[1]);
      results.push(chId2 || "");
      continue;
    }

    // それ以外はURL末尾をハンドルとして試行
    var lastSegment = url.replace(/\/$/, "").split("/").pop();
    if (lastSegment && lastSegment !== "youtube.com") {
      var chId3 = resolveChannelIdByHandle_(lastSegment);
      results.push(chId3 || "");
    } else {
      results.push("");
    }
  }
  return results;
}

/**
 * @handle からチャンネルIDを取得
 */
function resolveChannelIdByHandle_(handle) {
  try {
    var res = YouTube.Channels.list("id", { forHandle: handle });
    if (res.items && res.items.length > 0) return res.items[0].id;
  } catch (e) {}

  // forHandle が使えない場合は検索で代替
  try {
    var res2 = YouTube.Search.list("snippet", {
      q: handle,
      type: "channel",
      maxResults: 1
    });
    if (res2.items && res2.items.length > 0) return res2.items[0].snippet.channelId;
  } catch (e2) {}

  return "";
}

/**
 * カスタムURL / ユーザー名からチャンネルIDを取得
 */
function resolveChannelIdByCustomUrl_(name) {
  try {
    var res = YouTube.Search.list("snippet", {
      q: name,
      type: "channel",
      maxResults: 1
    });
    if (res.items && res.items.length > 0) return res.items[0].snippet.channelId;
  } catch (e) {}
  return "";
}

// -----------------------------------------------------------------------------
// チャンネル詳細取得
// -----------------------------------------------------------------------------

/**
 * チャンネルID配列から詳細情報を一括取得 (50件ずつバッチ処理)
 * @return {Object} channelId -> info のマップ
 */
function fetchChannelDetails_(channelIds) {
  var uniqueIds = Array.from(new Set(channelIds.filter(Boolean)));
  var dataMap = {};

  for (var i = 0; i < uniqueIds.length; i += 50) {
    var batch = uniqueIds.slice(i, i + 50);
    var res = YouTube.Channels.list("snippet,statistics,brandingSettings,contentDetails", {
      id: batch.join(",")
    });

    (res.items || []).forEach(function(item) {
      var sn = item.snippet || {};
      var st = item.statistics || {};
      var br = item.brandingSettings || {};
      var brCh = br.channel || {};
      var brImg = br.image || {};

      // バナー画像URL
      var bannerUrl = brImg.bannerExternalUrl || "";

      // アイコン画像URL（最高解像度を優先）
      var thumbs = sn.thumbnails || {};
      var iconUrl = (thumbs.high || thumbs.medium || thumbs.default || {}).url || "";

      // リンク: descriptionから抽出 or 空
      var links = extractLinksFromDescription_(sn.description || "");

      dataMap[item.id] = {
        channelId: item.id,
        title: sn.title || "",
        description: String(sn.description || "").slice(0, 1000),
        bannerFormula: bannerUrl ? '=IMAGE("' + bannerUrl + '")' : "",
        iconFormula: iconUrl ? '=IMAGE("' + iconUrl + '")' : "",
        subscriberCount: toNumber_(st.subscriberCount),
        videoCount: toNumber_(st.videoCount),
        viewCount: toNumber_(st.viewCount),
        publishedAt: sn.publishedAt ? formatDate_(new Date(sn.publishedAt)) : "",
        links: links
      };
    });
  }
  return dataMap;
}

/**
 * 概要欄からリンクを抽出する
 */
function extractLinksFromDescription_(description) {
  if (!description) return "";
  var urlRegex = /https?:\/\/[^\s\u3000\n]+/g;
  var matches = description.match(urlRegex);
  if (!matches) return "";
  // 重複除去して改行区切り
  return Array.from(new Set(matches)).join("\n");
}

// -----------------------------------------------------------------------------
// ヘッダー管理
// -----------------------------------------------------------------------------

/**
 * CHANNEL_HEADERS に定義された列が無ければ末尾に追加する
 */
function ensureChannelHeaders_(sheet, headerMap) {
  var lastCol = sheet.getLastColumn();
  CHANNEL_HEADERS.forEach(function(h) {
    if (!headerMap[h]) {
      lastCol++;
      sheet.getRange(1, lastCol).setValue(h);
      headerMap[h] = lastCol;
    }
  });
}

// -----------------------------------------------------------------------------
// セル書き込みヘルパー
// -----------------------------------------------------------------------------

function setCellIfHeaderExists_(sheet, row, headerMap, headerName, value) {
  var col = headerMap[headerName];
  if (!col) return;
  if (value !== undefined && value !== null && value !== "") {
    sheet.getRange(row, col).setValue(value);
  }
}

/**
 * バナー・アイコン列の幅と行高を調整
 */
function applyChannelImageSizing_(sheet, headerMap) {
  var bannerCol = headerMap["チャンネルのバナー"];
  var iconCol = headerMap["チャンネルのアイコン"];
  var lastRow = sheet.getLastRow();
  if (lastRow < 2) return;

  if (bannerCol) {
    sheet.setColumnWidth(bannerCol, 200);
  }
  if (iconCol) {
    sheet.setColumnWidth(iconCol, 80);
  }
  for (var r = 2; r <= lastRow; r++) {
    sheet.setRowHeight(r, 80);
  }
}
