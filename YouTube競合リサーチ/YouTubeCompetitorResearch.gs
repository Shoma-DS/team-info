/**
 * YoutubeデータリサーチAIカバー用
 * YouTube Data API v3 を使用
 *
 * スプレッドシートを開くと「YouTubeリサーチ」メニューが表示されます。
 * 各項目をクリックすると、対応する処理が実行されます。
 */

var CONFIG = {
  SPREADSHEET_ID: "1XTfZOQ3IFHU9uhgRmc3TF4Jk-YHe7FS8fS7BzvJPshc",
  HEADER_ROW: 1,
  DROPDOWN_VALUES: ["実行する操作を選択", "① 競合リサーチを実行", "② 検索キーワードリサーチを実行", "③ 再生数ランキングを実行"],
  SHEET_VIDEOS: "Youtube動画",
  SHEET_CHANNELS: "Youtubeチャンネル",
  SHEET_KEYWORDS: "検索キーワード",
  SHEET_KEYWORD_RESEARCH: "検索キーワードリサーチ",
  SHEET_VIEW_RANKING: "再生数ランキング",
  MAX_VIDEOS_PER_CHANNEL: 50,
  MAX_SEARCH_RESULTS_PER_KEYWORD: 20,
  MAX_VIEW_RANKING_PER_KEYWORD: 20,
  REGION_CODE: "JP",
  VIDEO_ID_HEADER: "video ID",
  CHANNEL_ID_KEYS: ["チャンネルID", "channelId", "channel ID", "Channel ID"],
  CHANNEL_URL_KEYS: ["チャンネルURL", "channelUrl", "channel URL", "URL", "url"],
  CHANNEL_VIEWS_KEYS: ["再生数", "viewCount", "views", "総再生数"],
  KEYWORD_HEADER_KEYS: ["キーワード", "keyword", "検索キーワード"]
};

var KEYWORD_RESEARCH_HEADERS = [
  "検索日", "検索キーワード", "順位", "video ID", "タイトル", "チャンネル名", "チャンネルID",
  "再生数", "高評価数", "コメント数", "投稿日", "動画URL", "動画の長さ", "ショート/長尺",
  "カテゴリ名", "カテゴリID", "ハッシュタグ", "サムネイル", "概要欄"
];

// -----------------------------------------------------------------------------
// カスタムメニュー（スプレッドシートを開いたときに「YouTubeリサーチ」が表示される）
// -----------------------------------------------------------------------------
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("YouTubeリサーチ")
    .addItem("① 競合リサーチを実行", "runCompetitorYouTubeResearch")
    .addItem("② 検索キーワードリサーチを実行", "runKeywordResearch")
    .addItem("③ 再生数ランキングを実行", "runKeywordViewRanking")
    .addSeparator()
    .addItem("リサーチパネルを開く", "openResearchSidebar_")
    .addItem("YouTubeリサーチボタンを設置", "setupYouTubeResearchButtons_")
    .addToUi();
}

function setupYouTubeResearchButtons_() {
  var ss = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  var sheet = ss.getSheets()[0];
  var lastCol = sheet.getLastColumn();
  var headers = lastCol >= 1 ? sheet.getRange(1, 1, 1, Math.max(lastCol, 5)).getValues()[0] : [];
  var colHelp = -1, colResearch = -1;
  for (var i = 0; i < headers.length; i++) {
    if (String(headers[i]).trim() === "項目ヘルプ") colHelp = i + 1;
    if (String(headers[i]).trim() === "YouTubeリサーチ") colResearch = i + 1;
  }
  if (colHelp <= 0) {
    sheet.insertRowBefore(1);
    sheet.getRange(1, 1).setValue("項目ヘルプ").setBackground("#f3f3f3");
    sheet.getRange(1, 2).setValue("YouTubeリサーチ").setBackground("#fff3e0");
    colHelp = 1; colResearch = 2;
  } else if (colResearch <= 0) {
    colResearch = colHelp + 1;
    sheet.getRange(1, colResearch).setValue("YouTubeリサーチ").setBackground("#fff3e0");
  }
  var dropdownCell = sheet.getRange(2, colResearch);
  dropdownCell.setDataValidation(SpreadsheetApp.newDataValidation().requireValueInList(CONFIG.DROPDOWN_VALUES, true).setAllowInvalid(false).build());
  dropdownCell.setValue(CONFIG.DROPDOWN_VALUES[0]).setBackground("#e8f0fe");
  if (sheet.getFrozenRows() < 2) sheet.setFrozenRows(2);
  SpreadsheetApp.getUi().alert("YouTubeリサーチボタンを設置しました。");
}

