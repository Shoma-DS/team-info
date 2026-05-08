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
let imagePromptModalMode = 'generate';
let imageGenerationJob = null;
let imageGenerationTimer = null;
let imageGenerationDraftId = null;
let autoPostJob = null;
let autoPostTimer = null;
let autoPostDraftId = null;
let accountPresets = [];
let selectedAccount = localStorage.getItem('x-preview-selected-account') || 'all';
let authState = { auth_enabled: false, user: null };
let draftTotal = 0;
let draftHasMore = false;
let draftOffset = 0;
let draftLoading = false;
let searchTimer = null;

// グループ折りたたみ状態（未投稿: 開く / 投稿済み: 閉じる）
const groupCollapsed = { draft: false, published: true };

// 一覧ページング
const DRAFT_PAGE_SIZE = 20;

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
  await loadAuthState();
  if (!authState.user) {
    renderLoginGate();
    return;
  }
  clearLoginGate();
  await loadAccounts();
  await loadDraftList();
}

async function loadAuthState() {
  try {
    const res = await apiFetch(`${API}/auth/me`);
    authState = await res.json();
  } catch (_) {
    authState = { auth_enabled: false, user: null };
  }
  renderAuthButton();
}

function renderAuthButton() {
  const btn = document.getElementById('auth-btn');
  if (!btn) return;
  if (!authState.auth_enabled) {
    btn.textContent = 'G';
    btn.title = 'Google OAuth 未設定';
    btn.classList.remove('active');
    return;
  }
  if (authState.user) {
    btn.textContent = '✓';
    btn.title = `${authState.user.email || authState.user.display_name || 'ログイン中'} / クリックでログアウト`;
    btn.classList.add('active');
  } else {
    btn.textContent = 'G';
    btn.title = 'Googleでログイン';
    btn.classList.remove('active');
  }
}

function handleAuthClick() {
  if (!authState.auth_enabled) {
    showToast('Google OAuth が未設定です', true);
    return;
  }
  window.location.href = authState.user ? '/auth/logout' : '/auth/google/start';
}

function renderLoginGate() {
  document.body.classList.add('auth-required');
  const existing = document.getElementById('login-gate');
  if (existing) existing.remove();

  const gate = document.createElement('main');
  gate.id = 'login-gate';
  gate.className = 'login-gate';
  const canLogin = !!authState.auth_enabled;
  gate.innerHTML = `
    <section class="login-panel">
      <div class="login-mark">𝕏</div>
      <h1>X 下書きプレビュー</h1>
      <p>${canLogin ? 'Googleアカウントでログインしてください。' : 'Googleログイン設定がまだ有効ではありません。'}</p>
      <button class="google-login-btn" onclick="handleAuthClick()" ${canLogin ? '' : 'disabled'}>
        <span>G</span>
        <strong>Googleでログイン</strong>
      </button>
    </section>`;
  document.body.appendChild(gate);
}

function clearLoginGate() {
  document.body.classList.remove('auth-required');
  document.getElementById('login-gate')?.remove();
}

async function loadAccounts() {
  try {
    const res = await apiFetch(`${API}/accounts`);
    const data = await res.json();
    accountPresets = Array.isArray(data.accounts) ? data.accounts : [];
  } catch (_) {
    accountPresets = [];
  }
  renderAccountSummary();
}

// ── 下書きリスト読み込み ─────────────────────────────

async function loadDraftList({ append = false } = {}) {
  const el = document.getElementById('draft-list');
  if (draftLoading) return;
  draftLoading = true;
  if (!append) {
    draftOffset = 0;
    draftTotal = 0;
    draftHasMore = false;
    allDrafts = [];
    renderDraftLoading(0, '下書きを読み込み中...');
  } else {
    renderDraftList();
  }

  try {
    const params = new URLSearchParams({
      limit: String(DRAFT_PAGE_SIZE),
      offset: String(draftOffset),
    });
    if (selectedAccount !== 'all') params.set('account', selectedAccount);
    if (searchQuery.trim()) params.set('q', searchQuery.trim());

    const res = await apiFetch(`${API}/drafts?${params.toString()}`);
    const payload = await res.json();
    const items = Array.isArray(payload) ? payload : (payload.items || []);
    draftTotal = Array.isArray(payload) ? items.length : Number(payload.total || 0);
    draftHasMore = Array.isArray(payload) ? false : !!payload.has_more;
    draftOffset += items.length;
    allDrafts = append ? [...allDrafts, ...items] : items;

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
  } finally {
    draftLoading = false;
    renderDraftList();
  }
}

function renderDraftLoading(progress = 0, label = '読み込み中...') {
  const el = document.getElementById('draft-list');
  const skeletons = Array.from({ length: 8 }, (_, i) => `
    <div class="draft-skeleton" style="--i:${i}">
      <div class="draft-skeleton-avatar"></div>
      <div class="draft-skeleton-lines">
        <div></div><div></div><div></div>
      </div>
    </div>`).join('');
  el.innerHTML = `
    <div class="list-loading-panel">
      <div class="list-loading-top">
        <span>${esc(label)}</span>
        <span>${Math.round(progress)}%</span>
      </div>
      <div class="list-progress"><div style="width:${Math.max(8, Math.min(100, progress))}%"></div></div>
    </div>
    ${skeletons}`;
}

// ── 下書きリストをフィルタして描画 ──────────────────

