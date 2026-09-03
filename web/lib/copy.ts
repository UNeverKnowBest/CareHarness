export type Locale = "en" | "zh-CN";

export const copy = {
  en: {
    eyebrow: "RESEARCH HARNESS · SYNTHETIC DATA ONLY",
    boundary: "Adult synthetic role-play research only",
    notice:
      "This is not therapy, diagnosis, crisis care, or an emergency service. The simulated review queue is not staffed care and contacts no clinicians, emergency services, family, authorities, or other third parties.",
    participant: "Participant studio",
    reviewer: "Review desk",
    admin: "Plugin control",
  },
  "zh-CN": {
    eyebrow: "研究工具 · 仅限合成数据",
    boundary: "仅限成人合成角色扮演研究",
    notice:
      "这不是治疗、诊断、危机照护或紧急服务。模拟审核队列并非有人值守的照护服务，也不会联系临床人员、急救服务、家人或政府部门。",
    participant: "参与者工作台",
    reviewer: "模拟审核台",
    admin: "插件控制台",
  },
} as const;

export function localeCopy(value: string) {
  return value === "zh-CN" ? copy["zh-CN"] : copy.en;
}
