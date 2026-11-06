# ADR-0003: Maxfiy ma’lumotlarni saqlashdan oldin maskalash

- **Sana:** 2026-11-05
- **Tegishli hujjatlar:** PRD 5, 6, 9–11-bo‘limlar, TRD 4, 5, 8-bo‘limlar

## Kontekst

Ticket matnlarida karta raqami, CVV/CVC, karta muddati, pasport va telefon raqamlari uchrashi mumkin.

Support rahbari barcha xom xabarlarni, karta raqamlari bilan, audit uchun abadiy saqlashni so‘ragan (topshiriq, 3-talab). PRD 10-bo‘limda bu talab asoslangan holda rad etilgan: maxfiy ma’lumotlar bazada va AI so‘rovlarida bo‘lmasligi kerak.

## Qaror

Ticket matni PostgreSQL'ga yozilishidan, Elasticsearch'ga indekslanishidan yoki LLM'ga yuborilishidan oldin tozalanadi va maxfiy ma’lumotlari maskalanadi.

- Karta raqamining faqat oxirgi 4 raqami qoldiriladi.
- CVV/CVC to‘liq o‘chiriladi.
- Karta amal qilish muddati o‘chiriladi.
- Pasport va telefon raqamlari maskalanadi.
- Xom CSV diskka saqlanmaydi.
- Loglarda ticket matni yozilmaydi.
- Maskalash xato bersa, xom matn hech qayerga yozilmaydi va LLM'ga yuborilmaydi (`fail-closed`).
- Ma’lumotlar 90 kunlik retention siyosati bo‘yicha o‘chiriladi.

## Ko‘rib chiqilgan alternativalar

1. **Faqat LLM'dan oldin maskalash:** bazada yoki loglarda maxfiy ma’lumot qolishi mumkin.
2. **Xom matnni shifrlab saqlash:** CVV shifrlangan holda ham saqlanmasligi kerak, kalit sizib chiqsa esa barcha karta ma’lumotlari ochiladi; audit uchun maskalangan matn va tuzatishlar tarixi yetarli deb hisoblanadi.
3. **Faqat frontendda maskalash:** backend va AI qatlamini himoya qilmaydi.

## Oqibatlar

### Ijobiy

- Maxfiy ma’lumotlar asosiy ombor va AI so‘rovlariga tushmaydi.
- Maskalash yagona pipeline'da bajariladi.
- Xato holatlar xavfsiz boshqariladi.

### Salbiy

- Dataset formatlariga mos maskalash qoidalari kerak.
- Noto‘g‘ri maskalash ticket mazmunining bir qismini yo‘qotishi mumkin.
- Testlar bilan tekshirish zarur.

## Qayta ko‘rib chiqish shartlari

Yangi maxfiy ma’lumot formatlari aniqlansa, maskalash qoidalari va testlari yangilanadi.
