// X 下書きプレビュー：一覧表示・検索・投稿・削除・編集・ステータス管理を提供するフロントエンド。

const API = `${window.location.origin}/api`;

// ngrok経由アクセス時はブラウザ警告をスキップするヘッダーを付与
function apiFetch(url, options = {}) {
  const isNgrok = window.location.hostname.includes('ngrok');
  if (isNgrok) {
    options.headers = { 'ngrok-skip-browser-warning': '1', ...(options.headers || {}) };
  }
  return fetch(url, options);
}

let allDrafts    = [];   // 全下書きキャッシュ
let currentDraft = null; // 現在選択中の下書き
let publicUrl    = window.location.origin;
let searchQuery  = '';   // 検索クエリ
let pendingDeleteId = null; // 削除モーダル用

// グループ折りたたみ状態（未投稿: 開く / 投稿済み: 閉じる）
const groupCollapsed = { draft: false, published: true };

// 文字数制限
const CHAR_LIMIT = 25000;
const CHAR_WARN  = 280;

// ── 初期化 ──────────────────────────────────────────

async function init() {
  try {
    const res  = await apiFetch(`${API}/public-url`);
    const data = await res.json();
    publicUrl  = data.url || publicUrl;
  } catch (_) {}
  await loadDraftList();
}

// ── 下書きリスト読み込み ─────────────────────────────

async function loadDraftList() {
  const el = document.getElementById('draft-list');
  try {
    const res    = await apiFetch(`${API}/drafts`);
    allDrafts    = await res.json();

    if (!Array.isArray(allDrafts) || allDrafts.length === 0) {
      el.innerHTML = '<div class="loading">下書きがありません</div>';
      return;
    }

    renderDraftList();

    // 現在の選択を維持 or 先頭を選択
    const targetId = currentDraft?.draft_id || allDrafts[0].draft_id;
    selectDraft(targetId);

  } catch (e) {
    el.innerHTML = `<div class="error-msg">取得エラー: ${e.message}</div>`;
  }
}

// ── 下書きリストをフィルタして描画 ──────────────────

function renderDraftList() {
  const el = document.getElementById('draft-list');
  const q  = searchQuery.trim().toLowerCase();

  const filtered = q
    ? allDrafts.filter(d => {
        const text = (d.display_name + ' @' + d.x_username + ' ' + (d.memo || '') +
          d.parts.map(p => p.content).join(' ')).toLowerCase();
        return text.includes(q);
      })
    : allDrafts;

  if (filtered.length === 0) {
    el.innerHTML = '<div class="loading">該当なし</div>';
    return;
  }

  const pendingItems = filtered.filter(d => d.status !== 'published');
  const postedItems  = filtered.filter(d => d.status === 'published');

  const renderItem = d => {
    const isThread  = d.parts.length > 1;
    const isPosted  = d.status === 'published';
    const preview   = d.parts[0]?.content?.slice(0, 48) || '';
    const initial   = (d.display_name || d.x_username).charAt(0).toUpperCase();
    const avatarHtml = d.profile_image_url
      ? `<div class="avatar-sm"><img src="${escAttr(d.profile_image_url)}" alt="${esc(initial)}" loading="lazy"></div>`
      : `<div class="avatar-sm">${esc(initial)}</div>`;
    const threadBadge = isThread
      ? `<span class="badge badge-thread">ツリー ${d.parts.length}</span>`
      : `<span class="badge badge-single">単発</span>`;
    return `
      <div class="draft-item${isPosted ? ' posted' : ''}" data-id="${d.draft_id}"
           onclick="selectDraft('${d.draft_id}')">
        <div class="draft-item-top">
          ${avatarHtml}
          <div class="draft-item-account">
            ${esc(d.display_name)} <span>@${esc(d.x_username)}</span>
          </div>
          <button class="delete-btn" title="削除" onclick="confirmDelete(event,'${d.draft_id}')">✕</button>
        </div>
        <div class="draft-item-preview">${esc(preview)}${preview.length >= 48 ? '…' : ''}</div>
        <div class="draft-item-meta">
          ${threadBadge}
          <span class="draft-item-date">${d.created_at}</span>
          ${d.memo ? `<span class="draft-item-date">・${esc(d.memo)}</span>` : ''}
        </div>
      </div>`;
  };

  const renderGroup = (key, label, items) => {
    if (items.length === 0) return '';
    const collapsed = groupCollapsed[key];
    return `
      <div class="group-header" onclick="toggleGroup('${key}')">
        <span class="group-chevron${collapsed ? '' : ' open'}">›</span>
        <span class="group-label">${label}</span>
        <span class="group-count">${items.length}</span>
      </div>
      <div class="group-body${collapsed ? ' collapsed' : ''}">
        ${items.map(renderItem).join('')}
      </div>`;
  };

  el.innerHTML =
    renderGroup('draft',  '未投稿', pendingItems) +
    renderGroup('published', '投稿済', postedItems);

  // アクティブ状態を再適用
  if (currentDraft) {
    document.querySelectorAll('.draft-item').forEach(el =>
      el.classList.toggle('active', el.dataset.id === currentDraft.draft_id)
    );
  }
}

