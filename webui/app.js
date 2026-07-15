/* Music Downloader — PulseTube-style glass UI */

const THEMES = {
  aurora: {
    label: "Aurora Glow",
    swatches: ["#e96100", "#ffb84d", "#2455f5", "#6b2edb"],
  },
  neon: {
    label: "Neon Pulse",
    swatches: ["#ff2f92", "#00d4ff", "#7a4dff", "#14f7c4"],
  },
  sunset: {
    label: "Sunset Drift",
    swatches: ["#ff5d3b", "#ffb347", "#ff2e6d", "#8a2be2"],
  },
  midnight: {
    label: "Midnight Bloom",
    swatches: ["#4f46e5", "#7c3aed", "#06b6d4", "#ec4899"],
  },
  ocean: {
    label: "Ocean Wave",
    swatches: ["#0ea5e9", "#22d3ee", "#2563eb", "#14b8a6"],
  },
  ember: {
    label: "Ember Rush",
    swatches: ["#f97316", "#fb923c", "#ef4444", "#b91c1c"],
  },
  lavender: {
    label: "Lavender Dream",
    swatches: ["#8b5cf6", "#c084fc", "#ec4899", "#38bdf8"],
  },
  sunrise: {
    label: "Sunrise Glow",
    swatches: ["#ff7a00", "#ffd166", "#ff4d6d", "#7c4dff"],
  },
  violet: {
    label: "Violet Pulse",
    swatches: ["#7c3aed", "#a78bfa", "#ec4899", "#06b6d4"],
  },
  crimson: {
    label: "Crimson Noir",
    swatches: ["#0a0a0a", "#c1121f", "#780000", "#9ca3af"],
  },
  blood: {
    label: "Blood Black",
    swatches: ["#030303", "#8a0808", "#520202", "#5c5c5c"],
  },
  graphite: {
    label: "Graphite",
    swatches: ["#0c0c0e", "#a8a29e", "#57534e", "#d6d3d1"],
  },
  arctic: {
    label: "Arctic Ice",
    swatches: ["#020617", "#38bdf8", "#0284c7", "#94a3b8"],
  },
  jade: {
    label: "Jade Grove",
    swatches: ["#02140f", "#10b981", "#047857", "#6ee7b7"],
  },
  copper: {
    label: "Copper Forge",
    swatches: ["#0c0804", "#d97706", "#92400e", "#fcd34d"],
  },
  ink: {
    label: "Mono Ink",
    swatches: ["#09090b", "#e5e5e5", "#525252", "#a3a3a3"],
  },
  void: {
    label: "Void Carbon",
    swatches: ["#010101", "#6b6b6f", "#1c1c1f", "#3f3f46"],
  },
  ashblood: {
    label: "Ash Blood",
    swatches: ["#010101", "#6e1212", "#2a0606", "#4a4a4e"],
  },
};

let playlist = [];
let downloading = false;

const $ = (id) => document.getElementById(id);

function api() {
  return window.pywebview?.api;
}

function setStatus(msg, color) {
  const el = $("status");
  el.textContent = msg;
  el.style.color = color || "";
}

function setProgress(pct, label) {
  $("barFill").style.width = `${Math.max(0, Math.min(100, pct * 100))}%`;
  $("pct").textContent = label || (pct > 0 ? `${Math.round(pct * 100)}%` : "");
}

function selectedIndices() {
  return [...document.querySelectorAll(".item-check:checked")].map((el) =>
    Number(el.dataset.index)
  );
}

function refreshSelected() {
  const total = playlist.length;
  const sel = selectedIndices().length;
  $("selected").textContent = total ? `${sel} / ${total} seçili` : "";
  const all = $("selectAll");
  all.checked = total > 0 && sel === total;
}

function renderPlaylist(items) {
  playlist = items || [];
  const list = $("list");
  $("count").textContent = playlist.length ? `${playlist.length} şarkı` : "";

  if (!playlist.length) {
    list.innerHTML = `<div class="empty">URL yapıştırıp Getir’e bas</div>`;
    refreshSelected();
    return;
  }

  list.innerHTML = playlist
    .map(
      (it, i) => `
    <div class="item" data-row="${i}">
      <span class="num">${String(it.id).padStart(2, "0")}</span>
      <input class="item-check" type="checkbox" data-index="${i}" checked />
      <span class="title" title="${escapeAttr(it.title)}">${escapeHtml(it.title)}</span>
      <span class="ch">${escapeHtml(it.channel || "")}</span>
      <span class="dur">${escapeHtml(it.duration || "--:--")}</span>
      <span class="st" id="st-${i}"></span>
    </div>`
    )
    .join("");

  list.querySelectorAll(".item-check").forEach((cb) => {
    cb.addEventListener("change", refreshSelected);
  });
  refreshSelected();
}