function onEdit(e) {
  if (!e || !e.range) return;
  var range = e.range, value = String(range.getValue() || "").trim();
  if (value === CONFIG.DROPDOWN_VALUES[0]) return;
  var sheet = range.getSheet();
  var headers = sheet.getRange(CONFIG.HEADER_ROW, 1, CONFIG.HEADER_ROW, sheet.getLastColumn()).getValues()[0];
  var colResearch = -1;
  for (var i = 0; i < headers.length; i++) { if (String(headers[i]).trim() === "YouTubeリサーチ") { colResearch = i + 1; break; } }
  if (colResearch <= 0 || range.getColumn() !== colResearch) return;
  range.setValue(CONFIG.DROPDOWN_VALUES[0]);
  if (value === CONFIG.DROPDOWN_VALUES[1]) runCompetitorYouTubeResearch();
  else if (value === CONFIG.DROPDOWN_VALUES[2]) runKeywordResearch();
  else if (value === CONFIG.DROPDOWN_VALUES[3]) runKeywordViewRanking();
}

function openResearchSidebar_() {
  var html = HtmlService.createHtmlOutput(
    '<!DOCTYPE html><html><head><base target="_top">' +
    '<style>body{font-family:Roboto,sans-serif;padding:16px;margin:0;}h3{margin:0 0 16px;color:#333;font-size:16px;}' +
    '.btn{display:block;width:100%;padding:12px 16px;margin-bottom:10px;border:none;border-radius:8px;font-size:14px;cursor:pointer;text-align:center;box-sizing:border-box;}' +
    '.btn-primary{background:#ff0000;color:white;}.btn-primary:hover{background:#cc0000;}' +
    '.btn-secondary{background:#065fd4;color:white;}.btn-secondary:hover{background:#004ba0;}' +
    '.btn-success{background:#0f9d58;color:white;}.btn-success:hover{background:#0a7d45;}.note{font-size:12px;color:#666;margin-top:16px;}</style></head><body>' +
    '<h3>YouTubeリサーチ</h3>' +
    '<button class="btn btn-primary" onclick="runResearch(\'competitor\')">① 競合リサーチを実行</button>' +
    '<button class="btn btn-secondary" onclick="runResearch(\'keyword\')">② 検索キーワードリサーチを実行</button>' +
    '<button class="btn btn-success" onclick="runResearch(\'ranking\')">③ 再生数ランキングを実行</button>' +
    '<p class="note">各ボタンをクリックすると、対応するリサーチが実行されます。</p>' +
    '<script>function runResearch(t){google.script.run.withSuccessHandler(function(){}).withFailureHandler(function(e){alert("エラー: "+e.message);}).runResearchFromSidebar_(t);}</script>' +
    '</body></html>'
  ).setTitle("YouTubeリサーチ").setWidth(280);
  SpreadsheetApp.getUi().showSidebar(html);
}

function runResearchFromSidebar_(type) {
  if (type === "competitor") runCompetitorYouTubeResearch();
  else if (type === "keyword") runKeywordResearch();
  else if (type === "ranking") runKeywordViewRanking();
}

/**
 * 件数をポップアップで入力してもらう。キャンセルまたは無効な値の場合はデフォルト値を返す。
 */