function toggleGroup(key) {
  groupCollapsed[key] = !groupCollapsed[key];
  renderDraftList();
}

// ── 検索 ─────────────────────────────────────────────

function onSearch(value) {
  searchQuery = value;
  renderDraftList();
}

// ── 下書き選択 ───────────────────────────────────────

async function selectDraft(draftId) {
  document.querySelectorAll('.draft-item').forEach(el =>
    el.classList.toggle('active', el.dataset.id === draftId)
  );

  const content = document.getElementById('preview-content');
  content.innerHTML = '<div class="loading">読み込み中...</div>';

  try {
    const res   = await apiFetch(`${API}/draft?id=${draftId}`);
    const draft = await res.json();
    currentDraft = draft;
    renderPreview(draft);

    // モバイル：プレビュータブに自動切り替え
    if (window.innerWidth <= 640) switchTab('preview');

  } catch (e) {
    content.innerHTML = `<div class="error-msg">エラー: ${e.message}</div>`;
  }
}

// ── プレビュー描画 ───────────────────────────────────

function renderPreview(draft) {
  const content    = document.getElementById('preview-content');
  const isThread   = draft.parts.length > 1;
  const isPosted   = draft.status === 'published';
  const initial    = (draft.display_name || draft.x_username).charAt(0).toUpperCase();
  const previewUrl = `${publicUrl}?draft=${draft.draft_id}`;
  const original   = draft.original_tweet;
  const hasOrig    = !!(original && original.text);

  // ── ヘッダー ──
  const postedBar = isPosted
    ? `<div class="posted-bar">✓ 投稿済み ${draft.published_at ? '— ' + draft.published_at : ''}</div>`
    : '';
  const statusBtn = isPosted
    ? `<button class="revert-draft-btn" onclick="setStatus('${draft.draft_id}','draft')">未投稿に戻す</button>`
    : `<button class="post-btn" onclick="onPostClick()"><span>𝕏</span> 投稿する</button>`;
  const markPostedBtn = isPosted
    ? ''
    : `<button class="mark-posted-btn" id="mark-posted-btn" onclick="setStatus('${draft.draft_id}','published')">✓ 投稿済みにする</button>`;

  const header = `
    <div class="preview-header">
      <div class="preview-header-info">
        <h3>${esc(draft.display_name)}
          <span style="color:var(--text-muted);font-weight:400;font-size:14px">
            @${esc(draft.x_username)}
          </span>
        </h3>
        <p>${isThread ? `ツリー (${draft.parts.length} パーツ)` : '単発'} ・ ${draft.created_at}</p>
      </div>
      <div class="header-actions">
        ${draft.memo ? `<span class="preview-memo">📝 ${esc(draft.memo)}</span>` : ''}
        ${statusBtn}
        ${markPostedBtn}
      </div>
    </div>
    ${postedBar}
    <div class="preview-url-bar">
      🔗 <a href="${previewUrl}" target="_blank">${previewUrl}</a>
    </div>
  `;

  // ── 下書きカード列 ──
  const draftCards = buildDraftCards(draft, initial, isThread);

  const imagePromptBlock = buildImagePromptBlock(draft);

  if (!hasOrig) {
    // 比較なし — 従来レイアウト
    content.className = 'preview-content';
    content.innerHTML = header + draftCards + imagePromptBlock;
    return;
  }

  // ── 比較モード ──
  content.className = 'preview-content has-comparison';

  const origCards  = buildOriginalCards(original);
  const labelBar   = `
    <div class="comparison-labels">
      <div class="comparison-label">
        <span class="comparison-label-tag original">元投稿</span>
        @${esc(original.author_username)}${original.author_name ? ' · ' + esc(original.author_name) : ''}
      </div>
      <div class="comparison-label">
        <span class="comparison-label-tag draft">下書き</span>
        ${isThread ? `ツリー ${draft.parts.length} パーツ` : '単発'}
      </div>
    </div>`;

  const toggleBar = `
    <div class="compare-toggle-bar" id="compare-toggle-bar">
      <button class="compare-toggle-btn active" id="ctoggle-draft"
              onclick="switchCompareCol('draft')">下書き</button>
      <button class="compare-toggle-btn" id="ctoggle-original"
              onclick="switchCompareCol('original')">元投稿</button>
    </div>`;

  const body = `
    <div class="comparison-body">
      <div class="comparison-col visible" id="col-original">${origCards}</div>
      <div class="comparison-col visible" id="col-draft">${draftCards}${imagePromptBlock}</div>
    </div>`;

  content.innerHTML = header + labelBar + toggleBar + body;

  // モバイル初期状態: 下書きのみ表示
  if (window.innerWidth <= 640) switchCompareCol('draft');
}