function renderDraftList() {
  const el = document.getElementById('draft-list');
  const q  = searchQuery.trim().toLowerCase();

  const filtered = q
    ? allDrafts.filter(d => {
        const text = (d.display_name + ' @' + d.x_username + ' ' + (d.memo || '') +
          ' ' + (d.preview_content || '')).toLowerCase();
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
    const partCount = Number(d.part_count || d.parts?.length || 1);
    const isThread  = partCount > 1;
    const isPosted  = d.status === 'published';
    const preview   = (d.preview_content || d.parts?.[0]?.content || '').slice(0, 48);
    const initial   = (d.display_name || d.x_username).charAt(0).toUpperCase();
    const avatarHtml = d.profile_image_url
      ? `<div class="avatar-sm"><img src="${escAttr(d.profile_image_url)}" alt="${esc(initial)}" loading="lazy"></div>`
      : `<div class="avatar-sm">${esc(initial)}</div>`;
    const threadBadge = isThread
      ? `<span class="badge badge-thread">ツリー ${partCount}</span>`
      : `<span class="badge badge-single">単発</span>`;
    const imageBadge = d.has_image
      ? `<span class="badge badge-image">画像付き</span>`
      : '';
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
          ${imageBadge}
          <span class="draft-item-date">${d.created_at}</span>
          ${d.memo ? `<span class="draft-item-date">・${esc(d.memo)}</span>` : ''}
        </div>
      </div>`;
  };

  const renderGroup = (key, label, items) => {
    if (items.length === 0) return '';
    const collapsed = groupCollapsed[key];
    const displayItems = items;
    return `
      <div class="group-header" onclick="toggleGroup('${key}')">
        <span class="group-chevron${collapsed ? '' : ' open'}">›</span>
        <span class="group-label">${label}</span>
        <span class="group-count">${items.length}</span>
      </div>
      <div class="group-body${collapsed ? ' collapsed' : ''}">
        ${displayItems.map(renderItem).join('')}
      </div>`;
  };

  const loaded = allDrafts.length;
  const total = Math.max(draftTotal, loaded);
  const progress = total ? Math.round((loaded / total) * 100) : 0;
  const loadMoreBtn = draftHasMore
    ? `<button class="load-more-btn" onclick="loadMoreDrafts()" ${draftLoading ? 'disabled' : ''}>
         ${draftLoading ? '読み込み中...' : `さらに表示 (${loaded}/${total})`}
       </button>`
    : `<div class="list-loaded-all">読み込み完了 (${loaded}/${total})</div>`;
  const progressBar = `
    <div class="list-loading-panel compact">
      <div class="list-loading-top">
        <span>${searchQuery.trim() ? '検索結果' : '下書き一覧'}</span>
        <span>${loaded}/${total} ・ ${progress}%</span>
      </div>
      <div class="list-progress"><div style="width:${Math.max(6, progress)}%"></div></div>
    </div>`;

  el.innerHTML =
    progressBar +
    renderGroup('draft',  '未投稿', pendingItems) +
    renderGroup('published', '投稿済', postedItems) +
    loadMoreBtn;

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

function loadMoreDrafts() {
  if (!draftHasMore || draftLoading) return;
  loadDraftList({ append: true });
}

// ── 検索 ─────────────────────────────────────────────

function onSearch(value) {
  searchQuery = value;
  clearTimeout(searchTimer);
  renderDraftLoading(20, '検索中...');
  searchTimer = setTimeout(() => loadDraftList(), 250);
}

function getSelectedAccountPreset() {
  if (selectedAccount === 'all') return null;
  return accountPresets.find(a => a.x_username === selectedAccount || a.id === selectedAccount) || null;
}

function renderAccountSummary() {
  const nameEl = document.getElementById('account-summary-name');
  const userEl = document.getElementById('account-summary-user');
  const avatarEl = document.querySelector('.account-summary-avatar');
  if (!nameEl || !userEl || !avatarEl) return;
  const preset = getSelectedAccountPreset();
  if (!preset) {
    nameEl.textContent = 'すべてのアカウント';
    userEl.textContent = '下書き全体を表示';
    avatarEl.innerHTML = '𝕏';
    return;
  }
  nameEl.textContent = preset.display_name || preset.x_username || preset.id;
  userEl.textContent = preset.x_username ? `@${preset.x_username}` : preset.id;
  avatarEl.innerHTML = preset.profile_image_url
    ? `<img src="${escAttr(preset.profile_image_url)}" alt="${escAttr(preset.display_name || preset.x_username)}" loading="lazy">`
    : esc((preset.display_name || preset.x_username || preset.id || 'X').charAt(0).toUpperCase());
}

function ensureAccountModal() {
  let overlay = document.getElementById('account-modal');
  if (overlay) return overlay;
  overlay = document.createElement('div');
  overlay.id = 'account-modal';
  overlay.className = 'modal-overlay';
  overlay.style.display = 'none';
  overlay.innerHTML = `
    <div class="modal account-modal" onclick="event.stopPropagation()">
      <div class="thread-modal-header">
        <div>
          <div class="thread-step-label">プリセット</div>
          <h3 class="image-modal-title">アカウント変更</h3>
        </div>
        <button class="thread-close-btn" onclick="closeAccountModal()">✕</button>
      </div>
      <div id="account-preset-list" class="account-preset-list"></div>
    </div>`;
  overlay.onclick = closeAccountModal;
  document.body.appendChild(overlay);
  return overlay;
}

async function openAccountModal() {
  const overlay = ensureAccountModal();
  if (accountPresets.length === 0) await loadAccounts();
  renderAccountPresetList();
  overlay.style.display = 'flex';
}

function closeAccountModal() {
  const overlay = document.getElementById('account-modal');
  if (overlay) overlay.style.display = 'none';
}

function renderAccountPresetList() {
  const list = document.getElementById('account-preset-list');
  if (!list) return;
  const allSelected = selectedAccount === 'all';
  const allCard = `
    <button class="account-preset-card ${allSelected ? 'active' : ''}" onclick="selectAccountPreset('all')">
      <span class="avatar-sm account-preset-avatar">𝕏</span>
      <span class="account-preset-main">
        <span class="account-preset-name">すべてのアカウント</span>
        <span class="account-preset-user">全下書きを表示</span>
      </span>
      <span class="account-preset-check">${allSelected ? '✓' : ''}</span>
    </button>`;
  const cards = accountPresets.map(account => {
    const key = account.x_username || account.id;
    const selected = selectedAccount === key;
    const initial = (account.display_name || account.x_username || account.id || 'X').charAt(0).toUpperCase();
    const avatar = account.profile_image_url
      ? `<img src="${escAttr(account.profile_image_url)}" alt="${escAttr(account.display_name || account.x_username)}" loading="lazy">`
      : esc(initial);
    return `
      <button class="account-preset-card ${selected ? 'active' : ''}" onclick="selectAccountPreset('${escAttr(key)}')">
        <span class="avatar-sm account-preset-avatar">${avatar}</span>
        <span class="account-preset-main">
          <span class="account-preset-name">${esc(account.display_name || account.x_username || account.id)}</span>
          <span class="account-preset-user">@${esc(account.x_username || account.id)}${Number(account.draft_count || 0) ? ` ・ ${Number(account.draft_count)}件` : ''}</span>
        </span>
        <span class="account-preset-check">${selected ? '✓' : ''}</span>
      </button>`;
  }).join('');
  list.innerHTML = allCard + cards;
}

async function selectAccountPreset(accountKey) {
  selectedAccount = accountKey || 'all';
  localStorage.setItem('x-preview-selected-account', selectedAccount);
  currentDraft = null;
  renderAccountSummary();
  closeAccountModal();
  await loadDraftList();
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

  // 投稿済みのときはプレビューエリア全体の背景を変える
  const previewArea = document.getElementById('preview-area');
  previewArea.classList.toggle('is-posted-bg', isPosted);
  const initial    = (draft.display_name || draft.x_username).charAt(0).toUpperCase();
  const previewUrl = `${publicUrl}?draft=${draft.draft_id}`;
  const original   = draft.original_tweet;
  const hasOrig    = !!(original && original.tweet_url);

  // ── ヘッダー ──
  const postedBar = isPosted
    ? `<div class="posted-bar">✓ 投稿済み ${draft.published_at ? '— ' + draft.published_at : ''}</div>`
    : '';
  const statusBtn = isPosted
    ? `<button class="revert-draft-btn" onclick="setStatus('${draft.draft_id}','draft')">未投稿に戻す</button>`
    : `<button class="post-btn" onclick="onPostClick()"><span>𝕏</span> 投稿する</button>`;
  const autoPostBtn = isPosted
    ? ''
    : `<button class="auto-post-btn" id="auto-post-btn" onclick="startAutoPost()"><span>▶</span> 自動投稿</button>`;
  const markPostedBtn = isPosted
    ? ''
    : `<button class="mark-posted-btn" id="mark-posted-btn" onclick="setStatus('${draft.draft_id}','published')">✓ 投稿済みにする</button>`;
  const rewriteImageBtn = draft.image_prompts?.[0]?.prompt
    ? `<button class="image-source-copy-btn" onclick="openImagePromptModal('rewrite')">AIリライト</button>`
    : '';
  const characterBtn = `<button class="image-source-copy-btn" onclick="openCharacterSettingsModal()">キャラ設定</button>`;
  const obsidianBtn = `<button class="obsidian-save-btn" id="obsidian-save-btn" onclick="saveToObsidian()">Obsidianへ保存</button>`;

  const header = `
    <div class="preview-header">
      <div class="preview-header-info">
        <h3>${esc(draft.display_name)}
          <span style="color:var(--text-muted);font-weight:400;font-size:14px">
            @${esc(draft.x_username)}
          </span>
        </h3>
        <p>
          ${isThread ? `ツリー (${draft.parts.length} パーツ)` : '単発'} ・ ${draft.created_at}
          ${draft.has_image ? '<span class="badge badge-image preview-image-badge">画像付き</span>' : ''}
        </p>
      </div>
      <div class="header-actions">
        ${draft.memo ? `<span class="preview-memo">📝 ${esc(draft.memo)}</span>` : ''}
        ${obsidianBtn}
        ${characterBtn}
        ${rewriteImageBtn}
        ${statusBtn}
        ${autoPostBtn}
        ${markPostedBtn}
      </div>
    </div>
    ${postedBar}
    <div class="preview-url-bar">
      🔗 <a href="${previewUrl}" target="_blank">${previewUrl}</a>
    </div>
    <div id="auto-post-progress-slot"></div>
  `;

  // ── 下書きカード列 ──
  const draftCards = buildDraftCards(draft, initial, isThread);

  const imagePromptBlock = buildImagePromptBlock(draft);

  if (!hasOrig) {
    // 比較なし — 従来レイアウト
    content.className = 'preview-content';
    content.innerHTML = header + draftCards + imagePromptBlock;
    if (autoPostDraftId === draft.draft_id) renderAutoPostProgress(autoPostJob);
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
      <button class="compare-toggle-btn" id="ctoggle-original"
              onclick="switchCompareCol('original')">元投稿</button>
      <button class="compare-toggle-btn active" id="ctoggle-draft"
              onclick="switchCompareCol('draft')">下書き</button>
    </div>`;

  const body = `
    <div class="comparison-body">
      <div class="comparison-col visible" id="col-original">${origCards}</div>
      <div class="comparison-col visible" id="col-draft">${draftCards}${imagePromptBlock}</div>
    </div>`;

  content.innerHTML = header + labelBar + toggleBar + body;
  if (autoPostDraftId === draft.draft_id) renderAutoPostProgress(autoPostJob);

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

  const textHtml = original.text
    ? `<div class="original-text-fallback">${formatText(original.text)}</div>`
    : '';

  const urlBar = `<div class="oembed-url-bar">
    <a href="${escAttr(original.tweet_url)}" target="_blank" title="Xで元投稿を開く">
      🔗 ${esc(original.tweet_url)}
    </a>
  </div>`;

  // 元投稿のメディア（画像・動画）
  const mediaItems = original.media || [];
  const mediaHtml = mediaItems.map(m => {
    if (m.type === 'photo' && m.url) {
      return `<div class="orig-media"><img src="${escAttr(m.url)}" alt="元投稿画像" loading="lazy"></div>`;
    }
    const thumb = m.preview_url || m.url;
    if ((m.type === 'video' || m.type === 'animated_gif') && thumb) {
      const label = m.type === 'animated_gif' ? 'GIF' : '動画';
      return `<div class="orig-media orig-media-video"><img src="${escAttr(thumb)}" alt="サムネイル" loading="lazy"><div class="orig-media-badge">▶ ${label}</div></div>`;
    }
    return '';
  }).join('');

  // 元投稿テキスト内のURL（t.co 短縮以外を優先表示）
  const extUrls = (original.urls || []).filter(u => !u.includes('//t.co/'));
  const urlsHtml = extUrls.length
    ? `<div class="orig-urls">${extUrls.map(u => `<a href="${escAttr(u)}" target="_blank" class="orig-url-link">🔗 ${esc(u.length > 60 ? u.slice(0, 58) + '…' : u)}</a>`).join('')}</div>`
    : '';

  return slots + textHtml + urlBar + mediaHtml + urlsHtml;
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
      ? `<div class="tweet-image">
          <div class="tweet-image-toolbar">
            <button class="image-source-copy-btn" onclick="saveGeneratedImageFromUrl('${escAttr(part.image_url)}')">画像保存</button>
            <button class="image-source-copy-btn" onclick="copyGeneratedImageFromUrl('${escAttr(part.image_url)}')">画像をコピー</button>
          </div>
          <img src="${escAttr(part.image_url)}" alt="画像" loading="lazy">
        </div>`
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
  const sourceImgUrl = draft.parts?.[0]?.image_url || null;
  const first   = (prompts && prompts[0]) || {};
  const copy    = (first.copy   || '').trim();
  const prompt  = (first.prompt || '').trim();

  const hasPrompt    = !!prompt;
  const hasSourceImg = !!sourceImgUrl;
  if (!hasPrompt && !hasSourceImg) return '';

  const copyLabel = copy
    ? `<span class="image-prompt-copy-label">${esc(copy)}</span>`
    : '';

  const sourceImgBtn = hasSourceImg
    ? `<button class="image-source-copy-btn" onclick="copyGeneratedImage()">画像をコピー</button>`
    : '';
  const saveImgBtn = hasSourceImg
    ? `<button class="image-source-copy-btn" onclick="saveGeneratedImage()">画像保存</button>`
    : '';
  const promptCopyBtn = hasPrompt && !hasSourceImg
    ? `<button class="image-prompt-copy-btn" onclick="copyImagePrompt()">プロンプトをコピー</button>`
    : '';
  const generateBtn = hasPrompt
    ? `<button class="image-source-copy-btn" onclick="startImageGeneration()">画像生成</button>`
    : '';
  const refineBtn = hasPrompt && hasSourceImg
    ? `<button class="image-source-copy-btn" onclick="openImagePromptModal('refine')">修正依頼</button>`
    : '';
  const attachBtn = `<button class="image-source-copy-btn" onclick="openImagePromptModal('attach')">画像を添付</button>`;

  const sourceImgPreview = hasSourceImg
    ? `<div class="source-img-preview"><img src="${escAttr(sourceImgUrl)}" alt="生成済み画像" loading="lazy"><a href="${escAttr(sourceImgUrl)}" target="_blank">🔗 ${esc(sourceImgUrl.length > 70 ? sourceImgUrl.slice(0, 68) + '…' : sourceImgUrl)}</a></div>`
    : '';

  return `
    <div class="image-prompt-block">
      <div class="image-prompt-header">
        <span class="image-prompt-title">🖼 画像</span>
        ${copyLabel}
        <div class="image-copy-btns">
          ${generateBtn}
          ${refineBtn}
          ${attachBtn}
          ${saveImgBtn}
          ${sourceImgBtn}
          ${promptCopyBtn}
        </div>
      </div>
      <div id="image-generation-progress-slot"></div>
      ${sourceImgPreview}
      ${hasPrompt ? `<pre class="image-prompt-pre">${esc(prompt)}</pre>` : ''}
    </div>`;
}

function ensureImagePromptModal() {
  let overlay = document.getElementById('image-prompt-modal');
  if (overlay) return overlay;

  overlay = document.createElement('div');
  overlay.id = 'image-prompt-modal';
  overlay.className = 'modal-overlay';
  overlay.style.display = 'none';
  overlay.innerHTML = `
    <div class="modal image-modal" onclick="event.stopPropagation()">
      <div class="thread-modal-header">
        <div>
          <div class="thread-step-label" id="image-modal-label">画像プロンプト</div>
          <h3 class="image-modal-title" id="image-modal-title">画像生成</h3>
        </div>
        <button class="thread-close-btn" onclick="closeImagePromptModal()">✕</button>
      </div>
      <label class="image-modal-label">画像コピー</label>
      <input class="image-modal-input" id="image-copy-input" type="text" placeholder="画像内コピー">
      <label class="image-modal-label">画像プロンプト</label>
      <textarea class="image-modal-textarea" id="image-prompt-textarea" rows="9"></textarea>
      <label class="image-modal-label">リライト/追記指示</label>
      <textarea class="image-modal-instruction" id="image-rewrite-instruction" rows="3"
        placeholder="例: もっとスマホで読みやすく。文字を減らして、3ステップを強調して"></textarea>
      <div id="image-refine-fields" class="image-refine-fields" style="display:none">
        <div class="image-refine-preview-grid">
          <div>
            <span class="image-modal-label">現在の生成画像</span>
            <img id="image-refine-current-preview" class="image-refine-preview" alt="現在の生成画像">
          </div>
          <div>
            <span class="image-modal-label">参照画像プレビュー</span>
            <img id="image-refine-reference-preview" class="image-refine-preview" alt="参照画像">
          </div>
        </div>
        <label class="image-modal-label">参照画像URL</label>
        <input class="image-modal-input" id="reference-image-url" type="url"
          placeholder="https://.../codex-logo.png">
        <label class="image-modal-label">参照画像ローカルパス</label>
        <input class="image-modal-input" id="reference-image-path" type="text"
          placeholder="/Users/.../reference.png">
      </div>
      <label class="image-modal-label">生成済み画像パス</label>
      <input class="image-modal-input" id="generated-image-path" type="text"
        placeholder="/Users/.../.codex/generated_images/.../image.png">
      <p class="image-modal-help" id="image-modal-help"></p>
      <div class="image-modal-actions">
        <button class="cancel-btn" onclick="closeImagePromptModal()">閉じる</button>
        <button class="image-source-copy-btn" onclick="copyImageGenerationRequest()">生成依頼をコピー</button>
        <button class="image-source-copy-btn" onclick="rewriteImagePrompt()">Codexでリライト</button>
        <button class="image-source-copy-btn" id="image-refine-start-btn" onclick="startImageRefinement()" style="display:none">フィードバックで再生成</button>
        <button class="image-source-copy-btn" onclick="attachGeneratedImage()">画像を添付</button>
        <button class="save-btn" onclick="saveImagePrompt()">保存</button>
      </div>
    </div>`;
  overlay.onclick = closeImagePromptModal;
  document.body.appendChild(overlay);
  return overlay;
}

function openImagePromptModal(mode = 'generate') {
  if (!currentDraft) return;
  imagePromptModalMode = mode;
  const overlay = ensureImagePromptModal();
  const first = currentDraft.image_prompts?.[0] || {};
  document.getElementById('image-copy-input').value = first.copy || '';
  document.getElementById('image-prompt-textarea').value = first.prompt || '';
  document.getElementById('image-rewrite-instruction').value = '';
  document.getElementById('generated-image-path').value = '';
  const refineFields = document.getElementById('image-refine-fields');
  const referenceUrlInput = document.getElementById('reference-image-url');
  const referencePathInput = document.getElementById('reference-image-path');
  const currentPreview = document.getElementById('image-refine-current-preview');
  const referencePreview = document.getElementById('image-refine-reference-preview');
  if (referenceUrlInput) referenceUrlInput.value = '';
  if (referencePathInput) referencePathInput.value = '';
  if (currentPreview) currentPreview.src = currentDraft.parts?.[0]?.image_url || '';
  if (referencePreview) referencePreview.removeAttribute('src');
  if (refineFields) refineFields.style.display = mode === 'refine' ? 'block' : 'none';
  const refineStartBtn = document.getElementById('image-refine-start-btn');
  if (refineStartBtn) refineStartBtn.style.display = mode === 'refine' ? 'inline-flex' : 'none';
  if (referenceUrlInput) {
    referenceUrlInput.oninput = () => {
      if (referencePreview) referencePreview.src = referenceUrlInput.value.trim();
    };
  }

  const title = mode === 'rewrite' ? 'AIリライト' : mode === 'attach' ? '生成画像を添付' : mode === 'refine' ? '画像の修正依頼' : 'Codex画像生成';
  document.getElementById('image-modal-title').textContent = title;
  document.getElementById('image-modal-help').textContent =
    mode === 'generate'
      ? 'APIは使いません。生成依頼をコピーしてCodex/ChatGPTサブスク内の画像生成に渡してください。生成後の画像パスを貼ると1投稿目に添付できます。'
      : mode === 'rewrite'
        ? 'リライト指示を書いて「Codexでリライト」を押すと、現在のプロンプトを後から改善できます。'
        : mode === 'refine'
          ? '現在の生成画像に対して、参照画像と修正フィードバックを渡して再生成します。例: Codexロゴは参照画像の形に合わせる。'
          : '生成済み画像のローカルパスを貼ると、1投稿目の画像としてプレビューに表示します。';
  overlay.style.display = 'flex';
}

function closeImagePromptModal() {
  const overlay = document.getElementById('image-prompt-modal');
  if (overlay) overlay.style.display = 'none';
}

function getImageModalValues() {
  return {
    copy: document.getElementById('image-copy-input')?.value?.trim() || '',
    prompt: document.getElementById('image-prompt-textarea')?.value?.trim() || '',
    instruction: document.getElementById('image-rewrite-instruction')?.value?.trim() || '',
    imagePath: document.getElementById('generated-image-path')?.value?.trim() || '',
    referenceImageUrl: document.getElementById('reference-image-url')?.value?.trim() || '',
    referenceImagePath: document.getElementById('reference-image-path')?.value?.trim() || '',
  };
}

async function copyImageGenerationRequest() {
  const { copy, prompt, instruction, referenceImageUrl, referenceImagePath } = getImageModalValues();
  if (!prompt) { showToast('画像プロンプトがありません', true); return; }
  const request = buildImageGenerationRequest(copy, prompt, {
    feedback: imagePromptModalMode === 'refine' ? instruction : '',
    currentImageUrl: imagePromptModalMode === 'refine' ? currentDraft?.parts?.[0]?.image_url || '' : '',
    referenceImageUrl,
    referenceImagePath,
  });
  try {
    await navigator.clipboard.writeText(request);
    showToast('✓ 画像生成依頼をコピーしました');
  } catch {
    showToast('コピーに失敗しました', true);
  }
}

async function copyActiveImageGenerationRequest() {
  if (!imageGenerationJob?.request) return;
  try {
    await navigator.clipboard.writeText(imageGenerationJob.request);
    showToast('✓ 画像生成依頼を再コピーしました');
  } catch {
    showToast('コピーに失敗しました', true);
  }
}

async function startImageGeneration() {
  if (!currentDraft) return;
  const first = currentDraft.image_prompts?.[0] || {};
  const copy = (first.copy || '').trim();
  const prompt = (first.prompt || '').trim();
  if (!prompt) { showToast('画像プロンプトがありません', true); return; }

  clearInterval(imageGenerationTimer);
  try {
    const res = await apiFetch(`${API}/image-generation/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        draft_id: currentDraft.draft_id,
        copy,
        prompt,
        character_reference_url: getCharacterReferenceUrl(),
        character_traits: getCharacterTraits(),
        character_negative: getCharacterNegative(),
        character_placement: getCharacterPlacement(),
      }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || '不明');
    imageGenerationJob = data;
    imageGenerationDraftId = currentDraft.draft_id;
    renderImageGenerationProgress(data);
    showToast('Codex App Serverで画像生成を開始しました');
    imageGenerationTimer = setInterval(pollImageGeneration, 2500);
  } catch (e) {
    showToast(`画像生成開始失敗: ${e.message}`, true);
  }
}

async function startImageRefinement() {
  if (!currentDraft) return;
  const { copy, prompt, instruction, referenceImageUrl, referenceImagePath } = getImageModalValues();
  const currentImageUrl = currentDraft.parts?.[0]?.image_url || '';
  if (!prompt) { showToast('画像プロンプトがありません', true); return; }
  if (!currentImageUrl) { showToast('修正元の画像がありません', true); return; }
  if (!instruction) { showToast('修正フィードバックを入力してください', true); return; }

  clearInterval(imageGenerationTimer);
  try {
    const res = await apiFetch(`${API}/image-generation/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        draft_id: currentDraft.draft_id,
        copy,
        prompt,
        feedback: instruction,
        current_image_url: currentImageUrl,
        reference_image_url: referenceImageUrl,
        reference_image_path: referenceImagePath,
        character_reference_url: getCharacterReferenceUrl(),
        character_traits: getCharacterTraits(),
        character_negative: getCharacterNegative(),
        character_placement: getCharacterPlacement(),
      }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || '不明');
    imageGenerationJob = data;
    imageGenerationDraftId = currentDraft.draft_id;
    closeImagePromptModal();
    renderImageGenerationProgress(data);
    showToast('修正フィードバック付きで再生成を開始しました');
    imageGenerationTimer = setInterval(pollImageGeneration, 2500);
  } catch (e) {
    showToast(`再生成開始失敗: ${e.message}`, true);
  }
}

function renderImageGenerationProgress(job) {
  const slot = document.getElementById('image-generation-progress-slot');
  if (!slot || !job) return;
  const progress = Math.max(0, Math.min(100, Number(job.progress || 0)));
  const label = job.message || (
    job.status === 'completed'
      ? '画像生成完了。プレビューに反映しました。'
      : job.status === 'failed'
        ? '画像生成に失敗しました。'
        : 'Codex App Serverで画像生成中です。'
  );
  const retryButton = job.status === 'failed' && job.request
    ? `<button class="image-generation-copy-btn" onclick="copyActiveImageGenerationRequest()">生成依頼をコピー</button>`
    : '';
  const logs = Array.isArray(job.logs) ? job.logs.slice(-12) : [];
  const logBlock = logs.length
    ? `<div class="image-generation-log">
        ${logs.map(log => `
          <div class="image-generation-log-row ${escAttr(log.level || 'info')}">
            <span class="image-generation-log-time">${esc(log.at || '')}</span>
            <span class="image-generation-log-message">${esc(log.message || '')}</span>
          </div>`).join('')}
      </div>`
    : '';
  slot.innerHTML = `
    <div class="image-generation-progress ${job.status === 'failed' ? 'failed' : ''}">
      <div class="image-generation-progress-top">
        <span>${esc(label)}</span>
        <span>${progress}%</span>
      </div>
      <div class="image-generation-bar"><div style="width:${progress}%"></div></div>
      ${retryButton}
      ${logBlock}
    </div>`;
}

function buildImageGenerationRequest(copy, prompt, options = {}) {
  const characterReferenceUrl = getCharacterReferenceUrl();
  const traits = getCharacterTraits();
  const negative = getCharacterNegative();
  const placement = getCharacterPlacement();
  const lines = [
    'Codex/ChatGPTサブスク内の画像生成で、次のX投稿用図解を1枚生成してください。',
    'APIは使わないでください。',
    '添付されたプロフィール画像をキャラクター参照として使い、同じキャラクターの外見を図解内に入れてください。',
    `重要特徴: ${traits}`,
    `禁止する見た目: ${negative}`,
    `配置: ${placement}`,
    '',
    `[CHARACTER REFERENCE]\n${characterReferenceUrl || '(なし)'}`,
    '',
    `[COPY]\n${copy || '(なし)'}`,
    '',
    `[IMAGE PROMPT]\n${prompt}`,
  ];
  if (options.currentImageUrl || options.feedback || options.referenceImageUrl || options.referenceImagePath) {
    lines.push(
      '',
      '[REGENERATION CONTEXT]',
      `現在の生成画像: ${options.currentImageUrl || '(なし)'}`,
      `参照画像URL: ${options.referenceImageUrl || '(なし)'}`,
      `参照画像ローカルパス: ${options.referenceImagePath || '(なし)'}`,
      '',
      `[USER FEEDBACK]\n${options.feedback || '(なし)'}`,
      '',
      '現在の生成画像の良い部分は保ち、ユーザーのフィードバックと参照画像を優先して再生成してください。'
    );
  }
  return lines.join('\n');
}

async function pollImageGeneration() {
  const draftId = imageGenerationDraftId || currentDraft?.draft_id;
  if (!imageGenerationJob?.job_id || !draftId) return;
  try {
    const res = await apiFetch(`${API}/image-generation/status?id=${encodeURIComponent(imageGenerationJob.job_id)}`);
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || '不明');
    imageGenerationJob = data;
    renderImageGenerationProgress(data);

    // サーバー側のジョブ完了イベントが遅れても、下書きに画像が入ったら即時反映する。
    const reflected = await refreshDraftAfterImageGeneration(draftId, data.status === 'completed');
    if (reflected) {
      clearInterval(imageGenerationTimer);
      imageGenerationTimer = null;
      imageGenerationDraftId = null;
      showToast('✓ 画像をプレビューに反映しました');
      return;
    }

    if (data.status === 'failed') {
      clearInterval(imageGenerationTimer);
      imageGenerationTimer = null;
      imageGenerationDraftId = null;
      showToast(`画像生成失敗: ${data.message || '不明'}`, true);
      return;
    }
    if (data.status === 'completed') {
      clearInterval(imageGenerationTimer);
      imageGenerationTimer = null;
      imageGenerationDraftId = null;
    }
  } catch (e) {
    clearInterval(imageGenerationTimer);
    imageGenerationTimer = null;
    imageGenerationDraftId = null;
    showToast(`画像生成確認失敗: ${e.message}`, true);
  }
}

