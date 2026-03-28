import { useState } from "react";
import { restaurantsApi, hitlistApi } from "../api/client";
import type { VenueResult } from "../types";

interface Props {
  onAdded: () => void;
  alreadyAddedIds: Set<string>;
}

export default function VenueSearch({ onAdded, alreadyAddedIds }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<VenueResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [adding, setAdding] = useState<string | null>(null);
  const [error, setError] = useState("");

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await restaurantsApi.search(query.trim());
      setResults(res);
      if (res.length === 0) setError("No venues found. Try a different search.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleAdd(venue: VenueResult) {
    setAdding(venue.venue_id);
    try {
      await hitlistApi.add(venue);
      onAdded();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Failed to add");
    } finally {
      setAdding(null);
    }
  }

  return (
    <div>
      <form onSubmit={handleSearch} style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search restaurants on Resy…"
          style={inputStyle}
        />
        <button type="submit" disabled={loading} style={btnPrimaryStyle}>
          {loading ? "Searching…" : "Search"}
        </button>
      </form>

      {error && <p style={{ color: "#e07070", fontSize: 13, marginBottom: 12 }}>{error}</p>}

      {results.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {results.map((v) => {
            const added = alreadyAddedIds.has(v.venue_id);
            return (
              <div key={v.venue_id} style={resultRowStyle}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: 15 }}>{v.name}</div>
                  <div style={{ color: "#888", fontSize: 13 }}>
                    {[v.location, v.cuisine].filter(Boolean).join(" · ")}
                  </div>
                </div>
                <button
                  onClick={() => handleAdd(v)}
                  disabled={added || adding === v.venue_id}
                  style={added ? btnDisabledStyle : btnSecondaryStyle}
                >
                  {added ? "On hitlist" : adding === v.venue_id ? "Adding…" : "+ Add"}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  flex: 1,
  background: "#1a1a1a",
  border: "1px solid #333",
  borderRadius: 8,
  color: "#f0ede8",
  fontSize: 14,
  padding: "10px 14px",
  outline: "none",
};

const btnPrimaryStyle: React.CSSProperties = {
  background: "#ff6b4a",
  border: "none",
  borderRadius: 8,
  color: "#fff",
  cursor: "pointer",
  fontSize: 14,
  fontWeight: 600,
  padding: "10px 20px",
  whiteSpace: "nowrap",
};

const btnSecondaryStyle: React.CSSProperties = {
  background: "#1e1e1e",
  border: "1px solid #444",
  borderRadius: 8,
  color: "#f0ede8",
  cursor: "pointer",
  fontSize: 13,
  fontWeight: 600,
  padding: "6px 14px",
  whiteSpace: "nowrap",
};

const btnDisabledStyle: React.CSSProperties = {
  ...btnSecondaryStyle,
  color: "#555",
  cursor: "default",
  border: "1px solid #2a2a2a",
};

const resultRowStyle: React.CSSProperties = {
  background: "#161616",
  border: "1px solid #222",
  borderRadius: 10,
  padding: "12px 16px",
  display: "flex",
  alignItems: "center",
  gap: 12,
};