// ── 比較: 元投稿カード（oEmbed対応）────────────────

function buildOriginalCards(original) {
  if (!original || !original.tweet_url) {
    return '<div class="original-unavailable">元投稿URLが不明です</div>';
  }

  // スレッドがあれば各パーツのURL一覧、なければルートURL1件
  const urls = (original.thread_parts && original.thread_parts.length > 0)
    ? original.thread_parts.map(p => p.tweet_url).filter(Boolean)
    : [original.tweet_url];

  // プレースホルダーを並べてからoEmbedを非同期で流し込む
  const slots = urls.map((url, i) => {
    const id = `oembed-slot-${Date.now()}-${i}`;
    requestAnimationFrame(() => loadOembed(url, id));
    return `<div class="oembed-slot" id="${id}">
      <div class="oembed-loading">読み込み中...</div>
    </div>`;
  }).join('');

  const urlBar = `<div class="oembed-url-bar">
    <a href="${escAttr(original.tweet_url)}" target="_blank" title="Xで元投稿を開く">
      🔗 ${esc(original.tweet_url)}
    </a>
  </div>`;

  return slots + urlBar;
}

async function loadOembed(tweetUrl, slotId) {
  const slot = document.getElementById(slotId);
  if (!slot) return;
  try {
    const res  = await apiFetch(`${API}/oembed?url=${encodeURIComponent(tweetUrl)}`);
    const data = await res.json();
    if (!slot.isConnected) return; // 別の下書きに切り替わっていたら無視
    if (data.ok && data.html) {
      slot.innerHTML = `<div class="oembed-wrapper">${data.html}</div>`;
      // widgets.js がすでにロード済みなら再描画を要求する
      if (window.twttr && window.twttr.widgets) {
        window.twttr.widgets.load(slot);
      }
    } else {
      slot.innerHTML = '<div class="oembed-loading oembed-error">元投稿を読み込めませんでした</div>';
    }
  } catch (_) {
    if (slot.isConnected) {
      slot.innerHTML = '<div class="oembed-loading oembed-error">元投稿を読み込めませんでした</div>';
    }
  }
}

// ── 比較: 下書きカード列 ─────────────────────────────