function promptNumber_(title, message, defaultVal, minVal, maxVal) {
  var ui = SpreadsheetApp.getUi();
  var response = ui.prompt(title, message + "\n（空欄またはキャンセルで " + defaultVal + " 件）", ui.ButtonSet.OK_CANCEL);
  if (response.getSelectedButton() !== ui.Button.OK) return defaultVal;
  var text = (response.getResponseText() || "").trim();
  if (text === "") return defaultVal;
  var num = parseInt(text, 10);
  if (isNaN(num) || num < minVal) return defaultVal;
  if (num > maxVal) num = maxVal;
  return num;
}

function runCompetitorYouTubeResearch() {
  var maxPerChannel = promptNumber_(
    "競合リサーチの件数",
    "1チャンネルあたり、何件の動画を取得しますか？（1〜50）",
    CONFIG.MAX_VIDEOS_PER_CHANNEL,
    1,
    50
  );

  var ss = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  var sheetVideos = ss.getSheetByName(CONFIG.SHEET_VIDEOS) || ss.insertSheet(CONFIG.SHEET_VIDEOS);
  var sheetChannels = ss.getSheetByName(CONFIG.SHEET_CHANNELS) || ss.insertSheet(CONFIG.SHEET_CHANNELS);
  var videoHeaderMap = buildHeaderMap_(sheetVideos);
  if (!videoHeaderMap[CONFIG.VIDEO_ID_HEADER]) {
    writeDefaultVideoHeaders_(sheetVideos);
    videoHeaderMap = buildHeaderMap_(sheetVideos);
  }
  var existingVideoIds = loadExistingIds_(sheetVideos, videoHeaderMap, CONFIG.VIDEO_ID_HEADER);
  var channelHeaderMap = buildHeaderMap_(sheetChannels);
  var channelIdKey = findFirstExistingKey_(channelHeaderMap, CONFIG.CHANNEL_ID_KEYS);
  var channelUrlKey = findFirstExistingKey_(channelHeaderMap, CONFIG.CHANNEL_URL_KEYS);
  var channelViewsKey = findFirstExistingKey_(channelHeaderMap, CONFIG.CHANNEL_VIEWS_KEYS);
  if (!channelIdKey && !channelUrlKey) throw new Error("チャンネルIDまたはURL列がありません。");
  var channels = loadChannels_(sheetChannels, channelHeaderMap, channelIdKey, channelUrlKey, channelViewsKey);
  var rowsToAppend = [];
  var categoryCache = {};
  for (var c = 0; c < channels.length; c++) {
    var ch = channels[c];
    if (!ch.channelId) continue;
    var topVideoIds = listTopVideosByView_(ch.channelId, maxPerChannel);
    if (topVideoIds.length === 0) continue;
    var videoItems = fetchVideosDetails_(topVideoIds);
    for (var v = 0; v < videoItems.length; v++) {
      var item = videoItems[v];
      if (!item.id || existingVideoIds.has(item.id)) continue;
      var rowObject = buildVideoRowObject_(item, categoryCache);
      rowsToAppend.push(objectToRowByHeader_(rowObject, videoHeaderMap));
      existingVideoIds.add(item.id);
    }
  }
  if (rowsToAppend.length > 0) {
    var startRow = sheetVideos.getLastRow() + 1;
    sheetVideos.getRange(startRow, 1, rowsToAppend.length, rowsToAppend[0].length).setValues(rowsToAppend);
    applyRowAndThumbnailSizing_(sheetVideos, videoHeaderMap, startRow, rowsToAppend.length);
  }

  SpreadsheetApp.getUi().alert("リサーチが完了しました。");
}

function runKeywordResearch() { runKeywordResearchCore_(CONFIG.SHEET_KEYWORD_RESEARCH, false); }
function runKeywordViewRanking() { runKeywordResearchCore_(CONFIG.SHEET_VIEW_RANKING, true); }

