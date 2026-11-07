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