async function refreshDraftAfterImageGeneration(draftId, forceRender = false) {
  const reloadRes = await apiFetch(`${API}/draft?id=${encodeURIComponent(draftId)}`);
  const draft = await reloadRes.json();
  const imageAttached = !!draft.parts?.some(part => (part.image_url || '').trim());
  if (!imageAttached && !forceRender) return false;

  const item = allDrafts.find(d => d.draft_id === draft.draft_id);
  if (item) {
    item.parts = draft.parts;
    item.has_image = imageAttached;
    item.status = draft.status;
    item.memo = draft.memo;
  }
  if (currentDraft?.draft_id === draft.draft_id) {
    currentDraft = draft;
    renderDraftList();
    renderPreview(currentDraft);
  } else {
    renderDraftList();
  }
  return imageAttached;
}

async function rewriteImagePrompt() {
  if (!currentDraft) return;
  const { copy, prompt, instruction } = getImageModalValues();
  if (!prompt) { showToast('画像プロンプトがありません', true); return; }
  showToast('Codexでリライト中...');
  try {
    const res = await apiFetch(`${API}/image-prompt/rewrite`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        draft_id: currentDraft.draft_id,
        copy,
        prompt,
        instruction,
        character_reference_url: getCharacterReferenceUrl(),
      }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || '不明');
    document.getElementById('image-prompt-textarea').value = data.prompt;
    showToast('✓ リライトしました。保存すると反映されます');
  } catch (e) {
    showToast(`リライト失敗: ${e.message}`, true);
  }
}