function runKeywordResearchCore_(resultSheetName, orderByViews) {
  var defaultNum = orderByViews ? CONFIG.MAX_VIEW_RANKING_PER_KEYWORD : CONFIG.MAX_SEARCH_RESULTS_PER_KEYWORD;
  var label = orderByViews ? "再生数ランキング" : "検索キーワードリサーチ";
  var maxPerKeyword = promptNumber_(
    label + "の件数",
    "1キーワードあたり、何件の動画を取得しますか？（1〜50）",
    defaultNum,
    1,
    50
  );

  var ss = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  var sheetKeywords = ss.getSheetByName(CONFIG.SHEET_KEYWORDS) || ss.insertSheet(CONFIG.SHEET_KEYWORDS);
  var sheetResult = ss.getSheetByName(resultSheetName) || ss.insertSheet(resultSheetName);

  var keywordHeaderMap = buildHeaderMap_(sheetKeywords);
  var keywordKey = findFirstExistingKey_(keywordHeaderMap, CONFIG.KEYWORD_HEADER_KEYS);
  if (!keywordKey) {
    sheetKeywords.getRange(1, 1).setValue("キーワード");
    if (sheetKeywords.getLastRow() < 2) sheetKeywords.getRange(2, 1).setValue("例: カバー 曲名");
    keywordHeaderMap = buildHeaderMap_(sheetKeywords);
    keywordKey = findFirstExistingKey_(keywordHeaderMap, CONFIG.KEYWORD_HEADER_KEYS);
  }
  var keywords = loadKeywords_(sheetKeywords, keywordHeaderMap, keywordKey);
  if (keywords.length === 0) throw new Error("キーワードを入力してください。");

  var searchDate = formatDate_(new Date());
  var resultRows = [];
  var categoryCache = {};
  for (var k = 0; k < keywords.length; k++) {
    var videoIds = orderByViews ? searchYouTubeByKeywordByViews_(keywords[k], maxPerKeyword) : searchYouTubeByKeyword_(keywords[k], maxPerKeyword);
    if (videoIds.length === 0) continue;
    var videoItems = fetchVideosDetails_(videoIds);
    for (var r = 0; r < videoItems.length; r++) {
      resultRows.push(buildKeywordResearchRowObject_(keywords[k], r + 1, videoItems[r], categoryCache, searchDate));
    }
  }
  writeKeywordResearchSheet_(sheetResult, resultRows);

  SpreadsheetApp.getUi().alert("リサーチが完了しました。");
}

function loadKeywords_(sheet, headerMap, keywordKey) {
  var col = headerMap[keywordKey];
  if (!col) return [];
  var lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  return sheet.getRange(2, col, lastRow, col).getValues().map(function(r){ return String(r[0]).trim(); }).filter(Boolean);
}

function searchYouTubeByKeyword_(keyword, maxResults) {
  var ids = [], pageToken = null;
  while (ids.length < maxResults) {
    var res = YouTube.Search.list("id", { q: keyword, type: "video", maxResults: Math.min(50, maxResults - ids.length), pageToken: pageToken || "" });
    (res.items || []).forEach(function(item){ if(item.id.videoId) ids.push(item.id.videoId); });
    pageToken = res.nextPageToken;
    if (!pageToken) break;
  }
  return ids;
}

function searchYouTubeByKeywordByViews_(keyword, maxResults) {
  var ids = [], pageToken = null;
  while (ids.length < maxResults) {
    var res = YouTube.Search.list("id", { q: keyword, type: "video", order: "viewCount", maxResults: Math.min(50, maxResults - ids.length), pageToken: pageToken || "" });
    (res.items || []).forEach(function(item){ if(item.id.videoId) ids.push(item.id.videoId); });
    pageToken = res.nextPageToken;
    if (!pageToken) break;
  }
  return ids;
}

