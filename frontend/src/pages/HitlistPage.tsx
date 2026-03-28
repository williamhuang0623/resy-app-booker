import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { hitlistApi } from "../api/client";
import VenueSearch from "../components/VenueSearch";

export default function HitlistPage() {
  const qc = useQueryClient();
  const { data: hitlist = [], isLoading } = useQuery({
    queryKey: ["hitlist"],
    queryFn: hitlistApi.list,
  });

  const removeMutation = useMutation({
    mutationFn: hitlistApi.remove,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["hitlist"] }),
  });

  const alreadyAddedIds = new Set(hitlist.map((r) => r.venue_id));

  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <h1 style={headingStyle}>Restaurant Hitlist</h1>
        <p style={subStyle}>
          Restaurants you want to eat at. Add them here, then create a Date to
          start auto-booking.
        </p>
      </div>

      {/* Search */}
      <section style={sectionStyle}>
        <h2 style={sectionHeadingStyle}>Find a Restaurant</h2>
        <VenueSearch
          onAdded={() => qc.invalidateQueries({ queryKey: ["hitlist"] })}
          alreadyAddedIds={alreadyAddedIds}
        />
      </section>

      {/* Hitlist */}
      <section style={sectionStyle}>
        <h2 style={sectionHeadingStyle}>
          Your Hitlist
          {hitlist.length > 0 && (
            <span style={{ color: "#555", fontWeight: 400, marginLeft: 8 }}>
              ({hitlist.length})
            </span>
          )}
        </h2>

        {isLoading && <p style={{ color: "#666", fontSize: 14 }}>Loading…</p>}

        {!isLoading && hitlist.length === 0 && (
          <p style={{ color: "#555", fontSize: 14 }}>
            Your hitlist is empty. Search above to add restaurants.
          </p>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {hitlist.map((r) => (
            <div key={r.id} style={cardStyle}>
              <div style={{ flex: 1 }}>
                <div style={{ fontWeight: 700, fontSize: 16 }}>{r.name}</div>
                <div style={{ color: "#777", fontSize: 13, marginTop: 3 }}>
                  {[r.location, r.cuisine].filter(Boolean).join(" · ")}
                </div>
              </div>

              <button
                onClick={() => removeMutation.mutate(r.id)}
                disabled={removeMutation.isPending}
                style={removeStyle}
                title="Remove from hitlist"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

const headingStyle: React.CSSProperties = {
  fontSize: 26,
  fontWeight: 700,
  letterSpacing: "-0.02em",
  marginBottom: 6,
};
const subStyle: React.CSSProperties = { color: "#777", fontSize: 14 };

const sectionStyle: React.CSSProperties = { marginBottom: 40 };

const sectionHeadingStyle: React.CSSProperties = {
  fontSize: 14,
  fontWeight: 700,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  color: "#666",
  marginBottom: 14,
};

const cardStyle: React.CSSProperties = {
  background: "#161616",
  border: "1px solid #222",
  borderRadius: 12,
  padding: "14px 18px",
  display: "flex",
  alignItems: "center",
  gap: 12,
};

const removeStyle: React.CSSProperties = {
  background: "transparent",
  border: "none",
  color: "#555",
  cursor: "pointer",
  fontSize: 16,
  padding: 4,
  lineHeight: 1,
};
