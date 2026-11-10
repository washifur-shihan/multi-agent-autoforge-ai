// ==========================================================================
// Autoforge AI — Workbench Client Controller
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
    // Elements
    const modeButtons = document.querySelectorAll(".mode-btn");
    const views = {
        pipeline: document.getElementById("view-pipeline"),
        chat: document.getElementById("view-chat"),
        archive: document.getElementById("view-archive"),
    };

    const presetButtons = document.querySelectorAll(".preset-item");
    const pipelineForm = document.getElementById("pipeline-form");
    const pipelinePrompt = document.getElementById("pipeline-prompt");
    const clearPipelineBtn = document.getElementById("clear-pipeline-btn");
    const runPipelineBtn = document.getElementById("run-pipeline-btn");
    const pipelineProgress = document.getElementById("pipeline-progress");
    const progressTimer = document.getElementById("progress-timer");
    const pipelineResults = document.getElementById("pipeline-results-container");

    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const chatTranscript = document.getElementById("chat-transcript");
    const chatProviderSelect = document.getElementById("chat-provider-select");
    const resetChatBtn = document.getElementById("reset-chat-btn");

    const refreshArchiveBtn = document.getElementById("refresh-archive-btn");
    const archiveTableWrapper = document.getElementById("archive-table-wrapper");

    const previewForm = document.getElementById("preview-form");
    const previewPathInput = document.getElementById("preview-path-input");
    const stopPreviewBtn = document.getElementById("stop-preview-btn");
    const previewStatusBox = document.getElementById("preview-status-box");

    let currentSessionId = "autoforge_" + Date.now();
    let timerInterval = null;

    // ----------------------------------------------------------------------
    // Mode Navigation
    // ----------------------------------------------------------------------
    function switchMode(targetMode) {
        modeButtons.forEach((btn) => {
            btn.classList.toggle("active", btn.dataset.mode === targetMode);
        });
        Object.keys(views).forEach((key) => {
            views[key].classList.toggle("hidden", key !== targetMode);
        });
        if (targetMode === "archive") {
            loadArchive();
        }
    }

    modeButtons.forEach((btn) => {
        btn.addEventListener("click", () => switchMode(btn.dataset.mode));
    });

    // ----------------------------------------------------------------------
    // Reference Presets
    // ----------------------------------------------------------------------
    presetButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            switchMode("pipeline");
            pipelinePrompt.value = btn.dataset.prompt || "";
            pipelinePrompt.focus();
        });
    });

    clearPipelineBtn.addEventListener("click", () => {
        pipelinePrompt.value = "";
        pipelinePrompt.focus();
    });

    // ----------------------------------------------------------------------
    // System Telemetry & Provider Status
    // ----------------------------------------------------------------------
    async function loadSystemStatus() {
        try {
            const res = await fetch("/api/status");
            const data = await res.json();

            const listEl = document.getElementById("provider-status-list");
            const providers = data.providers || {};
            const rows = [
                { label: "Mistral Vibe AI", ok: providers.mistral },
                { label: "OpenAI GPT", ok: providers.openai },
                { label: "Google Gemini", ok: providers.gemini },
                { label: "Anthropic Claude", ok: providers.claude },
                { label: "NVIDIA NIM", ok: providers.nvidia },
                { label: "Tavily Web Search", ok: data.web_search },
            ];

            listEl.innerHTML = rows
                .map(
                    (r) => `
                <li class="telemetry-row">
                    <span>${r.label}</span>
                    <span class="badge ${r.ok ? "badge-configured" : "badge-missing"}">
                        ${r.ok ? "Configured" : "Not Set"}
                    </span>
                </li>
            `
                )
                .join("");

            document.getElementById("metric-artifacts").textContent =
                data.artifact_count ?? 0;
            document.getElementById("metric-previews").textContent =
                (data.active_previews || []).length;
        } catch (err) {
            console.error("Failed to fetch system status:", err);
        }
    }

    // ----------------------------------------------------------------------
    // Autonomous Pipeline Execution
    // ----------------------------------------------------------------------
    pipelineForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const promptText = pipelinePrompt.value.trim();
        if (!promptText) return;

        runPipelineBtn.disabled = true;
        runPipelineBtn.textContent = "Executing...";
        pipelineProgress.classList.remove("hidden");

        const startTime = performance.now();
        const stageSteps = pipelineProgress.querySelectorAll(".stage-step");
        let stepIdx = 0;

        timerInterval = setInterval(() => {
            const elapsed = ((performance.now() - startTime) / 1000).toFixed(1);
            progressTimer.textContent = `${elapsed}s`;
            const targetStep = Math.min(3, Math.floor(elapsed / 3));
            if (targetStep !== stepIdx) {
                stepIdx = targetStep;
                stageSteps.forEach((s, i) =>
                    s.classList.toggle("active", i <= stepIdx)
                );
            }
        }, 200);

        try {
            const res = await fetch("/api/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt: promptText }),
            });

            const payload = await res.json();
            if (!res.ok) {
                throw new Error(payload.detail || "Pipeline execution error");
            }

            renderPipelineResult(promptText, payload.data);
            loadSystemStatus();
        } catch (err) {
            pipelineResults.innerHTML = `
                <div class="result-block">
                    <div class="result-header">
                        <span class="result-title">Execution Error</span>
                        <span class="badge badge-missing">Failed</span>
                    </div>
                    <div class="result-output">${escapeHtml(err.message)}</div>
                </div>
            `;
        } finally {
            clearInterval(timerInterval);
            runPipelineBtn.disabled = false;
            runPipelineBtn.textContent = "Execute Pipeline";
            pipelineProgress.classList.add("hidden");
        }
    });

    function renderPipelineResult(promptText, rawData) {
        // AgentController wraps result in {"result": {...}}
        const resultObj =
            rawData && rawData.result ? rawData.result : rawData || {};
        const formattedList = resultObj.formatted_results || [];
        const projectPath = resultObj.project_path || null;
        const zipPath = resultObj.zip_path || null;
        const pdfPath = resultObj.pdf_path || null;
        const imagePath = resultObj.image_path || null;

        let deliverablesHtml = "";
        if (projectPath || zipPath || pdfPath || imagePath) {
            const links = [];
            if (projectPath) {
                links.push(`<span>Project Directory: <code>${escapeHtml(projectPath)}</code></span>`);
                previewPathInput.value = projectPath;
            }
            if (zipPath) {
                links.push(
                    `<a class="btn btn-primary btn-sm" href="/api/download?path=${encodeURIComponent(
                        zipPath
                    )}">Download ZIP Package</a>`
                );
            }
            if (pdfPath) {
                links.push(
                    `<a class="btn btn-primary btn-sm" href="/api/download?path=${encodeURIComponent(
                        pdfPath
                    )}">Download PDF Report</a>`
                );
            }
            if (imagePath) {
                links.push(
                    `<a class="btn btn-primary btn-sm" href="/api/download?path=${encodeURIComponent(
                        imagePath
                    )}">Download Image</a>`
                );
            }
            deliverablesHtml = `
                <div class="deliverables-banner">
                    <div><strong>Generated Deliverables</strong></div>
                    <div class="button-group">${links.join(" ")}</div>
                </div>
            `;
        }

        const tasksHtml =
            formattedList.length > 0
                ? formattedList
                      .map(
                          (item, idx) => `
                <div class="result-block">
                    <div class="result-header">
                        <span class="result-title">Task ${idx + 1}: ${escapeHtml(
                              (item.task_type || "general").toUpperCase()
                          )}</span>
                        <div>
                            <span class="badge">Provider: ${escapeHtml(
                                item.provider || "auto"
                            )}</span>
                            <span class="badge ${
                                item.status === "success"
                                    ? "badge-configured"
                                    : "badge-missing"
                            }">
                                ${escapeHtml(item.status || "completed")}
                            </span>
                        </div>
                    </div>
                    <div class="result-output">${escapeHtml(
                        item.output || "No textual output returned."
                    )}</div>
                </div>
            `
                      )
                      .join("")
                : `<div class="result-block">
                       <div class="result-header">
                           <span class="result-title">Pipeline Output</span>
                       </div>
                       <div class="result-output">${escapeHtml(
                           JSON.stringify(resultObj, null, 2)
                       )}</div>
                   </div>`;

        pipelineResults.innerHTML = `
            <div class="card">
                <div class="card-header">
                    <div>
                        <h3 class="card-title">Execution Report</h3>
                        <p class="card-subtitle">Specification: ${escapeHtml(
                            promptText
                        )}</p>
                    </div>
                    <span class="badge badge-configured">Completed</span>
                </div>
                ${deliverablesHtml}
                ${tasksHtml}
            </div>
        `;
    }

    // ----------------------------------------------------------------------
    // Direct Consultation (Chat)
    // ----------------------------------------------------------------------
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const message = chatInput.value.trim();
        if (!message) return;

        appendChatMessage("user", "Washifur", message);
        chatInput.value = "";

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    prompt: message,
                    session_id: currentSessionId,
                    provider: chatProviderSelect.value,
                }),
            });

            const payload = await res.json();
            if (!res.ok) {
                throw new Error(payload.detail || "Consultation request failed");
            }

            const reply =
                payload.data && payload.data.response
                    ? payload.data.response
                    : "No response received.";
            const usedProvider =
                (payload.data && payload.data.provider) ||
                chatProviderSelect.value;

            appendChatMessage(
                "assistant",
                `Autoforge AI · ${usedProvider.toUpperCase()}`,
                reply
            );
        } catch (err) {
            appendChatMessage("assistant", "System Error", err.message);
        }
    });

    resetChatBtn.addEventListener("click", () => {
        currentSessionId = "autoforge_" + Date.now();
        chatTranscript.innerHTML = `
            <div class="chat-message assistant-message">
                <div class="message-meta">Autoforge AI &middot; New Session Initialized</div>
                <div class="message-body">Session history cleared. Ready for new architectural consultation.</div>
            </div>
        `;
    });

    function appendChatMessage(role, metaLabel, bodyText) {
        const div = document.createElement("div");
        div.className = `chat-message ${
            role === "user" ? "user-message" : "assistant-message"
        }`;
        div.innerHTML = `
            <div class="message-meta">${escapeHtml(metaLabel)}</div>
            <div class="message-body">${escapeHtml(bodyText)}</div>
        `;
        chatTranscript.appendChild(div);
        chatTranscript.scrollTop = chatTranscript.scrollHeight;
    }

    // ----------------------------------------------------------------------
    // Generated Archive Registry
    // ----------------------------------------------------------------------
    async function loadArchive() {
        archiveTableWrapper.innerHTML = `<p class="section-note">Loading archive registry&hellip;</p>`;
        try {
            const res = await fetch("/api/projects");
            const data = await res.json();
            const artifacts = data.artifacts || [];

            if (artifacts.length === 0) {
                archiveTableWrapper.innerHTML = `
                    <div class="empty-state">
                        <h3>No Generated Deliverables Yet</h3>
                        <p>Projects, ZIP archives, and PDF reports created by Autoforge AI will appear in this registry.</p>
                    </div>
                `;
                return;
            }

            const rowsHtml = artifacts
                .map((item) => {
                    let actions = "";
                    if (item.kind === "project_dir") {
                        actions += `<button type="button" class="btn btn-secondary btn-sm preview-trigger-btn" data-path="${escapeHtml(
                            item.path
                        )}">Preview</button> `;
                        if (item.zip_path) {
                            actions += `<a class="btn btn-primary btn-sm" href="/api/download?path=${encodeURIComponent(
                                item.zip_path
                            )}">Download ZIP</a>`;
                        }
                    } else {
                        actions += `<a class="btn btn-primary btn-sm" href="/api/download?path=${encodeURIComponent(
                            item.path
                        )}">Download ${escapeHtml(item.kind.toUpperCase())}</a>`;
                    }

                    const details =
                        item.kind === "project_dir"
                            ? `${item.file_count} files`
                            : `${item.size_kb} KB`;

                    return `
                        <tr>
                            <td><strong>${escapeHtml(item.name)}</strong></td>
                            <td><code>${escapeHtml(item.kind)}</code></td>
                            <td>${escapeHtml(details)}</td>
                            <td>${escapeHtml(item.modified)}</td>
                            <td>${actions}</td>
                        </tr>
                    `;
                })
                .join("");

            archiveTableWrapper.innerHTML = `
                <table class="archive-table">
                    <thead>
                        <tr>
                            <th>Deliverable Name</th>
                            <th>Type</th>
                            <th>Details</th>
                            <th>Modified</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>${rowsHtml}</tbody>
                </table>
            `;

            archiveTableWrapper
                .querySelectorAll(".preview-trigger-btn")
                .forEach((btn) => {
                    btn.addEventListener("click", () => {
                        previewPathInput.value = btn.dataset.path;
                        startPreview(btn.dataset.path);
                    });
                });
        } catch (err) {
            archiveTableWrapper.innerHTML = `<p class="section-note">Failed to load archive: ${escapeHtml(
                err.message
            )}</p>`;
        }
    }

    refreshArchiveBtn.addEventListener("click", loadArchive);

    // ----------------------------------------------------------------------
    // Live Preview Server Controls
    // ----------------------------------------------------------------------
    previewForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const path = previewPathInput.value.trim();
        if (path) startPreview(path);
    });

    stopPreviewBtn.addEventListener("click", async () => {
        const path = previewPathInput.value.trim();
        if (!path) return;
        try {
            const res = await fetch("/api/preview/stop", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ project_path: path }),
            });
            const data = await res.json();
            previewStatusBox.classList.remove("hidden");
            previewStatusBox.innerHTML = escapeHtml(
                data.message || data.error || "Stopped"
            );
            loadSystemStatus();
        } catch (err) {
            previewStatusBox.classList.remove("hidden");
            previewStatusBox.textContent = err.message;
        }
    });

    async function startPreview(projectPath) {
        previewStatusBox.classList.remove("hidden");
        previewStatusBox.textContent = "Starting preview server...";
        try {
            const res = await fetch("/api/preview", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ project_path: projectPath }),
            });
            const data = await res.json();
            if (data.success && data.url) {
                previewStatusBox.innerHTML = `Running (${escapeHtml(
                    data.project_type
                )}): <a href="${escapeHtml(
                    data.url
                )}" target="_blank" rel="noopener"><strong>${escapeHtml(
                    data.url
                )}</strong></a>`;
            } else {
                previewStatusBox.textContent =
                    data.error || "Could not start preview server.";
            }
            loadSystemStatus();
        } catch (err) {
            previewStatusBox.textContent = err.message;
        }
    }

    function escapeHtml(str) {
        return String(str ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

    // Initial load
    loadSystemStatus();
});