async function saveImagePrompt() {
  if (!currentDraft) return;
  const { copy, prompt } = getImageModalValues();
  if (!prompt) { showToast('画像プロンプトがありません', true); return; }
  try {
    const res = await apiFetch(`${API}/image-prompt`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        draft_id: currentDraft.draft_id,
        copy,
        prompt,
      }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || '不明');
    currentDraft.image_prompts = [data.image_prompt];
    renderPreview(currentDraft);
    showToast('✓ 画像プロンプトを保存しました');
  } catch (e) {
    showToast(`保存失敗: ${e.message}`, true);
  }
}

function ensureCharacterSettingsModal() {
  let overlay = document.getElementById('character-settings-modal');
  if (overlay) return overlay;

  overlay = document.createElement('div');
  overlay.id = 'character-settings-modal';
  overlay.className = 'modal-overlay';
  overlay.style.display = 'none';
  overlay.innerHTML = `
    <div class="modal image-modal character-modal" onclick="event.stopPropagation()">
      <div class="thread-modal-header">
        <div>
          <div class="thread-step-label">アカウント別に保存</div>
          <h3 class="image-modal-title">キャラクター設定</h3>
        </div>
        <button class="thread-close-btn" onclick="closeCharacterSettingsModal()">✕</button>
      </div>
      <div class="character-preview-row">
        <img id="character-reference-preview" class="character-reference-preview" alt="参照画像">
        <div class="character-preview-meta">
          <div id="character-account-label" class="thread-step-label"></div>
          <p class="image-modal-help">この設定は保存され、サーバー再起動後も画像生成で使われます。</p>
        </div>
      </div>
      <label class="image-modal-label">参照画像URL</label>
      <input class="image-modal-input" id="character-reference-url-input" type="url"
        placeholder="https://pbs.twimg.com/profile_images/...jpg">
      <label class="image-modal-label">キャラクターの重要特徴</label>
      <textarea class="image-modal-textarea" id="character-traits-input" rows="4"></textarea>
      <label class="image-modal-label">禁止する見た目</label>
      <textarea class="image-modal-instruction" id="character-negative-input" rows="3"></textarea>
      <label class="image-modal-label">配置ルール</label>
      <input class="image-modal-input" id="character-placement-input" type="text">
      <div class="image-modal-actions">
        <button class="cancel-btn" onclick="closeCharacterSettingsModal()">閉じる</button>
        <button class="save-btn" onclick="saveCharacterSettings()">保存</button>
      </div>
    </div>`;
  overlay.onclick = closeCharacterSettingsModal;
  document.body.appendChild(overlay);
  return overlay;
}

