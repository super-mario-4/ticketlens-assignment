import type { ReviewReason } from "./types";

export const REVIEW_REASON: Record<ReviewReason, string> = {
  no_content: "Mazmunsiz matn",
  unclear: "Mazmuni tushunarsiz",
  low_confidence: "AI ishonchi past",
  injection_suspected: "AI’ga buyruq berishga urinish",
  schema_error: "AI javobi noto‘g‘ri formatda",
  llm_unavailable: "AI javob bermadi",
  masking_error: "Maskalash xatosi",
};
