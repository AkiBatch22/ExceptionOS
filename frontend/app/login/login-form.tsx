"use client";

import { useActionState } from "react";

import { login, type LoginState } from "./actions";


const initialState: LoginState = { error: null };

export default function LoginForm({ nextPath }: { nextPath: string }) {
  const [state, action, pending] = useActionState(login, initialState);

  return (
    <form action={action} className="loginForm">
      <input name="next" type="hidden" value={nextPath} />
      <label>
        <span>Username</span>
        <input autoComplete="username" name="username" required />
      </label>
      <label>
        <span>Password</span>
        <input
          autoComplete="current-password"
          name="password"
          required
          type="password"
        />
      </label>
      <button className="button extractButton" disabled={pending} type="submit">
        {pending ? "Signing in..." : "Open private demo"}
      </button>
      {state.error && <p className="decisionError">{state.error}</p>}
    </form>
  );
}
