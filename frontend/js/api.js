/**
 * Shared REST API Client, Authentication Manager, Sidebar Builder & UI Helpers
 * AI-Powered Integrated Bid Compliance Verification Platform (SIH 26100)
 */

const API_BASE = "";

const Auth = {
  getToken() {
    return localStorage.getItem("gem_jwt_token");
  },
  getUser() {
    try {
      const raw = localStorage.getItem("gem_user");
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      return null;
    }
  },
  setSession(token, user) {
    localStorage.setItem("gem_jwt_token", token);
    localStorage.setItem("gem_user", JSON.stringify(user));
  },
  clearSession() {
    localStorage.removeItem("gem_jwt_token");
    localStorage.removeItem("gem_user");
  },
  async logout() {
    try {
      await apiRequest("/api/auth/logout", { method: "POST" });
    } catch (e) {
      // Ignore network errors during logout
    }
    this.clearSession();
    window.location.href = "/login.html";
  },
  requireRole(expectedRole) {
    const token = this.getToken();
    const user = this.getUser();
    if (!token || !user) {
      window.location.href = "/login.html";
      return null;
    }
    if (expectedRole && user.role !== expectedRole) {
      window.location.href =
        user.role === "PROCUREMENT_OFFICER"
          ? "/officer/dashboard.html"
          : "/company/dashboard.html";
      return null;
    }
    return user;
  },
};