function buildKeywordResearchRowObject_(keyword, rank, videoItem, categoryCache, searchDate) {
  var sn = videoItem.snippet || {}, st = videoItem.statistics || {}, cd = videoItem.contentDetails || {};
  var dur = iso8601DurationToSeconds_(cd.duration);
  return {
    "検索日": searchDate || formatDate_(new Date()),
    "検索キーワード": keyword,
    "順位": rank,
    "video ID": videoItem.id,
    "タイトル": sn.title || "",
    "チャンネル名": sn.channelTitle || "",
    "チャンネルID": sn.channelId || "",
    "再生数": toNumber_(st.viewCount),
    "高評価数": toNumber_(st.likeCount),
    "コメント数": toNumber_(st.commentCount),
    "投稿日": sn.publishedAt ? formatDate_(new Date(sn.publishedAt)) : "",
    "動画URL": videoItem.id ? "https://www.youtube.com/watch?v=" + videoItem.id : "",
    "動画の長さ": formatDurationHuman_(dur),
    "ショート/長尺": (dur > 0 && dur <= 60 ? "ショート" : "長尺"),
    "カテゴリ名": getCategoryName_(sn.categoryId, categoryCache),
    "カテゴリID": sn.categoryId || "",
    "ハッシュタグ": extractHashtags_(sn.tags, sn.description),
    "サムネイル": thumbnailToImageFormula_(pickThumbnailUrl_(sn.thumbnails)),
    "概要欄": String(sn.description || "").slice(0, 500)
  };
}

function writeKeywordResearchSheet_(sheet, resultRows) {
  sheet.clear();
  sheet.getRange(1, 1, 1, KEYWORD_RESEARCH_HEADERS.length).setValues([KEYWORD_RESEARCH_HEADERS]);
  if (resultRows.length === 0) return;
  var data = resultRows.map(function(row) {
    return KEYWORD_RESEARCH_HEADERS.map(function(h) { return row[h] !== undefined && row[h] !== null ? row[h] : ""; });
  });
  var numRows = data.length;
  sheet.getRange(2, 1, numRows, KEYWORD_RESEARCH_HEADERS.length).setValues(data);
  var thumbCol = KEYWORD_RESEARCH_HEADERS.indexOf("サムネイル") + 1;
  if (thumbCol > 0 && numRows > 0) {
    for (var r = 2; r <= 1 + numRows; r++) {
      sheet.setRowHeight(r, 90);
    }
    sheet.setColumnWidth(thumbCol, 120);
  }
}

function writeDefaultVideoHeaders_(sheet) {
  var headers = ["チャンネル名", "サムネイル", "タイトル", "ショート / 長尺判定", "動画の長さ", "動画URL", "投稿日", "再生数", "高評価数", "コメント数", "概要欄", "カテゴリ名", "カテゴリID", "video ID", "チャンネルID", "お気に入り"];
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
}

function buildHeaderMap_(sheet) {
  var lastCol = sheet.getLastColumn();
  if (lastCol < 1) return {};
  var headers = sheet.getRange(1, 1, 1, lastCol).getValues()[0];
  var map = {};
  headers.forEach(function(h, i){ if(h) map[String(h).trim()] = i + 1; });
  return map;
}

function findFirstExistingKey_(headerMap, candidates) {
  for (var i = 0; i < candidates.length; i++) { if (headerMap[candidates[i]]) return candidates[i]; }
  return null;
}

function loadExistingIds_(sheet, headerMap, idHeaderName) {
  var col = headerMap[idHeaderName];
  if (!col || sheet.getLastRow() < 2) return new Set();
  return new Set(sheet.getRange(2, col, sheet.getLastRow() - 1, 1).getValues().map(function(r){ return String(r[0]).trim(); }));
}

function objectToRowByHeader_(rowObject, headerMap) {
  var sorted = Object.keys(headerMap).map(function(k){ return {name: k, col: headerMap[k]}; }).sort(function(a,b){ return a.col - b.col; });
  return sorted.map(function(c){ return rowObject[c.name] || ""; });
}

function loadChannels_(sheet, headerMap, channelIdKey, channelUrlKey, channelViewsKey) {
  var lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  var data = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).getValues();
  return data.map(function(row){
    var id = channelIdKey ? String(row[headerMap[channelIdKey]-1]).trim() : "";
    var url = channelUrlKey ? String(row[headerMap[channelUrlKey]-1]).trim() : "";
    return { channelId: id || extractChannelIdFromUrl_(url), viewCount: channelViewsKey ? toNumber_(row[headerMap[channelViewsKey]-1]) : 0 };
  }).sort(function(a,b){ return b.viewCount - a.viewCount; });
}

function extractChannelIdFromUrl_(url) {
  var m = url.match(/\/channel\/(UC[\w-]+)/);
  return m ? m[1] : "";
}

