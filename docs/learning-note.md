# Learning note: Elasticsearch

> **Holat: deyarli tayyor qoralama.** Matnni AI agent loyiha tarixi, kod, testlar va `docs/ai-log.md` dagi yozuvlar asosida yozgan. Shaxsiy tajriba haqidagi qismlar **“Egasi to‘ldiradi”** deb belgilangan: agent ularni egasi nomidan yoza olmaydi. Topshiriq “qanday o‘rgandingiz va sizni nima hayratlantirdi” deb so‘raydi, shuning uchun bu maydonlar to‘ldirilmaguncha hujjat tugallangan hisoblanmaydi.

## 1. Tanlangan texnologiya

Topshiriqning 5-bo‘lim, 3-bandidagi ro‘yxatdan **Elasticsearch** tanlangan (ADR-0002). U maskalangan ticket matnlari bo‘yicha qidiruv uchun ishlatiladi; asosiy ma’lumot manbasi PostgreSQL bo‘lib qoladi.

**Egasi to‘ldiradi:** Elasticsearch’ni avval production’da ishlatmaganingizni tasdiqlang: `[ ] tasdiqlayman` — avvalgi tajribangiz (agar bo‘lsa): ______

## 2. Nima uchun aynan shu texnologiya

Ticketlar to‘rt xil yozuvda keladi: o‘zbek lotin, o‘zbek kirill, rus va lotin harfida ruscha; apostrof ham turlicha (`'`, `‘`, `’`, `ʻ`). Operator “karta” deb qidirsa, “карта” va “kartam” ham topilishi kerak. SQL `ILIKE` buni qila olmaydi. ClickHouse (tahlil), Temporal (workflow), Qdrant (vektor qidiruv) va k3s + Helm (orkestratsiya) bu muammoni to‘g‘ridan-to‘g‘ri hal qilmaydi; Elasticsearch esa aynan matn qidiruvi uchun.

**Egasi to‘ldiradi:** boshqa variantlarni ko‘rib chiqqanmisiz va tanlovga nima ta’sir qildi? ______

## 3. Loyihada qanday ishlatildi

Kodda tekshirish mumkin bo‘lgan qadamlar, ehtiyoj tug‘ilgan tartibda:

1. Compose’da bitta tugun (`discovery.type: single-node`), 512 MB heap, lokal rejimda xavfsizlik o‘chiq (`docker-compose.yml`).
2. Injection tekshiruvi uchun yozilgan `fold_text` funksiyasi qayta ishlatildi: indekslanadigan va qidiriladigan matn bir xil ko‘rinishga keltiriladi (kichik harf, yozuvni lotinga o‘tkazish, apostroflarni birlashtirish).
3. Indeks uchun maxsus analyzer: `standard` tokenizer, `lowercase`, so‘ng 2–20 belgili `edge_ngram`. `_analyze` so‘rovi bilan “kartam” uchun nima saqlanishi tekshirildi: `ka`, `kar`, `kart` va hokazo (`backend/app/search/`).
4. Outbox jadvali (`search_index_outbox`, migratsiya `0004`): Elasticsearch ishlamasa ham ticket saqlanadi, `worker` vazifalarni `_bulk` API orqali qayta yuboradi.
5. Qidiruv natijasi (ko‘pi bilan 1 000 ta ID) PostgreSQL’ga qaytariladi, filtr va sahifalash o‘sha yerda bajariladi; relevantlik tartibi `array_position` bilan saqlanadi.
6. Testlar mock bilan emas, haqiqiy tugun bilan: `backend/tests/test_search_index.py` (12 ta test), jumladan butun datasetning indeksga faqat maskalangan holda tushishi (`test_whole_dataset_reaches_the_index_masked`).

## 4. Qanday o‘rganildi

**Egasi to‘ldiradi:** nimani o‘qidingiz (hujjat, maqola, video), nimani o‘zingiz sinab ko‘rdingiz, AI agentdan nimalarni so‘radingiz va uning javobini qanday tekshirdingiz. ______

Loyiha yozuvlarida ko‘rinadigan o‘rganish usuli: analyzer natijasini `_analyze` bilan tekshirish, testlarni haqiqiy tugunga qarshi ishlatish va bulk javobdagi har bir element holatini o‘qish. Bular kod va testlarda bor; egasi ularning qaysi birini o‘zi qilgani yoki tekshirganini yozishi kerak.

## 5. Ish davomida aniqlangan faktlar