async function apiRequest(endpoint, options = {}) {
  const token = Auth.getToken();
  const headers = options.headers || {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  let payload = null;
  try {
    payload = await response.json();
  } catch (err) {
    throw new Error(`Unexpected server response (${response.status})`);
  }

  if (response.status === 401 && !endpoint.includes("/api/auth/login")) {
    Auth.clearSession();
    window.location.href = "/login.html";
    throw new Error(payload.message || "Session expired. Please login again.");
  }

  if (!response.ok || (payload && payload.success === false)) {
    const err = new Error(payload.message || "Request failed");
    err.error_code = payload.error_code || "API_ERROR";
    err.status = response.status;
    throw err;
  }

  return payload.data !== undefined ? payload.data : payload;
}

/* Status & Risk Badge Formatters (Green=Compliant, Red=Non-compliant, Yellow=Needs Review, Gray=N/A) */
function renderStatusBadge(status) {
  const s = (status || "UNASSESSED").toUpperCase();
  if (s === "COMPLIANT" || s === "VERIFIED" || s === "PUBLISHED" || s === "PROCESSED" || s === "ACTIVE" || s === "APPROVED") {
    return `<span class="badge badge-compliant">${s.replace(/_/g, " ")}</span>`;
  }
  if (s === "NON_COMPLIANT" || s === "FAILED" || s === "HIGH" || s === "REJECTED") {
    return `<span class="badge badge-noncompliant">${s.replace(/_/g, " ")}</span>`;
  }
  if (
    s === "NEEDS_REVIEW" ||
    s === "REQUIRES_CLARIFICATION" ||
    s === "PENDING" ||
    s === "PENDING_REVIEW" ||
    s === "REVIEWED" ||
    s === "MEDIUM"
  ) {
    return `<span class="badge badge-review">${s.replace(/_/g, " ")}</span>`;
  }
  return `<span class="badge badge-na">${s.replace(/_/g, " ")}</span>`;
}

function renderRiskBadge(riskLevel) {
  const r = (riskLevel || "UNASSESSED").toUpperCase();
  if (r === "LOW") return `<span class="badge badge-compliant">LOW RISK</span>`;
  if (r === "MEDIUM") return `<span class="badge badge-review">MEDIUM RISK</span>`;
  if (r === "HIGH") return `<span class="badge badge-noncompliant">HIGH RISK</span>`;
  return `<span class="badge badge-na">${r}</span>`;
}

function formatINR(amount) {
  const num = Number(amount || 0);
  return "₹" + num.toLocaleString("en-IN", { maximumFractionDigits: 2 });
}

function formatDate(isoStr) {
  if (!isoStr) return "-";
  const d = new Date(isoStr);
  if (isNaN(d.getTime())) return isoStr;
  return d.toLocaleDateString("en-IN", {
    year: "numeric",
    month: "short",
    day: "2-digit",
  });
}

function getQueryParam(key) {
  const params = new URLSearchParams(window.location.search);
  return params.get(key);
}

function showAlert(containerId, message, type = "danger") {
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `
    <div class="alert alert-${type} alert-dismissible fade show py-2" role="alert">
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
  `;
}

/* Public Navigation Header Builder */
function renderPublicNavbar(activePage = "") {
  return `
    <nav class="navbar navbar-expand-lg gov-navbar navbar-dark">
      <div class="container">
        <a class="navbar-brand d-inline-flex align-items-center text-decoration-none py-1" href="/index.html">
          <span class="bidverify-pill-brand">BidVerify</span>
        </a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#publicNav">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="publicNav">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item">
              <a class="nav-link ${activePage === 'home' ? 'active' : ''}" href="/index.html">Home</a>
            </li>
          </ul>
        </div>
      </div>
    </nav>
  `;
}


/* Authenticated Sidebar & Header Shell Renderer */
function initAuthenticatedLayout(role, activeMenuKey, pageTitle) {
  const user = Auth.requireRole(role);
  if (!user) return null;

  const currentBidId = getQueryParam("bid_id") || "1";
  const currentTenderId = getQueryParam("tender_id") || "1";

  const officerLinks = [
    { section: "Procurement Overview" },
    { key: "dashboard", label: "Officer Dashboard", href: "/officer/dashboard.html" },
    { key: "create-tender", label: "Create Tender", href: "/officer/create-tender.html" },
    { key: "manage-tenders", label: "Manage Tenders", href: "/officer/manage-tenders.html" },
    { section: "Bid Verification & Analysis" },
    { key: "submitted-bids", label: "Submitted Bids", href: "/officer/submitted-bids.html" },
    { key: "bid-details", label: "Bid Details & Review", href: `/officer/bid-details.html?bid_id=${currentBidId}` },
    { key: "document-analysis", label: "Document Intelligence", href: `/officer/document-analysis.html?bid_id=${currentBidId}` },
    { key: "compliance-dashboard", label: "Compliance Dashboard", href: `/officer/compliance-dashboard.html?bid_id=${currentBidId}` },
    { key: "risk-analysis", label: "Risk & Anomaly Analysis", href: `/officer/risk-analysis.html?bid_id=${currentBidId}` },
    { section: "Governance & Reports" },
    { key: "compliance-report", label: "PDF Compliance Report", href: `/officer/compliance-report.html?bid_id=${currentBidId}` },
  ];

  const companyLinks = [
    { section: "Bidder Workspace" },
    { key: "dashboard", label: "Company Dashboard", href: "/company/dashboard.html" },
    { key: "available-tenders", label: "Available GeM Tenders", href: "/company/available-tenders.html" },
    { section: "Bid Submission & Tracking" },
    { key: "submission-status", label: "Submission & Compliance Status", href: "/company/submission-status.html" },
  ];

  // Map contextual subpages to active parent sidebar items
  let effectiveKey = activeMenuKey;
  if (role === "COMPANY") {
    if (activeMenuKey === "tender-details" || activeMenuKey === "apply-tender") {
      effectiveKey = "available-tenders";
    } else if (activeMenuKey === "upload-documents") {
      effectiveKey = "submission-status";
    }
  } else if (role === "PROCUREMENT_OFFICER") {
    if (activeMenuKey === "tender-details") {
      effectiveKey = "manage-tenders";
    }
  }

  const links = role === "PROCUREMENT_OFFICER" ? officerLinks : companyLinks;
  const sidebarEl = document.getElementById("app-sidebar");
  if (sidebarEl) {
    const rawName = (user.full_name || user.email || (role === "PROCUREMENT_OFFICER" ? "Officer" : "Bidder")).trim();
    const cleanName = rawName.replace(/^(Dr\.|Mr\.|Mrs\.|Ms\.|Shri|Prof\.)\s+/i, "").trim();
    const avatarLetter = (cleanName.charAt(0) || rawName.charAt(0) || "U").toUpperCase();
    const profileHref = role === "PROCUREMENT_OFFICER" ? "/officer/profile.html" : "/company/profile.html";
    const profileTitle = role === "PROCUREMENT_OFFICER" ? "Officer Details & Profile" : "Company Details & Profile";
    const isProfileActive = activeMenuKey === "profile" ? "active-profile" : "";

    let navHtml = `
      <div class="sidebar-brand">
        <div class="d-flex align-items-center gap-2">
          <span class="bidverify-pill-brand">BidVerify</span>
          <span class="bidverify-portal-tag">PORTAL</span>
        </div>
        <div class="small text-white-50 mt-1">
          ${role === "PROCUREMENT_OFFICER" ? "Procurement Officer Console" : "Offering Company / Bidder"}
        </div>
      </div>
      <div class="py-2 flex-grow-1 sidebar-nav-list">
    `;
    for (const item of links) {
      if (item.section) {
        navHtml += `<div class="nav-section-title">${item.section}</div>`;
      } else {
        const isActive = item.key === effectiveKey ? "active" : "";
        navHtml += `<a class="nav-link ${isActive}" href="${item.href}">${item.label}</a>`;
      }
    }
    navHtml += `
      </div>
      <div class="sidebar-user-footer">
        <div class="d-flex align-items-center justify-content-between">
          <a href="${profileHref}" class="sidebar-profile-card d-flex align-items-center gap-2 text-decoration-none text-truncate flex-grow-1 ${isProfileActive}" title="${profileTitle}">
            <div class="avatar-circle-sm">
              ${avatarLetter}
            </div>
            <div class="text-truncate">
              <div class="fw-semibold text-white text-truncate" style="font-size:0.83rem; line-height:1.2;">${rawName}</div>
              <div class="text-white-50" style="font-size:0.69rem; line-height:1.1;">${role === "PROCUREMENT_OFFICER" ? "Officer Profile" : "Company Profile"}</div>
            </div>
          </a>
          <button class="btn btn-link text-white-50 p-1 ms-1 hover-logout" onclick="Auth.logout()" title="Sign Out" style="line-height:1;">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path fill-rule="evenodd" d="M10 12.5a.5.5 0 0 1-.5.5h-8a.5.5 0 0 1-.5-.5v-9a.5.5 0 0 1 .5-.5h8a.5.5 0 0 1 .5.5v2a.5.5 0 0 0 1 0v-2A1.5 1.5 0 0 0 9.5 2h-8A1.5 1.5 0 0 0 0 3.5v9A1.5 1.5 0 0 0 1.5 14h8a1.5 1.5 0 0 0 1.5-1.5v-2a.5.5 0 0 0-1 0z"/>
              <path fill-rule="evenodd" d="M15.854 8.354a.5.5 0 0 0 0-.708l-3-3a.5.5 0 0 0-.708.708L14.293 7.5H5.5a.5.5 0 0 0 0 1h8.793l-2.147 2.146a.5.5 0 0 0 .708.708z"/>
            </svg>
          </button>
        </div>
      </div>
    `;
    sidebarEl.innerHTML = navHtml;
  }

  const headerEl = document.getElementById("app-header");
  if (headerEl) {
    const orgSubtitle =
      role === "PROCUREMENT_OFFICER"
        ? user.officer?.department || "GeM Procurement Division"
        : user.company?.company_name || "Registered GeM Bidder";
    headerEl.innerHTML = `
      <div>
        <h5 class="mb-0 fw-bold text-dark">${pageTitle}</h5>
        <div class="small text-muted">${orgSubtitle}</div>
      </div>
      <div class="d-flex align-items-center gap-2 gap-md-3">
        <span class="badge bg-light text-dark border d-none d-sm-inline">Role: ${role.replace("_", " ")}</span>
        <button class="btn btn-sm btn-danger px-3 fw-semibold" onclick="Auth.logout()">Logout</button>
      </div>
    `;
  }

  return user;
}

async function refreshNotifications() {
  // Notifications UI removed per requirements
}

async function markAllNotificationsRead() {
  // Notifications UI removed per requirements
}

