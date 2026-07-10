// coding_agent/presentation/static/app.js
// WebSocket client + REST API for Coding Agent Harness WebUI
// Design system: Open Design → linear-app (Linear-inspired)

// ---- State ----
let ws = null;
let currentSessionId = null;
let pendingApproval = null;
let sessions = [];

// ---- DOM Refs ----
const statusIndicator = document.getElementById("status-indicator");
const goalInput = document.getElementById("goal-input");
const runBtn = document.getElementById("run-btn");
const cancelBtn = document.getElementById("cancel-btn");
const terminal = document.getElementById("terminal");
const approvalBar = document.getElementById("approval-bar");
const approvalDetail = document.getElementById("approval-detail");
const sessionsPanel = document.getElementById("sessions-panel");
const settingsPanel = document.getElementById("settings-panel");
const detailOverlay = document.getElementById("detail-overlay");
const detailTitle = document.getElementById("detail-title");
const detailMeta = document.getElementById("detail-meta");
const detailContent = document.getElementById("detail-content");
const credentialStatus = document.getElementById("credential-status");
const apiKeyInput = document.getElementById("api-key-input");
const toastContainer = document.getElementById("toast-container");

// ---- Init ----
document.addEventListener("DOMContentLoaded", function () {
  setConnectionStatus("offline", "Disconnected");
  loadCredentialStatus();
  loadSessions();
  goalInput.disabled = false;
  runBtn.disabled = false;

  // Sidebar tabs
  document.querySelectorAll(".sidebar-tab").forEach(function (tab) {
    tab.addEventListener("click", function () {
      document.querySelectorAll(".sidebar-tab").forEach(function (t) { t.classList.remove("active"); });
      tab.classList.add("active");
      var panel = tab.dataset.panel;
      sessionsPanel.classList.toggle("hidden", panel !== "sessions");
      settingsPanel.classList.toggle("hidden", panel !== "settings");
    });
  });

  // Enter to submit (Shift+Enter for newline)
  goalInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submitTask();
    }
  });

  // Esc to close detail
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeDetail();
  });

  // Click overlay to close
  detailOverlay.addEventListener("click", function (e) {
    if (e.target === detailOverlay) closeDetail();
  });
});

// ---- WebSocket ----
function connectWebSocket(sessionId) {
  if (ws && ws.readyState === WebSocket.OPEN) ws.close();
  var protocol = location.protocol === "https:" ? "wss:" : "ws:";
  var url = protocol + "//" + location.host + "/ws/" + sessionId;
  ws = new WebSocket(url);

  ws.onopen = function () {
    setConnectionStatus("online", "Connected");
  };

  ws.onmessage = function (event) {
    try {
      handleWebSocketMessage(JSON.parse(event.data));
    } catch (e) {
      console.error("WS parse error:", e);
    }
  };

  ws.onclose = function () {
    setConnectionStatus("offline", "Disconnected");
    ws = null;
  };

  ws.onerror = function (err) { console.error("WS error:", err); };
}

function handleWebSocketMessage(data) {
  switch (data.type) {
    case "connected": break;
    case "step": addStep(data); break;
    case "approval_required": showApproval(data); break;
    case "session_complete": handleComplete(data); break;
    case "session_error": handleError(data); break;
    case "echo": break;
    default: console.log("Unknown WS message:", data.type);
  }
}

function setConnectionStatus(className, text) {
  statusIndicator.className = "status-" + className;
  statusIndicator.textContent = text;
}

// ---- Task Submission ----
function submitTask() {
  var goal = goalInput.value.trim();
  if (!goal) { toast("Please enter a task description.", "error"); return; }
  if (runBtn.disabled) return;

  runBtn.disabled = true;
  cancelBtn.disabled = false;
  goalInput.disabled = true;
  clearTerminal();

  fetch("/api/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ goal: goal }),
  })
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.error) {
        toast("Error: " + data.error, "error");
        resetInputs();
        return;
      }
      currentSessionId = data.session_id || data.id;
      connectWebSocket(currentSessionId);
      setConnectionStatus("running", "Running");
      addStep({ step: 0, action: "Task submitted", output: "Session: " + currentSessionId, success: true });
      loadSessions();
    })
    .catch(function (err) {
      toast("Network error: " + err.message, "error");
      resetInputs();
    });
}

