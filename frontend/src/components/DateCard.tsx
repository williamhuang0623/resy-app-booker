import type { DateEvent, DateStatus } from "../types";

interface Props {
  date: DateEvent;
  onMonitor: (id: number) => void;
  onCancel: (id: number) => void;
  onDelete: (id: number) => void;
  busy: boolean;
}

const STATUS_CONFIG: Record<
  DateStatus,
  { label: string; color: string; bg: string }
> = {
  draft:      { label: "Draft",      color: "#aaa",    bg: "#1e1e1e" },
  monitoring: { label: "Monitoring", color: "#f0a04a", bg: "#2a1e0e" },
  booked:     { label: "Booked ✓",   color: "#4caf7a", bg: "#0e2018" },
  failed:     { label: "Missed",     color: "#888",    bg: "#1a1a1a" },
  cancelled:  { label: "Cancelled",  color: "#666",    bg: "#1a1a1a" },
};

function fmt(date: string) {
  return new Date(date + "T00:00:00").toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
}

function fmtTime(t: string) {
  const [h, m] = t.split(":").map(Number);
  const ampm = h >= 12 ? "pm" : "am";
  return `${h % 12 || 12}:${String(m).padStart(2, "0")}${ampm}`;
}

function fmtSlot(slot: string) {
  const d = new Date(slot);
  return d.toLocaleString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function DateCard({ date, onMonitor, onCancel, onDelete, busy }: Props) {
  const cfg = STATUS_CONFIG[date.status];

  const sameDay = date.desired_date_start === date.desired_date_end;
  const dateRange = sameDay
    ? fmt(date.desired_date_start)
    : `${fmt(date.desired_date_start)} – ${fmt(date.desired_date_end)}`;

  return (
    <div
      style={{
        background: cfg.bg,
        border: `1px solid ${date.status === "booked" ? "#1e4a30" : "#1e1e1e"}`,
        borderRadius: 14,
        padding: "18px 20px",
        display: "flex",
        flexDirection: "column",
        gap: 12,
      }}
    >
      {/* Top row */}
      <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: 17, marginBottom: 3 }}>
            {date.restaurant.name}
          </div>
          <div style={{ color: "#666", fontSize: 12 }}>
            {date.restaurant.location}
          </div>
        </div>

        <div style={{ display: "flex", gap: 6, alignItems: "center", flexShrink: 0 }}>
          {date.one_and_done && (
            <span style={oneAndDoneBadgeStyle}>1 &amp; done</span>
          )}
          <span
            style={{
              background: "transparent",
              border: `1px solid ${cfg.color}`,
              borderRadius: 20,
              color: cfg.color,
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: "0.06em",
              padding: "3px 10px",
              textTransform: "uppercase",
              whiteSpace: "nowrap",
            }}
          >
            {cfg.label}
          </span>
        </div>
      </div>

      {/* Details row */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: "6px 20px" }}>
        <Detail label="When" value={dateRange} />
        <Detail label="Time" value={`${fmtTime(date.desired_time_start)} – ${fmtTime(date.desired_time_end)}`} />
        <Detail label="Party" value={`${date.party_size} people`} />
        {date.notes && <Detail label="Notes" value={date.notes} />}
      </div>

      {/* Booking confirmation */}
      {date.status === "booked" && date.booked_slot && (
        <div
          style={{
            background: "#0a2016",
            border: "1px solid #1e4a30",
            borderRadius: 10,
            padding: "10px 14px",
            fontSize: 14,
          }}
        >
          <span style={{ color: "#4caf7a", fontWeight: 700 }}>Reserved: </span>
          <span style={{ color: "#a8d8b8" }}>{fmtSlot(date.booked_slot)}</span>
          {date.reservation_id && (
            <span style={{ color: "#555", fontSize: 12, marginLeft: 10 }}>
              #{date.reservation_id}
            </span>
          )}
        </div>
      )}

      {/* Actions */}
      <div style={{ display: "flex", gap: 8 }}>
        {date.status === "draft" && (
          <button
            onClick={() => onMonitor(date.id)}
            disabled={busy}
            style={primaryBtnStyle}
          >
            Start Monitoring
          </button>
        )}
        {date.status === "failed" && (
          <button
            onClick={() => onMonitor(date.id)}
            disabled={busy}
            style={primaryBtnStyle}
          >
            Retry Monitoring
          </button>
        )}
        {date.status === "monitoring" && (
          <button
            onClick={() => onCancel(date.id)}
            disabled={busy}
            style={ghostBtnStyle}
          >
            Stop
          </button>
        )}
        {(date.status === "cancelled" || date.status === "failed" || date.status === "booked") && (
          <button
            onClick={() => onDelete(date.id)}
            disabled={busy}
            style={ghostBtnStyle}
          >
            Remove
          </button>
        )}
        {date.status === "draft" && (
          <button
            onClick={() => onDelete(date.id)}
            disabled={busy}
            style={ghostBtnStyle}
          >
            Delete
          </button>
        )}
      </div>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 1 }}>
      <span style={{ fontSize: 10, color: "#555", textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 700 }}>
        {label}
      </span>
      <span style={{ fontSize: 13, color: "#ccc" }}>{value}</span>
    </div>
  );
}

const oneAndDoneBadgeStyle: React.CSSProperties = {
  background: "#2a1a0e",
  border: "1px solid #f0a04a",
  borderRadius: 20,
  color: "#f0a04a",
  fontSize: 10,
  fontWeight: 700,
  letterSpacing: "0.06em",
  padding: "3px 8px",
  textTransform: "uppercase",
  whiteSpace: "nowrap",
};

const primaryBtnStyle: React.CSSProperties = {
  background: "#ff6b4a",
  border: "none",
  borderRadius: 8,
  color: "#fff",
  cursor: "pointer",
  fontSize: 13,
  fontWeight: 600,
  padding: "7px 16px",
};

const ghostBtnStyle: React.CSSProperties = {
  background: "transparent",
  border: "1px solid #2a2a2a",
  borderRadius: 8,
  color: "#666",
  cursor: "pointer",
  fontSize: 13,
  padding: "7px 14px",
};