async function openCharacterSettingsModal() {
  if (!currentDraft) return;
  const overlay = ensureCharacterSettingsModal();
  const accountKey = currentDraft.x_username || currentDraft.draft_id;
  try {
    const res = await apiFetch(`${API}/character-settings?account=${encodeURIComponent(accountKey)}&fallback_url=${encodeURIComponent(currentDraft.profile_image_url || '')}`);
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || '不明');
    currentDraft.character_setting = data.setting;
  } catch (e) {
    showToast(`キャラ設定取得失敗: ${e.message}`, true);
  }
  const setting = getCharacterSetting();
  document.getElementById('character-account-label').textContent = `@${accountKey}`;
  document.getElementById('character-reference-url-input').value = setting.reference_url || '';
  document.getElementById('character-traits-input').value = setting.traits || '';
  document.getElementById('character-negative-input').value = setting.negative || '';
  document.getElementById('character-placement-input').value = setting.placement || '';
  const preview = document.getElementById('character-reference-preview');
  preview.src = setting.reference_url || currentDraft.profile_image_url || '';
  overlay.style.display = 'flex';
}

function closeCharacterSettingsModal() {
  const overlay = document.getElementById('character-settings-modal');
  if (overlay) overlay.style.display = 'none';
}

async function saveCharacterSettings() {
  if (!currentDraft) return;
  const accountKey = currentDraft.x_username || currentDraft.draft_id;
  const payload = {
    account_key: accountKey,
    reference_url: document.getElementById('character-reference-url-input')?.value?.trim() || '',
    traits: document.getElementById('character-traits-input')?.value?.trim() || '',
    negative: document.getElementById('character-negative-input')?.value?.trim() || '',
    placement: document.getElementById('character-placement-input')?.value?.trim() || '',
  };
  try {
    const res = await apiFetch(`${API}/character-settings`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || '不明');
    currentDraft.character_setting = data.setting;
    const first = currentDraft.image_prompts?.[0];
    if (first) first.character_reference_url = data.setting.reference_url;
    showToast('✓ キャラクター設定を保存しました');
    closeCharacterSettingsModal();
    renderPreview(currentDraft);
  } catch (e) {
    showToast(`キャラ設定保存失敗: ${e.message}`, true);
  }
}