function setRowStatus(idx, icon, color) {
  const el = $(`st-${idx}`);
  if (!el) return;
  el.textContent = icon;
  el.style.color = color || "";
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function escapeAttr(s) {
  return escapeHtml(s).replace(/'/g, "&#39;");
}

function showPanel(name) {
  $("panel-download").classList.toggle("hidden", name !== "download");
  $("panel-history").classList.toggle("hidden", name !== "history");
  $("panel-theme").classList.toggle("hidden", name !== "theme");
  const guide = $("panel-guide");
  if (guide) guide.classList.toggle("hidden", name !== "guide");
  document.querySelectorAll(".menu-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.panel === name);
  });
  if (name === "history") loadHistory();
}

function renderThemes(activeKey) {
  const grid = $("themeGrid");
  grid.innerHTML = Object.entries(THEMES)
    .map(([key, t]) => {
      const active = key === activeKey ? "active" : "";
      const sw = t.swatches
        .map((c) => `<span style="background:${c}"></span>`)
        .join("");
      return `<button type="button" class="theme-card ${active}" data-theme="${key}">
        <strong>${t.label}</strong>
        <div class="swatches">${sw}</div>
      </button>`;
    })
    .join("");

  grid.querySelectorAll(".theme-card").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const key = btn.dataset.theme;
      applyTheme(key);
      renderThemes(key);
      try {
        await api()?.set_theme(key);
      } catch (_) {}
    });
  });
}

function applyTheme(key) {
  if (!key || !THEMES[key]) return;
  document.body.dataset.theme = key;
  try {
    localStorage.setItem("md_theme", key);
  } catch (_) {}
}

function enhanceSelect(select) {
  if (!select || select.dataset.enhanced === "1") return;
  select.dataset.enhanced = "1";

  const wrap = document.createElement("div");
  wrap.className = "fancy-select";
  select.classList.add("fancy-select-native");
  select.parentNode.insertBefore(wrap, select);
  wrap.appendChild(select);

  const trigger = document.createElement("button");
  trigger.type = "button";
  trigger.className = "fancy-select-trigger";
  trigger.setAttribute("aria-haspopup", "listbox");
  trigger.setAttribute("aria-expanded", "false");

  const menu = document.createElement("div");
  menu.className = "fancy-select-menu";
  menu.setAttribute("role", "listbox");

  const syncLabel = () => {
    const opt = select.options[select.selectedIndex];
    trigger.textContent = opt ? opt.text : select.value;
  };

  const renderMenu = () => {
    menu.innerHTML = "";
    Array.from(select.options).forEach((opt) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "fancy-select-option" + (opt.selected ? " active" : "");
      btn.textContent = opt.text;
      btn.dataset.value = opt.value;
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        select.value = opt.value;
        select.dispatchEvent(new Event("change", { bubbles: true }));
        syncLabel();
        wrap.classList.remove("open");
        trigger.setAttribute("aria-expanded", "false");
        wrap.closest(".controls")?.classList.remove("dropdown-open");
        renderMenu();
      });
      menu.appendChild(btn);
    });
  };

  trigger.addEventListener("click", (e) => {
    e.stopPropagation();
    document.querySelectorAll(".fancy-select.open").forEach((el) => {
      if (el !== wrap) {
        el.classList.remove("open");
        el.querySelector(".fancy-select-trigger")?.setAttribute("aria-expanded", "false");
        el.closest(".controls")?.classList.remove("dropdown-open");
      }
    });
    const open = wrap.classList.toggle("open");
    trigger.setAttribute("aria-expanded", open ? "true" : "false");
    wrap.closest(".controls")?.classList.toggle("dropdown-open", open);
    if (open) renderMenu();
  });

  select.addEventListener("change", () => {
    syncLabel();
    renderMenu();
  });

  wrap.appendChild(trigger);
  wrap.appendChild(menu);
  syncLabel();
  renderMenu();
}

function enhanceAllSelects() {
  ["format", "quality"].forEach((id) => enhanceSelect($(id)));
}

document.addEventListener("click", () => {
  document.querySelectorAll(".fancy-select.open").forEach((el) => {
    el.classList.remove("open");
    el.querySelector(".fancy-select-trigger")?.setAttribute("aria-expanded", "false");
    el.closest(".controls")?.classList.remove("dropdown-open");
  });
});

