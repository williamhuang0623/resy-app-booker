import { useState } from "react";
import { datesApi } from "../api/client";
import type { CreateDatePayload, DateEvent, HitlistRestaurant } from "../types";

interface Props {
  hitlist: HitlistRestaurant[];
  onCreated: () => void;
  onClose: () => void;
  editing?: DateEvent;  // present = edit mode
}

export default function CreateDateModal({ hitlist, onCreated, onClose, editing }: Props) {
  const today = new Date().toISOString().slice(0, 10);
  const isEdit = !!editing;

  const [form, setForm] = useState<CreateDatePayload>({
    restaurant_id: editing?.restaurant_id ?? hitlist[0]?.id ?? 0,
    desired_date_start: editing?.desired_date_start ?? today,
    desired_date_end: editing?.desired_date_end ?? today,
    desired_time_start: editing?.desired_time_start ?? "18:00",
    desired_time_end: editing?.desired_time_end ?? "21:00",
    party_size: editing?.party_size ?? 2,
    one_and_done: editing?.one_and_done ?? false,
    notes: editing?.notes ?? "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  function set<K extends keyof CreateDatePayload>(k: K, v: CreateDatePayload[K]) {
    setForm((prev) => ({ ...prev, [k]: v }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      if (isEdit) {
        const { restaurant_id: _r, ...update } = form;
        await datesApi.update(editing!.id, update);
      } else {
        await datesApi.create(form);
      }
      onCreated();
      onClose();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : isEdit ? "Failed to update date" : "Failed to create date");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={overlayStyle} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div style={modalStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <h2 style={{ fontSize: 20, fontWeight: 700 }}>{isEdit ? "Edit Date" : "New Date"}</h2>
          <button onClick={onClose} style={closeStyle}>✕</button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Restaurant */}
          <div style={fieldStyle}>
            <label style={labelStyle}>Restaurant</label>
            <select
              value={form.restaurant_id}
              onChange={(e) => set("restaurant_id", Number(e.target.value))}
              style={{ ...inputStyle, opacity: isEdit ? 0.5 : 1 }}
              disabled={isEdit}
              required
            >
              {hitlist.map((r) => (
                <option key={r.id} value={r.id}>{r.name}</option>
              ))}
            </select>
          </div>

          {/* Date range */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div style={fieldStyle}>
              <label style={labelStyle}>Earliest date</label>
              <input
                type="date"
                value={form.desired_date_start}
                min={today}
                onChange={(e) => set("desired_date_start", e.target.value)}
                style={inputStyle}
                required
              />
            </div>
            <div style={fieldStyle}>
              <label style={labelStyle}>Latest date</label>
              <input
                type="date"
                value={form.desired_date_end}
                min={form.desired_date_start}
                onChange={(e) => set("desired_date_end", e.target.value)}
                style={inputStyle}
                required
              />
            </div>
          </div>

          {/* Time window */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <div style={fieldStyle}>
              <label style={labelStyle}>Earliest time</label>
              <input
                type="time"
                value={form.desired_time_start}
                onChange={(e) => set("desired_time_start", e.target.value)}
                style={inputStyle}
                required
              />
            </div>
            <div style={fieldStyle}>
              <label style={labelStyle}>Latest time</label>
              <input
                type="time"
                value={form.desired_time_end}
                onChange={(e) => set("desired_time_end", e.target.value)}
                style={inputStyle}
                required
              />
            </div>
          </div>

          {/* Party size */}
          <div style={fieldStyle}>
            <label style={labelStyle}>Party size</label>
            <input
              type="number"
              min={1}
              max={20}
              value={form.party_size}
              onChange={(e) => set("party_size", Number(e.target.value))}
              style={{ ...inputStyle, width: 100 }}
              required
            />
          </div>

          {/* One-and-done */}
          <label style={toggleRowStyle}>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600, fontSize: 14 }}>One-and-done</div>
              <div style={{ color: "#666", fontSize: 12, marginTop: 2 }}>
                If this books, automatically cancel all other monitoring Dates
              </div>
            </div>
            <div
              onClick={() => set("one_and_done", !form.one_and_done)}
              style={toggleTrackStyle(form.one_and_done)}
            >
              <div style={toggleThumbStyle(form.one_and_done)} />
            </div>
          </label>

          {/* Notes */}
          <div style={fieldStyle}>
            <label style={labelStyle}>Notes (optional)</label>
            <input
              type="text"
              value={form.notes}
              onChange={(e) => set("notes", e.target.value)}
              placeholder="Anniversary, prefer patio, etc."
              style={inputStyle}
            />
          </div>

          {error && <p style={{ color: "#e07070", fontSize: 13 }}>{error}</p>}

          <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 4 }}>
            <button type="button" onClick={onClose} style={cancelBtnStyle}>Cancel</button>
            <button type="submit" disabled={saving} style={submitBtnStyle}>
              {saving ? (isEdit ? "Saving…" : "Creating…") : (isEdit ? "Save Changes" : "Create Date")}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

const overlayStyle: React.CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(0,0,0,0.7)",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  zIndex: 100,
  padding: 20,
};

const modalStyle: React.CSSProperties = {
  background: "#181818",
  border: "1px solid #2a2a2a",
  borderRadius: 16,
  padding: 28,
  width: "100%",
  maxWidth: 480,
};

const closeStyle: React.CSSProperties = {
  background: "transparent",
  border: "none",
  color: "#666",
  cursor: "pointer",
  fontSize: 18,
  padding: 4,
};

const fieldStyle: React.CSSProperties = { display: "flex", flexDirection: "column", gap: 6 };
const labelStyle: React.CSSProperties = { fontSize: 12, fontWeight: 600, color: "#888", letterSpacing: "0.05em", textTransform: "uppercase" };
const inputStyle: React.CSSProperties = {
  background: "#111",
  border: "1px solid #333",
  borderRadius: 8,
  color: "#f0ede8",
  fontSize: 14,
  padding: "9px 12px",
  outline: "none",
};

const submitBtnStyle: React.CSSProperties = {
  background: "#ff6b4a",
  border: "none",
  borderRadius: 8,
  color: "#fff",
  cursor: "pointer",
  fontSize: 14,
  fontWeight: 600,
  padding: "10px 22px",
};

const cancelBtnStyle: React.CSSProperties = {
  background: "transparent",
  border: "1px solid #333",
  borderRadius: 8,
  color: "#999",
  cursor: "pointer",
  fontSize: 14,
  padding: "10px 18px",
};

const toggleRowStyle: React.CSSProperties = {
  display: "flex",
  alignItems: "center",
  gap: 16,
  background: "#111",
  border: "1px solid #333",
  borderRadius: 10,
  cursor: "pointer",
  padding: "12px 14px",
};

const toggleTrackStyle = (on: boolean): React.CSSProperties => ({
  background: on ? "#ff6b4a" : "#2a2a2a",
  borderRadius: 12,
  cursor: "pointer",
  flexShrink: 0,
  height: 24,
  position: "relative",
  transition: "background 0.2s",
  width: 44,
});

const toggleThumbStyle = (on: boolean): React.CSSProperties => ({
  background: "#fff",
  borderRadius: "50%",
  height: 18,
  left: on ? 22 : 3,
  position: "absolute",
  top: 3,
  transition: "left 0.2s",
  width: 18,
});
