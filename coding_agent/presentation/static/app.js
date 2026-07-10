// coding_agent/presentation/static/app.js
// WebSocket client + REST API calls for Coding Agent Harness WebUI

// ---- State ----

let ws = null;
let currentSessionId = null;
let reconnectTimer = null;
let pendingApproval = null;
let sessions = [];

// ---- DOM References ----

const statusIndicator = document.getElementById("status-indicator");
const goalInput = document.getElementById("goal-input");
const runBtn = document.getElementById("run-btn");
const cancelBtn = document.getElementById("cancel-btn");
const taskStatus = document.getElementById("task-status");
const monitorHeader = document.getElementById("monitor-header");
const monitorGoal = document.getElementById("monitor-goal");
const monitorStepCount = document.getElementById("monitor-step-count");
const stepLog = document.getElementById("step-log");
const approvalPanel = document.getElementById("approval-panel");
const approvalContent = document.getElementById("approval-content");
const sessionsList = document.getElementById("sessions-list");
const detailPanel = document.getElementById("detail-panel");
const detailContent = document.getElementById("detail-content");
const credentialStatus = document.getElementById("credential-status");
const apiKeyInput = document.getElementById("api-key-input");

// ---- WebSocket ----

function connectWebSocket(sessionId) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.close();
  }

  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${protocol}//${location.host}/ws/${sessionId}`;
  ws = new WebSocket(url);

  ws.onopen = function () {
    setConnectionStatus("online", "Connected");
    console.log("WebSocket connected:", sessionId);
  };

  ws.onmessage = function (event) {
    try {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    } catch (e) {
      console.error("Failed to parse WS message:", e);
    }
  };

  ws.onclose = function () {
    setConnectionStatus("offline", "Disconnected");
    ws = null;
  };

  ws.onerror = function (err) {
    console.error("WebSocket error:", err);
  };
}

function handleWebSocketMessage(data) {
  switch (data.type) {
    case "connected":
      console.log("WS connected confirmation");
      break;

    case "step":
      addStepToLog(data);
      updateMonitorHeader(data);
      break;

    case "approval_required":
      showApprovalPanel(data);
      break;

    case "session_complete":
      handleSessionComplete(data);
      break;

    case "session_error":
      handleSessionError(data);
      break;

    case "echo":
      // Ignore echo messages from the basic endpoint
      break;

    default:
      console.log("Unknown WS message type:", data.type, data);
  }
}

function setConnectionStatus(className, text) {
  statusIndicator.className = "status-" + className;
  statusIndicator.textContent = text;
}

// ---- Task Submission ----

async function submitTask() {
  const goal = goalInput.value.trim();
  if (!goal) {
    showTaskStatus("Please enter a task description.", "error");
    return;
  }

  runBtn.disabled = true;
  cancelBtn.disabled = false;
  showTaskStatus("Submitting task...", "hidden");
  clearStepLog();

  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ goal }),
    });

    const data = await response.json();

    if (data.error) {
      showTaskStatus("Error: " + data.error, "error");
      runBtn.disabled = false;
      cancelBtn.disabled = true;
      return;
    }

    currentSessionId = data.session_id || data.id;
    connectWebSocket(currentSessionId);
    setConnectionStatus("running", "Running");

    monitorHeader.classList.remove("hidden");
    monitorGoal.textContent = goal;
    monitorStepCount.textContent = "Step 0";

    addStepToLog({
      step: 0,
      action: "Task submitted",
      output: "Session: " + currentSessionId,
      success: true,
    });

    showTaskStatus("Task running: " + currentSessionId, "success");
    loadSessions();
  } catch (err) {
    showTaskStatus("Network error: " + err.message, "error");
    runBtn.disabled = false;
    cancelBtn.disabled = true;
  }
}

async function cancelTask() {
  if (!currentSessionId) return;

  try {
    await fetch("/api/sessions/" + currentSessionId + "/cancel", { method: "POST" });
    cancelBtn.disabled = true;
    showTaskStatus("Cancelling...", "hidden");
    setConnectionStatus("offline", "Disconnected");
    if (ws) ws.close();
    loadSessions();
  } catch (err) {
    console.error("Cancel error:", err);
  }
}

