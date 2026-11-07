# TicketLens

TicketLens — fintech kompaniyasining mijoz murojaatlarini (ticketlarni) avtomatik tasniflaydigan, ustuvorligini belgilaydigan, qisqa xulosa yozadigan va tegishli jamoaga yo‘naltiradigan tizim. Murojaatlar o‘zbek (lotin va kirill), rus tilida va aralash yoziladi. Operator tayyor navbatni ko‘radi va faqat xato yoki noaniq holatlarni tuzatadi.

Batafsil: [PRD](docs/PRD.md) (mahsulot talablari), [TRD](docs/TRD.md) (texnik yechim), [ADR](docs/adr/) (arxitektura qarorlari), [baholash](eval/README.md).

## Asosiy imkoniyatlar

- CSV import (`id, channel, created_at, text, customer_id`), takroriy `id` o‘tkazib yuboriladi (idempotent).
- Maxfiy ma’lumotni bazaga yozishdan oldin maskalash: karta raqami (oxirgi 4 raqam qoladi), CVV, karta muddati, pasport, telefon.
- Lokal LLM orqali kategoriya, ustuvorlik, ishonch darajasi va o‘zbekcha qisqa xulosa.
- Jamoa kategoriyadan `config/routing.yaml` bo‘yicha tanlanadi, model jamoa tanlamaydi (ADR-0004).
- Prompt injection evristikasi: shubhali ticket modelga yuborilmaydi va qo‘lda tekshiriladi.
- Operator ekrani: navbat, qo‘lda tekshirish navbati, ticket sahifasi, tuzatish (tarix bilan), CSV import.
- Rahbar statistikasi: holat, jamoa, kategoriya va ustuvorlik bo‘yicha sonlar, qo‘lda tekshirish va tuzatish ulushi.
- Elasticsearch orqali ko‘p yozuvli qidiruv: “karta” so‘rovi “карта” va “kartam” ni ham topadi.
- 90 kunlik saqlash muddati (retention): muddati o‘tgan ticketlar PostgreSQL va Elasticsearch’dan o‘chiriladi.

## Arxitektura va texnologiyalar

| Servis | Texnologiya | Vazifa |
| --- | --- | --- |
| `web` | React 19, Vite, TypeScript, Tailwind CSS, shadcn/ui (Radix UI), nginx | Operator va rahbar ekrani; `/api/` so‘rovlarini `api` ga uzatadi |
| `api` | Python 3.12, FastAPI, SQLAlchemy 2, Alembic | REST API, import, autentifikatsiya (JWT), tuzatish, statistika |
| `worker` | Python (`api` bilan bitta kod bazasi) | Navbatdagi ticketlarni tasniflash, Elasticsearch outbox, retention |
| `postgres` | PostgreSQL 17 | Asosiy ombor va ishlov navbati (`FOR UPDATE SKIP LOCKED`) |
| `elasticsearch` | Elasticsearch 8.19 | Faqat maskalangan matn bo‘yicha qidiruv (ADR-0002) |
| `llm` | Ollama 0.40, `qwen3.6:35b-a3b` | Lokal LLM, OpenAI-mos API (ADR-0001) |

Topshiriq talab qilgan yangi texnologiya — **Elasticsearch** ([learning note](docs/learning-note.md)). Arxitektura diagrammasi va ma’lumotlar oqimi: TRD 2- va 4-bo‘limlar.

## Talablar va uskuna

- Faqat Docker Engine va Docker Compose v2 (`docker compose`). `make` va `curl` ixtiyoriy.
- **Xotira:** model ishlaganda taxminan 22–23 GB RAM egallaydi (o‘lchangan: 22.7 GB RSS). Docker’ga kamida **28 GB RAM** berish tavsiya etiladi (taklif). 24 GB’da tizim ishladi, lekin bo‘sh xotira ~0.5 GB qoldi va swap ishlatildi.
- **Disk:** kamida **40 GB** bo‘sh joy (model ~23 GB, image’lar va volume’lar).
- **Internet:** birinchi ishga tushishda image’lar va model (~23 GB) yuklab olinadi.
- GPU shart emas; model CPU’da ishlaydi (o‘lchov 20 yadroli CPU’da qilingan).

## Sozlash

`.env` fayli ixtiyoriy: barcha sozlamalarning `docker-compose.yml` da standart qiymati bor. O‘zgartirish uchun:

```bash
cp .env.example .env
```

