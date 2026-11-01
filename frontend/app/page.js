"use client";
import { useState, useEffect, useRef } from "react";
import {
  list,
  profileData,
  analysisData,
  interviewData,
  reportData,
  apiError,
} from "../lib/data.mjs";

const API = "/backend";
async function request(path, body, method = "POST") {
  let r;
  try {
    r = await fetch(API + path, {
      method,
      cache: "no-store",
      headers:
        body instanceof FormData ? {} : { "Content-Type": "application/json" },
      ...(body === undefined
        ? {}
        : { body: body instanceof FormData ? body : JSON.stringify(body) }),
    });
  } catch {
    throw Error("ติดต่อเว็บไม่ได้ ตรวจว่า python launch.py ยังเปิดอยู่");
  }
  let value;
  try {
    value = await r.json();
  } catch {
    throw Error(
      `Backend ส่งข้อมูลที่อ่านไม่ได้ (HTTP ${r.status}) กรุณาตรวจ Terminal`,
    );
  }
  if (!r.ok) throw Error(apiError(value, r.status));
  return value;
}

function exportJSON(name, value) {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
const tabs = [
  ["home", "⌂", "เริ่มต้น"],
  ["prepare", "▤", "เตรียมเรซูเม่"],
  ["interview", "◉", "ซ้อมสัมภาษณ์"],
  ["faq", "☷", "ถามเรื่องสหกิจ"],
  ["results", "✓", "คำแนะนำและประวัติ"],
];
const demo = {
  company: "Example Company (สมมติ)",
  role: "Backend Developer Intern",
  resume:
    "นักศึกษาวิทยาการคอมพิวเตอร์\nโครงงานตัวอย่าง: พัฒนา Backend ด้วย Python และ FastAPI สร้าง REST API และใช้ GitHub ทำงานร่วมกับทีม\nรับผิดชอบเขียน endpoint และทดสอบข้อมูลตัวอย่าง 10 รายการ",
  role_brief: "Python, FastAPI, SQL, Git, REST API",
  language: "th",
  role_provenance: "User-provided Role Brief",
  consent: false,
};
const sampleFAQs = [
  {
    question: "ต้องเตรียมเอกสารอะไรบ้าง",
    answer:
      "ข้อมูลสมมติ: เรซูเม่ ใบแสดงผลการเรียน และแบบฟอร์มของหลักสูตร โปรดตรวจรายการจริงกับผู้ประสานงาน",
    source: "FAQ สมมติสำหรับทดสอบ ไม่ใช่ประกาศ BU",
    page: "1",
    version: "demo",
    approved: false,
    demo: true,
  },
  {
    question: "เกรด GPA เท่าไหร่ สมัครสหกิจได้",
    answer:
      "ชุดสาธิตไม่มีเกณฑ์ GPA ที่รับรอง กรุณาตรวจประกาศฉบับปัจจุบันหรือติดต่อผู้ประสานงาน",
    source: "FAQ สมมติสำหรับทดสอบ ไม่ใช่ประกาศ BU",
    page: "1",
    version: "demo",
    approved: false,
    demo: true,
  },
];

export default function App() {
  const [tab, setTab] = useState("home"),
    [mode, setMode] = useState("baseline"),
    [health, setHealth] = useState(null),
    [busy, setBusy] = useState(""),
    [error, setError] = useState(""),
    [notice, setNotice] = useState("");
  const [form, setForm] = useState({
      ...demo,
      company: "",
      role: "",
      role_brief: "",
      resume: "",
      consent: false,
    }),
    [sid, setSid] = useState(""),
    [session, setSession] = useState(null),
    [sessions, setSessions] = useState([]),
    [analysis, rawSetAnalysis] = useState(null),
    [profile, rawSetProfile] = useState(null);
  const [url, setUrl] = useState(""),
    [sourceText, setSourceText] = useState(""),
    [verified, setVerified] = useState(false),
    [summarize, setSummarize] = useState(false),
    [candidates, setCandidates] = useState([]);
  const [interview, rawSetInterview] = useState(null),
    [answer, setAnswer] = useState(""),
    [recording, setRecording] = useState(false),
    [autoSpeak, setAutoSpeak] = useState(false),
    [audioFallback, setAudioFallback] = useState(false),
    [report, rawSetReport] = useState(null),
    [audioMetrics, setAudioMetrics] = useState({
      stt_ms: 0,
      tts_ms: 0,
      stt_engine: "typed",
    });
  const [question, setQuestion] = useState(""),
    [messages, setMessages] = useState([]),
    [allowDemo, setAllowDemo] = useState(false),
    [faqRows, setFaqRows] = useState([]),
    [importText, setImportText] = useState("");
  const [reference, setReference] = useState(""),
    [hypothesis, setHypothesis] = useState(""),
    [speechMetric, setSpeechMetric] = useState(null),
    [truth, setTruth] = useState(""),
    [skillMetric, setSkillMetric] = useState(null);
  const setProfile = (value) => rawSetProfile(profileData(value));
  const setAnalysis = (value) => rawSetAnalysis(analysisData(value));
  const setInterview = (value) => rawSetInterview(interviewData(value));
  const setReport = (value) => rawSetReport(reportData(value));
  const taskLock = useRef(false),
    recordTimer = useRef(null),
    audioURL = useRef(null);
  function stopAudio() {
    audio.current?.pause();
    if (audioURL.current) {
      URL.revokeObjectURL(audioURL.current);
      audioURL.current = null;
    }
    window.speechSynthesis?.cancel();
  }
  function resetDraft(withDemo = false) {
    stopAudio();
    activeSid.current = "";
    setSid("");
    setSession(null);
    setProfile(null);
    setAnalysis(null);
    setInterview(null);
    setReport(null);
    setUrl("");
    setSourceText("");
    setVerified(false);
    setCandidates([]);
    setAnswer("");
    setSkillMetric(null);
    setTruth("");
    setAudioMetrics({ stt_ms: 0, tts_ms: 0, stt_engine: "typed" });
    if (withDemo) setForm({ ...demo });
    setNotice(
      withDemo
        ? "โหลดข้อมูลสมมติแล้ว ยืนยันสิทธิ์ก่อนสร้าง session"
        : "สร้างรายการใหม่ได้แล้ว",
    );
  }
  const errorRef = useRef(null);
  const media = useRef(null),
    parts = useRef([]),
    audio = useRef(null),
    stream = useRef(null),
    answerRef = useRef(null),
    activeSid = useRef("");
  useEffect(() => {
    activeSid.current = sid;
  }, [sid]);
  useEffect(() => {
    if (error)
      errorRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [error]);
  useEffect(() => {
    if (mode === "baseline") setSummarize(false);
  }, [mode]);
  useEffect(() => {
    task("ตรวจ Backend", async () => {
      const [h, ss, ff] = await Promise.all([
        request("/health", undefined, "GET"),
        request("/sessions", undefined, "GET"),
        request("/faq", undefined, "GET"),
      ]);
      setHealth(h);
      setSessions(list(ss));
      setFaqRows(list(ff));
    });
  }, []);
  useEffect(
    () => () => {
      clearTimeout(recordTimer.current);
      if (media.current) {
        media.current.onstop = null;
        if (media.current.state !== "inactive") media.current.stop();
      }
      stream.current?.getTracks().forEach((t) => t.stop());
      stopAudio();
    },
    [],
  );
  async function task(label, fn) {
    if (taskLock.current) return;
    taskLock.current = true;
    setBusy(label);
    setError("");
    setNotice("");
    try {
      return await fn();
    } catch (e) {
      setError(e.message || "เกิดข้อผิดพลาด");
    } finally {
      taskLock.current = false;
      setBusy("");
    }
  }
  function field(key, value) {
    setForm((f) => ({ ...f, [key]: value }));
  }
  async function refresh() {
    const [ss, ff] = await Promise.all([
      request("/sessions", undefined, "GET"),
      request("/faq", undefined, "GET"),
    ]);
    setSessions(list(ss));
    setFaqRows(list(ff));
  }
  async function loadSession(id) {
    const s = await request("/sessions/" + id, undefined, "GET");
    stopAudio();
    activeSid.current = id;
    setSid(id);
    setSession(s);
    setForm({
      company: s.company,
      role: s.role,
      resume: s.resume,
      role_brief: s.role_brief,
      language: s.language,
      role_provenance: s.role_provenance || "User-provided Role Brief",
      consent: s.consent,
    });
    setAnalysis(s.analysis);
    setProfile(s.profile);
    setInterview(s.interview);
    if (s.interview) setMode(s.interview.mode);
    setReport(s.interview?.report || null);
    setUrl(s.profile?.source?.url || "");
    setSourceText(s.profile?.source?.text || "");
    setVerified(s.profile?.human_verified === true);
    setCandidates([]);
    setSkillMetric(null);
    setAnswer("");
    setAudioMetrics({ stt_ms: 0, tts_ms: 0, stt_engine: "typed" });
  }
  async function create() {
    if (!form.consent) throw Error("ยืนยันสิทธิ์และความยินยอมก่อนสร้างรายการ");
    for (const key of ["company", "role", "resume", "role_brief"])
      if (!form[key]?.trim())
        throw Error("กรอกชื่อบริษัท ตำแหน่ง Resume และ Role Brief ให้ครบ");
    const data = await request("/sessions", form);
    activeSid.current = data.id;
    setSid(data.id);
    setSession(data.session);
    setProfile(null);
    setAnalysis(null);
    setInterview(null);
    setReport(null);
    setCandidates([]);
    setSkillMetric(null);
    setAudioMetrics({ stt_ms: 0, tts_ms: 0, stt_engine: "typed" });
    await refresh();
    setNotice("สร้าง session แล้ว ข้อมูลจะอยู่ในเครื่องตามระยะเวลาที่กำหนด");
  }
  function requireSession() {
    if (!sid) throw Error("เพิ่มเรซูเม่และบันทึกข้อมูลก่อนเริ่มฝึก");
  }
  async function parseFile(e) {
    const f = e.target.files?.[0];
    if (!f) return;
    if (!form.consent) {
      e.target.value = "";
      setError("ยืนยันสิทธิ์และความยินยอมก่อนนำเข้าไฟล์");
      return;
    }
    await task("อ่านเรซูเม่", async () => {
      const d = new FormData();
      d.append("file", f);
      const r = await request("/resume/parse", d);
      field("resume", r.text);
      setNotice(
        r.warning + (r.truncated ? " · ข้อความถูกตัดที่ 60,000 ตัวอักษร" : ""),
      );
    });
  }
  async function saveProfile() {
    requireSession();
    const p = await request(`/sessions/${sid}/profile`, {
      url,
      source_text: sourceText,
      human_verified: verified,
      summarize_with_llm: summarize,
    });
    setProfile(p);
    setSourceText(p.source?.text || "");
    setVerified(p.human_verified === true);
    setNotice(
      p.summary_warning ||
        "บันทึก Company / Role Profile แล้ว กรุณาตรวจข้อความและแหล่งอ้างอิง",
    );
  }
  async function runAnalysis() {
    requireSession();
    const a = await request(`/sessions/${sid}/analyze`, { mode });
    setAnalysis(a);
  }
  async function startInterview() {
    requireSession();
    if (
      interview?.turns.length &&
      !confirm(
        "เริ่มรอบใหม่จะทับรอบสัมภาษณ์เดิมใน session นี้ ต้องการเริ่มใหม่หรือไม่?",
      )
    )
      return;
    stopAudio();
    const r = await request(`/sessions/${sid}/interview/start`, { mode });
    setInterview(r);
    setReport(null);
    setAnswer("");
    setAudioMetrics({ stt_ms: 0, tts_ms: 0, stt_engine: "typed" });
    if (autoSpeak) await speakQuestion();
  }
  async function speakQuestion() {
    requireSession();
    stopAudio();
    if (audioFallback) {
      const data = await request("/sessions/" + sid, undefined, "GET");
      if (!window.speechSynthesis) throw Error("เครื่องนี้ไม่มี browser TTS");
      if (!data.interview?.question || data.interview.done)
        throw Error("ไม่มีคำถามที่กำลังใช้งาน");
      const u = new SpeechSynthesisUtterance(data.interview.question);
      u.lang = data.language === "th" ? "th-TH" : "en-US";
      u.onerror = (e) => {
        if (!["canceled", "interrupted"].includes(e.error))
          setError(
            "Browser TTS อ่านไม่ได้ ตรวจเสียงที่ติดตั้งและลองกดฟังคำถามอีกครั้ง",
          );
      };
      speechSynthesis.speak(u);
      setAudioMetrics((m) => ({ ...m, tts_ms: 0 }));
      setNotice("ใช้ Browser TTS สำรอง ไม่ถือเป็นหลักฐานการรัน Piper");
      return;
    }
    const r = await fetch(API + `/sessions/${sid}/voice/question`, {
      method: "POST",
    });
    if (!r.ok) {
      let e;
      try {
        e = await r.json();
      } catch {}
      throw Error(apiError(e, r.status));
    }
    const blob = await r.blob();
    const objectURL = URL.createObjectURL(blob);
    audioURL.current = objectURL;
    const player = new Audio(objectURL);
    audio.current = player;
    const release = () => {
      URL.revokeObjectURL(objectURL);
      if (audioURL.current === objectURL) audioURL.current = null;
    };
    player.onended = release;
    player.onerror = release;
    try {
      await player.play();
      setAudioMetrics((m) => ({
        ...m,
        tts_ms: Number(r.headers.get("X-TTS-MS") || 0),
      }));
    } catch {
      release();
      throw Error("เบราว์เซอร์ยังไม่อนุญาตเล่นเสียง ลองกดฟังคำถามอีกครั้ง");
    }
  }
  async function submitAnswer() {
    requireSession();
    if (!answer.trim()) throw Error("กรุณาตอบก่อนส่ง");
    stopAudio();
    const r = await request(`/sessions/${sid}/interview/answer`, {
      answer,
      question_id: interview?.question_id,
      ...audioMetrics,
    });
    setInterview(r);
    setAnswer("");
    setAudioMetrics({ stt_ms: 0, tts_ms: 0, stt_engine: "typed" });
    if (r.done) {
      setNotice("ครบคำถามแล้ว กดสร้างรายงานเพื่อประเมิน");
      await refresh();
    } else if (autoSpeak) await speakQuestion();
  }
  async function record() {
    if (recording) {
      if (media.current?.state === "recording") media.current.stop();
      return;
    }
    requireSession();
    if (!interview || interview.done)
      throw Error("เริ่มรอบสัมภาษณ์ก่อนอัดเสียง");
    if (!health?.packages?.["faster-whisper"])
      throw Error(
        "ยังไม่ได้ติดตั้งถอดเสียง: รัน python launch.py --install-ai stt แล้ว python launch.py --prepare-models stt จากนั้นเปิดเว็บใหม่",
      );
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder)
      throw Error(
        "เบราว์เซอร์นี้ไม่รองรับอัดเสียง ใช้ Chrome/Edge ผ่าน localhost และอนุญาตไมค์",
      );
    stopAudio();
    const currentSid = sid;
    try {
      stream.current = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });
      const chunks = [];
      const type = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/mp4",
        "audio/ogg",
      ].find((t) => MediaRecorder.isTypeSupported(t));
      const rec = new MediaRecorder(
        stream.current,
        type ? { mimeType: type } : undefined,
      );
      media.current = rec;
      const release = () => {
        clearTimeout(recordTimer.current);
        stream.current?.getTracks().forEach((t) => t.stop());
        setRecording(false);
      };
      rec.ondataavailable = (e) => {
        if (e.data.size) chunks.push(e.data);
      };
      rec.onerror = () => {
        rec.onstop = null;
        release();
        setError("บันทึกเสียงไม่สำเร็จ ตรวจไมค์และลองใหม่");
      };
      rec.onstop = async () => {
        release();
        const mime = rec.mimeType;
        const ext = mime.includes("mp4")
          ? "mp4"
          : mime.includes("ogg")
            ? "ogg"
            : "webm";
        const blob = new Blob(chunks, { type: mime });
        if (!blob.size || blob.size > 15000000) {
          setError("เสียงว่างหรือใหญ่เกิน 15 MB กรุณาอัดใหม่");
          return;
        }
        await task("faster-whisper กำลังถอดเสียง", async () => {
          const d = new FormData();
          d.append("file", blob, "answer." + ext);
          d.append("language", session?.language || form.language);
          const out = await request("/voice/transcribe", d);
          if (activeSid.current !== currentSid) return;
          if (!out.transcript?.trim())
            throw Error(
              "ไม่พบคำพูดในเสียง ตรวจไมค์ ระดับเสียง และภาษาที่เลือกแล้วลองใหม่",
            );
          setAnswer((prev) => (prev + " " + out.transcript).trim());
          setAudioMetrics((m) => ({
            ...m,
            stt_ms: m.stt_ms + out.stt_ms,
            stt_engine: out.engine,
          }));
          setNotice("ถอดเสียงแล้ว ตรวจและแก้ข้อความก่อนส่งคำตอบ");
        });
      };
      rec.start();
      setRecording(true);
      recordTimer.current = setTimeout(() => {
        if (rec.state === "recording") rec.stop();
      }, 180000);
    } catch (e) {
      stream.current?.getTracks().forEach((t) => t.stop());
      setRecording(false);
      if (e.name === "NotAllowedError")
        throw Error("ยังไม่ได้อนุญาตไมโครโฟน กดไอคอนข้าง URL แล้วอนุญาตไมค์");
      if (e.name === "NotFoundError")
        throw Error("ไม่พบไมโครโฟน ตรวจการเชื่อมต่ออุปกรณ์");
      throw e;
    }
  }
  async function askFAQ() {
    if (!question.trim()) throw Error("กรุณาพิมพ์คำถาม");
    const r = await request("/faq/ask", {
      question,
      mode,
      allow_demo: allowDemo,
    });
    setMessages((m) => [...m, { question, ...r }]);
    setQuestion("");
  }
  async function importFAQs(entries) {
    await request("/faq/import", { entries });
    await refresh();
    setNotice(
      "นำเข้า FAQ แล้ว รายการไม่อนุมัติหรือหมดอายุจะไม่ถูกใช้ตอบ ยกเว้นเปิดโหมดสาธิต",
    );
  }
  const locked = Boolean(sid);
  const heading = (tag, title, desc) => (
    <div className="heading">
      <div>
        <h1>{title}</h1>
        <p className="muted">{desc}</p>
      </div>
      <span className="pill">v1.4.3</span>
    </div>
  );
  const button = (text, fn, secondary = false) => (
    <button
      className={"btn" + (secondary ? " secondary" : "")}
      disabled={!!busy || recording}
      onClick={() => task(text, fn)}
    >
      {text}
    </button>
  );
  return (
    <>
      <aside>
        <a
          href="#"
          className="brand"
          onClick={(e) => {
            e.preventDefault();
            if (!recording && !busy) {
              stopAudio();
              setTab("home");
            }
          }}
        >
          CoopReady
        </a>
        <div className="workspace">พื้นที่เตรียมพร้อมสหกิจ</div>
        <nav>
          {tabs.map(([id, icon, name]) => (
            <button
              key={id}
              className={tab === id ? "active" : ""}
              disabled={recording || !!busy}
              onClick={() => {
                audio.current?.pause();
                window.speechSynthesis?.cancel();
                setTab(id);
                setError("");
              }}
            >
              <span>{name}</span>
            </button>
          ))}
        </nav>
        <div className="side-bottom">
          <span className="status-dot" />{" "}
          {health ? "ระบบเชื่อมต่อแล้ว" : "กำลังเชื่อมต่อระบบ"}
          <p>
            ประวัติเก็บไว้ในเครื่องนี้
            <br />
            พร้อมกลับมาฝึกต่อได้
          </p>
        </div>
      </aside>
      <main>
        <header>
          <span>ระบบเตรียมความพร้อมสหกิจศึกษา</span>
          <div>
            <label htmlFor="training-mode" className="mode-label">
              รูปแบบการฝึก
            </label>
            <select
              id="training-mode"
              aria-label="รูปแบบการฝึก"
              style={{ width: 242, padding: 9 }}
              value={mode}
              disabled={!!busy || (!!interview && !interview.done)}
              onChange={(e) => setMode(e.target.value)}
            >
              <option value="baseline">ฝึกพื้นฐาน · 5 คำถาม</option>
              <option value="proposed">ฝึกด้วย AI · มีคำถามต่อยอด</option>
            </select>
          </div>
        </header>
        <div id="page">
          {error && (
            <div ref={errorRef} className="error" role="alert">
              {error}
            </div>
          )}
          {notice && (
            <div className="success" role="status">
              {notice}
            </div>
          )}
          {tab === "home" && (
            <>
              {heading(
                "",
                "ภาพรวม",
                "เตรียมเรซูเม่ ฝึกตอบคำถาม และทบทวนผลการสัมภาษณ์",
              )}
              <section className="card home-start">
                <h2>เริ่มเตรียมตัว</h2>
                <p>
                  เพิ่มเรซูเม่และตำแหน่งที่สนใจ
                  จากนั้นเริ่มฝึกสัมภาษณ์ได้ด้วยการพิมพ์หรือพูด
                </p>
                <div className="row">
                  <button
                    className="btn"
                    disabled={!!busy}
                    onClick={() => setTab("prepare")}
                  >
                    เตรียมเรซูเม่
                  </button>
                  {sid && (
                    <button
                      className="btn secondary"
                      disabled={!!busy}
                      onClick={() => setTab("interview")}
                    >
                      กลับไปรอบฝึกปัจจุบัน
                    </button>
                  )}
                  <button
                    className="textbtn"
                    disabled={!!busy}
                    onClick={() => setTab("faq")}
                  >
                    สอบถามเรื่องสหกิจ
                  </button>
                </div>
              </section>
              <section className="card recent-practice">
                <div className="section-title">
                  <h2>รายการฝึกล่าสุด</h2>
                  <button
                    className="textbtn"
                    disabled={!!busy}
                    onClick={() => setTab("results")}
                  >
                    ดูประวัติทั้งหมด
                  </button>
                </div>
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>บริษัท</th>
                        <th>ตำแหน่ง</th>
                        <th>แก้ไขล่าสุด</th>
                        <th>สถานะ</th>
                        <th>
                          <span className="sr-only">เปิดรายการ</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {sessions.length ? (
                        sessions.slice(0, 5).map((item) => (
                          <tr key={item.id}>
                            <td>{item.company}</td>
                            <td>{item.role}</td>
                            <td>
                              {new Date(item.updated * 1000).toLocaleDateString(
                                "th-TH",
                              )}
                            </td>
                            <td>
                              <span className="plain-status">
                                {item.has_report
                                  ? "มีรายงานแล้ว"
                                  : "ยังไม่มีรายงาน"}
                              </span>
                            </td>
                            <td>
                              <button
                                className="table-link"
                                disabled={!!busy}
                                onClick={() =>
                                  task("เปิดรายการ", async () => {
                                    await loadSession(item.id);
                                    setTab(
                                      item.has_report ? "results" : "interview",
                                    );
                                  })
                                }
                              >
                                เปิด
                              </button>
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={5} className="table-empty">
                            ยังไม่มีประวัติการฝึก
                            เริ่มต้นได้ที่ปุ่มเตรียมเรซูเม่
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </section>
              <section className="usage-notes">
                <h2>วิธีใช้งาน</h2>
                <ol>
                  <li>อัปโหลดเรซูเม่ กรอกบริษัทและตำแหน่งที่สนใจ</li>
                  <li>
                    เลือกฝึกพื้นฐาน หรือฝึกด้วย AI เมื่อตั้งค่าโมเดลพร้อมแล้ว
                  </li>
                  <li>ตอบคำถามทีละข้อ แล้วสร้างรายงานเพื่อทบทวนคำตอบ</li>
                </ol>
              </section>
              <details
                className="card settings-panel"
                style={{ marginTop: 24 }}
              >
                <summary>ตั้งค่าระบบและตรวจความพร้อม</summary>
                <div
                  className="row"
                  style={{ justifyContent: "space-between" }}
                >
                  <h2>รายละเอียดระบบ</h2>
                  {button(
                    "ตรวจใหม่",
                    async () =>
                      setHealth(await request("/health", undefined, "GET")),
                    true,
                  )}
                </div>
                {health ? (
                  <>
                    <div className="table-wrap">
                      <table>
                        <thead>
                          <tr>
                            <th>ส่วนระบบ</th>
                            <th>สถานะที่ตรวจได้</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr>
                            <td>Baseline / FastAPI / SQLite</td>
                            <td>พร้อมเรียกใช้งาน</td>
                          </tr>
                          <tr>
                            <td>
                              Ollama /{" "}
                              {health.ollama?.configured || "ยังไม่มีข้อมูล"}
                            </td>
                            <td>
                              {health.ollama?.reachable
                                ? "เชื่อมต่อได้ · " +
                                  list(health.ollama?.models).join(", ")
                                : "ยังเชื่อมต่อไม่ได้"}
                            </td>
                          </tr>
                          <tr>
                            <td>Piper voice ({health.piper_language})</td>
                            <td>
                              {health.piper_files_present
                                ? "พบไฟล์ ยังต้องทดสอบเสียง"
                                : "ยังไม่พบ ONNX และ JSON"}
                            </td>
                          </tr>
                          {Object.entries(health.packages || {}).map(
                            ([k, v]) => (
                              <tr key={k}>
                                <td>{k}</td>
                                <td>{v || "ยังไม่ติดตั้ง"}</td>
                              </tr>
                            ),
                          )}
                        </tbody>
                      </table>
                    </div>
                    <p className="muted">
                      {health.python} · {health.system} · retention{" "}
                      {health.retention_days} วัน
                    </p>
                  </>
                ) : (
                  <p className="muted">เปิดโปรแกรมตามคู่มือ แล้วกดตรวจใหม่</p>
                )}
                <div className="notice">
                  โหมดพื้นฐานใช้ Fixed Question Bank; โหมด AI ใช้ Proposed
                  ตามแผนโครงงาน
                  <br />
                  ตรวจพบแพ็กเกจหรือไฟล์
                  ไม่ได้ยืนยันว่าโหลดโมเดลและสนทนาเสียงสำเร็จ
                  ต้องทดสอบบนเครื่องจริงก่อนนำเสนอ
                </div>
              </details>
            </>
          )}
          {tab === "prepare" && (
            <>
              {heading(
                "EVIDENCE WORKSPACE",
                "เตรียมเรซูเม่ของคุณ",
                "เพิ่มเรซูเม่และตำแหน่งที่สนใจ เพื่อเริ่มวิเคราะห์และฝึกสัมภาษณ์",
              )}
              <div className="split prepare-layout">
                <div>
                  <section className="card">
                    <div
                      className="row"
                      style={{ justifyContent: "space-between" }}
                    >
                      <h2>
                        <span className="step-badge">1</span>{" "}
                        เรซูเม่และตำแหน่งที่สนใจ
                      </h2>
                      <button
                        className="btn secondary small"
                        disabled={!!busy || recording}
                        onClick={() => resetDraft(true)}
                      >
                        ใช้ตัวอย่างสมมติ
                      </button>
                    </div>
                    {locked && (
                      <div className="notice green">
                        บันทึกข้อมูลนี้แล้ว หากต้องการแก้ไข
                        ให้สร้างรายการใหม่จากข้อความเดิม
                      </div>
                    )}
                    <label className="check-label">
                      <input
                        type="checkbox"
                        checked={form.consent}
                        disabled={locked}
                        onChange={(e) => field("consent", e.target.checked)}
                      />
                      ฉันมีสิทธิ์ใช้เรซูเม่นี้
                      และยินยอมเก็บข้อความ/คำตอบในเครื่องตามระยะเวลาที่กำหนด
                    </label>
                    <div className="field">
                      <label htmlFor="company">ชื่อบริษัท</label>
                      <input
                        id="company"
                        placeholder="ชื่อบริษัทที่สนใจ"
                        value={form.company}
                        disabled={locked}
                        onChange={(e) => field("company", e.target.value)}
                      />
                    </div>
                    <div className="field">
                      <label htmlFor="role">ตำแหน่งที่ต้องการฝึก</label>
                      <input
                        id="role"
                        placeholder="เช่น Backend Developer Intern"
                        value={form.role}
                        disabled={locked}
                        onChange={(e) => field("role", e.target.value)}
                      />
                    </div>
                    <div className="field">
                      <label htmlFor="resume-file">
                        เลือกไฟล์เรซูเม่ (PDF / DOCX / TXT)
                      </label>
                      <input
                        id="resume-file"
                        type="file"
                        accept=".pdf,.docx,.txt"
                        disabled={locked || !!busy}
                        onChange={parseFile}
                      />
                    </div>
                    <details className="inline-details">
                      <summary>ตรวจหรือวางข้อความเรซูเม่</summary>
                      <div className="field">
                        <label htmlFor="resume">ข้อความจากเรซูเม่</label>
                        <textarea
                          id="resume"
                          value={form.resume}
                          disabled={locked}
                          onChange={(e) => field("resume", e.target.value)}
                          rows={6}
                        />
                      </div>
                    </details>
                    <div className="field">
                      <label htmlFor="role-brief">
                        รายละเอียดงานหรือทักษะที่ต้องการฝึก
                      </label>
                      <textarea
                        id="role-brief"
                        value={form.role_brief}
                        disabled={locked}
                        onChange={(e) => field("role_brief", e.target.value)}
                        placeholder="เช่น Python, SQL, พัฒนา API หรือวางรายละเอียดงานที่มีอยู่"
                        rows={3}
                      />
                      <small>
                        ข้อมูลที่ผู้ใช้ให้
                        ไม่ถือเป็นข้อกำหนดเฉพาะบริษัทจนกว่าจะมีหลักฐานยืนยัน
                      </small>
                    </div>
                    <details className="inline-details">
                      <summary>ระบุที่มาของรายละเอียดงาน</summary>
                      <div className="field">
                        <label htmlFor="provenance">ที่มาข้อมูลบทบาทงาน</label>
                        <select
                          id="provenance"
                          value={form.role_provenance}
                          disabled={locked}
                          onChange={(e) =>
                            field("role_provenance", e.target.value)
                          }
                        >
                          <option value="User-provided Role Brief">
                            Role Brief ที่ผู้ใช้นำมา
                          </option>
                          <option value="General Role Guidance">
                            แนวทางบทบาททั่วไป ไม่เฉพาะบริษัท
                          </option>
                        </select>
                      </div>
                    </details>
                    <div className="field">
                      <label htmlFor="language">ภาษาฝึกสัมภาษณ์</label>
                      <select
                        id="language"
                        value={form.language}
                        disabled={locked}
                        onChange={(e) => field("language", e.target.value)}
                      >
                        <option value="th">ไทย</option>
                        <option value="en">English</option>
                      </select>
                    </div>
                    {locked ? (
                      <button
                        className="btn secondary"
                        disabled={!!busy || recording}
                        onClick={() => {
                          resetDraft();
                          setForm((f) => ({ ...f, consent: false }));
                        }}
                      >
                        สร้างรายการใหม่จากข้อความนี้
                      </button>
                    ) : (
                      button("บันทึกข้อมูลเพื่อเริ่มฝึก →", create)
                    )}
                  </section>
                  <details
                    className="card company-details"
                    style={{ marginTop: 20 }}
                  >
                    <summary>
                      ข้อมูลบริษัทเพิ่มเติม{" "}
                      <span className="optional-label">ไม่บังคับ</span>
                    </summary>
                    <p className="muted">
                      เพิ่มข้อมูลบริษัทเพื่อใช้ประกอบคำถาม
                      คุณเริ่มฝึกจากเรซูเม่ได้ก่อน
                    </p>
                    <div className="field">
                      <label htmlFor="source-url">
                        เว็บไซต์บริษัทหรือแหล่งอ้างอิง
                      </label>
                      <input
                        id="source-url"
                        placeholder="https://…"
                        value={url}
                        disabled={!!busy}
                        onChange={(e) => {
                          setUrl(e.target.value);
                          setSourceText("");
                          setVerified(false);
                          setProfile(null);
                        }}
                      />
                    </div>
                    <div className="field">
                      <label htmlFor="source-text">
                        หรือวางข้อความเกี่ยวกับบริษัท
                      </label>
                      <textarea
                        id="source-text"
                        value={sourceText}
                        disabled={!!busy}
                        onChange={(e) => {
                          setSourceText(e.target.value);
                          setVerified(false);
                        }}
                        rows={4}
                      />
                    </div>
                    <label className="check-label">
                      <input
                        type="checkbox"
                        checked={verified}
                        onChange={(e) => setVerified(e.target.checked)}
                      />
                      ผู้ใช้ตรวจข้อความและที่มาแล้ว (Baseline human-checked
                      profile)
                    </label>
                    <label className="check-label">
                      <input
                        type="checkbox"
                        checked={summarize}
                        disabled={mode === "baseline" || !!busy}
                        onChange={(e) => setSummarize(e.target.checked)}
                      />
                      ให้ AI สรุปข้อมูลพร้อมหลักฐาน (ใช้ในโหมดฝึกด้วย AI)
                    </label>
                    <div className="row">
                      {button("อ่านและบันทึกข้อมูลบริษัท", saveProfile)}
                      {button(
                        "ช่วยค้นเว็บไซต์บริษัท",
                        async () => {
                          requireSession();
                          setCandidates([]);
                          const result = await request(
                            `/sessions/${sid}/company-search`,
                            {},
                          );
                          setCandidates(
                            Array.isArray(result.candidates)
                              ? result.candidates
                              : [],
                          );
                          if (!Array.isArray(result.candidates))
                            throw Error(
                              "ผลค้นไม่มีรายการแหล่งข้อมูล กรุณากรอก Official URL หรือวางข้อความบริษัทเอง",
                            );
                          setNotice(
                            result.candidates.length
                              ? "เลือก URL แล้วเปิดอ่านเพื่อตรวจสอบ ผลค้นยังไม่ใช่ข้อเท็จจริงที่ยืนยันแล้ว"
                              : "ไม่พบแหล่งข้อมูล ลองกรอก Official URL หรือวางข้อความเกี่ยวกับบริษัทเอง",
                          );
                        },
                        true,
                      )}
                    </div>
                    {(Array.isArray(candidates) ? candidates : []).map(
                      (c, i) => (
                        <div className="box" key={i}>
                          <p>{c.title}</p>
                          <p className="muted output">{c.url}</p>
                          <button
                            className="textbtn"
                            onClick={() => {
                              setUrl(c.url);
                              setSourceText("");
                              setVerified(false);
                              setProfile(null);
                            }}
                          >
                            เลือก URL นี้ (ยังไม่ยืนยัน)
                          </button>
                        </div>
                      ),
                    )}
                    {profile?.summary_warning && (
                      <div className="notice" role="status">
                        {profile.summary_warning}
                      </div>
                    )}
                    {profile && (
                      <div className="box output">
                        <span className="tag">{profile.source_label}</span>
                        <p className="muted">
                          {profile.source?.url ||
                            "ข้อความที่ผู้ใช้วาง ไม่มี URL"}
                        </p>
                        {profile.summary &&
                        Array.isArray(profile.summary.facts) ? (
                          profile.summary.facts
                            .filter(
                              (f) =>
                                f &&
                                typeof f.text === "string" &&
                                typeof f.quote === "string",
                            )
                            .map((f, i) => (
                              <div key={i}>
                                <p>{f.text}</p>
                                <blockquote>{f.quote}</blockquote>
                              </div>
                            ))
                        ) : (
                          <>
                            <p>
                              {profile.source?.text ||
                                "ยังไม่มีข้อความแหล่งอ้างอิง"}
                            </p>
                            {profile.summary && (
                              <p className="notice">
                                สรุปเดิมมีรูปแบบไม่ครบ กรุณากดบันทึก / อ่าน
                                Profile อีกครั้ง
                              </p>
                            )}
                          </>
                        )}
                        <p className="muted">{profile.role_label}</p>
                        {profile.summary?.facts.length === 0 && (
                          <p className="muted">
                            ยังไม่มีข้อสรุปบริษัทที่ยืนยันได้
                          </p>
                        )}
                      </div>
                    )}
                  </details>
                </div>
                <div>
                  <section className="card">
                    <h2>
                      <span className="step-badge">2</span> ทักษะที่พบในเรซูเม่
                    </h2>
                    <p className="muted">เทียบกับรายละเอียดงานที่คุณระบุ</p>
                    {!sid && (
                      <div className="empty-hint">
                        บันทึกข้อมูลในขั้นที่ 1 ก่อน แล้วจึงเริ่มวิเคราะห์
                      </div>
                    )}
                    {sid &&
                      button(
                        analysis ? "วิเคราะห์อีกครั้ง" : "วิเคราะห์เรซูเม่",
                        runAnalysis,
                      )}
                    {sid && !analysis && (
                      <div className="resume-next">
                        <p className="muted">
                          พร้อมแล้ว? เริ่มฝึกจากเรซูเม่ได้ทันที
                          หรือวิเคราะห์ทักษะก่อน
                        </p>
                        <button
                          className="btn secondary"
                          disabled={!!busy}
                          onClick={() => setTab("interview")}
                        >
                          ไปซ้อมสัมภาษณ์ →
                        </button>
                      </div>
                    )}
                    {analysis && (
                      <>
                        <div className="skill-summary">
                          <div>
                            <strong>
                              {
                                analysis.skills.filter(
                                  (r) => r.status === "Matched",
                                ).length
                              }
                            </strong>
                            <span>ทักษะที่พบหลักฐาน</span>
                          </div>
                          <div>
                            <strong>
                              {
                                analysis.skills.filter(
                                  (r) => r.status !== "Matched",
                                ).length
                              }
                            </strong>
                            <span>ทักษะที่ควรเพิ่มข้อมูล</span>
                          </div>
                        </div>
                        {analysis.skills.length ? (
                          analysis.skills.map((r) => (
                            <div className="box" key={r.skill}>
                              <span
                                className={
                                  "tag" +
                                  (r.status === "Not Evidenced"
                                    ? " missing"
                                    : "")
                                }
                              >
                                {r.skill} ·{" "}
                                {r.status === "Matched"
                                  ? "พบหลักฐาน"
                                  : "ยังไม่พบหลักฐาน"}
                              </span>
                              <p className="output">
                                {r.evidence || "ยังไม่พบหลักฐานใน Resume"}
                              </p>
                              <p className="muted">{r.advice}</p>
                            </div>
                          ))
                        ) : (
                          <div className="notice">
                            ไม่พบทักษะในพจนานุกรมจาก Role Brief นี้
                            ยังสรุปการจับคู่ไม่ได้
                          </div>
                        )}
                        <details className="inline-details">
                          <summary>รายละเอียดการวิเคราะห์สำหรับโครงงาน</summary>{" "}
                          <div className="score">
                            {analysis.similarity.toFixed(3)}
                          </div>
                          <p className="muted">
                            ความคล้าย TF-IDF + ผลทักษะ{" "}
                            {analysis.mode === "proposed"
                              ? "MiniLM"
                              : "keyword"}{" "}
                            ไม่ใช่ Accuracy · {analysis.elapsed_ms} ms
                          </p>
                          {analysis.semantic_candidates?.map((r) => (
                            <details key={r.skill}>
                              <summary>
                                {r.skill} · MiniLM{" "}
                                {r.semantic_similarity.toFixed(3)}
                              </summary>
                              <p>{r.candidate_evidence}</p>
                              <p className="muted">{r.note}</p>
                            </details>
                          ))}
                        </details>
                        <div className="notice">
                          “ยังไม่พบหลักฐาน” หมายถึงยังไม่มีข้อมูลในเรซูเม่
                          ไม่ได้แปลว่าคุณไม่มีทักษะนั้น
                        </div>
                        <button
                          className="btn"
                          onClick={() => setTab("interview")}
                        >
                          เริ่มซ้อมสัมภาษณ์ →
                        </button>
                      </>
                    )}
                  </section>
                </div>
              </div>
            </>
          )}
          {tab === "interview" && (
            <>
              {heading(
                "VOICE INTERVIEW",
                "ซ้อมสัมภาษณ์",
                "ตอบทีละข้อ จะพิมพ์หรือพูดก็ได้ แล้วตรวจคำตอบก่อนส่ง",
              )}
              <div className="split interview-layout">
                <section className="card">
                  <h2>
                    {session
                      ? session.company + " · " + session.role
                      : "เตรียมเรซูเม่ก่อนเริ่มฝึก"}
                  </h2>
                  <p className="muted">
                    {mode === "baseline"
                      ? "ฝึกพื้นฐาน · คำถาม 5 ข้อ"
                      : "ฝึกด้วย AI · คำถามหลัก 5 ข้อ และคำถามต่อยอด 2 ข้อ"}
                  </p>
                  {!sid && (
                    <div className="empty-hint">
                      <p>
                        เพิ่มเรซูเม่และตำแหน่งที่สนใจก่อน
                        เพื่อให้คำถามมีบริบทของคุณ
                      </p>
                      <button className="btn" onClick={() => setTab("prepare")}>
                        เตรียมเรซูเม่ →
                      </button>
                    </div>
                  )}
                  {sid && (!interview || interview.done) ? (
                    <>
                      <div className="voice-stage">
                        <div className="question-label">การสัมภาษณ์</div>
                        <h2>
                          {interview?.done
                            ? "จบรอบฝึกแล้ว"
                            : "เริ่มฝึกจากประสบการณ์ของคุณ"}
                        </h2>
                        <p className="muted">
                          ภาษาปัจจุบัน: {session?.language || form.language} ·
                          {mode === "baseline" ? "ฝึกพื้นฐาน" : "ฝึกด้วย AI"}
                        </p>
                      </div>
                      {button(
                        interview?.done ? "เริ่มรอบใหม่" : "เริ่มซ้อมสัมภาษณ์",
                        startInterview,
                        !!interview?.done,
                      )}
                    </>
                  ) : sid ? (
                    <>
                      <div className="progress">
                        คำถามหลัก {interview.base_index + 1}/5 · ตอบแล้ว{" "}
                        {interview.turns.length} · ถามต่อ {interview.followups}{" "}
                        ครั้ง
                      </div>
                      <div className="voice-stage">
                        <div className="question-label">การสัมภาษณ์</div>
                        <p>{interview.question}</p>
                        {interview.is_followup && (
                          <p className="muted">
                            ต่อจาก “{interview.evidence_quote}”
                          </p>
                        )}
                        <div
                          className="row"
                          style={{ justifyContent: "center" }}
                        >
                          {button("ฟังคำถาม", speakQuestion, true)}
                          <button
                            className="btn secondary"
                            onClick={() => {
                              audio.current?.pause();
                              window.speechSynthesis?.cancel();
                            }}
                          >
                            หยุดเสียง
                          </button>
                        </div>
                      </div>
                      <div className="field">
                        <label htmlFor="answer">คำตอบของคุณ</label>
                        <textarea
                          ref={answerRef}
                          id="answer"
                          value={answer}
                          disabled={!!busy || recording}
                          onChange={(e) => setAnswer(e.target.value)}
                          placeholder="พิมพ์คำตอบที่นี่ หรือกดเริ่มพูดด้านล่าง…"
                          rows={5}
                        />
                      </div>
                      <div className="row">
                        <button
                          className={
                            "btn" + (recording ? " danger" : " secondary")
                          }
                          disabled={!!busy}
                          onClick={() => task("ไมโครโฟน", record)}
                        >
                          {recording ? "หยุดและถอดเสียง" : "เริ่มอัดเสียง"}
                        </button>
                        {button("ส่งคำตอบ →", submitAnswer)}
                        {button(
                          "จบรอบก่อน",
                          async () => {
                            requireSession();
                            setInterview(
                              await request(
                                `/sessions/${sid}/interview/finish`,
                                {},
                              ),
                            );
                          },
                          true,
                        )}
                      </div>
                      <p className="record-status" role="status">
                        {recording
                          ? "● กำลังอัดเสียง กดหยุดเมื่อพูดจบ"
                          : busy.includes("ถอดเสียง")
                            ? "กำลังถอดเสียง กรุณารอสักครู่"
                            : "เมื่อคำตอบพร้อมแล้ว กดส่งเพื่อไปคำถามถัดไป"}
                      </p>
                      <details className="inline-details">
                        <summary>รายละเอียดเวลาและระบบเสียง</summary>{" "}
                        <p className="muted" aria-live="polite">
                          {recording
                            ? "กำลังอัดเสียง (หยุดอัตโนมัติใน 3 นาที) กดหยุดเพื่อถอดเป็นข้อความ · "
                            : busy.includes("ถอดเสียง")
                              ? "กำลังถอดเสียง ครั้งแรกอาจต้องดาวน์โหลดโมเดล · "
                              : ""}
                          STT: {audioMetrics.stt_ms} ms · TTS:{" "}
                          {audioMetrics.tts_ms} ms · input:{" "}
                          {audioMetrics.stt_engine}
                        </p>
                      </details>
                    </>
                  ) : null}
                  {interview?.done && (
                    <div style={{ marginTop: 20 }}>
                      {button("ดูคำแนะนำหลังฝึก", async () => {
                        const r = await request(
                          `/sessions/${sid}/interview/report`,
                          {},
                        );
                        setReport(r);
                        setTab("results");
                        await refresh();
                      })}
                    </div>
                  )}
                </section>
                <section>
                  <details className="card settings-panel">
                    <summary>ตั้งค่าการอ่านเสียง</summary>
                    <p className="muted">
                      เลือกวิธีอ่านคำถามที่คุณสะดวก
                      คุณยังพิมพ์ตอบได้แม้ไม่ได้ตั้งค่าเสียง
                    </p>
                    <label className="check-label">
                      <input
                        type="checkbox"
                        checked={autoSpeak}
                        disabled={!!busy || recording}
                        onChange={(e) => setAutoSpeak(e.target.checked)}
                      />
                      อ่านคำถามอัตโนมัติ
                    </label>
                    <label className="check-label">
                      <input
                        type="checkbox"
                        checked={audioFallback}
                        disabled={!!busy || recording}
                        onChange={(e) => setAudioFallback(e.target.checked)}
                      />
                      อ่านด้วยเสียงของเบราว์เซอร์ (เสียงสำรอง)
                    </label>
                    <details className="inline-details">
                      <summary>รายละเอียดโมเดลเสียงและการเก็บข้อมูล</summary>{" "}
                      <p className="muted">
                        ค่าเริ่มต้นใช้ Piper + faster-whisper ในเครื่อง
                        หากโมเดลไม่พร้อมจะแจ้งข้อผิดพลาด
                        ไม่มีการเปลี่ยนเครื่องมือเงียบ ๆ
                      </p>
                      <div className="notice">
                        ต้องเลือก Piper voice ให้ตรงภาษาไทย/อังกฤษ และวาง ONNX +
                        JSON ก่อน ไม่ได้แนบเสียงไทยที่ยังไม่ตรวจสอบ
                      </div>
                      <p className="muted">
                        ใช้หูฟัง เปิดสิทธิ์ไมค์บน localhost
                        ไฟล์เสียงชั่วคราวถูกลบหลังถอด ข้อความคำตอบเก็บใน SQLite
                      </p>
                    </details>
                  </details>
                  <details
                    className="card settings-panel"
                    style={{ marginTop: 18 }}
                  >
                    <summary>ทบทวนคำตอบในรอบนี้</summary>

                    <div className="scroll-list">
                      {interview?.turns.map((t, i) => (
                        <div className="transcript" key={i}>
                          <p>{t.question}</p>
                          <p className="muted output">{t.answer}</p>
                        </div>
                      )) || <p className="muted">ยังไม่มีคำตอบ</p>}
                    </div>
                  </details>
                </section>
              </div>
            </>
          )}
          {tab === "faq" && (
            <>
              {heading(
                "ACADEMIC Q&A",
                "ถามเรื่องสหกิจศึกษา",
                "ตอบจากเอกสารที่อนุมัติ ยังมีผล และมีแหล่งอ้างอิงเท่านั้น",
              )}
              <div className="split faq-layout">
                <section className="card">
                  <h2>ผู้ช่วยเรื่องสหกิจ</h2>
                  <label className="check-label">
                    <input
                      type="checkbox"
                      checked={allowDemo}
                      onChange={(e) => setAllowDemo(e.target.checked)}
                    />
                    อนุญาตข้อมูลสมมติสำหรับสาธิต
                  </label>
                  <div className="chat" aria-live="polite">
                    {messages.length ? (
                      messages.map((m, i) => (
                        <div key={i}>
                          <div className="bubble user">{m.question}</div>
                          <div className="bubble">
                            {m.answer}
                            {m.demo_used && (
                              <p className="source">
                                ข้อมูลสมมติ ไม่ใช่ประกาศมหาวิทยาลัย
                              </p>
                            )}
                            {list(m.citations).map((c) => (
                              <p className="source" key={c.id}>
                                {c.source} · หน้า {c.page || "-"} · ฉบับ{" "}
                                {c.version || "-"}
                              </p>
                            ))}
                            <p className="source">
                              {m.elapsed_ms} ms ·{" "}
                              {m.abstained
                                ? "งดตอบเมื่อไม่พบหลักฐาน"
                                : "ค้นพบแหล่งอ้างอิง"}
                            </p>
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="bubble">
                        นำเข้า FAQ ที่ตรวจยืนยันแล้ว
                        หรือเปิดข้อมูลสาธิตเพื่อทดลอง
                        ระบบจะไม่เดาเงื่อนไขหรือวันส่งเอกสาร
                      </div>
                    )}
                  </div>
                  <form
                    className="chat-form"
                    onSubmit={(e) => {
                      e.preventDefault();
                      task("ค้นคำตอบ", askFAQ);
                    }}
                  >
                    <label htmlFor="faq-question" className="sr-only">
                      คำถามสหกิจ
                    </label>
                    <input
                      id="faq-question"
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      placeholder="พิมพ์คำถาม…"
                    />
                    <button className="btn" disabled={!!busy}>
                      ส่ง ↗
                    </button>
                  </form>
                </section>
                <details className="card settings-panel">
                  <summary>จัดการเอกสารและคำถามอ้างอิง</summary>
                  <h2>คลัง FAQ · {faqRows.length} รายการ</h2>
                  <p className="muted">
                    ไฟล์ JSON ใช้รายการที่มี question, answer, source, page,
                    version, approved และ valid_until (YYYY-MM-DD หรือ null)
                  </p>
                  <label htmlFor="faq-file">นำเข้า FAQ JSON</label>
                  <input
                    id="faq-file"
                    type="file"
                    accept=".json"
                    onChange={(e) => {
                      const f = e.target.files?.[0];
                      if (f)
                        task("นำเข้า FAQ", async () => {
                          const a = JSON.parse(await f.text());
                          await importFAQs(Array.isArray(a) ? a : a.entries);
                        });
                    }}
                  />
                  <div className="row" style={{ marginTop: 14 }}>
                    {button(
                      "เพิ่ม FAQ สมมติ",
                      () => importFAQs(sampleFAQs),
                      true,
                    )}
                    <button
                      className="btn secondary"
                      onClick={() => exportJSON("faq-demo.json", sampleFAQs)}
                    >
                      ดาวน์โหลดตัวอย่าง
                    </button>
                  </div>
                  <details>
                    <summary>หรือวาง JSON</summary>
                    <textarea
                      aria-label="FAQ JSON"
                      value={importText}
                      onChange={(e) => setImportText(e.target.value)}
                    />
                    {button("นำเข้า JSON ที่วาง", async () => {
                      const a = JSON.parse(importText);
                      await importFAQs(Array.isArray(a) ? a : a.entries);
                    })}
                  </details>
                  <div className="scroll-list">
                    {faqRows.map((f) => (
                      <div key={f.id} className="box">
                        <p>{f.data.question}</p>
                        <span className="tag">
                          {f.data.demo
                            ? "สมมติ"
                            : f.data.approved
                              ? "ผู้ใช้ยืนยันอนุมัติ"
                              : "ยังไม่อนุมัติ"}
                        </span>
                        <p className="muted">
                          {f.data.source} · หมดอายุ{" "}
                          {f.data.valid_until || "ไม่ระบุ"}
                        </p>
                        <button
                          className="textbtn"
                          disabled={!!busy}
                          onClick={() =>
                            task("ลบ FAQ", async () => {
                              if (confirm("ลบ FAQ นี้ออกจากเครื่อง?")) {
                                await request(
                                  "/faq/" + f.id,
                                  undefined,
                                  "DELETE",
                                );
                                await refresh();
                              }
                            })
                          }
                        >
                          ลบรายการ
                        </button>
                      </div>
                    ))}
                  </div>
                </details>
              </div>
            </>
          )}
          {tab === "results" && (
            <>
              {heading(
                "INITIAL RESULTS & EVALUATION",
                "คำแนะนำและประวัติการฝึก",
                "ทบทวนสิ่งที่ทำได้ดี และเลือกจุดที่อยากฝึกเพิ่มในครั้งต่อไป",
              )}
              <div className="split results-layout">
                <section>
                  {report && (
                    <div className="card" style={{ marginTop: 20 }}>
                      <h2>
                        คำแนะนำหลังฝึก ·{" "}
                        {report.mode === "baseline"
                          ? "ฝึกพื้นฐาน"
                          : "ฝึกด้วย AI"}
                      </h2>
                      <p className="muted">
                        ฝึกแล้ว {report.turns.length} คำตอบ ·
                        ทบทวนตามหัวข้อด้านล่าง
                      </p>
                      <details className="inline-details">
                        <summary>รายละเอียดรอบฝึกและการประเมิน</summary>{" "}
                        <p className="muted">
                          {report.duration_seconds} วินาที ·{" "}
                          {report.turns.length} รอบ · follow-up{" "}
                          {report.followups} · รอบที่มี STT/TTS local{" "}
                          {report.voice_turns}
                        </p>
                        <div className="notice">{report.warning}</div>
                      </details>
                      {report.dimensions.map((r, i) => (
                        <div className="box" key={i}>
                          <h3>
                            {r.dimension} ·{" "}
                            {r.score === null ? "รอผู้ประเมิน" : r.score + "/5"}
                          </h3>
                          {r.evidence && <blockquote>{r.evidence}</blockquote>}
                          <p>{r.feedback}</p>
                          {r.example_improvement && (
                            <p className="muted">{r.example_improvement}</p>
                          )}
                        </div>
                      ))}
                      {report.action_items?.map((a, i) => (
                        <p key={i}>• {a}</p>
                      ))}
                      <button
                        className="btn secondary"
                        onClick={() =>
                          exportJSON("interview-report.json", report)
                        }
                      >
                        ส่งออกรายงาน
                      </button>
                    </div>
                  )}
                  {!report && (
                    <div className="card empty-state">
                      <h2>คำแนะนำจะอยู่ตรงนี้</h2>
                      <p className="muted">
                        ฝึกสัมภาษณ์แล้วสร้างรายงาน
                        หรือเปิดรอบฝึกที่บันทึกไว้ด้านล่าง
                      </p>
                      <button
                        className="btn"
                        onClick={() => setTab(sid ? "interview" : "prepare")}
                      >
                        {sid ? "ไปซ้อมสัมภาษณ์" : "เริ่มเตรียมเรซูเม่"} →
                      </button>
                    </div>
                  )}
                  <div className="card">
                    <h2>ประวัติการฝึก</h2>
                    {button("โหลดรายการใหม่", refresh, true)}
                    {sessions.map((s) => (
                      <div className="box" key={s.id}>
                        <p>
                          {s.company} · {s.role}
                        </p>
                        <p className="muted">
                          {new Date(s.updated * 1000).toLocaleString("th-TH")}
                        </p>
                        <div className="row">
                          {button(
                            "เปิดรายการนี้",
                            async () => loadSession(s.id),
                            true,
                          )}
                          {button(
                            "ลบข้อมูลนี้",
                            async () => {
                              if (confirm("ลบ session และคำตอบในเครื่อง?")) {
                                await request(
                                  "/sessions/" + s.id,
                                  undefined,
                                  "DELETE",
                                );
                                if (s.id === sid) resetDraft();
                                await refresh();
                              }
                            },
                            true,
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </section>
                <details className="card settings-panel evaluation-panel">
                  <summary>เครื่องมือวัดผลสำหรับโครงงาน</summary>
                  <p className="muted">
                    ใช้เปรียบเทียบผลระบบกับข้อมูลอ้างอิง
                    ไม่ใช่คะแนนสัมภาษณ์ของคุณ
                  </p>
                  <div className="card">
                    <h2>วัดความผิดพลาดการถอดเสียง</h2>
                    <label htmlFor="reference">
                      ข้อความอ้างอิงที่คนตรวจแล้ว
                    </label>
                    <textarea
                      id="reference"
                      value={reference}
                      onChange={(e) => setReference(e.target.value)}
                    />
                    <label htmlFor="hypothesis">ข้อความที่ STT ถอดได้</label>
                    <textarea
                      id="hypothesis"
                      value={hypothesis}
                      onChange={(e) => setHypothesis(e.target.value)}
                    />
                    {button("คำนวณ CER / WER", async () => {
                      if (!reference.trim())
                        throw Error(
                          "กรุณากรอกข้อความอ้างอิงที่คนตรวจแล้วก่อนคำนวณ",
                        );
                      setSpeechMetric(
                        await request("/evaluate/speech", {
                          reference,
                          hypothesis,
                        }),
                      );
                    })}
                    {speechMetric && (
                      <div className="box">
                        <p>CER: {speechMetric.cer.toFixed(4)}</p>
                        <p>
                          WER (whitespace):{" "}
                          {speechMetric.wer_whitespace.toFixed(4)}
                        </p>
                        <p className="muted">{speechMetric.note}</p>
                      </div>
                    )}
                  </div>
                  <div className="card" style={{ marginTop: 20 }}>
                    <h2>วัดการจับคู่ทักษะ</h2>
                    <p className="muted">
                      กรอกชื่อทักษะ Matched ที่คนตรวจยืนยัน คั่นด้วย comma
                      ใช้ตัวพิมพ์และชื่อเดียวกับผลระบบ
                    </p>
                    <label htmlFor="truth">
                      Ground truth สำหรับ session ปัจจุบัน
                    </label>
                    <input
                      id="truth"
                      value={truth}
                      onChange={(e) => setTruth(e.target.value)}
                      placeholder="Python, FastAPI, Git"
                    />
                    {button("คำนวณ Precision / Recall / F1", async () => {
                      if (!analysis)
                        throw Error("วิเคราะห์ Resume ใน session นี้ก่อน");
                      setSkillMetric(
                        await request("/evaluate/skills", {
                          truth: truth
                            .split(",")
                            .map((s) => s.trim())
                            .filter(Boolean),
                          predicted: analysis.skills
                            .filter((r) => r.status === "Matched")
                            .map((r) => r.skill),
                        }),
                      );
                    })}
                    {skillMetric && (
                      <pre>{JSON.stringify(skillMetric, null, 2)}</pre>
                    )}
                  </div>
                  <div className="card" style={{ marginTop: 20 }}>
                    <h2>ส่งออกหลักฐานทดลอง</h2>
                    <p className="muted">
                      มีข้อมูลส่วนตัว ควรตรวจและลบตัวตนก่อนส่งต่อ
                      ไม่รวมไฟล์เสียงต้นฉบับ
                    </p>
                    {button(
                      "ส่งออกข้อมูลทั้งหมด",
                      async () =>
                        exportJSON(
                          "coopready-local-export.json",
                          await request("/export", undefined, "GET"),
                        ),
                      true,
                    )}
                    <p className="muted">
                      ข้อมูลที่นำเข้าไม่ใช่ชุดทดสอบที่ผ่านการประเมินโดยอัตโนมัติ
                      ยังต้องมีผู้ประเมิน 2 คนตามสไลด์
                      และแยกชุดปรับระบบจากชุดทดสอบ
                    </p>
                  </div>
                </details>
              </div>
            </>
          )}
        </div>
        <footer>CoopReady · ระบบเตรียมความพร้อมสหกิจศึกษา · v1.4.3</footer>
      </main>
      {busy && (
        <div className="loading" role="status">
          {busy}…
        </div>
      )}
    </>
  );
}