function cancelTask() {
  if (!currentSessionId) return;
  fetch("/api/sessions/" + currentSessionId + "/cancel", { method: "POST" })
    .catch(function () {})
    .finally(function () {
      cancelBtn.disabled = true;
      setConnectionStatus("offline", "Disconnected");
      if (ws) ws.close();
      resetInputs();
      loadSessions();
    });
}

function resetInputs() {
  runBtn.disabled = false;
  cancelBtn.disabled = true;
  goalInput.disabled = false;
  goalInput.focus();
}

// ---- Terminal / Step Log ----
function clearTerminal() {
  terminal.innerHTML = "";
}

function addStep(data) {
  var empty = terminal.querySelector(".empty-state");
  if (empty) empty.remove();

  var stepNum = data.step !== undefined ? data.step : "?";
  var success = data.success !== false;
  var cls = data.type === "warning" ? "step-warning"
    : success ? "step-success" : "step-error";

  var entry = document.createElement("div");
  entry.className = "step-entry " + cls;

  var time = new Date().toLocaleTimeString();

  var html =
    '<div class="step-gutter">' + esc(String(stepNum)) + "</div>" +
    '<div class="step-body">' +
    '<div class="step-action">' + esc(data.action || data.type || "") + "</div>";

  if (data.output) {
    html += '<div class="step-output">' + esc(String(data.output)) + "</div>";
  }
  html += "</div>";

  entry.innerHTML = html;
  terminal.appendChild(entry);
  terminal.scrollTop = terminal.scrollHeight;
}

// ---- Approval ----
function showApproval(data) {
  pendingApproval = data;
  approvalBar.classList.add("visible");
  approvalDetail.textContent = typeof data === "string" ? data : JSON.stringify(data);
}

function approve() { sendApproval(true); }
function deny() { sendApproval(false); }

function sendApproval(approved) {
  if (!currentSessionId) return;
  fetch("/api/sessions/" + currentSessionId + "/approve", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approved: approved }),
  }).catch(function () {});
  approvalBar.classList.remove("visible");
  pendingApproval = null;
}

// ---- Session Complete / Error ----
function handleComplete(data) {
  setConnectionStatus("online", "Connected");
  resetInputs();
  addStep({ step: data.total_steps || "?", action: "Task completed", output: "", success: true });
  currentSessionId = null;
  if (ws) ws.close();
  loadSessions();
  toast("Task completed successfully.", "success");
}

function handleError(data) {
  setConnectionStatus("online", "Connected");
  resetInputs();
  addStep({ step: "!", action: "Task failed", output: data.error || "Unknown error", success: false });
  currentSessionId = null;
  if (ws) ws.close();
  loadSessions();
  toast("Task failed: " + (data.error || "Unknown error"), "error");
}

// ---- Sessions ----
function loadSessions() {
  fetch("/api/sessions")
    .then(function (r) { return r.json(); })
    .then(function (data) {
      sessions = Array.isArray(data) ? data : [];
      renderSessions();
    })
    .catch(function (err) {
      sessionsPanel.innerHTML =
        '<div class="empty-state" style="text-align:center;padding:var(--space-6);color:var(--meta);font-size:var(--text-sm);">Failed to load sessions.</div>';
    });
}

function renderSessions() {
  if (sessions.length === 0) {
    sessionsPanel.innerHTML =
      '<div class="empty-state" style="text-align:center;padding:var(--space-6);color:var(--meta);font-size:var(--text-sm);">No sessions yet.</div>';
    return;
  }

  var html = "";
  sessions.forEach(function (s) {
    var status = s.status || "UNKNOWN";
    var goal = s.goal || "N/A";
    var id = s.id || "";
    var shortId = id.substring(0, 8);
    var active = id === currentSessionId ? " active" : "";
    html +=
      '<div class="session-item' + active + '" onclick="viewSession(\'' + esc(id) + "')\">" +
      '<div class="session-info">' +
      '<div class="session-goal">' + esc(goal) + "</div>" +
      '<div class="session-meta">' + esc(shortId) + "</div>" +
      "</div>" +
      '<span class="pill ' + esc(status) + '">' + esc(status) + "</span>" +
      "</div>";
  });
  sessionsPanel.innerHTML = html;
}