function buildDraftCards(draft, initial, isThread) {
  const cards = draft.parts.map((part, i) => {
    const isLast  = i === draft.parts.length - 1;
    const charLen = [...part.content].length;
    let charClass = 'char-ok';
    if (charLen > CHAR_LIMIT) charClass = 'char-over';
    else if (charLen > CHAR_WARN) charClass = 'char-warn';
    const charLabel = charLen > CHAR_LIMIT ? ' ⚠️ 上限超過' : charLen > CHAR_WARN ? ' (長文)' : '';

    const avatarEl = draft.profile_image_url
      ? `<div class="avatar"><img src="${escAttr(draft.profile_image_url)}" alt="${esc(initial)}" loading="lazy"></div>`
      : `<div class="avatar">${initial}</div>`;
    const avatarBlock = isThread && !isLast
      ? `<div class="thread-line-wrapper">${avatarEl}<div class="thread-line"></div></div>`
      : avatarEl;
    const imageHtml = part.image_url
      ? `<div class="tweet-image"><img src="${escAttr(part.image_url)}" alt="画像" loading="lazy"></div>`
      : '';

    return `
      <div class="tweet-card">
        <div class="tweet-header">
          ${avatarBlock}
          <div class="tweet-body">
            <div class="tweet-user-info">
              <span class="tweet-display-name">${esc(draft.display_name)}</span>
              <span class="tweet-verified">✓</span>
              <span class="tweet-handle">@${esc(draft.x_username)}</span>
            </div>
            <div class="tweet-text" id="text-${part.part_id}">${formatText(part.content)}</div>
            ${imageHtml}
            <div class="char-count ${charClass}">${charLen.toLocaleString()} 文字${charLabel}</div>
            <div class="tweet-actions">
              <div class="action-btn"><span class="action-icon">💬</span><span>0</span></div>
              <div class="action-btn repost"><span class="action-icon">🔁</span><span>0</span></div>
              <div class="action-btn like"><span class="action-icon">🤍</span><span>0</span></div>
              <div class="action-btn"><span class="action-icon">🔖</span><span>0</span></div>
            </div>
          </div>
        </div>
        <div class="tweet-footer">
          <button class="edit-btn" onclick="startEdit('${part.part_id}')">✎ 編集</button>
        </div>
      </div>`;
  }).join('');

  const addReplyZone = `
    <div class="add-reply-zone" id="add-reply-zone">
      <button class="add-reply-btn" onclick="startAddReply()">＋ リプを追加</button>
    </div>`;

  return cards + addReplyZone;
}

// ── 画像プロンプトブロック ────────────────────────────

function buildImagePromptBlock(draft) {
  const prompts = draft.image_prompts;
  if (!prompts || prompts.length === 0) return '';

  const first  = prompts[0];
  const copy   = (first.copy   || '').trim();
  const prompt = (first.prompt || '').trim();
  if (!prompt) return '';

  const copyLabel = copy
    ? `<span class="image-prompt-copy-label">${esc(copy)}</span>`
    : '';

  return `
    <div class="image-prompt-block">
      <div class="image-prompt-header">
        <span class="image-prompt-title">🖼 画像プロンプト</span>
        ${copyLabel}
        <button class="image-prompt-copy-btn" onclick="copyImagePrompt()">コピー</button>
      </div>
      <pre class="image-prompt-pre">${esc(prompt)}</pre>
    </div>`;
}

async function copyImagePrompt() {
  const prompts = currentDraft?.image_prompts;
  if (!prompts || prompts.length === 0) return;
  const text = (prompts[0].prompt || '').trim();
  if (!text) { showToast('プロンプトがありません', true); return; }
  try {
    await navigator.clipboard.writeText(text);
    showToast('✓ 画像プロンプトをコピーしました');
  } catch {
    showToast('コピーに失敗しました', true);
  }
}

// ── リプ追加 ─────────────────────────────────────────

function startAddReply() {
  const zone = document.getElementById('add-reply-zone');
  if (!zone) return;
  zone.innerHTML = `
    <div class="new-reply-area">
      <textarea class="tweet-textarea" id="new-reply-textarea"
        placeholder="リプの内容を入力..." rows="4"></textarea>
      <div class="edit-actions">
        <button class="save-btn" onclick="saveNewPart()">追加</button>
        <button class="cancel-btn" onclick="cancelAddReply()">キャンセル</button>
      </div>
    </div>`;
  const ta = document.getElementById('new-reply-textarea');
  if (ta) ta.focus();
}

