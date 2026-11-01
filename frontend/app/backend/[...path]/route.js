// Same-origin bridge with an explicit deadline; do not use the dev rewrite proxy for long AI calls.
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

async function forward(request, context) {
  const { path } = await context.params;
  const segments = path || [];
  if (
    segments.some(
      (p) => p === "." || p === ".." || p.includes("/") || p.includes("\\"),
    )
  ) {
    return Response.json({ detail: "เส้นทาง API ไม่ถูกต้อง" }, { status: 400 });
  }
  const backend = process.env.BACKEND_URL || "http://127.0.0.1:8001";
  const target = new URL(
    backend.replace(/\/$/, "") +
      "/" +
      segments.map(encodeURIComponent).join("/"),
  );
  target.search = new URL(request.url).search;
  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    Number(process.env.BACKEND_TIMEOUT_MS || 600000),
  );
  try {
    const contentType = request.headers.get("content-type");
    const body =
      request.method === "GET" || request.method === "HEAD"
        ? undefined
        : await request.arrayBuffer();
    if (body && body.byteLength > 16000000)
      return Response.json(
        { detail: "ไฟล์หรือคำขอใหญ่เกิน 16 MB" },
        { status: 413 },
      );
    const upstream = await fetch(target, {
      method: request.method,
      headers: contentType ? { "Content-Type": contentType } : {},
      body,
      cache: "no-store",
      signal: controller.signal,
    });
    // Read the complete bounded API response before clearing the deadline, including TTS WAV.
    const bytes = await upstream.arrayBuffer();
    const headers = { "Cache-Control": "no-store" };
    for (const name of ["content-type", "x-tts-ms"]) {
      const value = upstream.headers.get(name);
      if (value) headers[name] = value;
    }
    return new Response(bytes, { status: upstream.status, headers });
  } catch (error) {
    return Response.json(
      {
        detail: controller.signal.aborted
          ? "Backend ประมวลผลเกินเวลารอ กรุณาตรวจ Terminal และเปิด session ใหม่ก่อนส่งคำตอบซ้ำ"
          : "ติดต่อ Backend ไม่ได้ ตรวจว่า python launch.py ยังทำงานอยู่ และดูข้อผิดพลาดใน Terminal",
      },
      { status: controller.signal.aborted ? 504 : 502 },
    );
  } finally {
    clearTimeout(timeout);
  }
}
export { forward as GET, forward as POST, forward as DELETE };
