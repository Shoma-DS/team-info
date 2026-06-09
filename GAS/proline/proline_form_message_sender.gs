/**
 * このコードは、Web アプリ経由で受けたメッセージを ProLine のフォーム API へ転送する。
 * uid を指定して、ProLine 側のフォーム項目へ本文を書き込む送信役として使う。
 */
var FORM_URL = "https://mcxgj72y.autosns.app/fm/SFbKu9NOgT";
var FIELD_KEY = "form12-1";
var WEB_APP_SHARED_TOKEN = "";

function doGet() {
  return jsonOutput_({
    ok: true,
    message: "ProLine sender is running."
  });
}

/**
 * Web アプリ入口。
 * JSON body で userId / messageContent を受けて ProLine へ転送する。
 *
 * {
 *   "userId": "xxxx",
 *   "messageContent": "本文",
 *   "token": "optional"
 * }
 */
function doPost(e) {
  try {
    var request = parseWebAppRequest_(e);
    var result = sendProlineFormMessage(request.userId, request.messageContent);

    return jsonOutput_({
      ok: true,
      result: result
    });
  } catch (err) {
    return jsonOutput_({
      ok: false,
      error: String(err)
    });
  }
}

/**
 * ProLine Free の登録フォーム API に対して、指定ユーザー向けの動的メッセージを送る。
 *
 * @param {string} userId ProLine の uid
 * @param {string} messageContent フォーム項目へ流し込む文章
 * @return {Object} 実行結果
 */
function sendProlineFormMessage(userId, messageContent) {
  if (!userId) {
    throw new Error("userId は必須です。");
  }
  if (!messageContent) {
    throw new Error("messageContent は必須です。");
  }

  var requestUrl = buildProlineRequestUrl_(FORM_URL, userId);
  var payload = buildProlineFormPayload_(String(messageContent));

  var response = UrlFetchApp.fetch(requestUrl, {
    method: "post",
    payload: payload,
    muteHttpExceptions: true
  });

  var statusCode = response.getResponseCode();
  var responseText = response.getContentText();
  var result = {
    success: statusCode === 200,
    statusCode: statusCode,
    url: requestUrl,
    payload: payload,
    responseText: responseText
  };

  if (statusCode === 200) {
    Logger.log("送信成功: %s", JSON.stringify(result));
    return result;
  }

  if (statusCode >= 400 && statusCode < 500) {
    Logger.log("送信エラー: %s", JSON.stringify(result));
    throw new Error("ProLine API エラー (" + statusCode + "): " + responseText);
  }

  Logger.log("想定外レスポンス: %s", JSON.stringify(result));
  throw new Error("想定外のレスポンス (" + statusCode + "): " + responseText);
}

function buildProlineFormPayload_(messageContent) {
  var payload = {};
  payload[FIELD_KEY] = messageContent;
  payload["form_data[" + FIELD_KEY + "]"] = messageContent;
  return payload;
}

function buildProlineRequestUrl_(baseUrl, userId) {
  var separator = baseUrl.indexOf("?") === -1 ? "?" : "&";
  return baseUrl + separator + "uid=" + encodeURIComponent(String(userId));
}

function parseWebAppRequest_(e) {
  var raw = (e && e.postData && e.postData.contents) ? e.postData.contents : "";
  if (!raw) {
    throw new Error("リクエスト本文が空です。");
  }

  var data;
  try {
    data = JSON.parse(raw);
  } catch (err) {
    throw new Error("JSON の解析に失敗しました。");
  }

  if (WEB_APP_SHARED_TOKEN && data.token !== WEB_APP_SHARED_TOKEN) {
    throw new Error("token が不正です。");
  }
  if (!data.userId) {
    throw new Error("userId は必須です。");
  }
  if (!data.messageContent) {
    throw new Error("messageContent は必須です。");
  }

  return {
    userId: String(data.userId),
    messageContent: String(data.messageContent)
  };
}

function jsonOutput_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * 動作確認用のサンプル。
 * FORM_URL / FIELD_KEY / userId / messageContent を実値に変えて使う。
 */
function testSendProlineFormMessage() {
  var userId = "USER_ID";
  var messageContent = "ご注文番号は A-12345 です。";
  return sendProlineFormMessage(userId, messageContent);
}
