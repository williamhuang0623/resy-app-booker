import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { authApi } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const fn = mode === "login" ? authApi.login : authApi.register;
      const { access_token } = await fn(email.trim(), password);
      await login(access_token);
      navigate("/");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#0a0a0a",
        padding: 20,
      }}
    >
      <div
        style={{
          background: "#111",
          border: "1px solid #222",
          borderRadius: 16,
          padding: "40px 36px",
          width: "100%",
          maxWidth: 400,
        }}
      >
        {/* Logo */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.03em" }}>
            Resy Booker
          </div>
          <div style={{ fontSize: 13, color: "#555", marginTop: 4 }}>
            auto-book hard-to-get tables
          </div>
        </div>

        {/* Mode toggle */}
        <div
          style={{
            display: "flex",
            background: "#0a0a0a",
            borderRadius: 8,
            padding: 3,
            marginBottom: 28,
          }}
        >
          {(["login", "register"] as const).map((m) => (
            <button
              key={m}
              onClick={() => { setMode(m); setError(""); }}
              style={{
                flex: 1,
                background: mode === m ? "#1e1e1e" : "transparent",
                border: "none",
                borderRadius: 6,
                color: mode === m ? "#fff" : "#555",
                cursor: "pointer",
                fontSize: 13,
                fontWeight: 600,
                padding: "7px 0",
                textTransform: "capitalize",
                transition: "all 0.15s",
              }}
            >
              {m === "login" ? "Sign in" : "Create account"}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit}>
          <label style={labelStyle}>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
            style={inputStyle}
          />

          <label style={{ ...labelStyle, marginTop: 16 }}>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
            minLength={6}
            style={inputStyle}
          />

          {error && (
            <div
              style={{
                background: "#2a0a0a",
                border: "1px solid #5a1a1a",
                borderRadius: 8,
                color: "#ff6b6b",
                fontSize: 13,
                marginTop: 16,
                padding: "10px 14px",
              }}
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            style={{
              background: submitting ? "#333" : "#ff6b4a",
              border: "none",
              borderRadius: 10,
              color: "#fff",
              cursor: submitting ? "not-allowed" : "pointer",
              fontSize: 15,
              fontWeight: 700,
              marginTop: 24,
              padding: "13px 0",
              width: "100%",
              transition: "background 0.15s",
            }}
          >
            {submitting
              ? mode === "login"
                ? "Signing in…"
                : "Creating account…"
              : mode === "login"
              ? "Sign in"
              : "Create account"}
          </button>
        </form>
      </div>
    </div>
  );
}

const labelStyle: React.CSSProperties = {
  display: "block",
  color: "#888",
  fontSize: 12,
  fontWeight: 600,
  letterSpacing: "0.06em",
  marginBottom: 6,
  textTransform: "uppercase",
};

const inputStyle: React.CSSProperties = {
  background: "#0a0a0a",
  border: "1px solid #2a2a2a",
  borderRadius: 8,
  color: "#fff",
  fontSize: 14,
  outline: "none",
  padding: "11px 14px",
  width: "100%",
  boxSizing: "border-box",
};