function cancelAddReply() {
  const zone = document.getElementById('add-reply-zone');
  if (zone) zone.innerHTML =
    `<button class="add-reply-btn" onclick="startAddReply()">＋ リプを追加</button>`;
}

async function saveNewPart() {
  if (!currentDraft) return;
  const ta = document.getElementById('new-reply-textarea');
  const content = ta?.value?.trim();
  if (!content) { showToast('内容を入力してください', true); return; }

  try {
    const res = await apiFetch(`${API}/draft/part`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ draft_id: currentDraft.draft_id, content }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || '不明');

    // 再取得して再描画
    const reloadRes = await apiFetch(`${API}/draft?id=${currentDraft.draft_id}`);
    currentDraft    = await reloadRes.json();
    renderPreview(currentDraft);

    // サイドバーのキャッシュも更新
    const d = allDrafts.find(d => d.draft_id === currentDraft.draft_id);
    if (d) d.parts = currentDraft.parts;
    renderDraftList();
    showToast('✓ リプを追加しました');
  } catch (e) {
    showToast(`追加エラー: ${e.message}`, true);
  }
}

// ── モバイル比較トグル ────────────────────────────────

function switchCompareCol(col) {
  const colOrig   = document.getElementById('col-original');
  const colDraft  = document.getElementById('col-draft');
  const btnDraft  = document.getElementById('ctoggle-draft');
  const btnOrig   = document.getElementById('ctoggle-original');
  if (!colOrig || !colDraft) return;

  if (col === 'draft') {
    colDraft.classList.add('visible');
    colOrig.classList.remove('visible');
    btnDraft?.classList.add('active');
    btnOrig?.classList.remove('active');
  } else {
    colOrig.classList.add('visible');
    colDraft.classList.remove('visible');
    btnOrig?.classList.add('active');
    btnDraft?.classList.remove('active');
  }
}

// ── 投稿ボタン ───────────────────────────────────────

// スマホ: twitter:// アプリ起動 → 未インストールなら Web fallback
function openXCompose(text) {
  const encoded  = encodeURIComponent(text);
  const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
  if (isMobile) {
    window.location.href = `twitter://post?message=${encoded}`;
    setTimeout(() => window.open(`https://x.com/intent/post?text=${encoded}`, '_blank'), 1500);
  } else {
    window.open(`https://x.com/intent/post?text=${encoded}`, '_blank');
  }
}

async function onPostClick() {
  if (!currentDraft) return;
  if (currentDraft.parts.length > 1) {
    openThreadModal();
  } else {
    const text = currentDraft.parts[0]?.content || '';
    openXCompose(text);
    await notifyDiscord(text);
  }
}

// ── ツリー投稿ガイド ────────────────────────────────
let threadStep = 0;

function openThreadModal() {
  threadStep = 0;
  renderThreadStep();
  document.getElementById('thread-modal').style.display = 'flex';
}

function closeThreadModal() {
  document.getElementById('thread-modal').style.display = 'none';
}

function handleThreadModalBg(e) {
  if (e.target.id === 'thread-modal') closeThreadModal();
}

function renderThreadStep() {
  const parts  = currentDraft.parts;
  const part   = parts[threadStep];
  const isFirst = threadStep === 0;
  const isLast  = threadStep === parts.length - 1;

  document.getElementById('thread-step-label').textContent =
    `パート ${threadStep + 1} / ${parts.length}`;
  document.getElementById('thread-part-content').textContent = part.content;
  document.getElementById('thread-instruction').textContent = isFirst
    ? '① 内容をコピーして X アプリで投稿してください'
    : `② 前のツイートへの返信として投稿してください（パート ${threadStep + 1}）`;
  document.getElementById('thread-open-btn').style.display = isFirst ? '' : 'none';
  document.getElementById('thread-prev-btn').disabled = isFirst;
  document.getElementById('thread-next-btn').style.display = isLast ? 'none' : '';
  document.getElementById('thread-done-btn').style.display = isLast ? '' : 'none';
}

