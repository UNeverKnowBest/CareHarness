"use client";

import { FormEvent, useEffect, useState } from "react";

type PublicEvent = {
  event_id: string;
  public_state: string;
  release_disposition: "allow" | "hold_for_review" | "system_failure";
  released_turn: { text: string } | null;
};

export function ParticipantConsole({ locale }: { locale: string }) {
  const [sessionId, setSessionId] = useState("demo-session-001");
  const [message, setMessage] = useState("");
  const [state, setState] = useState("ready");
  const [answers, setAnswers] = useState<string[]>([]);
  const [created, setCreated] = useState(false);
  const [sequence, setSequence] = useState(0);
  const api = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

  useEffect(() => {
    if (!created) return;
    const stream = new EventSource(`${api}/api/v1/sessions/${sessionId}/events`, {
      withCredentials: true,
    });
    stream.onmessage = (event) => {
      const update = JSON.parse(event.data) as PublicEvent;
      setState(update.public_state);
      if (update.release_disposition === "allow" && update.released_turn) {
        setAnswers((current) => [...current, update.released_turn!.text]);
      }
    };
    stream.addEventListener("answer_released", stream.onmessage as EventListener);
    stream.addEventListener("review_required", stream.onmessage as EventListener);
    stream.addEventListener("failed_closed", stream.onmessage as EventListener);
    return () => stream.close();
  }, [api, created, sessionId]);

  async function createSession() {
    const response = await fetch(`${api}/api/v1/sessions`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify({
        contract_version: "v1",
        session_id: sessionId,
        scenario_id: locale === "zh-CN" ? "seed-support-zh-v1" : "seed-support-en-v1",
        locale: locale === "zh-CN" ? "zh-CN" : "en-US",
        model_id: "deterministic-demo-v1",
        policy_version: "v1",
        plugin_profile_id: "profile-local-v1",
        evidence_registry_version: "v1",
        adult_synthetic_role_play: true,
      }),
    });
    if (!response.ok) throw new Error("Synthetic session could not be created");
    setCreated(true);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!message.trim()) return;
    setState("processing");
    const response = await fetch(`${api}/api/v1/sessions/${sessionId}/turns`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify({
        contract_version: "v1",
        request_id: crypto.randomUUID(),
        turn_id: `${sessionId}:participant:${crypto.randomUUID()}`,
        sequence,
        text: message,
      }),
    });
    if (!response.ok) throw new Error("Synthetic turn was not accepted");
    const projection = (await response.json()) as {
      released_turns: { sequence: number }[];
    };
    const latest = projection.released_turns.at(-1);
    setSequence((current) => Math.max(current + 1, (latest?.sequence ?? -1) + 1));
    setMessage("");
  }

  return (
    <section className="workspace participant-grid">
      <div className="hero-card">
        <p className="kicker">SYNTHETIC SESSION · {locale}</p>
        <h1>A calm space for a controlled rehearsal.</h1>
        <p className="lede">Choose a versioned scenario, write only fictional content, and observe release controls.</p>
        <label>Session ID<input value={sessionId} disabled={created} onChange={(e) => setSessionId(e.target.value)} /></label>
        <button className="secondary" type="button" disabled={created} onClick={createSession}>{created ? "Synthetic session ready" : "Create synthetic session"}</button>
      </div>
      <div className="conversation-card">
        <div className="status-row"><span className={`status-dot ${state}`} />Public state: {state}</div>
        <div className="messages" aria-live="polite">
          {answers.length ? answers.map((answer, index) => <article key={index}>{answer}</article>) : <p className="empty">No released answer yet. Quarantined content is never shown here.</p>}
        </div>
        <form onSubmit={submit}>
          <label>Synthetic role-play text<textarea value={message} onChange={(e) => setMessage(e.target.value)} maxLength={4000} /></label>
          <button type="submit" disabled={!created}>Submit synthetic turn <span>↗</span></button>
        </form>
      </div>
    </section>
  );
}