async function loadHistory() {
  const box = $("historyList");
  try {
    const rows = (await api()?.get_history()) || [];
    if (!rows.length) {
      box.innerHTML = `<div class="empty">Henüz kayıt yok</div>`;
      return;
    }
    const icon = { success: "✓", cancelled: "◼", partial: "⚡" };
    box.innerHTML = rows
      .slice(0, 25)
      .map((r) => {
        const ic = icon[r.status] || "⚡";
        return `<div class="history-item">
          <span>${ic}</span>
          <span>${r.count}/${r.total} • ${escapeHtml(r.fmt || "")} → ${escapeHtml(r.path || "")}</span>
          <span style="color:var(--muted)">${escapeHtml(r.date || "")}</span>
        </div>`;
      })
      .join("");
  } catch (_) {
    box.innerHTML = `<div class="empty">Geçmiş okunamadı.</div>`;
  }
}

async function boot() {
  document.querySelectorAll(".menu-btn").forEach((btn) => {
    btn.addEventListener("click", () => showPanel(btn.dataset.panel));
  });

  enhanceAllSelects();

  $("fetchBtn").addEventListener("click", onFetch);
  $("url").addEventListener("keydown", (e) => {
    if (e.key === "Enter") onFetch();
  });
  $("folderBtn").addEventListener("click", onPickFolder);
  $("selectAll").addEventListener("change", (e) => {
    document.querySelectorAll(".item-check").forEach((cb) => {
      cb.checked = e.target.checked;
    });
    refreshSelected();
  });
  $("clearBtn").addEventListener("click", () => {
    $("url").value = "";
    renderPlaylist([]);
    setProgress(0, "");
    setStatus("Temizlendi.");
  });
  $("downloadBtn").addEventListener("click", onDownload);
  $("cancelBtn").addEventListener("click", async () => {
    try {
      await api()?.cancel_download();
      setStatus("Durduruluyor…", "var(--warning)");
    } catch (_) {}
  });
  $("resumeBtn").addEventListener("click", onResume);

  $("clearHistoryBtn").addEventListener("click", async () => {
    await api()?.clear_history();
    loadHistory();
  });

  $("clipYes").addEventListener("click", () => {
    const url = $("clipPreview").textContent.trim();
    hideClipboardPrompt();
    if (!url) return;
    $("url").value = url;
    setStatus("Panodaki link eklendi.", "var(--success)");
    showPanel("download");
  });

  $("clipNo").addEventListener("click", () => {
    hideClipboardPrompt();
    setStatus("Pano linki eklenmedi.");
  });

  $("clipModal").addEventListener("click", (e) => {
    if (e.target === $("clipModal")) {
      hideClipboardPrompt();
      setStatus("Pano linki eklenmedi.");
    }
  });

  $("folderYes").addEventListener("click", async () => {
    const path = $("folderPreview").textContent.trim();
    hideFolderPrompt();
    if (path) {
      try {
        await api()?.open_folder(path);
        setStatus(`Klasör açıldı: ${path}`, "var(--success)");
      } catch (_) {
        setStatus("Klasör açılamadı.", "var(--error)");
      }
    }
  });

  $("folderNo").addEventListener("click", () => {
    hideFolderPrompt();
    setStatus("Klasör açılmadı. İndirme tamamlandı.", "var(--success)");
  });

  $("folderModal").addEventListener("click", (e) => {
    if (e.target === $("folderModal")) {
      hideFolderPrompt();
      setStatus("Klasör açılmadı. İndirme tamamlandı.", "var(--success)");
    }
  });

  // API hazır olmasa bile izlemeyi erken başlat (hazır olunca çalışır)
  startClipboardWatch();

  // Önce cache'den temayı göster (flash önleme), sonra Python ayarını yükle
  try {
    const cached = localStorage.getItem("md_theme");
    if (cached && THEMES[cached]) {
      applyTheme(cached);
      renderThemes(cached);
    } else {
      renderThemes(document.body.dataset.theme || "aurora");
    }
  } catch (_) {
    renderThemes("aurora");
  }

  window.addEventListener("pywebviewready", initFromPython);
  setTimeout(initFromPython, 200);
}

