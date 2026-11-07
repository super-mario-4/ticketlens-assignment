# ADR-0001: MVP uchun lokal LLM tanlash

- **Sana:** 2026-11-05
- **Tegishli hujjatlar:** PRD 5–9-bo‘limlar, TRD 2, 7, 9, 13-bo‘limlar
- **Holat:** joriy qilingan (implemented). Kod, Compose va CI shu qarorga amal qiladi. Runtime o‘zgarishini (host’dagi LM Studio → Compose’dagi Ollama) egasi rasman tasdiqlashi kerak — pastdagi “Egasi uchun qaror” bandiga qarang.

## Kontekst

TicketLens mijoz murojaatlarini o‘zbek (lotin va kirill), rus va aralash tillarda tasniflashi, ustuvorlikni belgilashi va o‘zbek tilida qisqa xulosa yaratishi kerak.

Murojaatlarda karta, telefon va pasport kabi maxfiy ma’lumotlar uchrashi mumkin. Shu sababli AI xizmatini lokal ishlatish maqsadga muvofiq.

Topshiriqning majburiy talabi: butun tizim faqat Docker o‘rnatilgan toza Linux mashinada bitta buyruq bilan ishga tushishi kerak. AI tasniflash tizimning asosiy qismi, shuning uchun u Docker’dan tashqaridagi dasturga bog‘liq bo‘lishi mumkin emas.

## Qaror

MVP uchun Qwen3.6-35B-A3B modeli Docker Compose ichidagi `llm` servisida (Ollama) lokal ishlatiladi. Backend model bilan OpenAI-compatible HTTP API orqali bog‘lanadi.

- Model: Qwen3.6-35B-A3B (Ollama’da `qwen3.6:35b-a3b`, taxminan 23 GB).
- Runtime: Ollama, Compose servisi; model birinchi ishga tushishda Docker volume’ga avtomatik yuklanadi.
- API: OpenAI-compatible Chat Completions.
- Model sozlamalari muhit o‘zgaruvchilari orqali boshqariladi; Compose’da standart qiymatlar bor, `.env` ixtiyoriy.
- LM Studio majburiy emas: ishlab chiquvchi tezroq ishlash uchun `LLM_BASE_URL` orqali hostdagi LM Studio’ga ulanishi mumkin.
- LLM javobi JSON schema orqali tekshiriladi.
- Xato yoki mavjud bo‘lmagan LLM so‘rovi qo‘lda tekshirishga yuboriladi.

## Ko‘rib chiqilgan alternativalar

1. **Bulutli LLM API:** tashqi provayderga bog‘liqlik va API kaliti kerak; kalitsiz bitta buyruq bilan ishga tushmaydi.
2. **Bir nechta lokal model:** MVP uchun ortiqcha murakkablik keltiradi.
3. **Modelni ilova ichida boshqarish:** qo‘shimcha infratuzilma talab qiladi.
4. **Faqat hostdagi LM Studio (dastlabki reja):** toza mashinada Docker’dan tashqari dastur talab qiladi va topshiriqqa zid.
5. **LLM stub bilan ishga tushirish:** tizim haqiqiy tasnif bermaydi; stub faqat testlar uchun.

## Oqibatlar

### Ijobiy

- AI so‘rovlari tashqi provayderga yuborilmaydi.
- API integratsiyasi sodda bo‘ladi.
- Model natijalarini lokal benchmark qilish mumkin.
- Docker’dan boshqa dastur talab qilinmaydi.

### Salbiy

- Birinchi ishga tushish model yuklanguncha cho‘ziladi (taxminan 23 GB).
- Model katta xotira va disk talab qiladi.
- Toza mashinada CPU’da ishlaydi; ishlash tezligi kompyuter resurslariga bog‘liq va PRD’dagi yo‘naltirish vaqti maqsadiga yetmasligi mumkin.
- Model ishlamasa, ticket qo‘lda tekshirishga yuboriladi.

## Qayta ko‘rib chiqish shartlari

Agar model PRD'dagi aniqlik, Critical recall yoki tezlik maqsadlariga erishmasa yoki maqsadli mashinada ishga tushmasa, boshqa modellar (jumladan kichikroq lokal model) benchmark qilinadi.

## Joriy natijalar (o‘lchangan, 20 yadroli CPU, GPU’siz, WSL2)

- Aniqlik (`eval/report.md`, agent belgilari bilan): kategoriya 96.4%, ustuvorlik 82.9%, Critical recall 8/8. Belgilar muallif tomonidan hali tasdiqlanmagan, shuning uchun bu natija qarorni yakuniy tasdiqlamaydi.
- Tezlik: bittadan so‘rovda p50 9.7 s; ishlab turgan `worker` da (3 parallel so‘rov) bazadagi 1 897 javob bo‘yicha p50 18.9 s, p95 26.9 s, eng sekini 59.0 s; ~620 ticket/soat.
- Xotira: model 22.7 GB RSS. Standart `LLM_TIMEOUT=60` bu mashinada yetmadi (7 ta `llm_unavailable`); lokal `.env` da 120 s ishlatiladi.
- Yo‘naltirish vaqti maqsadi (o‘rtacha < 1 daqiqa) katta CSV import’da bajarilmagan; oddiy yuklamada o‘lchanmagan (TRD 10-bo‘lim). Bu yuqoridagi qayta ko‘rib chiqish shartiga tegishli: GPU’siz CPU’da kichikroq model bilan benchmark hali qilinmagan.

## Egasi uchun qaror

- [ ] Runtime (Compose’dagi Ollama, `qwen3.6:35b-a3b`) va yuqoridagi natijalar asosida qarorni tasdiqlayman.
- [ ] Standart `LLM_TIMEOUT` ni `docker-compose.yml` va `.env.example` da 120 s ga oshirish kerakmi (hozir faqat lokal `.env` da).

Tasdiqlangandan keyin “Holat” qatorini “Qabul qilingan” deb yangilang va sanani yozing.
