# ADR-0001: MVP uchun lokal LLM tanlash

- **Holat:** Accepted
- **Sana:** 2026-11-05
- **Tegishli hujjatlar:** PRD 5–9-bo‘limlar, TRD 2, 7, 9, 13-bo‘limlar

## Kontekst

TicketLens mijoz murojaatlarini o‘zbek (lotin va kirill), rus va aralash tillarda tasniflashi, ustuvorlikni belgilashi va o‘zbek tilida qisqa xulosa yaratishi kerak.

Murojaatlarda karta, telefon va pasport kabi maxfiy ma’lumotlar uchrashi mumkin. Shu sababli AI xizmatini lokal ishlatish maqsadga muvofiq.

## Qaror

MVP uchun Qwen3.6-35B-A3B modeli LM Studio orqali lokal ishlatiladi. Backend model bilan OpenAI-compatible HTTP API orqali bog‘lanadi.

- Model: Qwen3.6-35B-A3B.
- Runtime: LM Studio.
- API: OpenAI-compatible Chat Completions.
- Model sozlamalari `.env` orqali boshqariladi.
- LLM javobi JSON schema orqali tekshiriladi.
- Xato yoki mavjud bo‘lmagan LLM so‘rovi qo‘lda tekshirishga yuboriladi.

## Ko‘rib chiqilgan alternativalar

1. **Bulutli LLM API:** maxfiy ma’lumotlar va tashqi provayderga bog‘liqlik xavfi mavjud.
2. **Bir nechta lokal model:** MVP uchun ortiqcha murakkablik keltiradi.
3. **Modelni ilova ichida boshqarish:** qo‘shimcha infratuzilma talab qiladi.

## Oqibatlar

### Ijobiy

- AI so‘rovlari tashqi provayderga yuborilmaydi.
- API integratsiyasi sodda bo‘ladi.
- Model natijalarini lokal benchmark qilish mumkin.

### Salbiy

- LM Studio alohida ishga tushirilishi kerak.
- Model katta xotira talab qilishi mumkin.
- Ishlash tezligi kompyuter resurslariga bog‘liq.
- Model ishlamasa, ticket qo‘lda tekshirishga yuboriladi.

## Qayta ko‘rib chiqish shartlari

Agar model PRD'dagi aniqlik, Critical recall yoki tezlik maqsadlariga erishmasa, boshqa modellar benchmark qilinadi.