let booted = false;
let bootTries = 0;
async function initFromPython() {
  if (booted) return;
  const bridge = api();
  if (!bridge) {
    if (bootTries++ < 40) setTimeout(initFromPython, 100);
    return;
  }
  try {
    const state = await bridge.get_state();
    if (!state) {
      if (bootTries++ < 40) setTimeout(initFromPython, 100);
      return;
    }
    booted = true;
    const theme = state.theme && THEMES[state.theme] ? state.theme : "aurora";
    applyTheme(theme);
    renderThemes(theme);
    if (state.folder) $("folder").value = state.folder;
    if (state.format) {
      $("format").value = state.format;
      $("format").dispatchEvent(new Event("change", { bubbles: true }));
    }
    if (state.quality) {
      $("quality").value = state.quality;
      $("quality").dispatchEvent(new Event("change", { bubbles: true }));
    }
    if (state.ffmpeg_ok === false) $("ffmpegBanner").classList.add("show");
    startClipboardWatch();
  } catch (_) {
    if (bootTries++ < 40) setTimeout(initFromPython, 100);
  }
}

let lastClipboardSeen = "";
let clipboardPromptOpen = false;
let clipboardTimer = null;

function isYoutubeUrl(text) {
  return /(?:youtube\.com|youtu\.be|music\.youtube\.com)/i.test(text || "");
}

function extractYoutubeUrl(text) {
  const raw = (text || "").trim();
  if (!raw) return "";
  const first = raw.split(/\s+/)[0];
  if (/^https?:\/\//i.test(first) && isYoutubeUrl(first)) {
    return first.replace(/[)\],.]+$/g, "");
  }
  const m = raw.match(
    /https?:\/\/(?:www\.)?(?:music\.)?(?:youtube\.com\/[^\s<>"']+|youtu\.be\/[^\s<>"']+)/i
  );
  return m ? m[0].replace(/[)\],.]+$/g, "") : "";
}

function showClipboardPrompt(url) {
  clipboardPromptOpen = true;
  $("clipPreview").textContent = url;
  $("clipModal").classList.remove("hidden");
}

function hideClipboardPrompt() {
  clipboardPromptOpen = false;
  $("clipModal").classList.add("hidden");
}

async function checkClipboardOffer() {
  if (clipboardPromptOpen || downloading) return;
  const bridge = api();
  if (!bridge || typeof bridge.get_clipboard !== "function") return;
  try {
    const text = (await bridge.get_clipboard()) || "";
    const url = extractYoutubeUrl(text);
    if (!url || url === lastClipboardSeen) return;
    if ($("url").value.trim() === url) {
      lastClipboardSeen = url;
      return;
    }
    lastClipboardSeen = url;
    showClipboardPrompt(url);
  } catch (_) {}
}

function startClipboardWatch() {
  if (clipboardTimer) return;
  checkClipboardOffer();
  clipboardTimer = setInterval(() => {
    checkClipboardOffer();
    pollUiEvents();
  }, 500);
  window.addEventListener("focus", checkClipboardOffer);
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible") checkClipboardOffer();
  });
}

async function onFetch() {
  const url = $("url").value.trim();
  if (!url) {
    setStatus("Lütfen geçerli bir URL girin.", "var(--warning)");
    return;
  }
  $("fetchBtn").disabled = true;
  $("fetchBtn").textContent = "Yükleniyor…";
  setStatus("Playlist bilgileri alınıyor…");
  setProgress(0, "");
  try {
    const res = await api()?.fetch_playlist(url);
    if (!res || res.ok === false) {
      setStatus(`Hata: ${res?.error || "Bilinmeyen hata"}`, "var(--error)");
      renderPlaylist([]);
    } else {
      renderPlaylist(res.items || []);
      setStatus(`✓  ${(res.items || []).length} video bulundu.`, "var(--success)");
    }
  } catch (e) {
    setStatus(`Hata: ${e}`, "var(--error)");
  } finally {
    $("fetchBtn").disabled = false;
    $("fetchBtn").textContent = "Getir";
  }
}

async function onPickFolder() {
  try {
    const path = await api()?.pick_folder($("folder").value);
    if (path) $("folder").value = path;
  } catch (_) {}
}

async function onDownload() {
  if (downloading) return;
  const idxs = selectedIndices();
  if (!idxs.length) {
    setStatus("En az bir video seçin!", "var(--warning)");
    return;
  }
  setResumeEnabled(false);
  downloading = true;
  $("downloadBtn").disabled = true;
  $("downloadBtn").textContent = "İndiriliyor…";
  $("cancelBtn").disabled = false;
  $("fetchBtn").disabled = true;
  setProgress(0, "0%");

  idxs.forEach((i) => setRowStatus(i, "", ""));

  try {
    await api()?.start_download({
      indices: idxs,
      items: idxs.map((i) => playlist[i]),
      folder: $("folder").value,
      format: $("format").value,
      quality: $("quality").value,
    });
  } catch (e) {
    setStatus(`Hata: ${e}`, "var(--error)");
    finishDownloadUi();
  }
}