function ensureEnvSettingsModal() {
  let overlay = document.getElementById('env-settings-modal');
  if (overlay) return overlay;
  overlay = document.createElement('div');
  overlay.id = 'env-settings-modal';
  overlay.className = 'modal-overlay';
  overlay.style.display = 'none';
  overlay.innerHTML = `
    <div class="modal env-modal" onclick="event.stopPropagation()">
      <div class="thread-modal-header">
        <div>
          <div class="thread-step-label" id="env-settings-source">設定</div>
          <h3 class="image-modal-title">認証・連携設定</h3>
        </div>
        <button class="thread-close-btn" onclick="closeEnvSettingsModal()">✕</button>
      </div>
      <p class="image-modal-help">Googleログイン中はユーザー別DB設定へ保存します。未ログイン時だけローカル .env へ保存します。</p>
      <div id="env-settings-error" class="error-msg" style="display:none"></div>
      <div id="env-settings-list" class="env-settings-list">
        <div class="loading">読み込み中...</div>
      </div>
      <div class="env-add-row">
        <input id="env-new-key" class="image-modal-input" type="text" placeholder="X_... / NEON_... / DISCORD_WEBHOOK_X_DRAFT">
        <input id="env-new-value" class="image-modal-input" type="password" placeholder="値">
      </div>
      <div class="image-modal-actions">
        <button class="cancel-btn" onclick="closeEnvSettingsModal()">閉じる</button>
        <button class="save-btn" onclick="saveEnvSettings()">保存</button>
      </div>
    </div>`;
  overlay.onclick = closeEnvSettingsModal;
  document.body.appendChild(overlay);
  return overlay;
}

