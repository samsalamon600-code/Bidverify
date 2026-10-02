const API_BASE = '/api';

function getAuthHeader(): Record<string, string> {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('bidverify_token');
    if (token) {
      return { Authorization: `Bearer ${token}` };
    }
  }
  return {};
}

export const api = {
  // Auth
  async login(email: string, password: string) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Login failed');
    }
    const data = await res.json();
    if (typeof window !== 'undefined') {
      localStorage.setItem('bidverify_token', data.access_token);
      localStorage.setItem('bidverify_user', JSON.stringify(data));
    }
    return data;
  },

  async register(payload: {
    email: string;
    password: string;
    full_name: string;
    role: string;
    company_name?: string;
    gstin?: string;
  }) {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Registration failed');
    }
    const data = await res.json();
    if (typeof window !== 'undefined') {
      localStorage.setItem('bidverify_token', data.access_token);
      localStorage.setItem('bidverify_user', JSON.stringify(data));
    }
    return data;
  },

  async demoLogin(role: 'Procurement Officer' | 'Company / Vendor' | 'Admin') {
    const res = await fetch(`${API_BASE}/auth/demo-login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ role }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Demo login failed');
    }
    const data = await res.json();
    if (typeof window !== 'undefined') {
      localStorage.setItem('bidverify_token', data.access_token);
      localStorage.setItem('bidverify_user', JSON.stringify(data));
    }
    return data;
  },

  getCurrentUser() {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('bidverify_user');
      if (saved) return JSON.parse(saved);
    }
    return { full_name: 'Rajesh Sharma', role: 'Procurement Officer', email: 'officer@bidverify.com' };
  },

  logout() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('bidverify_token');
      localStorage.removeItem('bidverify_user');
    }
  },

  // Dashboard
  async getDashboard() {
    const res = await fetch(`${API_BASE}/dashboard/statistics`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Failed to load dashboard metrics');
    return res.json();
  },

  // Vendors
  async getVendors(params?: { search?: string; status?: string; risk_level?: string; sort_by?: string; sort_order?: string }) {
    const query = new URLSearchParams();
    if (params?.search) query.append('search', params.search);
    if (params?.status && params.status !== 'All') query.append('status', params.status);
    if (params?.risk_level && params.risk_level !== 'All') query.append('risk_level', params.risk_level);
    if (params?.sort_by) query.append('sort_by', params.sort_by);
    if (params?.sort_order) query.append('sort_order', params.sort_order);

    const res = await fetch(`${API_BASE}/vendors?${query.toString()}`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Failed to load vendors');
    return res.json();
  },

  async getVendor(id: number | string) {
    const res = await fetch(`${API_BASE}/vendors/${id}`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Vendor not found');
    return res.json();
  },

  async createVendor(payload: any) {
    const res = await fetch(`${API_BASE}/vendors`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to create vendor');
    }
    return res.json();
  },

  async updateVendor(id: number | string, payload: any) {
    const res = await fetch(`${API_BASE}/vendors/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to update vendor');
    return res.json();
  },

  async deleteVendor(id: number | string) {
    const res = await fetch(`${API_BASE}/vendors/${id}`, {
      method: 'DELETE',
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Failed to delete vendor');
    return res.json();
  },

  // Documents & OCR
  async uploadDocument(vendorId: number | string, file: File, docType: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('doc_type', docType);

    const res = await fetch(`${API_BASE}/vendors/${vendorId}/documents`, {
      method: 'POST',
      headers: getAuthHeader(),
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Upload failed');
    }
    return res.json();
  },

  async extractDocument(documentId: number | string) {
    const res = await fetch(`${API_BASE}/documents/${documentId}/extract`, {
      method: 'POST',
      headers: getAuthHeader(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Extraction failed');
    }
    return res.json();
  },

  async getVendorDocuments(vendorId: number | string) {
    const res = await fetch(`${API_BASE}/vendors/${vendorId}/documents`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
  },

  async getAllDocuments() {
    const res = await fetch(`${API_BASE}/documents`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Failed to fetch all documents');
    return res.json();
  },

  async deleteDocument(docId: number | string) {
    const res = await fetch(`${API_BASE}/documents/${docId}`, {
      method: 'DELETE',
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Failed to delete document');
    return res.json();
  },

  async loadSampleDocument(vendorId: number | string, sampleType: 'gst' | 'pan' | 'udyam') {
    const formData = new FormData();
    formData.append('sample_type', sampleType);
    const res = await fetch(`${API_BASE}/vendors/${vendorId}/load-sample-document`, {
      method: 'POST',
      headers: getAuthHeader(),
      body: formData,
    });
    if (!res.ok) throw new Error('Failed to load sample document');
    return res.json();
  },

  // Verification Engine
  async verifyVendor(vendorId: number | string) {
    const res = await fetch(`${API_BASE}/vendors/${vendorId}/verify`, {
      method: 'POST',
      headers: getAuthHeader(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Verification run failed');
    }
    return res.json();
  },

  // Mock Government Inquiries
  async queryMockGst(gstin: string) {
    const res = await fetch(`${API_BASE}/verification/gst/${encodeURIComponent(gstin)}`);
    return res.json();
  },

  async queryMockUdyam(number: string) {
    const res = await fetch(`${API_BASE}/verification/udyam/${encodeURIComponent(number)}`);
    return res.json();
  },

  async queryMockMca(cin: string) {
    const res = await fetch(`${API_BASE}/verification/mca/${encodeURIComponent(cin)}`);
    return res.json();
  },

  // Audit Trail
  async getAuditTrail(vendorId?: number | string) {
    const url = vendorId ? `${API_BASE}/vendors/${vendorId}/audit` : `${API_BASE}/audit`;
    const res = await fetch(url, { headers: getAuthHeader() });
    if (!res.ok) throw new Error('Failed to load audit logs');
    return res.json();
  },

  // Reports
  async generateReport(vendorId: number | string) {
    const res = await fetch(`${API_BASE}/vendors/${vendorId}/report`, {
      method: 'POST',
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Report generation failed');
    return res.json();
  },

  async getReports() {
    const res = await fetch(`${API_BASE}/reports`, {
      headers: getAuthHeader(),
    });
    if (!res.ok) throw new Error('Failed to load reports');
    return res.json();
  },

  getReportDownloadUrl(vendorId: number | string) {
    return `${API_BASE}/vendors/${vendorId}/report`;
  },

  // Settings
  async getWeights() {
    const res = await fetch(`${API_BASE}/settings/weights`);
    if (!res.ok) throw new Error('Failed to load weights');
    return res.json();
  },

  async updateWeights(payload: any) {
    const res = await fetch(`${API_BASE}/settings/weights`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeader(),
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to update weights');
    return res.json();
  },
};