Quyidagilar loyiha davomida haqiqatan uchragan va kod yoki testlarda aks etgan. Ularning qaysi biri **sizni** hayratlantirganini egasi tanlaydi.

- Indekslash va qidiruv analyzer’lari har xil bo‘lishi kerak. So‘z boshlari (`edge_ngram`) faqat indeksda: qidiruvda ham ishlatilsa, so‘rov ham bo‘laklarga bo‘linadi va “karta” “ka” bilan boshlanadigan hamma narsaga mos keladi.
- `_bulk` so‘rovi ichidagi elementlar xato bersa ham HTTP 200 qaytaradi. Har bir elementning o‘z holati bor, klient ularni o‘qishi shart. Allaqachon o‘chirilgan hujjatni o‘chirish 404 element beradi — bu loyihada xato emas.
- Yangi hujjat keyingi refresh’gacha qidiruvda ko‘rinmaydi, shuning uchun testlar qidirishdan oldin `_refresh` chaqiradi.
- Bitta tugunda standart bitta replika bilan klaster hech qachon `green` bo‘lmaydi: replika o‘z primary’si bilan bir tugunda tura olmaydi. `number_of_replicas: 0` buni tuzatadi.
- 512 MB heap bilan konteyner `docker stats` da taxminan 420–640 MB egalladi. Bu yerda muhim: model boshqa narsalarga juda kam xotira qoldiradi (TRD 13-bo‘lim).
- Indeks kutilganidan ancha kichik: 2 000 ticket so‘z boshlari bilan birga 476 KB egalladi.

**Egasi to‘ldiradi:** sizni eng ko‘p nima hayratlantirdi va nima uchun? ______

## 6. Boshqa texnologiyalardan amaliy saboqlar (loyiha misollari bilan)

| Soha | Nima bo‘ldi | Qayerda ko‘rinadi |
| --- | --- | --- |
| Docker Compose | PostgreSQL healthcheck Unix socket orqali birinchi init paytida ham “healthy” bo‘lib qolgan, API migratsiyasi bir marta yiqilgan; endi TCP orqali tekshiriladi. Compose barcha image’larni oldin tortadi: birinchi ishga tushish 13 daq 42 s. | `docker-compose.yml`, `docs/ai-log.md` |
| FastAPI | Multipart yuklashda katta fayl diskka tushmasligi uchun middleware hajmni kelish paytida cheklaydi; Swagger orqali fayl tanlash ishlaydi. | `backend/app/api/middleware.py`, `test_imports_api.py` |
| PostgreSQL | `review_reason = 'masking_error'` sharti ikkala ustun NULL bo‘lganda NULL qaytargan va noto‘g‘ri qatorni o‘tkazib yuborgan; `IS NOT DISTINCT FROM` bilan tuzatildi. Navbat `FOR UPDATE SKIP LOCKED` bilan. | migratsiya `0002`, `test_ticket_models.py` |
| LLM integratsiyasi | Ollama model yuklanmaguncha `"data": null` qaytaradi, mock’lar esa `[]` ishlatgan; buni faqat haqiqiy konteyner ko‘rsatdi. 60 s timeout eng sekin javobga (59.0 s) juda yaqin bo‘lib chiqdi, 7 ta ticket `llm_unavailable` ga tushdi; lokal `LLM_TIMEOUT=120` bilan qayta tasniflashda hammasi o‘tdi. | `classification/llm.py`, TRD 7.2 |
| Prompt injection | Birinchi detektor 21 tadan 18 tasini topgan; beshinchi shablon (kalit so‘zsiz ruscha rol almashtirish) son TRD bilan solishtirilganda topildi. | `preprocess/injection.py`, `test_preprocess.py` |
| Baholash | `v1` da ustuvorlik 77.5% bo‘lgan; `v2` 82.9% ga chiqdi, lekin shu to‘plamda sozlangani uchun mustaqil emas. Belgilarni agent yozgan — muallif tekshiruvi kerak. | `eval/README.md` |
| AI bilan ishlash | Agent ishlab turgan bazaga qarshi tekshiruv ishlatib, muallifning import qilingan ticketlarini o‘chirib yuborgan; shundan keyin barcha tekshiruvlar alohida Compose loyihasida. Agent “tayyor” degan joylarni qayta ishga tushirib tekshirish kerak bo‘ldi. | `docs/ai-log.md` |

**Egasi to‘ldiradi:** shu saboqlardan qaysi biri keyingi loyihangizda ishlash usulingizni o‘zgartiradi? ______
