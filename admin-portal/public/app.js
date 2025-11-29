// VRecommendation Admin Portal - Application Logic

let whitelistData = [];
let currentTheme = localStorage.getItem("adminTheme") || "dark";

// Initialize
document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    checkConnection();
    fetchWhitelist();

    // Check connection periodically
    setInterval(checkConnection, 30000);
});

// Theme Management
function initTheme() {
    document.documentElement.setAttribute("data-theme", currentTheme);
    updateThemeIcons();
}

function toggleTheme() {
    currentTheme = currentTheme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", currentTheme);
    localStorage.setItem("adminTheme", currentTheme);
    updateThemeIcons();
}

function updateThemeIcons() {
    const sunIcon = document.getElementById("sunIcon");
    const moonIcon = document.getElementById("moonIcon");
    if (sunIcon && moonIcon) {
        sunIcon.classList.toggle("hidden", currentTheme !== "light");
        moonIcon.classList.toggle("hidden", currentTheme !== "dark");
    }
}

// Sidebar Management
function toggleSidebar() {
    const sidebar = document.getElementById("sidebar");
    const backdrop = document.getElementById("sidebarBackdrop");
    sidebar.classList.toggle("-translate-x-full");
    backdrop.classList.toggle("hidden");
}

function closeSidebar() {
    const sidebar = document.getElementById("sidebar");
    const backdrop = document.getElementById("sidebarBackdrop");
    sidebar.classList.add("-translate-x-full");
    backdrop.classList.add("hidden");
}

// Connection Check
async function checkConnection() {
    const statusDot = document.getElementById("statusDot");
    const textEl = document.getElementById("connectionText");

    try {
        const response = await fetch("/api/check-connection");
        const data = await response.json();

        if (data.connected) {
            statusDot.classList.remove("bg-error");
            statusDot.classList.add("bg-success", "animate-pulse");
            textEl.textContent = "API Connected";
            textEl.classList.remove("text-error");
            textEl.classList.add("text-success");
        } else {
            throw new Error(data.error || "Connection failed");
        }
    } catch (error) {
        statusDot.classList.remove("bg-success", "animate-pulse");
        statusDot.classList.add("bg-error");
        textEl.textContent = "API Offline";
        textEl.classList.remove("text-success");
        textEl.classList.add("text-error");
        console.error("Connection error:", error);
    }
}

// Fetch Whitelist
async function fetchWhitelist() {
    const container = document.getElementById("tableContainer");
    if (!container) return;

    container.innerHTML = `
        <div class="flex flex-col items-center justify-center py-12 text-base-content/60">
            <span class="loading loading-spinner loading-lg"></span>
            <p class="mt-4 text-sm">Loading whitelist...</p>
        </div>
    `;

    try {
        const response = await fetch("/api/whitelist");
        const result = await response.json();

        if (result.error) {
            throw new Error(result.error);
        }

        whitelistData = result.data || [];
        updateStats();
        renderTable();
    } catch (error) {
        container.innerHTML = `
            <div class="flex flex-col items-center justify-center py-12 text-base-content/60">
                <svg class="h-12 w-12 opacity-50 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" x2="12" y1="8" y2="12"></line>
                    <line x1="12" x2="12.01" y1="16" y2="16"></line>
                </svg>
                <p class="text-sm mb-4">Failed to load whitelist: ${escapeHtml(error.message)}</p>
                <button class="btn btn-primary btn-sm" onclick="fetchWhitelist()">
                    <svg class="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"></path>
                        <path d="M3 3v5h5"></path>
                        <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16"></path>
                        <path d="M16 16h5v5"></path>
                    </svg>
                    Retry
                </button>
            </div>
        `;
    }
}

// Update Statistics
function updateStats() {
    const total = whitelistData.length;
    const active = whitelistData.filter((e) => e.is_active).length;
    const inactive = total - active;

    document.getElementById("totalEmails").textContent = total;
    document.getElementById("activeEmails").textContent = active;
    document.getElementById("inactiveEmails").textContent = inactive;
}

// Render Table
function renderTable() {
    const container = document.getElementById("tableContainer");
    if (!container) return;

    if (whitelistData.length === 0) {
        container.innerHTML = `
            <div class="flex flex-col items-center justify-center py-12 text-base-content/60">
                <svg class="h-12 w-12 opacity-50 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect width="20" height="16" x="2" y="4" rx="2"></rect>
                    <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"></path>
                </svg>
                <p class="text-sm font-medium">No emails in whitelist</p>
                <p class="text-xs mt-1 text-base-content/50">Click "Add Email" to add the first entry.</p>
            </div>
        `;
        return;
    }

    const html = `
        <div class="overflow-x-auto">
            <table class="table table-zebra w-full">
                <thead>
                    <tr>
                        <th class="bg-base-200">Email</th>
                        <th class="bg-base-200">Status</th>
                        <th class="bg-base-200">Added By</th>
                        <th class="bg-base-200">Notes</th>
                        <th class="bg-base-200">Created</th>
                        <th class="bg-base-200">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${whitelistData
                        .map(
                            (entry) => `
                        <tr class="hover">
                            <td class="font-mono text-sm">${escapeHtml(entry.email_encrypted)}</td>
                            <td>
                                <span class="badge ${entry.is_active ? "badge-success" : "badge-error"} badge-sm">
                                    ${entry.is_active ? "Active" : "Inactive"}
                                </span>
                            </td>
                            <td class="text-sm text-base-content/70">${escapeHtml(entry.added_by || "-")}</td>
                            <td class="text-sm text-base-content/70 max-w-[200px] truncate" title="${escapeHtml(entry.notes || "")}">${escapeHtml(entry.notes || "-")}</td>
                            <td class="text-sm text-base-content/70 whitespace-nowrap">${formatDate(entry.created_at)}</td>
                            <td>
                                <div class="flex gap-1">
                                    <button class="btn btn-ghost btn-xs" onclick="openEditModal('${entry.id}')" title="Edit">
                                        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                            <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"></path>
                                            <path d="m15 5 4 4"></path>
                                        </svg>
                                    </button>
                                    <button class="btn btn-ghost btn-xs text-error" onclick="openDeleteModal('${entry.id}')" title="Delete">
                                        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                            <path d="M3 6h18"></path>
                                            <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"></path>
                                            <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"></path>
                                            <line x1="10" x2="10" y1="11" y2="17"></line>
                                            <line x1="14" x2="14" y1="11" y2="17"></line>
                                        </svg>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `,
                        )
                        .join("")}
                </tbody>
            </table>
        </div>
    `;

    container.innerHTML = html;
}