async function openEnvSettingsModal() {
  const overlay = ensureEnvSettingsModal();
  overlay.style.display = 'flex';
  await loadEnvSettings();
}

function closeEnvSettingsModal() {
  const overlay = document.getElementById('env-settings-modal');
  if (overlay) overlay.style.display = 'none';
}

function isEditableEnvKey(key) {
  return key === 'DISCORD_WEBHOOK_X_DRAFT' || key === 'NEON_DATABASE_URL' || key.startsWith('X_') || key.startsWith('NEON_');
}

async function loadEnvSettings() {
  const list = document.getElementById('env-settings-list');
  const error = document.getElementById('env-settings-error');
  if (!list || !error) return;
  error.style.display = 'none';
  list.innerHTML = '<div class="loading">読み込み中...</div>';
  try {
    const res = await apiFetch(`${API}/env-settings`);
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || '取得できませんでした');
    const items = Array.isArray(data.items) ? data.items : [];
    const source = document.getElementById('env-settings-source');
    if (source) source.textContent = data.storage === 'user_settings' ? 'ユーザー別DB設定' : data.path || '.env';
    if (items.length === 0) {
      list.innerHTML = '<div class="loading">設定がありません</div>';
      return;
    }
    list.innerHTML = items.map(item => `
      <label class="env-row">
          <span class="env-row-key">
            <span>${esc(item.key)}</span>
          <span>${item.source === 'user_settings' ? 'ユーザー別' : 'fallback'} ・ ${item.is_set ? esc(item.masked || 'set') : '未設定'}</span>
        </span>
        <input class="image-modal-input env-input" data-env-key="${escAttr(item.key)}"
          type="${item.sensitive ? 'password' : 'text'}"
          value="${escAttr(item.value || '')}"
          autocomplete="off">
      </label>`).join('');
  } catch (e) {
    list.innerHTML = '';
    error.textContent = e.message;
    error.style.display = 'block';
  }
}

async function saveEnvSettings() {
  const updates = {};
  document.querySelectorAll('.env-input').forEach(input => {
    const key = input.dataset.envKey;
    if (key) updates[key] = input.value;
  });
  const newKey = document.getElementById('env-new-key')?.value?.trim() || '';
  const newValue = document.getElementById('env-new-value')?.value || '';
  if (newKey && !isEditableEnvKey(newKey)) {
    showToast('X / Neon / DISCORD_WEBHOOK_X_DRAFT のキーだけ追加できます', true);
    return;
  }
  if (newKey) updates[newKey] = newValue;
  try {
    const res = await apiFetch(`${API}/env-settings`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ updates }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || '保存できませんでした');
    showToast(data.storage === 'user_settings' ? '✓ ユーザー別設定を保存しました' : '✓ .env を保存しました');
    document.getElementById('env-new-key').value = '';
    document.getElementById('env-new-value').value = '';
    await loadEnvSettings();
    await loadAccounts();
  } catch (e) {
    showToast(`環境変数保存失敗: ${e.message}`, true);
  }
}

async function attachGeneratedImage() {
  if (!currentDraft) return;
  const { imagePath } = getImageModalValues();
  if (!imagePath) { showToast('画像パスを入力してください', true); return; }
  try {
    const res = await apiFetch(`${API}/draft/image`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        draft_id: currentDraft.draft_id,
        image_path: imagePath,
      }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || '不明');

    const reloadRes = await apiFetch(`${API}/draft?id=${currentDraft.draft_id}`);
    currentDraft = await reloadRes.json();
    const item = allDrafts.find(d => d.draft_id === currentDraft.draft_id);
    if (item) {
      item.parts = currentDraft.parts;
      item.has_image = true;
    }
    renderDraftList();
    renderPreview(currentDraft);
    showToast('✓ 1投稿目に画像を添付しました');
  } catch (e) {
    showToast(`画像添付失敗: ${e.message}`, true);
  }
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

async function copySourceImageUrl() {
  const imageUrl = currentDraft?.parts?.[0]?.image_url;
  if (!imageUrl) { showToast('元画像URLがありません', true); return; }
  try {
    await navigator.clipboard.writeText(imageUrl);
    showToast('✓ 元画像URLをコピーしました');
  } catch {
    showToast('コピーに失敗しました', true);
  }
}

async function copyGeneratedImage() {
  const imageUrl = currentDraft?.parts?.[0]?.image_url;
  return copyGeneratedImageFromUrl(imageUrl);
}

async function saveGeneratedImage() {
  const imageUrl = currentDraft?.parts?.[0]?.image_url;
  return saveGeneratedImageFromUrl(imageUrl);
}

async function saveGeneratedImageFromUrl(imageUrl) {
  if (!imageUrl) { showToast('画像がありません', true); return; }
  const absoluteUrl = new URL(imageUrl, window.location.href).href;
  const filename = imageUrl.split('?')[0].split('/').pop() || `x-draft-${currentDraft?.draft_id || 'image'}.png`;
  try {
    const res = await fetch(absoluteUrl);
    if (!res.ok) throw new Error('image fetch failed');
    const blob = await res.blob();
    const objectUrl = URL.createObjectURL(blob);
    triggerImageDownload(objectUrl, filename);
    setTimeout(() => URL.revokeObjectURL(objectUrl), 3000);
    showToast('✓ 画像を保存しました');
  } catch {
    triggerImageDownload(absoluteUrl, filename);
    showToast('画像保存を開始しました');
  }
}

