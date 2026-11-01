export const list = (value) => (Array.isArray(value) ? value : []);
export const text = (value) => (typeof value === "string" ? value : "");
export const number = (value) =>
  typeof value === "number" && Number.isFinite(value) ? value : 0;
const object = (value) =>
  value && typeof value === "object" && !Array.isArray(value);
export function profileData(value) {
  if (!object(value)) return null;
  const source = object(value.source) ? value.source : {};
  const summary = object(value.summary) ? value.summary : null;
  return {
    ...value,
    source: { url: text(source.url), text: text(source.text) },
    summary: summary
      ? {
          facts: list(summary.facts).filter(
            (f) =>
              object(f) &&
              typeof f.text === "string" &&
              typeof f.quote === "string",
          ),
          missing_fields: list(summary.missing_fields).filter(
            (x) => typeof x === "string",
          ),
        }
      : null,
    summary_warning:
      text(value.summary_warning) ||
      (summary && !Array.isArray(summary.facts)
        ? "สรุปเดิมมีรูปแบบไม่ครบ กรุณาสร้างสรุปใหม่"
        : ""),
    source_label: text(value.source_label),
    role_label: text(value.role_label),
  };
}
export function analysisData(value) {
  if (!object(value)) return null;
  return {
    ...value,
    similarity: number(value.similarity),
    skills: list(value.skills).filter(object),
    semantic_candidates: list(value.semantic_candidates)
      .filter(object)
      .map((r) => ({
        ...r,
        semantic_similarity: number(r.semantic_similarity),
      })),
  };
}
export function reportData(value) {
  if (!object(value)) return null;
  return {
    ...value,
    turns: list(value.turns).filter(object),
    dimensions: list(value.dimensions).filter(object),
    action_items: list(value.action_items).filter((x) => typeof x === "string"),
  };
}
export function interviewData(value) {
  if (!object(value)) return null;
  return {
    ...value,
    turns: list(value.turns).filter(object),
    base_index: number(value.base_index),
    followups: number(value.followups),
    question: text(value.question),
    report: reportData(value.report),
  };
}
export function apiError(value, status) {
  if (typeof value?.detail === "string") return value.detail;
  if (Array.isArray(value?.detail))
    return value.detail
      .map(
        (e) => `${list(e.loc).slice(1).join(".") || "ข้อมูล"}: ${text(e.msg)}`,
      )
      .join(" · ");
  return `เรียก Backend ไม่สำเร็จ (HTTP ${status}) กรุณาตรวจ Terminal`;
}