Asosiy o‘zgaruvchilar: `API_PORT` (8000), `WEB_PORT` (3000), `JWT_SECRET`, `OPERATOR_PASSWORD`, `LEAD_PASSWORD`, `POSTGRES_*`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_TIMEOUT`, `WORKER_CONCURRENCY` (3), `ES_JAVA_OPTS`.

**`LLM_TIMEOUT`:** standart qiymat 60 s. Bu mashinada eng sekin muvaffaqiyatli javob 59.0 s bo‘lgan va 60 s’da 7 ta ticket `llm_unavailable` ga tushgan, shuning uchun lokal `.env` da `LLM_TIMEOUT=120` ishlatiladi (TRD 7.2). Sekin CPU’da ham shunday qilish tavsiya etiladi.

`.env` repozitoriyga kirmaydi (`.gitignore`). Unga haqiqiy sirlarni yozing, `.env.example` ga emas.

## Ishga tushirish

```bash
git clone https://github.com/super-mario-4/ticketlens-assignment.git
cd ticketlens-assignment
docker compose up --build
```

`make up` ham xuddi shu buyruqni bajaradi.

- Ekran: <http://localhost:3000>. API hujjati (Swagger): <http://localhost:8000/docs>.
- **Migratsiya alohida bajarilmaydi:** `api` konteyneri har ishga tushganda `alembic upgrade head` ni o‘zi bajaradi, keyin demo foydalanuvchilarni yaratadi.
- **Model:** `llm` servisi birinchi ishga tushishda modelni `llm_data` volume’iga yuklaydi. Shu vaqtda `web` va `api` ishlayveradi, `worker` esa model tayyor bo‘lguncha ticket olmaydi (ticketlar `pending` holatida kutadi). Keyingi ishga tushirishlarda model volume’dan olinadi.
- **Birinchi ishga tushish vaqti (o‘lchangan, WSL2):** bo‘sh Docker’da `web` va `api` 13 daqiqa 42 soniyada ko‘tarildi, chunki Compose avval barcha image’larni tortadi. Model yuklanishi bunga kirmaydi.
- Holatni tekshirish: `curl http://localhost:8000/api/health/ready` — `postgres`, `elasticsearch` va `llm` holatini qaytaradi.
- To‘xtatish: `docker compose down` (ma’lumotlar volume’larda qoladi). `docker compose down -v` barcha ma’lumotni, jumladan yuklangan modelni ham o‘chiradi.

## Demo foydalanuvchilar

| Login | Parol (standart) | Rol | Ruxsatlar |
| --- | --- | --- | --- |
| `operator` | `operator` | operator | navbat, ticket, tuzatish, qayta tasniflash, CSV import |
| `lead` | `lead` | lead | navbat, ticket ko‘rish, statistika |

> **Ogohlantirish:** bu parollar va `JWT_SECRET` faqat lokal demo uchun. Tizimni boshqa kompyuterlar ochadigan tarmoqda ishlatishdan oldin `.env` da `OPERATOR_PASSWORD`, `LEAD_PASSWORD` va `JWT_SECRET` ni o‘zgartiring. Foydalanuvchilar faqat **birinchi** ishga tushishda yaratiladi: keyin `.env` dagi parol o‘zgarsa, mavjud foydalanuvchining paroli o‘zgarmaydi. Parolni almashtirish uchun uni birinchi ishga tushirishdan oldin o‘rnating.

## Ticketlarni yuklash va ishlatish

1. `operator` bilan kiring va **Import** sahifasida `data/tickets.csv` ni tanlang (10 MB gacha). Yoki terminalda: `make import FILE=data/tickets.csv` (host’da `make` va `curl` kerak).
2. Import natijasi darhol ko‘rinadi: qo‘shilgan, o‘tkazib yuborilgan va xato qatorlar. Mazmunsiz va shubhali (injection) ticketlar shu zahoti qo‘lda tekshirish navbatiga tushadi.
3. `worker` qolgan ticketlarni fonda tasniflaydi. 2 000 ticket bu mashinada taxminan 3.2 soat oladi (~620 ticket/soat).
4. **Navbat:** ustuvorlik (Critical → Low), keyin kelgan vaqt bo‘yicha. Kategoriya, ustuvorlik, jamoa va kanal bo‘yicha filtr, matn bo‘yicha qidiruv.
5. **Qo‘lda tekshirish:** sababi bilan (`no_content`, `unclear`, `low_confidence`, `injection_suspected`, `schema_error`, `llm_unavailable`, `masking_error`).
6. **Ticket sahifasi:** maskalangan matn, AI xulosasi, kategoriya, ustuvorlik, jamoa, ishonch darajasi va tuzatish formasi. Tuzatish alohida yoziladi, AI natijasi o‘chirilmaydi; qo‘lda tekshirilgan ticket o‘z sababini saqlaydi.
7. **Qayta tasniflash:** faqat `llm_unavailable` yoki `schema_error` bo‘lgan ticketlar uchun (“Qayta tasniflash” tugmasi yoki `POST /api/tickets/{id}/reclassify`). Injection ticketlarini shu yo‘l bilan modelga yuborib bo‘lmaydi.
8. **Statistika:** `lead` bilan kiring.

