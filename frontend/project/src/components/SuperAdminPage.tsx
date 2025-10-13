import { Lock, Mail, Plus, Shield, Trash2, UserCheck, UserX } from "lucide-react";
import React, { useEffect, useState } from "react";
import { apiService } from "../services/api";
import { useAuth } from "../contexts/AuthContext";

interface WhitelistEntry {
  id: string;
  email_hash: string;
  email_encrypted: string;
  added_by: string;
  added_at: string;
  is_active: boolean;
  notes: string;
  created_at: string;
  updated_at: string;
}

const SuperAdminPage: React.FC = () => {
  const { user } = useAuth();
  const [emails, setEmails] = useState<WhitelistEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedEntry, setSelectedEntry] = useState<WhitelistEntry | null>(null);
  const [formData, setFormData] = useState({
    email: "",
    notes: "",
  });
  const [editFormData, setEditFormData] = useState({
    isActive: true,
    notes: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLocalhost, setIsLocalhost] = useState(false);

  useEffect(() => {
    const hostname = window.location.hostname;
    const isLocal = hostname === "localhost" || hostname === "127.0.0.1";
    setIsLocalhost(isLocal);

    if (isLocal) {
      fetchEmails();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchEmails = async () => {
    try {
      const response = await apiService.getWhitelistEmails();
      if (response.data?.data) {
        setEmails(response.data.data);
      }
    } catch (error) {
      console.error("Failed to fetch whitelist:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const response = await apiService.addEmailToWhitelist(
        formData.email,
        user?.email || "system",
        formData.notes
      );

      if (response.error) {
        alert("Error: " + response.error);
      } else {
        alert("Email added to whitelist successfully!");
        setShowAddModal(false);
        setFormData({ email: "", notes: "" });
        fetchEmails();
      }
    } catch (error) {
      alert("Failed to add email to whitelist");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEditEntry = (entry: WhitelistEntry) => {
    setSelectedEntry(entry);
    setEditFormData({
      isActive: entry.is_active,
      notes: entry.notes || "",
    });
    setShowEditModal(true);
  };

  const handleUpdateEntry = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEntry) return;

    setIsSubmitting(true);

    try {
      const response = await apiService.updateWhitelistEmail(
        selectedEntry.id,
        editFormData.isActive,
        editFormData.notes
      );

      if (response.error) {
        alert("Error: " + response.error);
      } else {
        alert("Whitelist entry updated successfully!");
        setShowEditModal(false);
        setSelectedEntry(null);
        fetchEmails();
      }
    } catch (error) {
      alert("Failed to update whitelist entry");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRemoveEmail = async (entry: WhitelistEntry) => {
    if (
      window.confirm(
        `Are you sure you want to remove ${entry.email_encrypted} from the whitelist?`
      )
    ) {
      try {
        const response = await apiService.removeEmailFromWhitelist(entry.id);
        if (response.error) {
          alert("Error: " + response.error);
        } else {
          alert("Email removed from whitelist successfully!");
          fetchEmails();
        }
      } catch (error) {
        alert("Failed to remove email from whitelist");
      }
    }
  };

  if (!isLocalhost) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-base-200">
        <div className="card bg-base-100 shadow-xl max-w-md">
          <div className="card-body text-center">
            <Lock className="h-16 w-16 text-error mx-auto mb-4" />
            <h2 className="card-title text-error justify-center">
              Access Denied
            </h2>
            <p className="text-base-content/70">
              This page is only accessible from localhost for security reasons.
            </p>
            <p className="text-sm text-base-content/50 mt-2">
              Current hostname: {window.location.hostname}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center">
        <div className="text-center">
          <div className="loading loading-spinner loading-lg"></div>
          <p className="text-base-content/70 mt-4">Loading whitelist...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Shield className="h-8 w-8 text-error" />
            <h1 className="text-3xl font-bold text-base-content">
              Super Admin Panel
            </h1>
          </div>
          <p className="text-base-content/70">
            Manage email whitelist for system access control
          </p>
          <div className="badge badge-warning mt-2">
            Localhost Only - Security Protected
          </div>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="btn btn-error gap-2"
        >
          <Plus className="h-5 w-5" />
          <span>Add Email</span>
        </button>
      </div>

      <div className="stats shadow mb-6 w-full">
        <div className="stat">
          <div className="stat-figure text-primary">
            <Mail className="h-8 w-8" />
          </div>
          <div className="stat-title">Total Emails</div>
          <div className="stat-value text-primary">{emails.length}</div>
        </div>

        <div className="stat">
          <div className="stat-figure text-success">
            <UserCheck className="h-8 w-8" />
          </div>
          <div className="stat-title">Active</div>
          <div className="stat-value text-success">
            {emails.filter((e) => e.is_active).length}
          </div>
        </div>

        <div className="stat">
          <div className="stat-figure text-error">
            <UserX className="h-8 w-8" />
          </div>
          <div className="stat-title">Inactive</div>
          <div className="stat-value text-error">
            {emails.filter((e) => !e.is_active).length}
          </div>
        </div>
      </div>

      <div className="overflow-x-auto bg-base-100 rounded-lg shadow">
        <table className="table">
          <thead>
            <tr>
              <th>Email</th>
              <th>Status</th>
              <th>Added By</th>
              <th>Added At</th>
              <th>Notes</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {emails.map((entry) => (
              <tr key={entry.id} className="hover">
                <td>
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-base-content/60" />
                    <span className="font-medium">{entry.email_encrypted}</span>
                  </div>
                </td>
                <td>
                  {entry.is_active ? (
                    <div className="badge badge-success gap-1">
                      <UserCheck className="h-3 w-3" />
                      Active
                    </div>
                  ) : (
                    <div className="badge badge-error gap-1">
                      <UserX className="h-3 w-3" />
                      Inactive
                    </div>
                  )}
                </td>
                <td className="text-sm text-base-content/70">
                  {entry.added_by}
                </td>
                <td className="text-sm text-base-content/70">
                  {new Date(entry.added_at).toLocaleDateString()}
                </td>
                <td className="text-sm text-base-content/70 max-w-xs truncate">
                  {entry.notes || "-"}
                </td>
                <td>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleEditEntry(entry)}
                      className="btn btn-sm btn-ghost"
                      title="Edit"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleRemoveEmail(entry)}
                      className="btn btn-sm btn-error"
                      title="Remove"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {emails.length === 0 && (
          <div className="text-center py-12">
            <Shield className="h-12 w-12 text-base-content/40 mx-auto mb-4" />
            <p className="text-base-content/70 text-lg">No emails in whitelist</p>
            <p className="text-base-content/50 text-sm">
              Add emails to grant system access
            </p>
          </div>
        )}
      </div>

      {showAddModal && (
        <div className="modal modal-open">
          <div className="modal-box">
            <h2 className="text-xl font-bold text-base-content mb-4">
              Add Email to Whitelist
            </h2>
            <form onSubmit={handleAddEmail} className="space-y-4">
              <div>
                <label className="label">
                  <span className="label-text">Email Address</span>
                </label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                  className="input input-bordered w-full"
                  placeholder="user@example.com"
                />
              </div>

              <div>
                <label className="label">
                  <span className="label-text">Notes (Optional)</span>
                </label>
                <textarea
                  value={formData.notes}
                  onChange={(e) =>
                    setFormData({ ...formData, notes: e.target.value })
                  }
                  className="textarea textarea-bordered w-full"
                  rows={3}
                  placeholder="Add notes about this user..."
                />
              </div>

              <div className="modal-action">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="btn btn-error"
                >
                  {isSubmitting ? "Adding..." : "Add to Whitelist"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowAddModal(false);
                    setFormData({ email: "", notes: "" });
                  }}
                  className="btn btn-ghost"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showEditModal && selectedEntry && (
        <div className="modal modal-open">
          <div className="modal-box">
            <h2 className="text-xl font-bold text-base-content mb-4">
              Edit Whitelist Entry
            </h2>
            <p className="text-sm text-base-content/70 mb-4">
              Email: <strong>{selectedEntry.email_encrypted}</strong>
            </p>
            <form onSubmit={handleUpdateEntry} className="space-y-4">
              <div>
                <label className="label cursor-pointer justify-start gap-3">
                  <input
                    type="checkbox"
                    checked={editFormData.isActive}
                    onChange={(e) =>
                      setEditFormData({
                        ...editFormData,
                        isActive: e.target.checked,
                      })
                    }
                    className="checkbox checkbox-success"
                  />
                  <span className="label-text">Active Status</span>
                </label>
                <p className="text-xs text-base-content/50 ml-9">
                  Inactive emails cannot log in to the system
                </p>
              </div>

              <div>
                <label className="label">
                  <span className="label-text">Notes</span>
                </label>
                <textarea
                  value={editFormData.notes}
                  onChange={(e) =>
                    setEditFormData({ ...editFormData, notes: e.target.value })
                  }
                  className="textarea textarea-bordered w-full"
                  rows={3}
                  placeholder="Add notes about this user..."
                />
              </div>

              <div className="modal-action">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="btn btn-error"
                >
                  {isSubmitting ? "Updating..." : "Update Entry"}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false);
                    setSelectedEntry(null);
                  }}
                  className="btn btn-ghost"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default SuperAdminPage;
