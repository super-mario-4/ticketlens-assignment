# ADR-0004: Deterministic Rule-Based Ticket Routing

- **Date:** 2026-11-05

## Context

TicketLens tizimi kelib tushgan murojaatlarni tegishli support yo'nalishlariga avtomatik taqsimlashi kerak.

AI modeli murojaatning kategoriyasi, ustuvorligi va ishonchlilik darajasini aniqlaydi. Biroq ticketni qaysi jamoaga yuborish qarori AI modelining erkin javobiga bog'liq bo'lmasligi kerak.

AI natijalari o'zgaruvchan bo'lishi mumkin. Shu sababli bir xil shartlarga ega ticketlar har doim bir xil routing natijasini olishi kerak.

## Decision

TicketLens deterministic rule-based routing yondashuvidan foydalanadi.

Routing quyidagi tartibda amalga oshiriladi:

1. AI tomonidan aniqlangan category, priority va confidence qiymatlari tekshiriladi.
2. Confidence belgilangan threshold'dan (0.7) past bo'lsa, ticket `manual_review` holatiga yuboriladi.
3. `security_fraud` kabi xavfsizlik bilan bog'liq murojaatlar tegishli xavfsizlik jamoasiga yo'naltiriladi.
4. Qolgan kategoriyalar oldindan belgilangan routing qoidalari orqali tegishli support jamoalariga yuboriladi.
5. Aniqlanmagan yoki mos kelmaydigan kategoriyalar `general_support` yoki `manual_review` yo'nalishiga yuboriladi.

Routing qoidalari konfiguratsiya orqali boshqariladi. AI modeli to'g'ridan-to'g'ri routing qarorini qabul qilmaydi.

## Alternatives Considered

### 1. AI-Based Routing

AI modelidan ticket uchun to'g'ridan-to'g'ri jamoani tanlash so'raladi.

**Rejected because:**

- Natijalar deterministik bo'lmasligi mumkin.
- Noto'g'ri routing ehtimoli yuqori.
- Qarorlarni tekshirish va audit qilish qiyinlashadi.

### 2. Hybrid AI and Rule-Based Routing

AI modelidan routing tavsiyasi olinadi, keyin qoidalar orqali tekshiriladi.

**Rejected because:**

- MVP uchun ortiqcha murakkablik keltiradi.
- Routing qarorining yagona manbasini saqlash qiyinlashadi.

## Consequences

### Positive

- Bir xil sharoitlarda bir xil routing natijasi olinadi.
- Routing qoidalarini test qilish oson.
- Qarorlar tushunarli va audit qilish mumkin.
- AI modelining o'zgarishi routing qoidalariga ta'sir qilmaydi.
- Noto'g'ri yoki noaniq natijalarni manual review orqali tekshirish mumkin.

### Negative

- Yangi kategoriyalar uchun routing qoidalarini qo'lda yangilash kerak.
- Murakkab holatlarda qoidalar soni ortishi mumkin.
- AI modeli kategoriyani noto'g'ri aniqlasa, routing ham noto'g'ri bo'lishi mumkin.

## Related Documents

- [PRD](../PRD.md)
- [TRD](../TRD.md)
