(() => {
  const C = window.CHAT_CONFIG;
  const box = document.getElementById("messages");
  const input = document.getElementById("textInput");
  const form = document.getElementById("composer");
  const stateEl = document.getElementById("connectionState");
  const wsProto = location.protocol === "https:" ? "wss" : "ws";

  let ws = null;
  let reconnectTimer = null;
  let typingTimer;
  let recorder = null;
  let chunks = [];
  let recordTimer = null;
  let recordStarted = 0;
  let cancelRecording = false;
  let lastMessageId = 0;

  const esc = s => {
    const d = document.createElement("div");
    d.textContent = s || "";
    return d.innerHTML;
  };
  const scroll = () => { box.scrollTop = box.scrollHeight; };
  const removeIds = ids => ids.forEach(id => document.querySelector(`[data-id="${id}"]`)?.remove());

  const render = m => {
    lastMessageId = Math.max(lastMessageId, Number(m.id) || 0);
    if (document.querySelector(`[data-id="${m.id}"]`)) return null;

    const row = document.createElement("div");
    row.className = "msg-row " + (m.sender_id === C.userId ? "mine" : "");
    row.dataset.id = m.id;

    let body = "";
    if (m.type === "text") {
      body = `<div class="msg-text">${esc(m.text).replace(/\n/g, "<br>")}</div>`;
    } else if (m.type === "image") {
      body = `<a href="${m.url}" target="_blank"><img class="msg-image" src="${m.url}" loading="lazy"></a>`;
    } else if (m.type === "video") {
      body = `<video class="msg-video" controls playsinline preload="metadata" src="${m.url}"></video>`;
    } else if (m.type === "voice" || m.type === "audio") {
      body = `<div class="voice"><span>🎤</span><audio controls preload="metadata" src="${m.url}"></audio></div>`;
    } else {
      body = `<a class="file-card" href="${m.url}" target="_blank" rel="noopener">📎 <span>${esc(m.name || "File")}</span></a>`;
    }

    const tick = m.seen ? "✓✓" : m.delivered ? "✓✓" : "✓";
    row.innerHTML = `<div class="bubble">${body}<div class="meta">${m.time}${
      m.sender_id === C.userId
        ? `<span class="ticks ${m.seen ? "seen" : ""}" data-status-id="${m.id}">${tick}</span>`
        : ""
    }</div></div>`;
    box.appendChild(row);
    scroll();
    return row;
  };

  const send = payload => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(payload));
      return true;
    }
    return false;
  };

  const markVisibleSeen = () => {
    const ids = [...box.querySelectorAll(".msg-row:not(.mine)")]
      .map(x => Number(x.dataset.id)).filter(Boolean);
    if (ids.length) send({action:"seen", ids});
  };

  const handleMessage = m => {
    const row = render(m);
    if (row && m.sender_id === C.otherId) {
      // Seen immediately after the receiver's DOM receives the message.
      send({action:"seen", ids:[m.id]});
    }
  };

  const connect = () => {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;
    stateEl.textContent = "Connecting…";
    const url = `${wsProto}://${location.host}/ws/chat/${C.otherId}/`;
    ws = new WebSocket(url);

    ws.onopen = () => {
      stateEl.textContent = "Live";
      stateEl.classList.add("live");
      markVisibleSeen();
      syncFallback();
    };

    ws.onmessage = e => {
      let d;
      try { d = JSON.parse(e.data); } catch { return; }
      if (d.event === "message") {
        handleMessage(d.message);
      } else if (d.event === "presence") {
        const dot = document.getElementById("statusDot");
        dot.classList.toggle("online", d.online);
        document.getElementById("presenceText").textContent = d.online ? "Online" : "Offline";
      } else if (d.event === "delivered") {
        d.ids.forEach(id => {
          const t = document.querySelector(`[data-status-id="${id}"]`);
          if (t && !t.classList.contains("seen")) t.textContent = "✓✓";
        });
      } else if (d.event === "typing") {
        document.getElementById("typing").classList.toggle("show", d.typing);
      } else if (d.event === "seen") {
        d.ids.forEach(id => {
          const t = document.querySelector(`[data-status-id="${id}"]`);
          if (t) {
            t.textContent = "✓✓";
            t.classList.add("seen");
          }
        });
      }
    };

    ws.onclose = () => {
      stateEl.textContent = "Reconnecting…";
      stateEl.classList.remove("live");
      document.getElementById("presenceText").textContent = "Offline";
      document.getElementById("statusDot").classList.remove("online");
      clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(connect, 1000);
    };
  };

  // HTTP fallback catches a temporary WebSocket/channel-layer interruption without refresh.
  const syncFallback = async () => {
    if (document.hidden) return;
    const fd = new FormData();
    fd.append("after_id", String(lastMessageId));
    try {
      const r = await fetch(C.stateUrl, {
        method:"POST",
        headers:{"X-CSRFToken":C.csrf, "X-Requested-With":"XMLHttpRequest"},
        body:fd,
        cache:"no-store"
      });
      if (!r.ok) return;
      const data = await r.json();
      (data.messages || []).forEach(handleMessage);
    } catch {}
  };

  connect();
  setInterval(syncFallback, 1200);

  input.addEventListener("input", () => {
    send({action:"typing", typing:true});
    clearTimeout(typingTimer);
    typingTimer = setTimeout(() => send({action:"typing", typing:false}), 900);
  });

  form.addEventListener("submit", e => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    if (!send({action:"text", text})) {
      stateEl.textContent = "Connecting…";
      return;
    }
    input.value = "";
    send({action:"typing", typing:false});
  });

  document.getElementById("attachBtn").onclick = () =>
    document.getElementById("fileMenu").classList.toggle("show");

  document.querySelectorAll("#fileMenu button").forEach(btn => {
    btn.onclick = () => {
      document.getElementById("fileMenu").classList.remove("show");
      document.getElementById("fileInput").click();
    };
  });

  const upload = async f => {
    if (!f) return;
    const fd = new FormData();
    fd.append("file", f, f.name || `file-${Date.now()}`);
    try {
      const r = await fetch(C.uploadUrl, {
        method:"POST",
        headers:{"X-CSRFToken":C.csrf, "X-Requested-With":"XMLHttpRequest"},
        body:fd,
        cache:"no-store"
      });
      if (!r.ok) throw new Error(await r.text());
      const m = await r.json();
      // WebSocket broadcasts it to both clients. This local render is a safety net
      // if the websocket event was lost during a reconnect.
      render(m);
    } catch (err) {
      console.error(err);
      alert("File could not be sent.");
    }
  };

  document.getElementById("fileInput").onchange = async e => {
    await upload(e.target.files[0]);
    e.target.value = "";
  };
  document.getElementById("cameraBtn").onclick = () => document.getElementById("cameraInput").click();
  document.getElementById("cameraInput").onchange = async e => {
    await upload(e.target.files[0]);
    e.target.value = "";
  };

  const timerEl = document.getElementById("recordTimer");
  const recordingBar = document.getElementById("recordingBar");
  const voiceBtn = document.getElementById("voiceBtn");

  const startTimer = () => {
    recordStarted = Date.now();
    timerEl.textContent = "0:00";
    recordTimer = setInterval(() => {
      const sec = Math.floor((Date.now() - recordStarted) / 1000);
      timerEl.textContent = `${Math.floor(sec/60)}:${String(sec%60).padStart(2,"0")}`;
    }, 200);
  };
  const stopTimer = () => { clearInterval(recordTimer); recordTimer = null; };

  const startRecording = async e => {
    e.preventDefault();
    if (recorder && recorder.state !== "inactive") return;
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      alert("Voice recording is not supported by this browser.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({audio:true});
      chunks = [];
      cancelRecording = false;
      const mime = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus"].find(x => MediaRecorder.isTypeSupported(x)) || "";
      recorder = mime ? new MediaRecorder(stream, {mimeType:mime}) : new MediaRecorder(stream);
      recorder.ondataavailable = x => { if (x.data.size) chunks.push(x.data); };
      recorder.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        stopTimer();
        recordingBar.classList.remove("show");
        voiceBtn.classList.remove("recording");
        if (cancelRecording || !chunks.length) { chunks = []; return; }
        const blob = new Blob(chunks, {type: recorder.mimeType || "audio/webm"});
        const ext = blob.type.includes("ogg") ? "ogg" : "webm";
        await upload(new File([blob], `voice-${Date.now()}.${ext}`, {type:blob.type}));
        chunks = [];
      };
      recorder.start(250);
      recordingBar.classList.add("show");
      voiceBtn.classList.add("recording");
      startTimer();
    } catch {
      alert("Microphone permission was denied.");
    }
  };
  const stopRecording = () => { if (recorder && recorder.state !== "inactive") recorder.stop(); };
  const cancelRecord = e => { e.preventDefault(); cancelRecording = true; stopRecording(); };

  voiceBtn.addEventListener("mousedown", startRecording);
  voiceBtn.addEventListener("touchstart", startRecording, {passive:false});
  voiceBtn.addEventListener("mouseup", stopRecording);
  voiceBtn.addEventListener("mouseleave", stopRecording);
  voiceBtn.addEventListener("touchend", stopRecording);
  voiceBtn.addEventListener("touchcancel", stopRecording);
  document.getElementById("cancelRecord").addEventListener("click", cancelRecord);

  setInterval(() => {
    fetch(C.pingUrl, {
      method:"POST",
      headers:{"X-CSRFToken":C.csrf, "X-Requested-With":"XMLHttpRequest"}
    }).catch(() => {});
  }, 30000);

  window.addEventListener("load", () => { scroll(); markVisibleSeen(); });
  document.addEventListener("visibilitychange", () => { if (!document.hidden) { markVisibleSeen(); syncFallback(); } });
})();
