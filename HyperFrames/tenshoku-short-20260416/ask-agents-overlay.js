/*
 * HyperFrames Studio の Ask agent モーダルにローカル実行UIを足す。
 * Copy prompt が生成するプロンプトを捕捉し、実行中の進捗表示から
 * 結果報告と確認リロードまでを同じモーダル体験で扱う。
 */
(function () {
  const STATE = {
    patched: false,
    lastCopiedPrompt: "",
    activeJobId: null,
    pollTimer: null,
  };

  function patchClipboardCapture() {
    if (STATE.patched) return;
    STATE.patched = true;

    try {
      const clipboard = navigator.clipboard;
      if (clipboard && typeof clipboard.writeText === "function" && !clipboard.__askAgentsPatched) {
        const originalWriteText = clipboard.writeText.bind(clipboard);
        clipboard.writeText = async function askAgentsWriteText(text) {
          STATE.lastCopiedPrompt = String(text || "");
          window.__askAgentsLastCopiedPrompt = STATE.lastCopiedPrompt;
          return originalWriteText(text);
        };
        clipboard.__askAgentsPatched = true;
      }
    } catch (_) {
      // Clipboard is not always patchable. The execCommand fallback below still helps.
    }

    try {
      if (document.__askAgentsExecPatched) return;
      const originalExecCommand = document.execCommand.bind(document);
      document.execCommand = function askAgentsExecCommand(command, showUi, value) {
        if (String(command || "").toLowerCase() === "copy") {
          const active = document.activeElement;
          if (active && typeof active.value === "string" && active.value.trim()) {
            STATE.lastCopiedPrompt = active.value;
            window.__askAgentsLastCopiedPrompt = STATE.lastCopiedPrompt;
          }
        }
        return originalExecCommand(command, showUi, value);
      };
      document.__askAgentsExecPatched = true;
    } catch (_) {
      // Ignore unsupported execCommand patching.
    }
  }

  function injectStyles() {
    if (document.getElementById("ask-agents-overlay-style")) return;
    const style = document.createElement("style");
    style.id = "ask-agents-overlay-style";
    style.textContent = `
      .ask-agents-panel {
        margin: 0 20px 12px;
        padding: 10px 12px;
        border: 1px solid rgba(64, 64, 64, 0.9);
        border-radius: 10px;
        background: rgba(23, 23, 23, 0.72);
        color: #d4d4d4;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      }
      .ask-agents-panel * { box-sizing: border-box; }
      .ask-agents-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        flex-wrap: wrap;
      }
      .ask-agents-title {
        font-size: 11px;
        color: #a3a3a3;
        font-weight: 600;
      }
      .ask-agents-checks {
        display: flex;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
      }
      .ask-agents-check {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        font-size: 11px;
        color: #d4d4d4;
        user-select: none;
      }
      .ask-agents-check input {
        width: 13px;
        height: 13px;
        accent-color: #34d399;
      }
      .ask-agents-run,
      .ask-agents-primary,
      .ask-agents-secondary {
        height: 30px;
        padding: 0 12px;
        border: 0;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 700;
        cursor: pointer;
      }
      .ask-agents-run,
      .ask-agents-primary {
        background: rgba(52, 211, 153, 0.92);
        color: #06130f;
      }
      .ask-agents-secondary {
        background: rgba(38, 38, 38, 0.92);
        color: #d4d4d4;
        border: 1px solid rgba(82, 82, 82, 0.9);
      }
      .ask-agents-run:disabled,
      .ask-agents-primary:disabled,
      .ask-agents-secondary:disabled {
        opacity: 0.45;
        cursor: not-allowed;
      }
      .ask-agents-note {
        margin-top: 7px;
        font-size: 10px;
        color: #737373;
        line-height: 1.45;
      }
      .ask-agents-dialog-backdrop {
        position: fixed;
        inset: 0;
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 18px;
        background: rgba(0, 0, 0, 0.68);
        backdrop-filter: blur(8px);
      }
      .ask-agents-dialog {
        width: min(680px, calc(100vw - 36px));
        max-height: min(760px, calc(100vh - 36px));
        display: flex;
        flex-direction: column;
        overflow: hidden;
        border: 1px solid rgba(64, 64, 64, 0.95);
        border-radius: 16px;
        background: #0a0a0a;
        color: #e5e5e5;
        box-shadow: 0 24px 80px rgba(0, 0, 0, 0.55);
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
      }
      .ask-agents-dialog-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 16px;
        padding: 18px 20px 14px;
        border-bottom: 1px solid rgba(38, 38, 38, 0.95);
      }
      .ask-agents-dialog-title {
        margin: 0;
        font-size: 15px;
        font-weight: 700;
        color: #f5f5f5;
      }
      .ask-agents-dialog-subtitle {
        margin-top: 4px;
        font-size: 11px;
        color: #737373;
      }
      .ask-agents-close {
        width: 28px;
        height: 28px;
        border: 0;
        border-radius: 8px;
        background: transparent;
        color: #737373;
        cursor: pointer;
        font-size: 18px;
        line-height: 1;
      }
      .ask-agents-close:hover {
        background: rgba(38, 38, 38, 0.8);
        color: #d4d4d4;
      }
      .ask-agents-dialog-body {
        min-height: 0;
        overflow: auto;
        padding: 18px 20px;
      }
      .ask-agents-progress-wrap {
        display: grid;
        gap: 11px;
      }
      .ask-agents-progress-meta {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        font-size: 11px;
        color: #a3a3a3;
      }
      .ask-agents-progress-track {
        height: 8px;
        overflow: hidden;
        border-radius: 999px;
        background: rgba(38, 38, 38, 0.95);
      }
      .ask-agents-progress-fill {
        height: 100%;
        width: 0%;
        border-radius: inherit;
        background: linear-gradient(90deg, #22c55e, #34d399, #67e8f9);
        transition: width 300ms ease;
      }
      .ask-agents-spinner-row {
        display: flex;
        align-items: center;
        gap: 9px;
        color: #d4d4d4;
        font-size: 12px;
      }
      .ask-agents-spinner {
        width: 18px;
        height: 18px;
        border-radius: 999px;
        border: 2px solid rgba(115, 115, 115, 0.5);
        border-top-color: #34d399;
        animation: ask-agents-spin 0.85s linear infinite;
      }
      @keyframes ask-agents-spin {
        to { transform: rotate(360deg); }
      }
      .ask-agents-provider-list {
        display: grid;
        gap: 8px;
        margin-top: 16px;
      }
      .ask-agents-provider {
        display: grid;
        gap: 6px;
        padding: 10px;
        border: 1px solid rgba(38, 38, 38, 0.95);
        border-radius: 10px;
        background: rgba(23, 23, 23, 0.72);
      }
      .ask-agents-provider-head {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        color: #d4d4d4;
        font-size: 11px;
        font-weight: 700;
      }
      .ask-agents-provider-detail {
        font-size: 10px;
        color: #737373;
      }
      .ask-agents-mini-track {
        height: 4px;
        overflow: hidden;
        border-radius: 999px;
        background: rgba(64, 64, 64, 0.8);
      }
      .ask-agents-mini-fill {
        height: 100%;
        width: 0%;
        border-radius: inherit;
        background: #34d399;
        transition: width 300ms ease;
      }
      .ask-agents-report {
        display: grid;
        gap: 14px;
      }
      .ask-agents-report-section {
        display: grid;
        gap: 8px;
      }
      .ask-agents-report-title {
        font-size: 11px;
        color: #a3a3a3;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
      }
      .ask-agents-report-text,
      .ask-agents-log {
        margin: 0;
        padding: 10px;
        border: 1px solid rgba(38, 38, 38, 0.95);
        border-radius: 10px;
        background: rgba(23, 23, 23, 0.86);
        color: #d4d4d4;
        font-size: 11px;
        line-height: 1.55;
        white-space: pre-wrap;
      }
      .ask-agents-log {
        color: #a3e7c6;
        max-height: 190px;
        overflow: auto;
      }
      .ask-agents-file-list {
        display: grid;
        gap: 6px;
      }
      .ask-agents-file {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        padding: 7px 9px;
        border-radius: 8px;
        background: rgba(23, 23, 23, 0.86);
        border: 1px solid rgba(38, 38, 38, 0.9);
        color: #d4d4d4;
        font-size: 11px;
      }
      .ask-agents-file code {
        color: #e5e5e5;
        overflow-wrap: anywhere;
      }
      .ask-agents-badge {
        color: #34d399;
        font-size: 10px;
        text-transform: uppercase;
      }
      .ask-agents-dialog-foot {
        display: flex;
        justify-content: flex-end;
        gap: 8px;
        padding: 14px 20px 18px;
        border-top: 1px solid rgba(38, 38, 38, 0.95);
      }
    `;
    document.head.appendChild(style);
  }

  function textOf(node) {
    return (node && node.textContent ? node.textContent : "").trim();
  }

  function findAskAgentModal() {
    const headings = Array.from(document.querySelectorAll("h3"));
    const heading = headings.find((node) => textOf(node) === "Ask agent");
    if (!heading) return null;
    return heading.closest(".rounded-2xl") || heading.parentElement?.parentElement?.parentElement || null;
  }

  function findCopyButton(modal) {
    return Array.from(modal.querySelectorAll("button")).find((button) => textOf(button) === "Copy prompt");
  }

  function getTextareaPrompt(modal) {
    const textarea = modal.querySelector("textarea");
    return textarea && textarea.value ? textarea.value.trim() : "";
  }

  function selectedProviders(panel) {
    return Array.from(panel.querySelectorAll("input[data-provider]:checked")).map((input) => input.dataset.provider);
  }

  function providerLabel(provider) {
    if (provider === "codex") return "Codex App Server";
    if (provider === "claude") return "Claude Code";
    return provider;
  }

  function closeRunModal() {
    if (STATE.pollTimer) {
      clearTimeout(STATE.pollTimer);
      STATE.pollTimer = null;
    }
    const modal = document.getElementById("ask-agents-run-modal");
    if (modal) modal.remove();
  }

  function ensureRunModal(providers) {
    let modal = document.getElementById("ask-agents-run-modal");
    if (modal) return modal;
    modal = document.createElement("div");
    modal.id = "ask-agents-run-modal";
    modal.className = "ask-agents-dialog-backdrop";
    modal.innerHTML = `
      <div class="ask-agents-dialog" role="dialog" aria-modal="true" aria-labelledby="ask-agents-run-title">
        <div class="ask-agents-dialog-head">
          <div>
            <h3 id="ask-agents-run-title" class="ask-agents-dialog-title">Ask agent</h3>
            <div class="ask-agents-dialog-subtitle">Running ${providers.map(providerLabel).join(" / ")}</div>
          </div>
          <button class="ask-agents-close" type="button" aria-label="Close">×</button>
        </div>
        <div class="ask-agents-dialog-body"></div>
        <div class="ask-agents-dialog-foot">
          <button class="ask-agents-secondary" type="button" data-action="close">Close</button>
        </div>
      </div>
    `;
    modal.querySelector(".ask-agents-close").addEventListener("click", closeRunModal);
    modal.querySelector('[data-action="close"]').addEventListener("click", closeRunModal);
    document.body.appendChild(modal);
    return modal;
  }

  function setFooterForResult(modal, success) {
    const footer = modal.querySelector(".ask-agents-dialog-foot");
    footer.innerHTML = `
      <button class="ask-agents-secondary" type="button" data-action="close">閉じる</button>
      <button class="ask-agents-primary" type="button" data-action="reload">${success ? "確認してリロード" : "リロードして確認"}</button>
    `;
    footer.querySelector('[data-action="close"]').addEventListener("click", closeRunModal);
    footer.querySelector('[data-action="reload"]').addEventListener("click", () => window.location.reload());
  }

  function renderProgress(modal, job) {
    const body = modal.querySelector(".ask-agents-dialog-body");
    const progress = Math.max(0, Math.min(100, Number(job.progress || 0)));
    const providers = Array.isArray(job.providers) ? job.providers : [];
    const states = job.providerStates || {};
    body.innerHTML = `
      <div class="ask-agents-progress-wrap">
        <div class="ask-agents-spinner-row">
          <div class="ask-agents-spinner" aria-hidden="true"></div>
          <div>${escapeHtml(job.phase || "Running agent")}</div>
        </div>
        <div class="ask-agents-progress-meta">
          <span>${escapeHtml(job.currentProvider ? providerLabel(job.currentProvider) : "Preparing")}</span>
          <span>${progress}%</span>
        </div>
        <div class="ask-agents-progress-track">
          <div class="ask-agents-progress-fill" style="width: ${progress}%"></div>
        </div>
      </div>
      <div class="ask-agents-provider-list">
        ${providers.map((provider) => renderProvider(provider, states[provider])).join("")}
      </div>
      <div class="ask-agents-report-section" style="margin-top: 16px;">
        <div class="ask-agents-report-title">Live log</div>
        <pre class="ask-agents-log">${escapeHtml((job.logs || []).slice(-50).join("\n"))}</pre>
      </div>
    `;
  }

  function renderProvider(provider, state) {
    const status = state?.status || "pending";
    const progress = Math.max(0, Math.min(100, Number(state?.progress || 0)));
    const detail = state?.detail || "Waiting";
    return `
      <div class="ask-agents-provider">
        <div class="ask-agents-provider-head">
          <span>${escapeHtml(providerLabel(provider))}</span>
          <span>${escapeHtml(status)}</span>
        </div>
        <div class="ask-agents-mini-track">
          <div class="ask-agents-mini-fill" style="width: ${progress}%"></div>
        </div>
        <div class="ask-agents-provider-detail">${escapeHtml(detail)}</div>
      </div>
    `;
  }

  function renderResult(modal, job) {
    const body = modal.querySelector(".ask-agents-dialog-body");
    const report = job.report || {};
    const changedFiles = Array.isArray(report.changedFiles) ? report.changedFiles : [];
    const success = job.status === "succeeded";
    const title = modal.querySelector(".ask-agents-dialog-title");
    const subtitle = modal.querySelector(".ask-agents-dialog-subtitle");
    title.textContent = success ? "Agent result" : "Agent failed";
    subtitle.textContent = success ? "変更内容を確認してからプレビューをリロードできます" : "ログとエラー内容を確認してください";
    body.innerHTML = `
      <div class="ask-agents-progress-wrap" style="margin-bottom: 16px;">
        <div class="ask-agents-progress-meta">
          <span>${escapeHtml(job.phase || (success ? "Completed" : "Failed"))}</span>
          <span>${Math.max(0, Math.min(100, Number(job.progress || 100)))}%</span>
        </div>
        <div class="ask-agents-progress-track">
          <div class="ask-agents-progress-fill" style="width: ${Math.max(0, Math.min(100, Number(job.progress || 100)))}%"></div>
        </div>
      </div>
      <div class="ask-agents-report">
        <div class="ask-agents-report-section">
          <div class="ask-agents-report-title">AI agent report</div>
          <pre class="ask-agents-report-text">${escapeHtml(report.summary || job.error || "No report was returned.")}</pre>
        </div>
        <div class="ask-agents-report-section">
          <div class="ask-agents-report-title">Changed files</div>
          <div class="ask-agents-file-list">
            ${changedFiles.length ? changedFiles.map(renderChangedFile).join("") : '<div class="ask-agents-report-text">このプロジェクト内のファイル変更は検出されませんでした。</div>'}
          </div>
        </div>
        ${report.diffStat ? `<div class="ask-agents-report-section"><div class="ask-agents-report-title">Diff stat</div><pre class="ask-agents-report-text">${escapeHtml(report.diffStat)}</pre></div>` : ""}
        ${report.gitStatus ? `<div class="ask-agents-report-section"><div class="ask-agents-report-title">Git status</div><pre class="ask-agents-report-text">${escapeHtml(report.gitStatus)}</pre></div>` : ""}
        <div class="ask-agents-report-section">
          <div class="ask-agents-report-title">Execution log</div>
          <pre class="ask-agents-log">${escapeHtml((job.logs || []).slice(-80).join("\n"))}</pre>
        </div>
      </div>
    `;
    setFooterForResult(modal, success);
  }

  function renderChangedFile(file) {
    return `
      <div class="ask-agents-file">
        <code>${escapeHtml(file.path || "")}</code>
        <span class="ask-agents-badge">${escapeHtml(file.status || "changed")}</span>
      </div>
    `;
  }

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    })[char]);
  }

  async function waitForPrompt(modal) {
    STATE.lastCopiedPrompt = "";
    window.__askAgentsLastCopiedPrompt = "";

    const copyButton = findCopyButton(modal);
    if (copyButton) copyButton.click();

    for (let i = 0; i < 12; i += 1) {
      const captured = window.__askAgentsLastCopiedPrompt || STATE.lastCopiedPrompt;
      if (captured && captured.trim()) return captured.trim();
      await new Promise((resolve) => setTimeout(resolve, 90));
    }

    return getTextareaPrompt(modal);
  }

  async function runAgents(modal, panel) {
    const providers = selectedProviders(panel);
    if (providers.length === 0) {
      const runModal = ensureRunModal(["none"]);
      renderResult(runModal, {
        status: "failed",
        progress: 100,
        phase: "No agent selected",
        error: "Codex App Server か Claude Code を選んでください。",
        report: { summary: "Codex App Server か Claude Code を選んでください。", changedFiles: [] },
        logs: [],
      });
      return;
    }

    const runButton = panel.querySelector(".ask-agents-run");
    const runModal = ensureRunModal(providers);
    runButton.disabled = true;
    renderProgress(runModal, {
      status: "pending",
      progress: 2,
      phase: "Capturing prompt",
      providers,
      providerStates: Object.fromEntries(providers.map((provider) => [provider, { status: "pending", progress: 0, detail: "Waiting" }])),
      logs: ["Capturing HyperFrames Ask agent prompt."],
    });

    try {
      const prompt = await waitForPrompt(modal);
      if (!prompt) {
        renderResult(runModal, {
          status: "failed",
          progress: 100,
          phase: "Prompt capture failed",
          error: "Ask agent prompt was empty.",
          report: { summary: "Ask agent prompt が空でした。入力内容を確認してください。", changedFiles: [] },
          logs: [],
        });
        return;
      }

      renderProgress(runModal, {
        status: "pending",
        progress: 6,
        phase: "Starting agent job",
        providers,
        providerStates: Object.fromEntries(providers.map((provider) => [provider, { status: "pending", progress: 0, detail: "Waiting" }])),
        logs: [`Providers: ${providers.map(providerLabel).join(", ")}`],
      });

      const response = await fetch("/ask-agents/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt, providers }),
      });
      const body = await response.json().catch(() => ({}));
      if (!response.ok) {
        renderResult(runModal, {
          status: "failed",
          progress: 100,
          phase: "Failed to start",
          error: body.error || `HTTP ${response.status}`,
          report: { summary: body.error || `HTTP ${response.status}`, changedFiles: [] },
          logs: [],
        });
        return;
      }
      STATE.activeJobId = body.jobId;
      pollJob(body.jobId, runModal);
    } catch (error) {
      renderResult(runModal, {
        status: "failed",
        progress: 100,
        phase: "Ask agents failed",
        error: String(error && error.message ? error.message : error),
        report: { summary: String(error && error.message ? error.message : error), changedFiles: [] },
        logs: [],
      });
    } finally {
      runButton.disabled = false;
    }
  }

  async function pollJob(jobId, modal) {
    if (STATE.pollTimer) {
      clearTimeout(STATE.pollTimer);
      STATE.pollTimer = null;
    }
    try {
      const response = await fetch(`/ask-agents/jobs/${encodeURIComponent(jobId)}`);
      const job = await response.json();
      if (job.status === "running" || job.status === "pending") {
        renderProgress(modal, job);
        STATE.pollTimer = setTimeout(() => pollJob(jobId, modal), 1200);
      } else {
        renderResult(modal, job);
      }
    } catch (error) {
      renderResult(modal, {
        status: "failed",
        progress: 100,
        phase: "Could not read job",
        error: String(error && error.message ? error.message : error),
        report: { summary: String(error && error.message ? error.message : error), changedFiles: [] },
        logs: [],
      });
    }
  }

  function injectPanel() {
    patchClipboardCapture();
    injectStyles();

    const modal = findAskAgentModal();
    if (!modal || modal.querySelector(".ask-agents-panel")) return;

    const footer = Array.from(modal.children).find((node) => node.className && String(node.className).includes("border-t"));
    const panel = document.createElement("div");
    panel.className = "ask-agents-panel";
    panel.innerHTML = `
      <div class="ask-agents-row">
        <div class="ask-agents-title">Run prompt with</div>
        <div class="ask-agents-checks">
          <label class="ask-agents-check"><input type="checkbox" data-provider="codex" checked /> Codex App Server</label>
          <label class="ask-agents-check"><input type="checkbox" data-provider="claude" /> Claude Code</label>
          <button class="ask-agents-run" type="button">Run selected</button>
        </div>
      </div>
      <div class="ask-agents-note">入力後は実行モーダルに切り替わり、進捗、結果報告、変更ファイル、確認リロードを表示します。</div>
    `;
    panel.querySelector(".ask-agents-run").addEventListener("click", () => runAgents(modal, panel));

    if (footer) {
      modal.insertBefore(panel, footer);
    } else {
      modal.appendChild(panel);
    }
  }

  const observer = new MutationObserver(injectPanel);
  observer.observe(document.documentElement, { childList: true, subtree: true });
  injectPanel();
})();
