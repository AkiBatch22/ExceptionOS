"use client";

import { useState, useTransition } from "react";

import { findFieldSource, type SourceResult } from "./source-actions";

export default function SourceLookup({
  documentId,
  fieldPath,
  value,
  context = "",
}: {
  documentId: string;
  fieldPath: string;
  value: string | number;
  context?: string;
}) {
  const [result, setResult] = useState<SourceResult | null>(null);
  const [isPending, startTransition] = useTransition();

  function requestSource() {
    startTransition(async () => {
      setResult(
        await findFieldSource({
          documentId,
          fieldPath,
          value: String(value),
          context,
        }),
      );
    });
  }

  return (
    <div className="sourceLookup">
      <button
        className="sourceButton"
        disabled={isPending}
        onClick={requestSource}
        type="button"
      >
        {isPending ? "Finding…" : result ? "Find again" : "Find source"}
      </button>
      {result && (
        <div className="sourceResult" aria-live="polite">
          {result.found ? (
            <>
              <p><strong>Page {result.page}:</strong> {result.snippet}</p>
              <a
                href={`/api/documents/${encodeURIComponent(documentId)}#page=${result.page}`}
                rel="noreferrer"
                target="_blank"
              >
                Open source page
              </a>
              {result.cached && <span className="cachedLabel">Cached result</span>}
            </>
          ) : (
            <p>{result.reason ?? "No reliable source match was found."}</p>
          )}
        </div>
      )}
    </div>
  );
}
