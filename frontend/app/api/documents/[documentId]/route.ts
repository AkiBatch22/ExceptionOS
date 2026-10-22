import { getSession } from "../../../../lib/auth";
import { apiFetch } from "../../../../lib/api-fetch";

export async function GET(
  _request: Request,
  context: { params: Promise<{ documentId: string }> },
) {
  if (!(await getSession())) {
    return new Response("Unauthorized", { status: 401 });
  }

  const { documentId } = await context.params;
  if (!documentId.startsWith("DOC-")) {
    return new Response("Invalid document", { status: 400 });
  }

  const apiUrl = process.env.API_URL ?? "http://127.0.0.1:8000";
  try {
    const response = await apiFetch(
      `${apiUrl}/documents/${encodeURIComponent(documentId)}`,
      { cache: "no-store" },
    );
    if (!response.ok) {
      return new Response("Document not found", { status: response.status });
    }

    return new Response(response.body, {
      status: 200,
      headers: {
        "Content-Type": response.headers.get("Content-Type") ?? "application/pdf",
        "Content-Disposition": response.headers.get("Content-Disposition") ?? "inline",
        "Cache-Control": "private, no-store",
      },
    });
  } catch {
    return new Response("Unable to reach the ExceptionOS API", { status: 502 });
  }
}