async function copyThreadPart() {
  const part = currentDraft.parts[threadStep];
  try {
    await navigator.clipboard.writeText(part.content);
    showToast('コピーしました');
  } catch {
    showToast('コピーに失敗しました', true);
  }
}

function openXForThread() {
  openXCompose(currentDraft.parts[0].content);
}

function prevThreadPart() {
  if (threadStep > 0) { threadStep--; renderThreadStep(); }
}

function nextThreadPart() {
  if (threadStep < currentDraft.parts.length - 1) { threadStep++; renderThreadStep(); }
}

async function doneThreadPost() {
  closeThreadModal();
  await notifyDiscord(currentDraft.parts[0]?.content || '');
}

async function notifyDiscord(mainContent) {
  const btn = document.querySelector('.post-btn');
  if (btn) { btn.disabled = true; btn.textContent = '送信中…'; }

  try {
    const res  = await apiFetch(`${API}/notify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        draft_id:     currentDraft.draft_id,
        main_content: mainContent,
        x_username:   currentDraft.x_username,
      }),
    });
    const data = await res.json();
    showToast(data.ok ? '✓ Discord に通知しました' : `Discord 通知失敗: ${data.error || '不明'}`, !data.ok);
  } catch (e) {
    showToast(`通知エラー: ${e.message}`, true);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<span>𝕏</span> 投稿する';
    }
  }
}

// ── ステータス変更（投稿済み ⇔ 未投稿） ─────────────

async function setStatus(draftId, status) {
  try {
    const res  = await apiFetch(`${API}/draft/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ draft_id: draftId, status }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || '不明');

    // ローカルキャッシュ更新
    const d = allDrafts.find(d => d.draft_id === draftId);
    if (d) {
      d.status = status;
      d.published_at = status === 'published' ? new Date().toISOString().slice(0,16).replace('T',' ') : null;
    }
    if (currentDraft?.draft_id === draftId) {
      currentDraft.status = status;
    }

    renderDraftList();
    // プレビューを再取得して再描画
    const reloadRes = await apiFetch(`${API}/draft?id=${draftId}`);
    currentDraft    = await reloadRes.json();
    renderPreview(currentDraft);

    showToast(status === 'published' ? '✓ 投稿済みにしました' : '↩ 未投稿に戻しました');
  } catch (e) {
    showToast(`ステータス更新エラー: ${e.message}`, true);
  }
}

// ── 削除 ─────────────────────────────────────────────

function confirmDelete(event, draftId) {
  event.stopPropagation();
  pendingDeleteId = draftId;
  document.getElementById('delete-modal').style.display = 'flex';
  document.getElementById('modal-confirm-btn').onclick = () => deleteDraft(draftId);
}

function closeDeleteModal() {
  pendingDeleteId = null;
  document.getElementById('delete-modal').style.display = 'none';
}

async function deleteDraft(draftId) {
  closeDeleteModal();
  try {
    const res  = await apiFetch(`${API}/draft?id=${draftId}`, { method: 'DELETE' });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || '不明');

    // ローカルキャッシュから削除
    allDrafts = allDrafts.filter(d => d.draft_id !== draftId);

    // プレビューリセット
    if (currentDraft?.draft_id === draftId) {
      currentDraft = null;
      const next = allDrafts[0];
      if (next) {
        selectDraft(next.draft_id);
      } else {
        document.getElementById('preview-content').innerHTML = `
          <div class="empty-state">
            <div class="x-logo-large">𝕏</div>
            <p>下書きがありません</p>
          </div>`;
      }
    }

    renderDraftList();
    showToast('🗑 削除しました');
  } catch (e) {
    showToast(`削除エラー: ${e.message}`, true);
  }
}

// ── インライン編集 ───────────────────────────────────

