import { NextRequest, NextResponse } from "next/server";

const apiUrl = process.env.FARODOCS_API_URL ?? "http://127.0.0.1:8000";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const target = new URL(`${apiUrl}/${path.join("/")}`);
  target.search = request.nextUrl.search;
  const headers = new Headers();
  const type = request.headers.get("content-type");
  if (type) headers.set("content-type", type);
  try {
    const body = request.method === "GET" || request.method === "HEAD" ? undefined : request.body;
    const response = await fetch(target, {
      method: request.method,
      headers,
      body,
      duplex: body ? "half" : undefined,
      cache: "no-store",
    } as RequestInit & { duplex?: "half" });
    const outgoing = new Headers();
    for (const name of ["content-type", "content-disposition"]) {
      const value = response.headers.get(name);
      if (value) outgoing.set(name, value);
    }
    return new NextResponse(response.body, { status: response.status, headers: outgoing });
  } catch {
    return NextResponse.json({ detail: "Local API is unavailable" }, { status: 503 });
  }
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
