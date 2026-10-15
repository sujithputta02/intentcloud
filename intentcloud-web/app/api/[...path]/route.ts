import { NextRequest, NextResponse } from "next/server";

const PRIMARY_URL = process.env.API_PROXY_URL || "http://127.0.0.1:8000";
const LOCAL_FALLBACK_URL = "http://127.0.0.1:8000";

let lastPrimaryFailure = 0;
const FAILURE_COOLDOWN_MS = 8000; // Skip dead primary for 8s to guarantee 2ms response times

async function proxyRequest(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  const targetPath = path.join("/");
  const searchParams = req.nextUrl.search;

  // Determine which URL to try first
  const now = Date.now();
  const primaryIsDown = PRIMARY_URL !== LOCAL_FALLBACK_URL && (now - lastPrimaryFailure < FAILURE_COOLDOWN_MS);
  const targetUrlCandidates = primaryIsDown
    ? [LOCAL_FALLBACK_URL, PRIMARY_URL]
    : [PRIMARY_URL, LOCAL_FALLBACK_URL];

  // Forward all headers except host
  const headers = new Headers();
  req.headers.forEach((value, key) => {
    if (key.toLowerCase() !== "host") {
      headers.set(key, value);
    }
  });

  // Extract body once if needed
  let bodyBuffer: ArrayBuffer | null = null;
  if (req.method !== "GET" && req.method !== "HEAD") {
    try {
      bodyBuffer = await req.arrayBuffer();
    } catch {
      bodyBuffer = null;
    }
  }

  let lastError: any = null;

  for (const baseUrl of targetUrlCandidates) {
    const fullUrl = `${baseUrl}/${targetPath}${searchParams}`;
    const isPrimary = baseUrl === PRIMARY_URL;
    // Fast timeout for remote edge devices (800ms) to prevent slow UI stalls
    const timeoutMs = isPrimary && PRIMARY_URL !== LOCAL_FALLBACK_URL ? 800 : 30000;

    try {
      const init: RequestInit = {
        method: req.method,
        headers,
        signal: AbortSignal.timeout(timeoutMs),
      };

      if (bodyBuffer && bodyBuffer.byteLength > 0) {
        init.body = bodyBuffer.slice(0);
      }

      const upstreamRes = await fetch(fullUrl, init);

      // If primary succeeded, reset cooldown
      if (isPrimary) {
        lastPrimaryFailure = 0;
      }

      // Forward response headers
      const resHeaders = new Headers();
      upstreamRes.headers.forEach((val, key) => {
        if (!["transfer-encoding", "content-encoding"].includes(key.toLowerCase())) {
          resHeaders.set(key, val);
        }
      });
      resHeaders.set("X-Backend-Source", baseUrl);

      return new NextResponse(upstreamRes.body, {
        status: upstreamRes.status,
        statusText: upstreamRes.statusText,
        headers: resHeaders,
      });
    } catch (err: any) {
      lastError = err;
      if (isPrimary && PRIMARY_URL !== LOCAL_FALLBACK_URL) {
        lastPrimaryFailure = Date.now();
      }
      // If there's another candidate (e.g. local backend), try it immediately
      continue;
    }
  }

  // If both failed
  const isTimeout = lastError?.name === "TimeoutError" || lastError?.message?.includes("timeout");
  return NextResponse.json(
    {
      error: `Backend unavailable: ${lastError?.message || "Connection refused"}`,
      code: isTimeout ? "GATEWAY_TIMEOUT" : "BACKEND_UNAVAILABLE",
      timestamp: new Date().toISOString(),
    },
    { status: isTimeout ? 504 : 503 }
  );
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const DELETE = proxyRequest;
export const PATCH = proxyRequest;