// ---- Step Log ----

function clearStepLog() {
  stepLog.innerHTML = "";
}

function addStepToLog(data) {
  // Remove empty state if present
  const empty = stepLog.querySelector(".empty-state");
  if (empty) empty.remove();

  const card = document.createElement("div");
  const stepNum = data.step !== undefined ? data.step : "?";
  const success = data.success !== false;
  const statusClass = data.type === "warning"
    ? "step-warning"
    : success
      ? "step-success"
      : "step-error";

  card.className = "step-card " + statusClass;

  const time = new Date().toLocaleTimeString();

  card.innerHTML =
    '<div class="step-header">' +
    '<span class="step-number">Step ' + escapeHtml(String(stepNum)) + "</span>" +
    '<span class="step-time">' + escapeHtml(time) + "</span>" +
    "</div>" +
    '<div class="step-action">' + escapeHtml(data.action || data.type || "") + "</div>" +
    (data.output
      ? '<div class="step-body">' + escapeHtml(String(data.output)) + "</div>"
      : "");

  stepLog.appendChild(card);
  stepLog.scrollTop = stepLog.scrollHeight;
}

function updateMonitorHeader(data) {
  if (data.step !== undefined) {
    monitorStepCount.textContent = "Step " + data.step;
  }
}

// ---- Approval ----

function showApprovalPanel(data) {
  pendingApproval = data;
  approvalPanel.style.display = "block";
  approvalContent.textContent = JSON.stringify(data, null, 2);
}

function approve() {
  if (!pendingApproval) return;
  sendApprovalResponse(true);
}

function deny() {
  if (!pendingApproval) return;
  sendApprovalResponse(false);
}

async function sendApprovalResponse(approved) {
  if (!currentSessionId) return;

  try {
    await fetch("/api/sessions/" + currentSessionId + "/approve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approved }),
    });
    approvalPanel.style.display = "none";
    pendingApproval = null;
  } catch (err) {
    console.error("Approval error:", err);
  }
}

// ---- Session Complete / Error ----

function handleSessionComplete(data) {
  setConnectionStatus("online", "Connected");
  runBtn.disabled = false;
  cancelBtn.disabled = true;
  monitorStepCount.textContent = "Step " + (data.total_steps || "?") + " (complete)";
  showTaskStatus("Task completed successfully.", "success");
  currentSessionId = null;
  if (ws) ws.close();
  loadSessions();
}

function handleSessionError(data) {
  setConnectionStatus("online", "Connected");
  runBtn.disabled = false;
  cancelBtn.disabled = true;
  showTaskStatus("Task failed: " + (data.error || "Unknown error"), "error");
  currentSessionId = null;
  if (ws) ws.close();
  loadSessions();
}

// ---- Sessions ----

async function loadSessions() {
  try {
    const response = await fetch("/api/sessions");
    const data = await response.json();
    sessions = Array.isArray(data) ? data : [];

    if (sessions.length === 0) {
      sessionsList.innerHTML =
        '<div class="empty-state">No sessions yet. Submit a task to get started.</div>';
      return;
    }

    sessionsList.innerHTML = sessions
      .map(function (s) {
        const status = s.status || "UNKNOWN";
        const goal = s.goal || "N/A";
        const id = s.id || "";
        const shortId = id.substring(0, 8);
        return (
          '<div class="session-item" onclick="viewSession(\'' +
          escapeHtml(id) +
          "')\">" +
          '<div class="session-info">' +
          '<div class="session-goal">' +
          escapeHtml(goal) +
          "</div>" +
          '<div class="session-meta">' +
          escapeHtml(shortId) +
          "</div>" +
          "</div>" +
          '<span class="session-status ' +
          escapeHtml(status) +
          '">' +
          escapeHtml(status) +
          "</span>" +
          "</div>"
        );
      })
      .join("");
  } catch (err) {
    sessionsList.innerHTML =
      '<div class="empty-state">Failed to load sessions: ' +
      escapeHtml(err.message) +
      "</div>";
  }
}