## Testlar va sifat tekshiruvlari

```bash
make test                        # = docker compose run --rm --build tests
```

`tests` servisi `ruff check .` va `pytest` ni haqiqiy PostgreSQL (`ticketlens_test` bazasi) va Elasticsearch (`tickets_test` indeksi) bilan bajaradi; LLM soxta (stub) bilan almashtiriladi. Ishlab turgan stack’ga tegmaslik uchun alohida Compose loyihasida ishlatish mumkin:

```bash
docker compose -p tlverify --profile test run --rm --build tests
docker compose -p tlverify --profile test down -v
```

Frontend: `web` image’ini build qilish `npm ci`, `npm run typecheck`, `npm run lint` va `npm run build` ni bajaradi:

```bash
docker compose build web
```

CI (`.github/workflows/ci.yml`) har bir push’da backend lint va testlarni, barcha image’larni build qilishni va `postgres`, `elasticsearch`, `api`, `web` bilan health smoke testni bajaradi. CI’da model yuklanmaydi.

## Baholash (evaluation)

Batafsil: [eval/README.md](eval/README.md). Ishga tushirish (stack ishlab turgan va ticketlar import qilingan bo‘lishi kerak):

```bash
docker compose stop worker   # model bir vaqtda ikkalasiga xizmat qila olmaydi
make eval                    # eval/report.md ni qayta yozadi
docker compose start worker
make bench                   # eval/bench.md, saqlangan natijalardan
```

**Joriy natija** (`eval/report.md`, prompt `v2`, 111 ta baholangan ticket):

| Ko‘rsatkich | Natija | Maqsad |
| --- | --- | --- |
| Kategoriya aniqligi | 107/111 = 96.4% | ≥ 85% |
| Ustuvorlik aniqligi | 92/111 = 82.9% | ≥ 80% |
| Critical recall | 8/8 = 100% | ≥ 95% |
| Qo‘lda tekshirishga tushgan | 3/111 = 2.7% | ≤ 15% |
| To‘g‘ri JSON | 119/119 = 100% | ≥ 98% |

**Bu natijalarga ehtiyot bo‘lib qarash kerak:**

- **Belgilarni AI agent yozgan, muallif hali tekshirmagan.** Topshiriq “o‘zingiz belgilagan kamida 50 ta ticket” talab qiladi; bu talab hali bajarilmagan. Tekshirish tartibi: `eval/README.md`.
- Prompt `v2` shu to‘plam natijasini ko‘rgandan keyin o‘zgartirilgan (`v1` da ustuvorlik 77.5% edi), shuning uchun `v2` raqamlari mustaqil emas.
- Critical holatlar faqat 8 ta: 100% natijaning 95% ishonch oralig‘i 67.6–100%.
- Ruscha lotin harfida yozilgan matnlarda ustuvorlik aniqligi past: 6/11 = 54.5%.
- Dataset kam sonli shablonlardan tuzilgan; natija faqat shu to‘plam uchun.

## Ma’lum cheklovlar va xavflar

- **Yo‘naltirish vaqti maqsadi bajarilmagan.** PRD maqsadi — o‘rtacha 1 daqiqadan kam. 2 000 ticketli CSV bir vaqtda navbatga tushgani uchun bazada `classified_at − ingested_at` o‘rtachasi ~15.7 soat (o‘lchangan). Bu asosan navbatda kutish. Bitta ticketga model vaqti: p50 18.9 s, p95 26.9 s (3 parallel so‘rov, o‘lchangan). Kuniga 3 000 ticketlik oddiy yuklamada (125 ticket/soat, sig‘im ~620/soat) maqsad bajarilishi *kutiladi*, lekin bu o‘lchanmagan.
- **Ishonch darajasi kalibrlanmagan:** saqlangan 1 897 javobning hammasida 0.85–1.0, ya’ni 0.7 chegara amalda ishlamaydi; `low_confidence` holati bir marta ham uchramagan.
- **Uskuna:** model katta RAM va disk talab qiladi; kichik mashinada ishga tushmasligi yoki swap tufayli sekinlashishi mumkin.
- **Toza Linux mashinada tekshirilmagan:** ishga tushirish Windows’dagi WSL2 Docker’da, bo‘sh Docker daemon bilan tekshirilgan. Alohida Linux mashinada tekshirish tartibi quyida.
- **99.99% uptime kafolatlanmaydi:** bitta mashina, replikatsiya va zaxira nusxa yo‘q (PRD №4).
- **Real kanallar yo‘q:** Telegram, email va web-forma bilan integratsiya MVP’dan tashqarida; ma’lumot CSV orqali keladi.
- **Injection evristikasi** naqshlarga asoslangan va har qanday urinishni topishga kafolat bermaydi; prompt va JSON sxema qo‘shimcha himoya qatlamlari.
- `llm` javob bermasa, ticket ikki urinishdan keyin `llm_unavailable` bo‘ladi va operator uni qo‘lda qayta tasniflashi kerak.

