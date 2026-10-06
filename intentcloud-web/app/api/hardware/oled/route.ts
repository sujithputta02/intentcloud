import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    
    // Forward payload to local ESP32 bridge daemon
    try {
      const bridgeRes = await fetch("http://127.0.0.1:8765/push", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(1000), // non-blocking 1s timeout
      });
      if (bridgeRes.ok) {
        return NextResponse.json({ success: true, hardware: "esp32_oled_pushed" });
      }
    } catch {
      // Bridge daemon optional fallback
    }

    return NextResponse.json({ success: true, hardware: "simulated_only" });
  } catch (error) {
    return NextResponse.json({ success: false, error: String(error) }, { status: 500 });
  }
}

export async function GET() {
  try {
    const bridgeRes = await fetch("http://127.0.0.1:8765/", {
      signal: AbortSignal.timeout(1000),
    });
    if (bridgeRes.ok) {
      const data = await bridgeRes.json();
      return NextResponse.json(data);
    }
  } catch {}
  return NextResponse.json({ status: "bridge_offline" });
}
