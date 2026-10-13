"use client";

import { useActionState } from "react";

import {
  submitReviewDecision,
  type DecisionState,
} from "./actions";

const initialState: DecisionState = { error: null };

export default function DecisionForm({ reviewId }: { reviewId: string }) {
  const action = submitReviewDecision.bind(null, reviewId);
  const [state, formAction, isPending] = useActionState(action, initialState);

  return (
    <form action={formAction}>
      <div className="decisionButtons">
        <button
          className="button approveButton"
          disabled={isPending}
          name="decision"
          type="submit"
          value="approved"
        >
          {isPending ? "Submitting…" : "Approve"}
        </button>
        <button
          className="button rejectButton"
          disabled={isPending}
          name="decision"
          type="submit"
          value="rejected"
        >
          {isPending ? "Submitting…" : "Reject"}
        </button>
      </div>
      {state.error && <p className="decisionError">{state.error}</p>}
    </form>
  );
}
