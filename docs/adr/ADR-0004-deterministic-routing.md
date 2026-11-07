# ADR-0004: Qoidaga asoslangan deterministik yo‘naltirish

- **Sana:** 2026-11-05
- **Tegishli hujjatlar:** PRD 7-bo‘lim, TRD 5- va 7.3-bo‘limlar
- **Holat:** qabul qilingan va joriy qilingan. Kod: `backend/app/classification/routing.py` (`decide`), `config/routing.yaml`. Testlar: `backend/tests/test_classification_rules.py`.

## Kontekst

TicketLens kelib tushgan murojaatlarni tegishli support jamoalariga avtomatik taqsimlashi kerak.

AI modeli murojaatning kategoriyasi, ustuvorligi va ishonch darajasini aniqlaydi. Biroq ticketni qaysi jamoaga yuborish qarori modelning erkin javobiga bog‘liq bo‘lmasligi kerak.

Model natijalari o‘zgaruvchan bo‘lishi mumkin. Shu sababli bir xil shartlarga ega ticketlar har doim bir xil yo‘naltirish natijasini olishi kerak.

## Qaror

TicketLens qoidaga asoslangan deterministik yo‘naltirishdan foydalanadi. Tartib:

1. Model aniqlagan `category`, `priority` va `confidence` qiymatlari sxema bo‘yicha tekshiriladi.
2. `confidence` belgilangan chegaradan (0.7) past bo‘lsa, ticket `needs_review` holatiga o‘tadi (`low_confidence`).
3. `category = other` bo‘lsa, ticket `needs_review` holatiga o‘tadi (`unclear`).
4. Qolgan kategoriyalar uchun jamoa `config/routing.yaml` dan olinadi (PRD 7-bo‘lim) va ticket `classified` holatiga o‘tadi.

Yo‘naltirish qoidalari konfiguratsiya orqali boshqariladi. Model to‘g‘ridan-to‘g‘ri yo‘naltirish qarorini qabul qilmaydi. Alohida umumiy jamoa yo‘q: mos kelmagan murojaatlarni operator qo‘lda tekshirish navbatida ko‘rib chiqadi. Operator tuzatishida jamoani tanlamasa, jamoa yangi kategoriyadan xuddi shu jadval bo‘yicha olinadi.

## Ko‘rib chiqilgan alternativalar

### 1. Jamoani model tanlaydi

Modeldan ticket uchun to‘g‘ridan-to‘g‘ri jamoani tanlash so‘raladi.

**Rad etildi, chunki:**

- natijalar deterministik bo‘lmasligi mumkin;
- noto‘g‘ri yo‘naltirish ehtimoli yuqori;
- qarorlarni tekshirish va audit qilish qiyinlashadi.

### 2. Aralash yondashuv (model tavsiyasi + qoidalar)

Modeldan yo‘naltirish tavsiyasi olinadi, keyin qoidalar bilan tekshiriladi.

**Rad etildi, chunki:**

- MVP uchun ortiqcha murakkablik keltiradi;
- yo‘naltirish qarorining yagona manbasini saqlash qiyinlashadi.

## Oqibatlar

### Ijobiy

- Bir xil sharoitda bir xil yo‘naltirish natijasi olinadi.
- Qoidalarni test qilish oson.
- Qarorlar tushunarli va audit qilinadi.
- Model almashsa ham yo‘naltirish qoidalari o‘zgarmaydi.
- “Jamoa aniqligi” alohida model xatosi emas: u kategoriya aniqligiga teng.
- Noto‘g‘ri yoki noaniq natijalar qo‘lda tekshirish orqali ko‘riladi.

### Salbiy

- Yangi kategoriyalar uchun qoidalarni qo‘lda yangilash kerak.
- Murakkab holatlarda qoidalar soni ortishi mumkin.
- Model kategoriyani noto‘g‘ri aniqlasa, yo‘naltirish ham noto‘g‘ri bo‘ladi.
- **O‘lchangan cheklov:** model `confidence` qiymati kalibrlanmagan. Saqlangan 1 897 javobning hammasi 0.85–1.0 oralig‘ida, shuning uchun 2-qadam (0.7 chegara) amalda hech bir ticketni ushlab qolmagan. Noaniq ticketlar asosan 3-qadam (`other`) orqali ushlanadi. Chegara va ishonch bahosini qayta ko‘rib chiqish TRD 16-bo‘limda qayd etilgan.

## Tegishli hujjatlar

- [PRD](../PRD.md)
- [TRD](../TRD.md)
