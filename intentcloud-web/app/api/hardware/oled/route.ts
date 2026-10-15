import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    let pushedLocally = false;
    let pushedPi = false;

    // 1. Forward to local ESP32 bridge daemon (USB serial attached to laptop)
    try {
      const bridgeRes = await fetch("http://127.0.0.1:8765/push", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(400),
      });
      if (bridgeRes.ok) {
        pushedLocally = true;
      }
    } catch {}

    // 2. Forward to local backend telemetry endpoint
    try {
      await fetch("http://127.0.0.1:8000/device/oled/push", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(400),
      });
    } catch {}

    // 3. Forward to Raspberry Pi OLED endpoint directly if reachable
    try {
      const piRes = await fetch("http://192.168.2.2:8000/device/oled/push", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(400),
      });
      if (piRes.ok) {
        pushedPi = true;
      }
    } catch {}

    return NextResponse.json({
      success: true,
      hardware: pushedLocally ? "esp32_usb_pushed" : pushedPi ? "pi_network_pushed" : "simulated_only",
      local_bridge: pushedLocally,
      pi_edge: pushedPi,
    });
  } catch (error) {
    return NextResponse.json({ success: false, error: String(error) }, { status: 500 });
  }
}

export async function GET() {
  // 1. Query local bridge first (direct USB serial hardware)
  try {
    const bridgeRes = await fetch("http://127.0.0.1:8765/", {
      signal: AbortSignal.timeout(400),
    });
    if (bridgeRes.ok) {
      const data = await bridgeRes.json();
      return NextResponse.json(data);
    }
  } catch {}

  // 2. Query local backend telemetry endpoint (127.0.0.1:8000)
  try {
    const localRes = await fetch("http://127.0.0.1:8000/device/telemetry", {
      signal: AbortSignal.timeout(400),
    });
    if (localRes.ok) {
      const data = await localRes.json();
      return NextResponse.json({
        status: "online",
        transport: "local_api",
        serial_connected: true,
        latest_state: data,
      });
    }
  } catch {}

  // 3. Fallback to Raspberry Pi telemetry
  try {
    const piRes = await fetch("http://192.168.2.2:8000/device/oled", {
      signal: AbortSignal.timeout(400),
    });
    if (piRes.ok) {
      const data = await piRes.json();
      return NextResponse.json({ status: "online", transport: "pi_network", latest_state: data });
    }
  } catch {}

  return NextResponse.json({ status: "bridge_offline" });
}
