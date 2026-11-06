// Display names only. The allowed values come from `GET /api/meta`.
export const CATEGORY: Record<string, string> = {
  payments_transfers: "To‘lov va o‘tkazma",
  technical_issues: "Texnik muammo",
  account_access: "Akkauntga kirish",
  card_issues: "Karta",
  fees_charges: "Komissiya va to‘lovlar",
  credit_installments: "Kredit va muddatli to‘lov",
  identity_verification: "Identifikatsiya",
  security_fraud: "Xavfsizlik va firibgarlik",
  refunds: "Pulni qaytarish",
  support_complaints: "Xizmatdan shikoyat",
  feature_request: "Taklif",
  other: "Boshqa",
};

export const STATUS: Record<string, string> = {
  pending: "Navbatda",
  processing: "Tasniflanmoqda",
  classified: "Yo‘naltirilgan",
  needs_review: "Qo‘lda tekshirish",
};

export const REASON: Record<string, string> = {
  no_content: "Mazmunsiz matn",
  unclear: "Mazmuni tushunarsiz",
  low_confidence: "AI ishonchi past",
  injection_suspected: "AI’ga buyruq berishga urinish",
  schema_error: "AI javobi noto‘g‘ri formatda",
  llm_unavailable: "AI javob bermadi",
  masking_error: "Maskalash xatosi",
};

export const ERROR: Record<string, string> = {
  invalid_credentials: "Login yoki parol noto‘g‘ri.",
  search_unavailable: "Qidiruv vaqtincha ishlamayapti. Filtrlar ishlaydi.",
  ticket_not_found: "Ticket topilmadi.",
  ticket_not_correctable: "Ticket hali tasniflanmagan.",
  ticket_not_reclassifiable: "Bu ticketni qayta tasniflab bo‘lmaydi.",
  invalid_team: "Bunday jamoa yo‘q.",
  file_too_large: "Fayl 10 MB dan katta.",
  unsupported_media_type: "Faqat CSV fayl yuklanadi.",
  missing_columns: "CSV’da kerakli ustunlar yo‘q.",
  forbidden: "Bu amal uchun ruxsat yo‘q.",
  database_unavailable: "Ma’lumotlar bazasi vaqtincha ishlamayapti.",
};

export function errorText(code: string): string {
  return ERROR[code] ?? "Xatolik yuz berdi.";
}

export function dateText(value: string): string {
  return new Date(value).toLocaleString("uz-UZ", { dateStyle: "short", timeStyle: "short" });
}
