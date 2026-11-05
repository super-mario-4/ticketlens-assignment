# ADR-0002: PostgreSQL asosiy ombor, Elasticsearch qidiruv uchun

- **Sana:** 2026-11-05
- **Tegishli hujjatlar:** PRD 5–9-bo‘limlar, TRD 2–6-bo‘limlar

## Kontekst

TicketLens ticketlarni saqlashi, qayta ishlashi, operator tuzatishlari va audit tarixini yuritishi kerak. Operatorlar esa ko‘p tilli ticket matnlaridan qidirishi kerak.

Kutilayotgan yuklama kuniga taxminan 3 000 ta murojaat.

## Qaror

PostgreSQL tizimning asosiy ma’lumotlar ombori bo‘ladi. Elasticsearch faqat matnli qidiruv uchun ishlatiladi.

- Ticketlar, importlar, tasniflar va tuzatishlar PostgreSQL'da saqlanadi.
- Ishlov navbati PostgreSQL orqali boshqariladi.
- Elasticsearch faqat maskalangan ticket matnini indekslaydi.
- Elasticsearch'dan olingan ID'lar bo‘yicha yakuniy ma’lumot PostgreSQL'dan olinadi.
- Indekslashdagi xatolar `search_index_outbox` orqali qayta ishlanadi.
- Retention muddati tugaganda ikkala tizimdagi tegishli ma’lumotlar o‘chiriladi.

## Ko‘rib chiqilgan alternativalar

1. **Faqat PostgreSQL:** sodda, lekin ko‘p tilli matnli qidiruv imkoniyatlari cheklangan.
2. **Elasticsearch'ni asosiy ombor qilish:** tranzaksion ma’lumotlar uchun qo‘shimcha murakkablik tug‘diradi.
3. **Kafka yoki boshqa broker:** MVP uchun ortiqcha infratuzilma.

## Oqibatlar

### Ijobiy

- PostgreSQL yagona ishonchli ma’lumot manbasi bo‘ladi.
- Elasticsearch matnli qidiruvga ixtisoslashadi.
- Alohida message broker talab qilinmaydi.

### Salbiy

- Ikkita servisni boshqarish kerak.
- Elasticsearch indeksi PostgreSQL bilan vaqtincha nomuvofiq bo‘lishi mumkin.
- Outbox va retry mexanizmini implementatsiya qilish kerak.

## Qayta ko‘rib chiqish shartlari

Agar PostgreSQL qidiruvi PRD talablarini yetarli darajada bajarsa yoki Elasticsearch resurs sarfi yuqori bo‘lsa, qaror qayta baholanadi.
