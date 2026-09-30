import { NextRequest } from "next/server";

// Read at request time (not build time) so the container's env is honored.
function apiBase(): string {
  return process.env.API_INTERNAL_URL || "http://localhost:8000";
}

// Never cache proxied API calls.
export const dynamic = "force-dynamic";

async function proxy(req: NextRequest, path: string[]): Promise<Response> {
  const target = `${apiBase()}/${path.join("/")}${req.nextUrl.search}`;
  const hasBody = req.method !== "GET" && req.method !== "HEAD";

  try {
    const upstream = await fetch(target, {
      method: req.method,
      headers: {
        "content-type": req.headers.get("content-type") || "application/json",
      },
      body: hasBody ? await req.text() : undefined,
      cache: "no-store",
    });
    const body = await upstream.text();
    return new Response(body, {
      status: upstream.status,
      headers: {
        "content-type":
          upstream.headers.get("content-type") || "application/json",
      },
    });
  } catch {
    return Response.json(
      { detail: `Cannot reach API at ${apiBase()}` },
      { status: 502 },
    );
  }
}

type Ctx = { params: { path: string[] } };

export function GET(req: NextRequest, { params }: Ctx) {
  return proxy(req, params.path);
}
export function POST(req: NextRequest, { params }: Ctx) {
  return proxy(req, params.path);
}
export function PUT(req: NextRequest, { params }: Ctx) {
  return proxy(req, params.path);
}
export function DELETE(req: NextRequest, { params }: Ctx) {
  return proxy(req, params.path);
}