async function viewSession(sessionId) {
  try {
    const response = await fetch("/api/sessions/" + sessionId);
    const data = await response.json();

    if (data.error) {
      detailContent.innerHTML =
        '<div class="empty-state">Session not found.</div>';
      return;
    }

    document.querySelectorAll("#history-panel, #task-panel, #monitor-panel").forEach(function (el) {
      el.style.display = "none";
    });
    detailPanel.style.display = "block";

    const steps = data.steps || data.trace || [];
    const status = data.status || "UNKNOWN";

    let html =
      '<div class="detail-header">' +
      "<h3>" +
      escapeHtml(data.goal || "N/A") +
      "</h3>" +
      '<div class="detail-meta">' +
      "<span>ID: " +
      escapeHtml(sessionId.substring(0, 8)) +
      "</span>" +
      "<span>Status: " +
      escapeHtml(status) +
      "</span>" +
      "<span>Steps: " +
      steps.length +
      "</span>" +
      "</div>" +
      "</div>";

    if (steps.length === 0) {
      html += '<div class="empty-state">No steps recorded for this session.</div>';
    } else {
      html += '<div class="step-log">';
      steps.forEach(function (step, i) {
        const s = step.success !== false ? "step-success" : "step-error";
        html +=
          '<div class="step-card ' +
          s +
          '">' +
          '<div class="step-header">' +
          '<span class="step-number">Step ' +
          (i + 1) +
          "</span>" +
          "</div>" +
          '<div class="step-action">' +
          escapeHtml(step.action || step.type || "") +
          "</div>" +
          (step.output
            ? '<div class="step-body">' +
              escapeHtml(String(step.output)) +
              "</div>"
            : "") +
          (step.result
            ? '<div class="step-body detail">' +
              escapeHtml(JSON.stringify(step.result, null, 2)) +
              "</div>"
            : "") +
          (step.feedback
            ? '<div class="step-body detail">Feedback: ' +
              escapeHtml(String(step.feedback)) +
              "</div>"
            : "") +
          "</div>";
      });
      html += "</div>";
    }

    detailContent.innerHTML = html;
  } catch (err) {
    detailContent.innerHTML =
      '<div class="empty-state">Error loading session: ' +
      escapeHtml(err.message) +
      "</div>";
  }
}

function closeDetail() {
  detailPanel.style.display = "none";
  document.querySelectorAll("#history-panel, #task-panel, #monitor-panel").forEach(function (el) {
    el.style.display = "";
  });
}

// ---- Credentials ----

async function setCredentials() {
  const key = apiKeyInput.value.trim();
  if (!key) {
    showCredentialStatus("Please enter an API key.", false);
    return;
  }
  try {
    await fetch("/api/credentials", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: key }),
    });
    apiKeyInput.value = "";
    showCredentialStatus("API key configured.", true);
  } catch (err) {
    showCredentialStatus("Failed to set API key: " + err.message, false);
  }
}

async function clearCredentials() {
  try {
    await fetch("/api/credentials", { method: "DELETE" });
    apiKeyInput.value = "";
    showCredentialStatus("API key cleared.", false);
  } catch (err) {
    showCredentialStatus("Failed to clear API key: " + err.message, false);
  }
}

async function loadCredentialStatus() {
  try {
    const response = await fetch("/api/credentials/status");
    const data = await response.json();
    const configured = data.configured || data.has_key || false;
    showCredentialStatus(
      configured ? "API key configured" : "No API key configured",
      configured
    );
  } catch (err) {
    showCredentialStatus("Failed to check credentials", false);
  }
}

function showCredentialStatus(text, configured) {
  credentialStatus.textContent = text;
  credentialStatus.className = "credential-status " + (configured ? "configured" : "not-configured");
}

// ---- Task Status ----

function showTaskStatus(message, type) {
  taskStatus.textContent = message;
  taskStatus.className = "task-status " + type;
}

// ---- Utilities ----

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ---- Initialize ----

document.addEventListener("DOMContentLoaded", function () {
  setConnectionStatus("offline", "Disconnected");
  loadCredentialStatus();
  loadSessions();

  // Allow Enter to submit (Shift+Enter for newline)
  goalInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submitTask();
    }
  });
});