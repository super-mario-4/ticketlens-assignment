import { ApiError } from "./client";

const ERROR: Record<string, string> = {
  invalid_credentials: "Login yoki parol noto‘g‘ri.",
  search_unavailable: "Qidiruv vaqtincha ishlamayapti. Filtrlar ishlaydi.",
  ticket_not_found: "Ticket topilmadi.",
  ticket_not_correctable: "Ticket hali tasniflanmagan.",
  ticket_not_reclassifiable: "Bu ticketni qayta tasniflab bo‘lmaydi.",
  invalid_team: "Bunday jamoa yo‘q.",
  file_too_large: "Fayl 10 MB dan katta.",
  unsupported_media_type: "Faqat CSV fayl yuklanadi.",
  invalid_filename: "Fayl nomi noto‘g‘ri.",
  invalid_file_format: "Fayl CSV formatida emas.",
  invalid_encoding: "Fayl UTF-8 kodlashida emas.",
  empty_file: "Fayl bo‘sh.",
  malformed_csv: "CSV fayl buzilgan.",
  missing_columns: "CSV’da kerakli ustunlar yo‘q.",
  unexpected_columns: "CSV’da ortiqcha ustunlar bor.",
  forbidden: "Bu amal uchun ruxsat yo‘q.",
  database_unavailable: "Ma’lumotlar bazasi vaqtincha ishlamayapti.",
};

export function errorText(code: string): string {
  return ERROR[code] ?? "Xatolik yuz berdi.";
}

export function errorMessage(error: unknown): string {
  return errorText(error instanceof ApiError ? error.code : "error");
}