async function onResume() {
  if (downloading) return;
  setResumeEnabled(false);
  downloading = true;
  $("downloadBtn").disabled = true;
  $("downloadBtn").textContent = "İndiriliyor…";
  $("cancelBtn").disabled = false;
  $("fetchBtn").disabled = true;
  setStatus("Kaldığı yerden devam ediliyor…", "var(--warning)");
  try {
    const ok = await api()?.resume_download();
    if (!ok) {
      setStatus("Devam edilecek indirme bulunamadı.", "var(--warning)");
      finishDownloadUi();
    }
  } catch (e) {
    setStatus(`Hata: ${e}`, "var(--error)");
    finishDownloadUi();
  }
}

function setResumeEnabled(on) {
  const btn = $("resumeBtn");
  if (btn) btn.disabled = !on;
}

function showFolderPrompt(path) {
  const modal = $("folderModal");
  const preview = $("folderPreview");
  if (!modal || !preview) return;
  preview.textContent = path || "";
  modal.classList.remove("hidden");
  modal.style.display = "grid";
  modal.style.zIndex = "99999";
}

function hideFolderPrompt() {
  const modal = $("folderModal");
  if (!modal) return;
  modal.classList.add("hidden");
  modal.style.display = "";
}

function finishDownloadUi(canResume = false) {
  downloading = false;
  const dl = $("downloadBtn");
  const cancel = $("cancelBtn");
  const fetch = $("fetchBtn");
  if (dl) {
    dl.disabled = false;
    dl.textContent = "İndir";
  }
  if (cancel) cancel.disabled = true;
  if (fetch) fetch.disabled = false;
  setResumeEnabled(!!canResume);
}

let lastHandledDownloadToken = "";

function handleDownloadDone(payload) {
  if (!payload) return;
  // Çift tetiklemeyi engelle (evaluate_js + poll)
  const token = [
    payload.status,
    payload.done,
    payload.total,
    payload.path,
    payload.can_resume,
    payload.ask_folder,
  ].join("|");
  if (token === lastHandledDownloadToken && !downloading) return;
  lastHandledDownloadToken = token;

  const { done, total, status, path, can_resume, ask_folder } = payload;
  try {
    finishDownloadUi(!!can_resume);
  } catch (_) {}

  if (status === "cancelled") {
    setStatus(
      can_resume
        ? `Durduruldu — ${done}/${total} tamam. Devam Et ile sürdürebilirsin.`
        : `Durduruldu — ${done}/${total} tamam.`,
      "var(--warning)"
    );
    return; // iptalde klasör sorulmaz
  }

  if (status === "partial") {
    setStatus(`⚠ ${done}/${total} başarıyla indirildi.`, "var(--warning)");
  } else {
    setStatus(`✓ ${done}/${total} video indirildi.`, "var(--success)");
    setProgress(1, "100%");
  }

  // Uygulama içi klasör onay modalı
  if (ask_folder) {
    showFolderPrompt(path || ($("folder") && $("folder").value) || "");
  }
}

// Python → JS callbacks
window.md = {
  onItemStart(idx, title) {
    setRowStatus(idx, "⟳", "var(--warning)");
    setStatus(`İndiriliyor: ${title}`);
  },
  onItemProgress(overall, speed) {
    const spd = speed ? `  ${speed}` : "";
    setProgress(overall, `${Math.round(overall * 100)}%${spd}`);
  },
  onItemDone(idx, ok, err) {
    setRowStatus(idx, ok ? "✓" : "✗", ok ? "var(--success)" : "var(--error)");
    if (!ok && err) setRowStatus(idx, "✗", "var(--error)");
  },
  onDownloadDone(payload) {
    handleDownloadDone(payload);
  },
  askOpenFolder(path) {
    showFolderPrompt(path || "");
  },
};

async function pollUiEvents() {
  try {
    const bridge = api();
    if (!bridge || typeof bridge.poll_ui_event !== "function") return;
    const ev = await bridge.poll_ui_event();
    if (ev && ev.type === "download_done") handleDownloadDone(ev);
  } catch (_) {}
}

boot();
