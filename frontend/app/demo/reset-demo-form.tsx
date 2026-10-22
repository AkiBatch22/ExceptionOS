"use client";

import { useActionState } from "react";

import { resetDemoData, type ResetState } from "./actions";


const initialState: ResetState = { error: null, message: null };

export default function ResetDemoForm() {
  const [state, action, pending] = useActionState(resetDemoData, initialState);

  return (
    <form action={action} className="resetForm">
      <label>
        <span>Type RESET to remove all demonstration data</span>
        <input autoComplete="off" name="confirmation" required />
      </label>
      <button className="button rejectButton" disabled={pending} type="submit">
        {pending ? "Resetting..." : "Reset demo data"}
      </button>
      {state.error && <p className="decisionError">{state.error}</p>}
      {state.message && <p className="correctionSuccess">{state.message}</p>}
    </form>
  );
}
