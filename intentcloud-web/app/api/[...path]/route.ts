import { NextRequest, NextResponse } from "next/server";

const BACKEND_URL = process.env.API_PROXY_URL || "http://192.168.2.2:8000";

async function proxyRequest(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  const targetPath = path.join("/");
  const searchParams = req.nextUrl.search;
  const targetUrl = `${BACKEND_URL}/${targetPath}${searchParams}`;

  // Forward all headers except host
  const headers = new Headers();
  req.headers.forEach((value, key) => {
    if (key.toLowerCase() !== "host") {
      headers.set(key, value);
    }
  });

  const init: RequestInit = {
    method: req.method,
    headers,
    signal: AbortSignal.timeout(60000), // 60s timeout for edge device processing
  };

  // Only attach body for methods that allow it
  if (req.method !== "GET" && req.method !== "HEAD") {
    try {
      const bodyBlob = await req.blob();
      if (bodyBlob.size > 0) {
        init.body = bodyBlob;
      }
    } catch {
      // No body or already consumed
    }
  }

  try {
    const upstreamRes = await fetch(targetUrl, init);

    // Forward upstream response headers
    const resHeaders = new Headers();
    upstreamRes.headers.forEach((val, key) => {
      // Do not forward transfer-encoding or content-encoding if decompressed
      if (!["transfer-encoding", "content-encoding"].includes(key.toLowerCase())) {
        resHeaders.set(key, val);
      }
    });

    return new NextResponse(upstreamRes.body, {
      status: upstreamRes.status,
      statusText: upstreamRes.statusText,
      headers: resHeaders,
    });
  } catch (error: any) {
    const isTimeout = error?.name === "TimeoutError" || error?.message?.includes("timeout");
    const statusCode = isTimeout ? 504 : 503;
    const errorMsg = isTimeout
      ? "Gateway Timeout: Edge device search took longer than 60s"
      : `Edge device connection failed (${error?.message || "ECONNRESET"})`;

    return NextResponse.json(
      {
        error: errorMsg,
        code: error?.code || (isTimeout ? "GATEWAY_TIMEOUT" : "BACKEND_UNAVAILABLE"),
        timestamp: new Date().toISOString(),
      },
      { status: statusCode }
    );
  }
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PUT = proxyRequest;
export const DELETE = proxyRequest;
export const PATCH = proxyRequest;