function listTopVideosByView_(channelId, maxCount) {
  var ids = [], pageToken = null;
  while (ids.length < maxCount) {
    var res = YouTube.Search.list("id", { channelId: channelId, type: "video", order: "viewCount", maxResults: Math.min(50, maxCount - ids.length), pageToken: pageToken || "" });
    (res.items || []).forEach(function(item){ if(item.id.videoId) ids.push(item.id.videoId); });
    pageToken = res.nextPageToken;
    if (!pageToken) break;
  }
  return ids;
}

function fetchVideosDetails_(videoIds) {
  var all = [];
  for (var i = 0; i < videoIds.length; i += 50) {
    var res = YouTube.Videos.list("snippet,contentDetails,statistics", { id: videoIds.slice(i, i + 50).join(",") });
    all = all.concat(res.items || []);
  }
  return all;
}

function buildVideoRowObject_(videoItem, categoryCache) {
  var sn = videoItem.snippet || {}, st = videoItem.statistics || {}, cd = videoItem.contentDetails || {};
  var dur = iso8601DurationToSeconds_(cd.duration);
  return {
    "再生数": toNumber_(st.viewCount), "動画URL": "https://www.youtube.com/watch?v=" + videoItem.id, "投稿日": formatDate_(new Date(sn.publishedAt)), "コメント数": toNumber_(st.commentCount), "概要欄": sn.description, "タイトル": sn.title, "高評価数": toNumber_(st.likeCount), "動画の長さ": formatDurationHuman_(dur), "ハッシュタグ": extractHashtags_(sn.tags, sn.description), "サムネイル": thumbnailToImageFormula_(pickThumbnailUrl_(sn.thumbnails)), "チャンネル名": sn.channelTitle, "ショート / 長尺判定": (dur <= 60 ? "ショート" : "長尺"), "video ID": videoItem.id, "チャンネルID": sn.channelId, "カテゴリID": sn.categoryId, "カテゴリ名": getCategoryName_(sn.categoryId, categoryCache)
  };
}

function applyRowAndThumbnailSizing_(sheet, headerMap, startRow, rowCount) {
  var thumbCol = headerMap["サムネイル"];
  if (thumbCol) { sheet.setRowHeights(startRow, rowCount, 90); sheet.setColumnWidth(thumbCol, 120); }
}

function extractHashtags_(tags, description) {
  var res = (tags || []).filter(function(t){ return String(t).indexOf("#") === 0; });
  var m, re = /#[\w\u0080-\uFFFF]+/g;
  while ((m = re.exec(description || "")) !== null) res.push(m[0]);
  return Array.from(new Set(res)).join(" ");
}

function pickThumbnailUrl_(thumbs) {
  if (!thumbs) return "";
  return (thumbs.maxres || thumbs.standard || thumbs.high || thumbs.medium || thumbs.default || {}).url || "";
}

function toNumber_(v) { var n = Number(v); return isNaN(n) ? 0 : n; }

function formatDate_(date) {
  return date.getFullYear() + "-" + ("0"+(date.getMonth()+1)).slice(-2) + "-" + ("0"+date.getDate()).slice(-2);
}

function iso8601DurationToSeconds_(iso) {
  var m = (iso || "").match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
  if (!m) return 0;
  return (parseInt(m[1]||0)*3600) + (parseInt(m[2]||0)*60) + parseInt(m[3]||0);
}

function formatDurationHuman_(seconds) {
  var h = Math.floor(seconds/3600), m = Math.floor((seconds%3600)/60), s = seconds%60;
  return (h>0?h+"時間":"") + (m>0?m+"分":"") + s + "秒";
}

function getCategoryName_(id, cache) {
  if (!id) return "";
  if (cache[id]) return cache[id];
  try {
    var res = YouTube.VideoCategories.list("snippet", { id: id, regionCode: "JP" });
    cache[id] = res.items[0].snippet.title;
    return cache[id];
  } catch(e) { return ""; }
}

function thumbnailToImageFormula_(url) { return url ? '=IMAGE("' + url + '")' : ""; }
