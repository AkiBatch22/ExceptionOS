"use client";

import { useState } from "react";

import type { SuggestedCorrection } from "./actions";

export default function MemoryAwareInput({
  name,
  defaultValue,
  suggestion,
  required = false,
}: {
  name: string;
  defaultValue: string;
  suggestion?: SuggestedCorrection;
  required?: boolean;
}) {
  const [value, setValue] = useState(defaultValue);
  const [choice, setChoice] = useState<"pending" | "accepted" | "rejected">(
    "pending",
  );

  function applySuggestion() {
    if (!suggestion) return;
    setValue(suggestion.corrected_value);
    setChoice("accepted");
  }

  function undoSuggestion() {
    if (!suggestion) return;
    setValue(suggestion.original_value);
    setChoice("pending");
  }

  return (
    <>
      <input
        name={name}
        onChange={(event) => setValue(event.target.value)}
        required={required}
        value={value}
      />
      {suggestion && choice === "pending" && (
        <aside className="memorySuggestion">
          <strong>Suggested from this supplier&apos;s past corrections</strong>
          <span>
            {suggestion.original_value} → {suggestion.corrected_value}
          </span>
          <small>
            Previously accepted {suggestion.confirmation_count} time
            {suggestion.confirmation_count === 1 ? "" : "s"}. Nothing has been
            changed yet.
          </small>
          <div>
            <button onClick={applySuggestion} type="button">Apply suggestion</button>
            <button onClick={() => setChoice("rejected")} type="button">Ignore</button>
          </div>
        </aside>
      )}
      {suggestion && choice === "accepted" && (
        <aside className="memoryApplied">
          <strong>Applied from past supplier behavior</strong>
          <span>{suggestion.original_value} → {suggestion.corrected_value}</span>
          <button onClick={undoSuggestion} type="button">Undo</button>
        </aside>
      )}
      {suggestion && choice === "rejected" && (
        <aside className="memoryIgnored">
          <span>Suggestion ignored.</span>
          <button onClick={() => setChoice("pending")} type="button">Reconsider</button>
        </aside>
      )}
      {suggestion && choice === "accepted" && (
        <input name="accepted_pattern_ids" type="hidden" value={suggestion.pattern_id} />
      )}
      {suggestion && choice === "rejected" && (
        <input name="rejected_pattern_ids" type="hidden" value={suggestion.pattern_id} />
      )}
    </>
  );
}