function viewSession(sessionId) {
  fetch("/api/sessions/" + sessionId)
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (data.error) {
        detailContent.innerHTML =
          '<div class="empty-state" style="text-align:center;padding:var(--space-6);color:var(--meta);">Session not found.</div>';
        return;
      }

      detailTitle.textContent = data.goal || "N/A";
      detailMeta.innerHTML =
        "<span>ID: " + esc((data.id || "").substring(0, 8)) + "</span>" +
        "<span>Status: " + esc(data.status || "UNKNOWN") + "</span>" +
        "<span>Steps: " + (data.steps || []).length + "</span>";

      var steps = data.steps || [];
      var body = "";
      if (steps.length === 0) {
        body = '<div class="empty-state" style="text-align:center;padding:var(--space-6);color:var(--meta);">No steps recorded.</div>';
      } else {
        steps.forEach(function (step, i) {
          var cls = step.success !== false ? "step-success" : "step-error";
          body +=
            '<div class="step-entry ' + cls + '">' +
            '<div class="step-gutter">' + (i + 1) + "</div>" +
            '<div class="step-body">' +
            '<div class="step-action">' + esc(step.action || step.type || "") + "</div>" +
            (step.output ? '<div class="step-output">' + esc(String(step.output)) + "</div>" : "") +
            (step.result ? '<div class="step-detail">' + esc(JSON.stringify(step.result, null, 2)) + "</div>" : "") +
            (step.feedback ? '<div class="step-detail">Feedback: ' + esc(String(step.feedback)) + "</div>" : "") +
            "</div></div>";
        });
      }
      detailContent.innerHTML = body;
      detailOverlay.classList.add("visible");
    })
    .catch(function (err) {
      detailContent.innerHTML =
        '<div class="empty-state" style="text-align:center;padding:var(--space-6);color:var(--meta);">Error: ' + esc(err.message) + "</div>";
    });
}

function closeDetail() {
  detailOverlay.classList.remove("visible");
}

// ---- Credentials ----
function setCredentials() {
  var key = apiKeyInput.value.trim();
  if (!key) { showCredentialStatus("Please enter an API key.", false); return; }
  fetch("/api/credentials", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ api_key: key }),
  })
    .then(function () {
      apiKeyInput.value = "";
      showCredentialStatus("API key configured.", true);
      toast("API key saved.", "success");
    })
    .catch(function (err) {
      showCredentialStatus("Failed to set API key: " + err.message, false);
    });
}

function clearCredentials() {
  fetch("/api/credentials", { method: "DELETE" })
    .then(function () {
      apiKeyInput.value = "";
      showCredentialStatus("API key cleared.", false);
      toast("API key cleared.", "success");
    })
    .catch(function (err) {
      showCredentialStatus("Failed to clear API key: " + err.message, false);
    });
}

function loadCredentialStatus() {
  fetch("/api/credentials/status")
    .then(function (r) { return r.json(); })
    .then(function (data) {
      var configured = data.configured || data.has_key || false;
      showCredentialStatus(configured ? "API key configured" : "No API key configured", configured);
    })
    .catch(function () {
      showCredentialStatus("Failed to check credentials", false);
    });
}

function showCredentialStatus(text, configured) {
  credentialStatus.textContent = text;
  credentialStatus.className = "credential-status " + (configured ? "configured" : "not-configured");
}

// ---- Toast ----
function toast(message, type) {
  var el = document.createElement("div");
  el.className = "toast " + (type || "");
  el.textContent = message;
  toastContainer.appendChild(el);
  setTimeout(function () {
    el.style.opacity = "0";
    el.style.transition = "opacity 200ms ease";
    setTimeout(function () { el.remove(); }, 200);
  }, 3000);
}

// ---- Utilities ----
function esc(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}