function startEdit(partId) {
  // currentDraft から本文を取得（onclick 属性に本文を埋め込むと特殊文字で壊れるため）
  const part = currentDraft?.parts.find(p => p.part_id === partId);
  if (!part) return;
  const originalContent = part.content;

  const textEl = document.getElementById(`text-${partId}`);
  if (!textEl) return;

  const parent = textEl.parentElement;
  textEl.style.display = 'none';

  const editArea = document.createElement('div');
  editArea.className = 'tweet-edit-area';
  editArea.id        = `edit-${partId}`;

  const textarea = document.createElement('textarea');
  textarea.className = 'tweet-textarea';
  textarea.value     = originalContent;

  const actions = document.createElement('div');
  actions.className  = 'edit-actions';

  const saveBtn = document.createElement('button');
  saveBtn.className  = 'save-btn';
  saveBtn.textContent = '保存';
  saveBtn.onclick    = () => saveEdit(partId, textarea.value, originalContent);

  const cancelBtn = document.createElement('button');
  cancelBtn.className  = 'cancel-btn';
  cancelBtn.textContent = 'キャンセル';
  cancelBtn.onclick    = () => cancelEdit(partId, originalContent);

  actions.append(saveBtn, cancelBtn);
  editArea.append(textarea, actions);
  parent.insertBefore(editArea, textEl);

  textarea.focus();
  textarea.setSelectionRange(textarea.value.length, textarea.value.length);
}

async function saveEdit(partId, newContent, originalContent) {
  if (newContent === originalContent) {
    cancelEdit(partId, originalContent);
    return;
  }
  try {
    const res  = await apiFetch(`${API}/draft/part`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ part_id: partId, content: newContent }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || '不明');

    // ローカルキャッシュ更新
    if (currentDraft) {
      const part = currentDraft.parts.find(p => p.part_id === partId);
      if (part) part.content = newContent;
      // allDrafts のプレビュー文字列も更新
      const d = allDrafts.find(d => d.draft_id === currentDraft.draft_id);
      if (d) {
        const dp = d.parts.find(p => p.part_id === partId);
        if (dp) dp.content = newContent;
      }
    }

    cancelEdit(partId, newContent);
    renderDraftList();
    showToast('✓ 保存しました');
  } catch (e) {
    showToast(`保存エラー: ${e.message}`, true);
  }
}

function cancelEdit(partId, content) {
  const editArea = document.getElementById(`edit-${partId}`);
  const textEl   = document.getElementById(`text-${partId}`);
  if (editArea) editArea.remove();
  if (textEl) {
    textEl.innerHTML = formatText(content);
    textEl.style.display = '';
  }
}

// ── モバイルタブ切り替え ─────────────────────────────

function switchTab(tab) {
  const sidebar  = document.getElementById('sidebar');
  const preview  = document.getElementById('preview-area');
  const btnList  = document.getElementById('tab-list-btn');
  const btnPrev  = document.getElementById('tab-preview-btn');

  if (tab === 'list') {
    sidebar.classList.add('tab-active');
    preview.classList.remove('tab-active');
    btnList.classList.add('active');
    btnPrev.classList.remove('active');
  } else {
    sidebar.classList.remove('tab-active');
    preview.classList.add('tab-active');
    btnList.classList.remove('active');
    btnPrev.classList.add('active');
  }
}

// モバイル初期表示はリスト側を出す
function initMobileTab() {
  if (window.innerWidth <= 640) {
    document.getElementById('sidebar').classList.add('tab-active');
  }
}

// ── ユーティリティ ───────────────────────────────────

function showToast(msg, isError = false) {
  const existing = document.getElementById('toast');
  if (existing) existing.remove();

  const toast       = document.createElement('div');
  toast.id          = 'toast';
  toast.className   = `toast${isError ? ' toast-error' : ''}`;
  toast.textContent = msg;
  document.body.appendChild(toast);

  requestAnimationFrame(() => toast.classList.add('toast-show'));
  setTimeout(() => {
    toast.classList.remove('toast-show');
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function formatText(text) {
  return esc(text)
    .replace(/(https?:\/\/\S+)/g, '<a href="$1" target="_blank">$1</a>')
    .replace(/#(\S+)/g,  '<span style="color:var(--accent)">#$1</span>')
    .replace(/@(\w+)/g,  '<span style="color:var(--accent)">@$1</span>');
}

function esc(str) {
  return String(str ?? '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

function escAttr(str) { return String(str ?? '').replace(/"/g,'&quot;'); }

// ── 起動 ─────────────────────────────────────────────

initMobileTab();
init();
