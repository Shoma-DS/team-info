// Neon DBから下書きを取得してXライクなプレビューを表示するフロントエンドスクリプト。
// 投稿ボタン押下時にXのWeb Intent（入力済み）を開き、Discord通知を送る。

const API = 'http://localhost:8765/api';
let currentDraft = null;
let publicUrl = `http://localhost:8765`;

// X有料課金ユーザー向け文字数上限（長文投稿対応）
const CHAR_LIMIT = 25000;
const CHAR_WARN  = 280;

async function init() {
  try {
    const res = await fetch(`${API}/public-url`);
    const data = await res.json();
    publicUrl = data.url || publicUrl;
  } catch (_) {}
  await loadDraftList();
}

async function loadDraftList() {
  const el = document.getElementById('draft-list');
  try {
    const res = await fetch(`${API}/drafts`);
    const drafts = await res.json();

    if (!Array.isArray(drafts) || drafts.length === 0) {
      el.innerHTML = '<div class="loading">下書きがありません</div>';
      document.getElementById('preview-content').innerHTML = `
        <div class="empty-state">
          <div class="x-logo-large">𝕏</div>
          <p>下書きがありません</p>
        </div>`;
      return;
    }

    el.innerHTML = drafts.map(d => {
      const isThread = d.parts.length > 1;
      const preview = d.parts[0]?.content?.slice(0, 50) || '';
      const badge = isThread
        ? `<span class="badge badge-thread">ツリー ${d.parts.length}件</span>`
        : `<span class="badge badge-single">単発</span>`;
      return `
        <div class="draft-item" data-id="${d.draft_id}" onclick="selectDraft('${d.draft_id}')">
          <div class="draft-item-account">
            ${esc(d.display_name)} <span>@${esc(d.x_username)}</span>
          </div>
          <div class="draft-item-preview">${esc(preview)}${preview.length >= 50 ? '…' : ''}</div>
          <div class="draft-item-meta">
            ${badge}
            <span class="draft-item-date">${d.created_at}</span>
            ${d.memo ? `<span class="draft-item-date">・${esc(d.memo)}</span>` : ''}
          </div>
        </div>`;
    }).join('');

    // 現在選択中のドラフトを維持 or 先頭を選択
    const targetId = currentDraft?.draft_id || drafts[0].draft_id;
    selectDraft(targetId);

  } catch (e) {
    el.innerHTML = `<div class="error-msg">取得エラー: ${e.message}</div>`;
  }
}

async function selectDraft(draftId) {
  document.querySelectorAll('.draft-item').forEach(el =>
    el.classList.toggle('active', el.dataset.id === draftId)
  );

  const content = document.getElementById('preview-content');
  content.innerHTML = '<div class="loading">読み込み中...</div>';

  try {
    const res = await fetch(`${API}/draft?id=${draftId}`);
    const draft = await res.json();
    currentDraft = draft;
    renderPreview(draft);
  } catch (e) {
    content.innerHTML = `<div class="error-msg">エラー: ${e.message}</div>`;
  }
}

function renderPreview(draft) {
  const content = document.getElementById('preview-content');
  const isThread = draft.parts.length > 1;
  const initial = draft.display_name?.charAt(0)?.toUpperCase() || 'X';
  const previewUrl = `${publicUrl}?draft=${draft.draft_id}`;

  const header = `
    <div class="preview-header">
      <div class="preview-header-info">
        <h3>${esc(draft.display_name)}
          <span style="color:var(--text-secondary);font-weight:400;font-size:15px">
            @${esc(draft.x_username)}
          </span>
        </h3>
        <p>${isThread ? `ツリー投稿 (${draft.parts.length} パーツ)` : '単発投稿'} ・ ${draft.created_at}</p>
      </div>
      <div class="header-actions">
        ${draft.memo ? `<span class="preview-memo">📝 ${esc(draft.memo)}</span>` : ''}
        <button class="post-btn" onclick="onPostClick()">
          <span>𝕏</span> 投稿する
        </button>
      </div>
    </div>
    <div class="preview-url-bar">
      🔗 プレビューURL: <a href="${previewUrl}" target="_blank">${previewUrl}</a>
    </div>
  `;

  const tweets = draft.parts.map((part, i) => {
    const isLast = i === draft.parts.length - 1;
    const charLen = [...part.content].length; // Unicode対応
    let charClass = 'char-ok';
    if (charLen > CHAR_LIMIT) charClass = 'char-over';
    else if (charLen > CHAR_WARN) charClass = 'char-warn';

    const avatarBlock = isThread && !isLast
      ? `<div class="thread-line-wrapper">
           <div class="avatar">${initial}</div>
           <div class="thread-line"></div>
         </div>`
      : `<div class="avatar">${initial}</div>`;

    const imageHtml = part.image_url
      ? `<div class="tweet-image"><img src="${escAttr(part.image_url)}" alt="画像" loading="lazy"></div>`
      : '';

    const charLabel = charLen > CHAR_LIMIT
      ? ` ⚠️ 上限超過`
      : charLen > CHAR_WARN
      ? ` (長文投稿)`
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
            <div class="tweet-text">${formatText(part.content)}</div>
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
      </div>`;
  }).join('');

  content.innerHTML = header + tweets;
}

async function onPostClick() {
  if (!currentDraft) return;

  const mainContent = currentDraft.parts[0]?.content || '';

  // X Web Intent で投稿画面を開く（最初のパーツのみ入力済み）
  const intentUrl = `https://x.com/intent/post?text=${encodeURIComponent(mainContent)}`;
  window.open(intentUrl, '_blank');

  // Discord 通知
  await notifyDiscord(mainContent);
}

async function notifyDiscord(mainContent) {
  const btn = document.querySelector('.post-btn');
  if (btn) { btn.disabled = true; btn.textContent = '通知送信中…'; }

  try {
    const res = await fetch(`${API}/notify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        draft_id: currentDraft.draft_id,
        main_content: mainContent,
        x_username: currentDraft.x_username,
      }),
    });
    const data = await res.json();
    if (data.ok) {
      showToast('✅ Discord に通知しました');
    } else {
      showToast(`⚠️ Discord 通知失敗: ${data.error || '不明'}`, true);
    }
  } catch (e) {
    showToast(`⚠️ 通知エラー: ${e.message}`, true);
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = '<span>𝕏</span> 投稿する'; }
  }
}

function showToast(msg, isError = false) {
  const existing = document.getElementById('toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'toast';
  toast.className = `toast${isError ? ' toast-error' : ''}`;
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
    .replace(/#(\S+)/g, '<span style="color:var(--text-link)">#$1</span>')
    .replace(/@(\w+)/g, '<span style="color:var(--text-link)">@$1</span>');
}

function esc(str) {
  return String(str ?? '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}
function escAttr(str) { return String(str ?? '').replace(/"/g, '&quot;'); }

init();
setInterval(loadDraftList, 30000);
