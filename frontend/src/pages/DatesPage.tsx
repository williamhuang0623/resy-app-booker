import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { datesApi, hitlistApi } from "../api/client";
import DateCard from "../components/DateCard";
import CreateDateModal from "../components/CreateDateModal";
import type { DateStatus } from "../types";

const STATUS_ORDER: DateStatus[] = ["monitoring", "draft", "booked", "failed", "cancelled"];

export default function DatesPage() {
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);

  const { data: dates = [], isLoading: datesLoading } = useQuery({
    queryKey: ["dates"],
    queryFn: datesApi.list,
    refetchInterval: 15_000, // auto-refresh every 15s to reflect booking updates
  });

  const { data: hitlist = [] } = useQuery({
    queryKey: ["hitlist"],
    queryFn: hitlistApi.list,
  });

  const monitorMutation = useMutation({
    mutationFn: datesApi.monitor,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dates"] }),
  });

  const cancelMutation = useMutation({
    mutationFn: datesApi.cancel,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dates"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: datesApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["dates"] }),
  });

  const busy =
    monitorMutation.isPending || cancelMutation.isPending || deleteMutation.isPending;

  const sorted = [...dates].sort(
    (a, b) => STATUS_ORDER.indexOf(a.status) - STATUS_ORDER.indexOf(b.status)
  );

  const activeCount = dates.filter((d) => d.status === "monitoring").length;
  const bookedCount = dates.filter((d) => d.status === "booked").length;

  return (
    <div>
      {/* Header */}
      <div
        style={{
          display: "flex",
          alignItems: "flex-start",
          justifyContent: "space-between",
          marginBottom: 28,
          gap: 16,
        }}
      >
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 6 }}>
            Dates
          </h1>
          <p style={{ color: "#777", fontSize: 14 }}>
            Set a restaurant + time window. We'll auto-book the moment a slot opens.
          </p>
        </div>

        <button
          onClick={() => setShowCreate(true)}
          disabled={hitlist.length === 0}
          title={hitlist.length === 0 ? "Add restaurants to your hitlist first" : undefined}
          style={{
            background: hitlist.length === 0 ? "#1a1a1a" : "#ff6b4a",
            border: "none",
            borderRadius: 10,
            color: hitlist.length === 0 ? "#444" : "#fff",
            cursor: hitlist.length === 0 ? "not-allowed" : "pointer",
            fontSize: 14,
            fontWeight: 700,
            padding: "10px 20px",
            whiteSpace: "nowrap",
            flexShrink: 0,
          }}
        >
          + New Date
        </button>
      </div>

      {/* Stats */}
      {dates.length > 0 && (
        <div style={{ display: "flex", gap: 16, marginBottom: 28 }}>
          <Stat label="Monitoring" value={activeCount} accent="#f0a04a" />
          <Stat label="Booked" value={bookedCount} accent="#4caf7a" />
          <Stat label="Total" value={dates.length} accent="#555" />
        </div>
      )}

      {/* Empty state */}
      {!datesLoading && dates.length === 0 && (
        <div
          style={{
            background: "#111",
            border: "1px dashed #222",
            borderRadius: 16,
            padding: "48px 32px",
            textAlign: "center",
          }}
        >
          <div style={{ fontSize: 32, marginBottom: 12 }}>📅</div>
          <div style={{ fontWeight: 600, marginBottom: 8 }}>No dates yet</div>
          <div style={{ color: "#666", fontSize: 14, marginBottom: 20 }}>
            {hitlist.length === 0
              ? "First, add restaurants to your hitlist."
              : "Create your first date to start auto-booking."}
          </div>
          {hitlist.length > 0 && (
            <button onClick={() => setShowCreate(true)} style={primaryBtnStyle}>
              Create a Date
            </button>
          )}
        </div>
      )}

      {/* Date cards */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {sorted.map((d) => (
          <DateCard
            key={d.id}
            date={d}
            onMonitor={(id) => monitorMutation.mutate(id)}
            onCancel={(id) => cancelMutation.mutate(id)}
            onDelete={(id) => deleteMutation.mutate(id)}
            busy={busy}
          />
        ))}
      </div>

      {/* Create modal */}
      {showCreate && hitlist.length > 0 && (
        <CreateDateModal
          hitlist={hitlist}
          onCreated={() => qc.invalidateQueries({ queryKey: ["dates"] })}
          onClose={() => setShowCreate(false)}
        />
      )}
    </div>
  );
}

function Stat({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent: string;
}) {
  return (
    <div
      style={{
        background: "#111",
        border: "1px solid #1e1e1e",
        borderRadius: 10,
        padding: "12px 18px",
        minWidth: 90,
      }}
    >
      <div style={{ fontSize: 24, fontWeight: 700, color: accent }}>{value}</div>
      <div style={{ fontSize: 11, color: "#555", textTransform: "uppercase", letterSpacing: "0.06em", fontWeight: 700 }}>
        {label}
      </div>
    </div>
  );
}

const primaryBtnStyle: React.CSSProperties = {
  background: "#ff6b4a",
  border: "none",
  borderRadius: 10,
  color: "#fff",
  cursor: "pointer",
  fontSize: 14,
  fontWeight: 700,
  padding: "10px 24px",
};