function triggerImageDownload(url, filename) {
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.rel = 'noopener';
  document.body.appendChild(a);
  a.click();
  a.remove();
}

async function copyGeneratedImageFromUrl(imageUrl) {
  if (!imageUrl) { showToast('画像がありません', true); return; }
  try {
    const res = await fetch(imageUrl);
    if (!res.ok) throw new Error('image fetch failed');
    const blob = await res.blob();
    if (!navigator.clipboard || typeof ClipboardItem === 'undefined') {
      await navigator.clipboard.writeText(new URL(imageUrl, window.location.href).href);
      showToast('画像URLをコピーしました');
      return;
    }
    await navigator.clipboard.write([
      new ClipboardItem({ [blob.type || 'image/png']: blob })
    ]);
    showToast('✓ 画像をコピーしました');
  } catch {
    try {
      await navigator.clipboard.writeText(new URL(imageUrl, window.location.href).href);
      showToast('画像URLをコピーしました');
    } catch {
      showToast('画像コピーに失敗しました', true);
    }
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

async function startAutoPost() {
  if (!currentDraft) return;
  const ok = window.confirm('OpenClaw の専用ブラウザで X を開き、この下書きを自動投稿します。X にログイン済みの状態で実行してください。');
  if (!ok) return;
  clearInterval(autoPostTimer);
  try {
    const res = await apiFetch(`${API}/auto-post/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ draft_id: currentDraft.draft_id }),
    });
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || '不明');
    autoPostJob = data;
    autoPostDraftId = currentDraft.draft_id;
    renderAutoPostProgress(data);
    setAutoPostButtonState(true);
    showToast('自動投稿を開始しました');
    autoPostTimer = setInterval(pollAutoPost, 2500);
  } catch (e) {
    showToast(`自動投稿開始失敗: ${e.message}`, true);
  }
}

async function pollAutoPost() {
  if (!autoPostJob?.job_id) return;
  try {
    const res = await apiFetch(`${API}/auto-post/status?id=${encodeURIComponent(autoPostJob.job_id)}`);
    const data = await res.json();
    if (!res.ok || !data.ok) throw new Error(data.error || '不明');
    autoPostJob = data;
    renderAutoPostProgress(data);
    if (data.status === 'completed') {
      clearInterval(autoPostTimer);
      autoPostTimer = null;
      setAutoPostButtonState(false);
      showToast('✓ 自動投稿が完了しました');
      await refreshDraftAfterAutoPost(autoPostDraftId || currentDraft?.draft_id);
      autoPostDraftId = null;
      return;
    }
    if (data.status === 'failed') {
      clearInterval(autoPostTimer);
      autoPostTimer = null;
      setAutoPostButtonState(false);
      autoPostDraftId = null;
      showToast(`自動投稿失敗: ${data.message || '不明'}`, true);
    }
  } catch (e) {
    clearInterval(autoPostTimer);
    autoPostTimer = null;
    setAutoPostButtonState(false);
    autoPostDraftId = null;
    showToast(`自動投稿確認失敗: ${e.message}`, true);
  }
}

function setAutoPostButtonState(isRunning) {
  const btn = document.getElementById('auto-post-btn');
  if (!btn) return;
  btn.disabled = !!isRunning;
  btn.innerHTML = isRunning ? '<span>…</span> 自動投稿中' : '<span>▶</span> 自動投稿';
}

function renderAutoPostProgress(job) {
  const slot = document.getElementById('auto-post-progress-slot');
  if (!slot || !job) return;
  const progress = Math.max(0, Math.min(100, Number(job.progress || 0)));
  const logs = Array.isArray(job.logs) ? job.logs.slice(-10) : [];
  const logBlock = logs.length
    ? `<div class="auto-post-log">
        ${logs.map(log => `
          <div class="image-generation-log-row ${escAttr(log.level || 'info')}">
            <span class="image-generation-log-time">${esc(log.at || '')}</span>
            <span class="image-generation-log-message">${esc(log.message || '')}</span>
          </div>`).join('')}
      </div>`
    : '';
  slot.innerHTML = `
    <div class="auto-post-progress ${job.status === 'failed' ? 'failed' : ''}">
      <div class="image-generation-progress-top">
        <span>${esc(job.message || '自動投稿中です')}</span>
        <span>${progress}%</span>
      </div>
      <div class="image-generation-bar"><div style="width:${progress}%"></div></div>
      ${logBlock}
    </div>`;
}

async function refreshDraftAfterAutoPost(draftId) {
  if (!draftId) return;
  const reloadRes = await apiFetch(`${API}/draft?id=${encodeURIComponent(draftId)}`);
  const draft = await reloadRes.json();
  const item = allDrafts.find(d => d.draft_id === draft.draft_id);
  if (item) {
    item.status = draft.status;
    item.published_at = draft.published_at;
    item.parts = draft.parts;
    item.memo = draft.memo;
  }
  if (currentDraft?.draft_id === draft.draft_id) {
    currentDraft = draft;
    renderDraftList();
    renderPreview(currentDraft);
  } else {
    renderDraftList();
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

async function saveToObsidian() {
  if (!currentDraft?.draft_id) return;
  const btn = document.getElementById('obsidian-save-btn');
  if (btn) {
    btn.disabled = true;
    btn.textContent = '保存中…';
  }

  try {
    const res = await apiFetch(`${API}/obsidian/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ draft_id: currentDraft.draft_id }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || '保存に失敗しました');
    showToast(`✓ Obsidianに保存しました: ${data.relative_path || data.path}`);
    if (data.obsidian_url) window.open(data.obsidian_url, '_blank');
  } catch (e) {
    showToast(`Obsidian保存エラー: ${e.message}`, true);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = 'Obsidianへ保存';
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

function normalizeXProfileImageUrl(url) {
  return String(url || '').replace('_normal.', '_400x400.');
}

function getCharacterSetting() {
  return currentDraft?.character_setting || {};
}

function getCharacterReferenceUrl() {
  return getCharacterSetting().reference_url ||
    currentDraft?.image_prompts?.[0]?.character_reference_url ||
    currentDraft?.character_reference?.url ||
    normalizeXProfileImageUrl(currentDraft?.profile_image_url);
}

function getCharacterTraits() {
  return getCharacterSetting().traits ||
    '半目、眠そうな表情、舌を少し出す、頬杖、黒い短髪、黒いスーツ、白シャツ、赤ネクタイ、気だるい表情';
}

function getCharacterNegative() {
  return getCharacterSetting().negative ||
    '明るい丸目の少年、パーカー、元気な笑顔、指差しポーズ';
}

function getCharacterPlacement() {
  return getCharacterSetting().placement ||
    '右下20〜25%。図解が主役、キャラクターは補助。';
}

// ── 起動 ─────────────────────────────────────────────

initMobileTab();
init();
