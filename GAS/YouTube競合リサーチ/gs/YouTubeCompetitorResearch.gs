/**
 * YoutubeデータリサーチAIカバー用
 * YouTube Data API v3 を使用
 *
 * スプレッドシートを開くと「YouTubeリサーチ」メニューが表示されます。
 * 各項目をクリックすると、設定ダイアログが開き、条件を指定して実行できます。
 */

var CONFIG = {
  SPREADSHEET_ID: "1XTfZOQ3IFHU9uhgRmc3TF4Jk-YHe7FS8fS7BzvJPshc",
  SHEET_VIDEOS: "Youtube動画",
  SHEET_CHANNELS: "Youtubeチャンネル",
  SHEET_KEYWORDS: "検索キーワード",
  SHEET_KEYWORD_RESEARCH: "検索キーワードリサーチ",
  SHEET_VIEW_RANKING: "再生数ランキング",
  MAX_VIDEOS_PER_CHANNEL: 20,
  MAX_SEARCH_RESULTS_PER_KEYWORD: 10,
  MAX_VIEW_RANKING_PER_KEYWORD: 10,
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

// =============================================================================
// メニュー / ダイアログ起動
// =============================================================================

/**
 * ① 競合リサーチ: 設定ダイアログを表示
 */
function runCompetitorYouTubeResearch() {
  var html = HtmlService.createHtmlOutputFromFile('CompetitorResearchDialog')
    .setWidth(520)
    .setHeight(640);
  SpreadsheetApp.getUi().showModalDialog(html, '競合リサーチ設定');
}

/**
 * ② 検索キーワードリサーチ: 設定ダイアログを表示
 */
function runKeywordResearch() {
  var tmpl = HtmlService.createTemplateFromFile('KeywordResearchDialog');
  tmpl.mode = 'keyword';
  tmpl.defaultCount = CONFIG.MAX_SEARCH_RESULTS_PER_KEYWORD;
  var html = tmpl.evaluate().setWidth(440).setHeight(380);
  SpreadsheetApp.getUi().showModalDialog(html, '検索キーワードリサーチ設定');
}

/**
 * ③ 再生数ランキング: 設定ダイアログを表示
 */
function runKeywordViewRanking() {
  var tmpl = HtmlService.createTemplateFromFile('KeywordResearchDialog');
  tmpl.mode = 'ranking';
  tmpl.defaultCount = CONFIG.MAX_VIEW_RANKING_PER_KEYWORD;
  var html = tmpl.evaluate().setWidth(440).setHeight(380);
  SpreadsheetApp.getUi().showModalDialog(html, '再生数ランキング設定');
}

/**
 * サイドバーからの呼び出しディスパッチャー
 */
function runResearchFromSidebar_(type) {
  if (type === 'competitor') runCompetitorYouTubeResearch();
  else if (type === 'keyword') runKeywordResearch();
  else if (type === 'ranking') runKeywordViewRanking();
  else if (type === 'channel') runChannelInfoFetch();
}

// =============================================================================
// ダイアログ用サーバーサイド関数
// =============================================================================

/**
 * チャンネル一覧を返す（CompetitorResearchDialog 用）
 * @return {Array<{channelId:string, name:string}>}
 */
function getChannelListForDialog() {
  var ss = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  var sheet = ss.getSheetByName(CONFIG.SHEET_CHANNELS);
  if (!sheet || sheet.getLastRow() < 2) return [];

  var headerMap = buildHeaderMap_(sheet);
  var channelIdKey = findFirstExistingKey_(headerMap, CONFIG.CHANNEL_ID_KEYS);
  var channelUrlKey = findFirstExistingKey_(headerMap, CONFIG.CHANNEL_URL_KEYS);
  var nameCol = headerMap['チャンネル名'] || null;

  var lastRow = sheet.getLastRow();
  var data = sheet.getRange(2, 1, lastRow - 1, sheet.getLastColumn()).getValues();

  var results = [];
  data.forEach(function(row) {
    var id  = channelIdKey ? String(row[headerMap[channelIdKey] - 1]).trim() : '';
    var url = channelUrlKey ? String(row[headerMap[channelUrlKey] - 1]).trim() : '';
    var name = nameCol ? String(row[nameCol - 1]).trim() : '';
    var chId = id || extractChannelIdFromUrl_(url);
    if (!chId && !url) return;
    results.push({
      channelId: chId,
      name: name || url || chId
    });
  });
  return results;
}

/**
 * 競合リサーチをダイアログのパラメータで実行
 * @param {Object} params - { maxPerChannel, videoType, selectedChannelIds, selectAll }
 * @return {number} 追加件数
 */
function runCompetitorResearchWithParams(params) {
  var maxPerChannel   = Math.min(Math.max(parseInt(params.maxPerChannel) || CONFIG.MAX_VIDEOS_PER_CHANNEL, 1), 50);
  var videoType       = params.videoType || 'both'; // 'both' | 'short' | 'long'
  var selectedIds     = params.selectedChannelIds || [];
  var selectAll       = !!params.selectAll;
  // フィルタリング後に十分な件数を確保するため多めに取得
  var fetchCount      = Math.min(maxPerChannel * (videoType !== 'both' ? 3 : 1), 50);

  var ss = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  var sheetVideos   = ss.getSheetByName(CONFIG.SHEET_VIDEOS)   || ss.insertSheet(CONFIG.SHEET_VIDEOS);
  var sheetChannels = ss.getSheetByName(CONFIG.SHEET_CHANNELS) || ss.insertSheet(CONFIG.SHEET_CHANNELS);

  var videoHeaderMap = buildHeaderMap_(sheetVideos);
  if (!videoHeaderMap[CONFIG.VIDEO_ID_HEADER]) {
    writeDefaultVideoHeaders_(sheetVideos);
    videoHeaderMap = buildHeaderMap_(sheetVideos);
  }

  var existingVideoIds = loadExistingIds_(sheetVideos, videoHeaderMap, CONFIG.VIDEO_ID_HEADER);
  var channelHeaderMap = buildHeaderMap_(sheetChannels);
  var channelIdKey   = findFirstExistingKey_(channelHeaderMap, CONFIG.CHANNEL_ID_KEYS);
  var channelUrlKey  = findFirstExistingKey_(channelHeaderMap, CONFIG.CHANNEL_URL_KEYS);
  var channelViewsKey = findFirstExistingKey_(channelHeaderMap, CONFIG.CHANNEL_VIEWS_KEYS);
  if (!channelIdKey && !channelUrlKey) throw new Error('チャンネルIDまたはURL列がありません。');

  var channels = loadChannels_(sheetChannels, channelHeaderMap, channelIdKey, channelUrlKey, channelViewsKey);

  // 選択チャンネルでフィルタ（全選択でない場合のみ）
  if (!selectAll && selectedIds.length > 0) {
    channels = channels.filter(function(ch) {
      return selectedIds.indexOf(ch.channelId) !== -1;
    });
  }

  var rowsToAppend = [];
  var categoryCache = {};

  for (var c = 0; c < channels.length; c++) {
    var ch = channels[c];
    if (!ch.channelId) continue;

    var topVideoIds = listTopVideosByView_(ch.channelId, fetchCount);
    if (topVideoIds.length === 0) continue;

    var videoItems = fetchVideosDetails_(topVideoIds);
    var added = 0;
    for (var v = 0; v < videoItems.length && added < maxPerChannel; v++) {
      var item = videoItems[v];
      if (!item.id || existingVideoIds.has(item.id)) continue;

      var dur = iso8601DurationToSeconds_((item.contentDetails || {}).duration);
      if (videoType === 'short' && dur > 60) continue;
      if (videoType === 'long'  && dur <= 60) continue;

      var rowObject = buildVideoRowObject_(item, categoryCache);
      rowsToAppend.push(objectToRowByHeader_(rowObject, videoHeaderMap));
      existingVideoIds.add(item.id);
      added++;
    }
  }

  var resultMsg;
  if (rowsToAppend.length > 0) {
    var startRow = findLastDataRow_(sheetVideos, videoHeaderMap, CONFIG.VIDEO_ID_HEADER) + 1;
    sheetVideos.getRange(startRow, 1, rowsToAppend.length, rowsToAppend[0].length).setValues(rowsToAppend);
    applyRowAndThumbnailSizing_(sheetVideos, videoHeaderMap, startRow, rowsToAppend.length);
    var endRow = startRow + rowsToAppend.length - 1;
    resultMsg = '✅ リサーチが完了しました。\n\n'
      + '📄 シート：' + CONFIG.SHEET_VIDEOS + '\n'
      + '📍 追加行：' + startRow + ' 行目 〜 ' + endRow + ' 行目\n'
      + '📊 追加件数：' + rowsToAppend.length + ' 件';
  } else {
    resultMsg = '⚠️ 追加できる動画がありませんでした。\n\n'
      + '（すでに取得済み、または条件に一致する動画がありません）';
  }
  SpreadsheetApp.getUi().alert(resultMsg);
  return rowsToAppend.length;
}

/**
 * キーワードリサーチをダイアログのパラメータで実行
 * @param {Object} params - { mode, maxPerKeyword, videoType }
 * @return {number} 結果件数
 */
function runKeywordResearchWithParams(params) {
  var mode        = params.mode || 'keyword';
  var orderByViews = (mode === 'ranking');
  var defaultMax  = orderByViews ? CONFIG.MAX_VIEW_RANKING_PER_KEYWORD : CONFIG.MAX_SEARCH_RESULTS_PER_KEYWORD;
  var maxPerKeyword = Math.min(Math.max(parseInt(params.maxPerKeyword) || defaultMax, 1), 50);
  var videoType   = params.videoType || 'both';
  var resultSheetName = orderByViews ? CONFIG.SHEET_VIEW_RANKING : CONFIG.SHEET_KEYWORD_RESEARCH;
  return runKeywordResearchCore_(resultSheetName, orderByViews, maxPerKeyword, videoType);
}

// =============================================================================
// 内部: リサーチ処理
// =============================================================================

function runKeywordResearchCore_(resultSheetName, orderByViews, maxPerKeyword, videoType) {
  var fetchCount = Math.min(maxPerKeyword * (videoType !== 'both' ? 3 : 1), 50);

  var ss = SpreadsheetApp.openById(CONFIG.SPREADSHEET_ID);
  var sheetKeywords = ss.getSheetByName(CONFIG.SHEET_KEYWORDS) || ss.insertSheet(CONFIG.SHEET_KEYWORDS);
  var sheetResult   = ss.getSheetByName(resultSheetName)       || ss.insertSheet(resultSheetName);

  var keywordHeaderMap = buildHeaderMap_(sheetKeywords);
  var keywordKey = findFirstExistingKey_(keywordHeaderMap, CONFIG.KEYWORD_HEADER_KEYS);
  if (!keywordKey) {
    sheetKeywords.getRange(1, 1).setValue('キーワード');
    if (sheetKeywords.getLastRow() < 2) sheetKeywords.getRange(2, 1).setValue('例: カバー 曲名');
    keywordHeaderMap = buildHeaderMap_(sheetKeywords);
    keywordKey = findFirstExistingKey_(keywordHeaderMap, CONFIG.KEYWORD_HEADER_KEYS);
  }
  var keywords = loadKeywords_(sheetKeywords, keywordHeaderMap, keywordKey);
  if (keywords.length === 0) throw new Error('キーワードを入力してください。');

  var searchDate = formatDate_(new Date());
  var resultRows = [];
  var categoryCache = {};

  for (var k = 0; k < keywords.length; k++) {
    var videoIds = orderByViews
      ? searchYouTubeByKeywordByViews_(keywords[k], fetchCount)
      : searchYouTubeByKeyword_(keywords[k], fetchCount);
    if (videoIds.length === 0) continue;

    var videoItems = fetchVideosDetails_(videoIds);
    var rank = 0;
    for (var r = 0; r < videoItems.length && rank < maxPerKeyword; r++) {
      var item = videoItems[r];
      var dur = iso8601DurationToSeconds_((item.contentDetails || {}).duration);
      if (videoType === 'short' && dur > 60) continue;
      if (videoType === 'long'  && dur <= 60) continue;
      rank++;
      resultRows.push(buildKeywordResearchRowObject_(keywords[k], rank, item, categoryCache, searchDate));
    }
  }

  writeKeywordResearchSheet_(sheetResult, resultRows);
  var kwMsg;
  if (resultRows.length > 0) {
    var kwStartRow = 2;
    var kwEndRow   = 1 + resultRows.length;
    kwMsg = '✅ リサーチが完了しました。\n\n'
      + '📄 シート：' + resultSheetName + '\n'
      + '📍 記載行：' + kwStartRow + ' 行目 〜 ' + kwEndRow + ' 行目\n'
      + '📊 取得件数：' + resultRows.length + ' 件';
  } else {
    kwMsg = '⚠️ 取得できる動画がありませんでした。\n\n'
      + '（キーワードシートにキーワードが入力されているか確認してください）';
  }
  SpreadsheetApp.getUi().alert(kwMsg);
  return resultRows.length;
}

// =============================================================================
// 以下: 既存ユーティリティ関数（変更なし）
// =============================================================================

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
    sheet.setRowHeights(2, numRows, 200);
    sheet.setColumnWidth(thumbCol, 360);
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

/**
 * video ID列を上から走査し、最後に値が入っている行番号を返す。
 * getLastRow() は =IMAGE() 数式の残骸などで実際のデータ末尾より大きくなるため、
 * ID列だけを確認してデータの実末尾を確定する。
 * @return {number} 最終データ行（データなし＝ヘッダー行の1を返す）
 */
function findLastDataRow_(sheet, headerMap, idHeaderName) {
  var col = headerMap[idHeaderName];
  if (!col) return sheet.getLastRow();
  var sheetLastRow = sheet.getLastRow();
  if (sheetLastRow < 2) return sheetLastRow;
  var values = sheet.getRange(2, col, sheetLastRow - 1, 1).getValues();
  for (var i = values.length - 1; i >= 0; i--) {
    if (String(values[i][0]).trim() !== '') return i + 2;
  }
  return 1; // ヘッダーのみ
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
    var id  = channelIdKey  ? String(row[headerMap[channelIdKey]  - 1]).trim() : "";
    var url = channelUrlKey ? String(row[headerMap[channelUrlKey] - 1]).trim() : "";
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
    "再生数": toNumber_(st.viewCount), "動画URL": "https://www.youtube.com/watch?v=" + videoItem.id,
    "投稿日": formatDate_(new Date(sn.publishedAt)), "コメント数": toNumber_(st.commentCount),
    "概要欄": sn.description, "タイトル": sn.title, "高評価数": toNumber_(st.likeCount),
    "動画の長さ": formatDurationHuman_(dur), "ハッシュタグ": extractHashtags_(sn.tags, sn.description),
    "サムネイル": thumbnailToImageFormula_(pickThumbnailUrl_(sn.thumbnails)), "チャンネル名": sn.channelTitle,
    "ショート / 長尺判定": (dur <= 60 ? "ショート" : "長尺"), "video ID": videoItem.id,
    "チャンネルID": sn.channelId, "カテゴリID": sn.categoryId, "カテゴリ名": getCategoryName_(sn.categoryId, categoryCache)
  };
}

function applyRowAndThumbnailSizing_(sheet, headerMap, startRow, rowCount) {
  var thumbCol = headerMap["サムネイル"];
  if (thumbCol) { sheet.setRowHeights(startRow, rowCount, 200); sheet.setColumnWidth(thumbCol, 360); }
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