## Xavfsizlik va maxfiy ma’lumotlar

- Xom matn hech qayerda saqlanmaydi: maskalash import paytida, bazaga, Elasticsearch’ga va LLM’ga yuborishdan oldin bajariladi (ADR-0003). Yuklangan CSV diskka yozilmaydi.
- Maskalash xato bersa, ticket matnsiz `masking_error` holatida saqlanadi va modelga yuborilmaydi (fail-closed).
- Loglarda ticket matni yozilmaydi; nginx access log o‘chirilgan.
- Model lokal ishlaydi: tashqi AI provayderiga hech narsa yuborilmaydi.
- Ma’lumotlar 90 kun saqlanadi (`retention_days`, `backend/app/core/config.py`); muddati o‘tgan ticketlarni `worker` kuniga bir marta o‘chiradi.
- Butun dataset bo‘yicha maxfiylik testlari: `backend/tests/test_imports_api.py` (`test_whole_dataset_import_and_privacy`) va `backend/tests/test_search_index.py` (`test_whole_dataset_reaches_the_index_masked`).

## Toza Linux mashinada tekshirish tartibi

Hali bajarilmagan; taqdimotdan oldin tavsiya etiladi.

1. Ubuntu 24.04 (yoki boshqa Linux), kamida 28 GB RAM, 40 GB bo‘sh disk, faqat Docker Engine va Compose plagini o‘rnatilgan; `make` va Python shart emas.
2. `git clone ...` va `cd ticketlens-assignment`; `.env` yaratmang.
3. `time docker compose up --build` va boshqa terminalda `docker compose ps` bilan barcha servislar `healthy` bo‘lishini kuting (`llm` model yuklanguncha `starting` bo‘lib turadi).
4. `curl http://localhost:8000/api/health/ready` da `"llm":"ok"` chiqishini kuting.
5. <http://localhost:3000> da `operator` / `operator` bilan kiring va `data/tickets.csv` ni import qiling.
6. Bir necha daqiqadan keyin navbatda `classified` ticketlar paydo bo‘lishini va ticket sahifasida xulosa ko‘rinishini tekshiring.
7. Natijani (vaqt, xotira — `docker stats`, xatolar) TRD 13-bo‘limga yozing.

## Keyingi ikki haftada nima qilinadi

1. **Baholash:** muallif belgilarni tekshiradi; keyin modeldan mustaqil yangi 100+ ticketli to‘plam belgilanib, prompt o‘zgarishlarisiz qayta baholanadi. Ikkinchi belgilovchi bilan kelishuv o‘lchanadi.
2. **Ishonch darajasini kalibrlash:** model o‘z bahosi o‘rniga tuzatishlar tarixi asosida chegara tanlash yoki bir nechta javob kelishuvini o‘lchash.
3. **Yo‘naltirish vaqtini to‘g‘ri o‘lchash:** oddiy yuklama (125 ticket/soat) bilan sinov va navbatda kutish vaqtini model vaqtidan alohida statistikada ko‘rsatish.
4. **Tezlik va narx:** GPU’da va kichikroq model bilan benchmark; ruscha-lotin matnlar uchun aniqlikni oshirish.
5. **Ishonchlilik:** LLM xatolarida kutish vaqtini oshirib qayta urinish, HTTP status kodini loglash, monitoring va zaxira nusxa.
6. **Foydalanuvchilar:** parolni almashtirish, foydalanuvchi qo‘shish va audit logi.
7. **Real kanallar:** Telegram bot va email qabul qilish.
8. **Frontend testlari** (Vitest) va brauzerda end-to-end test.

## Repozitoriy tuzilmasi

| Yo‘l | Tarkibi |
| --- | --- |
| `backend/` | FastAPI ilova (`app/`), Alembic migratsiyalari, pytest testlari |
| `web/` | React frontend (`src/app`, `src/features`, `src/shared`) |
| `config/routing.yaml` | Kategoriya → jamoa |
| `data/tickets.csv` | Namuna dataset (o‘zgartirilmaydi) |
| `eval/` | Etalon belgilar, baholash va tezlik hisobotlari, tekshirish workbook’lari |
| `docs/` | PRD, TRD, ADR, learning note, AI log |
| `ai-usage/` | AI agentlarga berilgan promptlar logi (hook’lar yozadi) |
| `AGENTS.md` | AI agentlar uchun ko‘rsatmalar |