// Alert Functions
function showAlert(message, type = "success") {
    const container = document.getElementById("alertContainer");
    const alertId = "alert-" + Date.now();

    const alertClass = type === "success" ? "alert-success" : "alert-error";
    const iconSvg =
        type === "success"
            ? '<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>'
            : '<svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" x2="12" y1="8" y2="12"></line><line x1="12" x2="12.01" y1="16" y2="16"></line></svg>';

    const alertHtml = `
        <div id="${alertId}" class="alert ${alertClass} shadow-lg animate-slide-up">
            ${iconSvg}
            <span>${escapeHtml(message)}</span>
        </div>
    `;

    container.insertAdjacentHTML("beforeend", alertHtml);

    setTimeout(() => {
        const alert = document.getElementById(alertId);
        if (alert) {
            alert.style.opacity = "0";
            alert.style.transform = "translateX(100%)";
            alert.style.transition = "all 0.3s ease";
            setTimeout(() => alert.remove(), 300);
        }
    }, 4000);
}

// Modal Functions
function openAddModal() {
    document.getElementById("addModal").showModal();
    document.getElementById("addEmail").focus();
}

function closeAddModal() {
    document.getElementById("addModal").close();
    document.getElementById("addForm").reset();
}

function openEditModal(id) {
    const entry = whitelistData.find((e) => e.id === id);
    if (!entry) return;

    document.getElementById("editId").value = entry.id;
    document.getElementById("editEmail").value = entry.email_encrypted;
    document.getElementById("editIsActive").checked = entry.is_active;
    document.getElementById("editNotes").value = entry.notes || "";
    document.getElementById("editModal").showModal();
}

function closeEditModal() {
    document.getElementById("editModal").close();
    document.getElementById("editForm").reset();
}

function openDeleteModal(id) {
    const entry = whitelistData.find((e) => e.id === id);
    if (!entry) return;

    document.getElementById("deleteId").value = entry.id;
    document.getElementById("deleteEmailDisplay").textContent =
        entry.email_encrypted;
    document.getElementById("deleteModal").showModal();
}

function closeDeleteModal() {
    document.getElementById("deleteModal").close();
}

// CRUD Operations
async function handleAddEmail(event) {
    event.preventDefault();

    const email = document.getElementById("addEmail").value;
    const addedBy = document.getElementById("addAddedBy").value || "Admin";
    const notes = document.getElementById("addNotes").value;

    try {
        const response = await fetch("/api/whitelist/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, added_by: addedBy, notes }),
        });

        const result = await response.json();

        if (result.error) {
            throw new Error(result.error);
        }

        showAlert("Email added successfully!", "success");
        closeAddModal();
        fetchWhitelist();
    } catch (error) {
        showAlert("Failed to add email: " + error.message, "error");
    }
}

async function handleUpdateEmail(event) {
    event.preventDefault();

    const id = document.getElementById("editId").value;
    const isActive = document.getElementById("editIsActive").checked;
    const notes = document.getElementById("editNotes").value;

    try {
        const response = await fetch(`/api/whitelist/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ is_active: isActive, notes }),
        });

        const result = await response.json();

        if (result.error) {
            throw new Error(result.error);
        }

        showAlert("Email updated successfully!", "success");
        closeEditModal();
        fetchWhitelist();
    } catch (error) {
        showAlert("Failed to update email: " + error.message, "error");
    }
}

async function handleDeleteEmail() {
    const id = document.getElementById("deleteId").value;

    try {
        const response = await fetch(`/api/whitelist/${id}`, {
            method: "DELETE",
        });

        const result = await response.json();

        if (result.error) {
            throw new Error(result.error);
        }

        showAlert("Email deleted successfully!", "success");
        closeDeleteModal();
        fetchWhitelist();
    } catch (error) {
        showAlert("Failed to delete email: " + error.message, "error");
    }
}

// Utility Functions
function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return "-";
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString("vi-VN", {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
        });
    } catch {
        return dateString;
    }
}

// Keyboard Shortcuts
document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
        closeAddModal();
        closeEditModal();
        closeDeleteModal();
        closeSidebar();
    }
});
