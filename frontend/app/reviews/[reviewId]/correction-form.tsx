"use client";

import { useActionState, useState } from "react";

import { submitReviewCorrection, type CorrectionState } from "./actions";

export type CorrectionOption = {
  label: string;
  path: string;
  value: string;
  rememberable: boolean;
};

const initialState: CorrectionState = { error: null, message: null };

export default function CorrectionForm({
  reviewId,
  options,
}: {
  reviewId: string;
  options: CorrectionOption[];
}) {
  const action = submitReviewCorrection.bind(null, reviewId);
  const [state, formAction, pending] = useActionState(action, initialState);
  const [selectedPath, setSelectedPath] = useState(options[0]?.path ?? "");
  const selected = options.find((option) => option.path === selectedPath);
  const [value, setValue] = useState(selected?.value ?? "");

  function selectField(path: string) {
    setSelectedPath(path);
    setValue(options.find((option) => option.path === path)?.value ?? "");
  }

  return (
    <form action={formAction} className="correctionForm">
      <label>
        <span>Field to correct</span>
        <select
          name="field_path"
          onChange={(event) => selectField(event.target.value)}
          value={selectedPath}
        >
          {options.map((option) => (
            <option key={option.path} value={option.path}>{option.label}</option>
          ))}
        </select>
      </label>
      <label>
        <span>Corrected value</span>
        <input
          name="corrected_value"
          onChange={(event) => setValue(event.target.value)}
          required
          value={value}
        />
      </label>
      <p className="correctionNote">
        Applying once changes only this review. Remembering stores a suggestion for
        future orders from this supplier and never changes them silently.
      </p>
      <div className="correctionButtons">
        <button className="button correctionOnce" disabled={pending} name="remember" value="false">
          {pending ? "Applying…" : "Apply correction once"}
        </button>
        <button
          className="button rememberCorrection"
          disabled={pending || !selected?.rememberable}
          name="remember"
          value="true"
        >
          Apply and remember for supplier
        </button>
      </div>
      {!selected?.rememberable && (
        <small>Only customer, ship-to, and SKU corrections can be remembered.</small>
      )}
      {state.error && <p className="decisionError">{state.error}</p>}
      {state.message && <p className="correctionSuccess">{state.message}</p>}
    </form>
  );
}
