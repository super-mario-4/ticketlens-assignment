# AI log

Asosiy AI agent sessiyalari, muhim promptlar, agent xato qilgan holatlar va ular qanday aniqlangani, taxminiy token va xarajat. Promptlarning aynan matni `ai-usage/` da (hook’lar yozadi). Bu hujjatdagi har bir raqam `ai-usage/*.jsonl` dagi yozuvlardan olingan; yozuvi yo‘q narsa taxmin qilinmagan.

## Umumiy ko‘rinish

| Sessiya (`ai-usage/`) | Vosita va model | Vaqt (UTC) | Promptlar | Xarajat va tokenlar (yozuvdan) |
| --- | --- | --- | --- | --- |
| `2026-11-06_claude_aac7a993` | Claude Code 2.1.318 | 11-06 09:03 | 1 | $0; ish bajarilmagan (sessiya darhol yopilgan) |
| `2026-11-06_claude_105e3fbd` | Claude Code 2.1.318 | 11-06 09:08 | 1 | $0; ish bajarilmagan |
| `2026-11-06_claude_4cccfcf6` | Claude Code 2.1.319, Opus 5.5 (+ Haiku 5.5) | 11-06 09:15 – 20:32 | 17 | **$36.45**; Opus: 15K kirish, 610K chiqish, 195K fikrlash, 78.0M cache o‘qish, 1.07M cache yozish token; Haiku: $0.02. 11 536 qator qo‘shilgan |
| `2026-11-07_claude_c064d082` | Claude Code, Opus 5.5 | 11-07 07:58 – davom etmoqda | 11 (shu yozuvgacha) | Sessiya hali tugamagan: `end` qatori yo‘q, xarajat **noma’lum** |
| `ai-usage/manual.md` | ChatGPT-5 (web) | 11-06, 15:00 – 23:00 va “01:30” (yozuvdagi vaqtlar, vaqt zonasi ko‘rsatilmagan) | 13 | Yozuvlarda `Usage:` qatori yo‘q, xarajat **noma’lum** |

Jami yozilgan xarajat: **$36.45** (faqat tugagan Claude Code sessiyalari; ChatGPT xarajati yozilmagan).

## Kim nima qildi

- **AI agent (Claude Code):** backend, frontend, testlar, Docker va CI kodi; `eval/labels.csv` dagi belgilar; baholash va benchmark ishga tushirish; PRD/TRD/ADR’ga tuzatishlar; ushbu log, README, AGENTS.md, learning note qoralamasi; tekshirish workbook’lari.
- **ChatGPT-5 (web), egasi ishlatgan:** Claude Code uchun bosqichma-bosqich promptlarni tayyorlash, loyihani topshiriq bilan solishtirish uchun prompt yozish, README’ni tiklash buyrug‘ini tuzish, login xatosini muhokama qilish (`ai-usage/manual.md`, 13 ta yozuv).
- **Egasi (muallif):** har bir bosqich vazifasi va cheklovlari (promptlar); 2026-11-05 dagi PRD, TRD va ADR commit’lari (egasining `manual.md` dagi birinchi yozuviga ko‘ra, PRD, TRD va ADR’larni u o‘zi yaratgan); README’ni asl holatiga qaytarish va keyinroq (2026-11-07) o‘zbekcha README’ga ruxsat berish; ADR-0001 bo‘yicha ishlashni buyurish; ishlab turgan bazani testlardan himoya qilish talabi; `LLM_TIMEOUT=120` ga oshirish, 7 ta ticketni qayta tasniflash va konteynerlarni qayta yaratish qarori; `3765a8b` commit’i.
- **Egasi 2026-11-07 da tasdiqladi:** ADR-0001 (lokal model qarori).
- **Egasi hali qilmagan:** belgilarni tekshirish (`eval/README.md`), learning note’ning shaxsiy qismlari.

## Logdagi bo‘shliqlar

- **2026-11-04 va 2026-11-05:** `ai-usage/` da bu kunlar uchun hech qanday yozuv yo‘q: hook yozuvlari ham, `ai-usage/manual.md` dagi yozuvlar ham 2026-11-06 dan boshlanadi. PRD, TRD va ADR’lar 2026-11-05 da commit qilingan. **Egasi to‘ldiradi:** agar shu kunlari chat ilovasi yoki boshqa AI ishlatilgan bo‘lsa, promptlarni `ai-usage/manual.md` ga uning formatida qo‘shing; ishlatilmagan bo‘lsa, shu yerda yozing: ______
- **ChatGPT xarajati:** `ai-usage/manual.md` dagi 13 ta yozuvning hech birida `Usage:` qatori yo‘q (fayl formati sessiya oxirida shunday qatorni talab qiladi). **Egasi to‘ldiradi:** ilova ko‘rsatgan foydalanishni yoki “unknown” ni qo‘shing.
- `4cccfcf6` sessiyasidagi quyidagi bosqichlar bitta sessiya ichida bo‘lgan; har bir bosqich uchun alohida xarajat yozilmagan, faqat sessiya jami bor.

## 2026-11-06 · Claude Code · Opus 5.5 · Backend rejasi va hujjatlarni ko‘rib chiqish

**Muhim promptlar**

- Spec va datasetni o‘qib, kod yozmasdan backend rejasini taklif qilish.
- PRD, TRD, ADR va README’ni `TicketLens_Task.md` bilan solishtirib tuzatish.

**Natija**

- `data/tickets.csv` tahlil qilindi va TRD’dagi dataset faktlari tuzatildi.
- “Bitta buyruq” talabini bajarish uchun LLM faqat host’dagi LM Studio’dan Docker Compose ichiga ko‘chirildi (egasi tasdig‘ini kutib).
- `README.md` topshiriqda aytilgan deliverable sifatida qayta yozildi.

**Agent qayerda xato qildi**

- Rejada agent LM Studio’ni README’da shart qilib qo‘yishni va toza mashina uchun stub qo‘shishni taklif qilgan. Topshiriq bilan solishtirish bu “faqat Docker o‘rnatilgan” talabiga mos emasligini ko‘rsatdi: stub haqiqiy tasnif bermaydi.
- Agentning birinchi injection qidiruvi 18 ta ticket topgan. Datasetni gap darajasida ko‘rib chiqish 21 tasini topdi.

**Keyingi tuzatish:** README’ni qayta yozish egasining talabi bilan bekor qilindi va fayl asl shablon holatiga qaytarildi.

## 2026-11-06 · Claude Code · Opus 5.5 · Backend asosi

**Muhim prompt**

- Backend asosini qurish: FastAPI, SQLAlchemy 2 va Alembic bilan PostgreSQL, sozlamalar, health check’lar va Docker; hammasi konteyner ichida ishlaydi.

**Natija**

- Qatlamli FastAPI ilova, Alembic boshlang‘ich migratsiyasi, `postgres`, `elasticsearch` va `api` Compose servislari hamda talab bo‘yicha ishlaydigan `tests` servisi qo‘shildi.
- Bo‘sh volume’lardan `.env` siz ishga tushish tekshirildi; `/api/health/ready` ni tekshirish uchun PostgreSQL va Elasticsearch haqiqatan to‘xtatildi.

**Agent qayerda xato qildi**

- Birinchi 15 ta testdan ikkitasi test xatolari tufayli yiqildi: biri standart foydalanuvchi nomiga teng parol ishlatgan, ikkinchisi o‘zgargan FastAPI ichki qismlarini o‘qigan. Docker’dagi test ishga tushirish ikkalasini ko‘rsatdi.
- Agentning birinchi hisoboti ishga tushirishni “tekshirilgan” degan, lekin PostgreSQL healthcheck Unix socket’dan foydalangan va birinchi init paytida ham o‘tib ketishi mumkin edi. PostgreSQL 0.1 CPU bilan cheklanganda API migratsiyasi bir marta yiqildi. Endi healthcheck TCP orqali.
- Bo‘sh daemon’dagi birinchi ishga tushirish jim yiqildi: `tar` arxiv yo‘lidagi `C:` ni masofaviy host deb o‘qidi, repozitoriy ko‘chirilmadi, skript esa 25 daqiqa kutdi. Logda testlar umuman ishlamagan bo‘lsa ham `tests exit 0` chiqdi. Egasi holatni so‘ragach log sababni ko‘rsatdi va skript birinchi xatoda to‘xtaydigan qilib qayta yozildi.

## 2026-11-06 · Claude Code · Opus 5.5 · Ticket ma’lumotlar modeli

**Muhim prompt**

- Ticket ma’lumotlar modeli, Alembic migratsiyasi, repository va baza testlari; AI, routing va frontend’siz.

**Natija**

- `users`, `import_jobs`, `tickets`, `classifications` va `corrections` jadvallari, `0002` migratsiyasi va `TicketRepository` qo‘shildi.
- TRD talabiga ko‘ra kategoriya, ustuvorlik va jamoa `tickets` jadvalida saqlanmaydi: amaldagi qiymat eng so‘nggi tuzatishdan, u bo‘lmasa eng so‘nggi AI natijasidan olinadi.

**Agent qayerda xato qildi**

- `tickets` matn shartining birinchi varianti `review_reason = 'masking_error'` ishlatgan. Ikkala ustun NULL bo‘lganda u NULL qaytardi va PostgreSQL matnsiz va sababsiz ticketni qabul qildi. Cheklov testi buni ushladi; endi shart `IS NOT DISTINCT FROM` ishlatadi.
- Bitta indeks testi PostgreSQL `source_ticket_id` unique cheklovini indeks sifatida ko‘rsatishini kutmagan. Docker’dagi test buni ko‘rsatdi.

## 2026-11-06 · Claude Code · Opus 5.5 · Ticket import pipeline’i

**Muhim prompt**

- Tekshiruv, takroriy qatorlar, PII maskalash, prompt injection, import jarayonini kuzatish, API endpoint’lar va testlar bilan CSV import; LLM, routing va frontend’siz.

**Natija**

- `preprocess` moduli, `ImportService`, `POST /api/imports` va `GET /api/imports/{id}` qo‘shildi.
- Butun dataset 21 ta injection, 82 ta mazmunsiz ticket bilan import qilinadi; bazada, javoblarda va loglarda xom maxfiy ma’lumot yo‘q.

**Agent qayerda xato qildi**

- Birinchi detektor 21 ta injection ticketidan 18 tasini topgan. Sonni TRD bilan solishtirish beshinchi shablonni ko‘rsatdi: odatdagi kalit so‘zlarsiz ruscha rol almashtirish.
- Birinchi karta naqshi keyingi `11/27` dagi oyni qo‘shimcha raqam sifatida olgan va muddatning bir qismi matnda qolgan. Unit test buni ushladi; datasetda bunday holat yo‘q.
- Agentning `sed` tuzatishi qo‘llanmadi, skripti esa testlar yiqilgandan keyin ham end-to-end yuklashni ishga tushirdi va ilova bazasiga 2 000 ta test ticketi tushdi. Chiqish ikkalasini ko‘rsatdi. Tuzatish qayta qilindi, test ma’lumotlari o‘chirildi.

## 2026-11-06 · Claude Code · Opus 5.5 · Multipart CSV yuklash

**Muhim prompt**

- `POST /api/imports` ni import mantiqini saqlab, Swagger’da fayl tanlash bilan multipart `UploadFile` ga o‘tkazish va testlar qo‘shish.

**Natija**

- `UploadFile` va `File` qo‘shildi, image’ga `python-multipart` kiritildi. Chegaradagi yuklamalar xotirada qoladi, middleware esa katta yuklamani kelish paytida to‘xtatadi, shuning uchun xom CSV diskka tushmaydi.
- Headless Chromium Swagger’dagi fayl tanlash va u orqali ishlaydigan yuklashni tasdiqladi.

**Agent qayerda xato qildi**

- Agent end-to-end tekshiruvini ilova bazasiga qarshi ishlatdi. Skript `rows before: 2005` ni chiqardi-yu, baribir shartsiz `DELETE` larni bajardi va o‘sha paytda stack’dan foydalanayotgan muallifning import qilingan ticketlari va import tarixini o‘chirdi. Zaxira nusxa yo‘q edi. 2 000 ticket `data/tickets.csv` dan yangi ichki ID’lar bilan qayta tiklandi; import tarixi yo‘qoldi. Shundan keyin barcha tekshiruvlar alohida Compose loyihasida bajariladi.
- Oldingi `test_upload_is_not_written_to_disk` juda zaif edi: yuklama 1 MB chegaradan kichik bo‘lgan va noto‘g‘ri funksiya almashtirilgan. Yangi testlar har bir himoyani olib tashlab, testning yiqilishini ko‘rish bilan tekshirildi.

## 2026-11-06 · Claude Code · Opus 5.5 · Tasniflash va routing

**Muhim prompt**

- Tasniflash, saqlash, routing, ishonch darajasi, ishlov jarayoni va testlar. ADR-0001 hali kutilayotgan bo‘lsa, faqat provayderga bog‘liq bo‘lmagan qismlarni qurish va to‘siqlarni aytish.

**Natija**

- ADR-0001 hali kutilayotgani uchun LLM adapteri, provayder yoki `worker` servisi qo‘shilmadi.
- Javob sxemasi, prompt, `Classifier` interfeysi, `config/routing.yaml`, routing qarorlari va `ClassificationService` qo‘shildi. Hammasi soxta classifier bilan testlangan, shuning uchun haqiqiy model sifati haqida hech narsa aytmaydi.

**Agent qayerda xato qildi**

- Ticket tegini ekranlashning birinchi varianti `< /ticket>` va `<ticket id="1">` ni o‘tkazib yuborgan, buning uchun yozilgan test esa buni aniqlay olmagan. Testni ko‘rib chiqish bosqich tugashidan oldin bo‘shliqni topdi.

## 2026-11-06 · Claude Code · Opus 5.5 · LLM integratsiyasi va worker

**Muhim prompt**

- 5-bosqichni ADR-0001 ga aniq amal qilib bajarish. Bosqichlarni hech qaysi hujjat belgilamagan, shuning uchun hajm egasining izohi va 4-bosqich to‘siqlaridan olindi: runtime, adapter, worker, `/api/health/ready` dagi LLM holati va reclassify endpoint’i.

**Natija**

- `llm` va `worker` Compose servislari, `LLMClassifier`, `app/worker.py` va `POST /api/tickets/{id}/reclassify` qo‘shildi.
- ADR-0001 hali runtime tasdiqni kutayotganini aytadi. Egasi agentga unga amal qilishni buyurdi, shuning uchun kod qarorda nomlangan narsani ishlatadi.
- Kichik test modeli bilan alohida loyihada haqiqiy `ollama/ollama:0.40.15` konteyneriga qarshi tekshirildi. Sozlangan model taxminan 22.6 GB va bu yerdagi 15.5 GB’li Docker’ga sig‘madi, shuning uchun u o‘sha paytda ishga tushirilmadi.

**Agent qayerda xato qildi**

- Model yuklanayotganda `is_ready()` har so‘rovda yiqildi: modellar yo‘qligida Ollama `"data": null` yuboradi, mock’lar esa `[]` ishlatgan. 505 ta o‘tgan test buni o‘tkazib yubordi; faqat haqiqiy konteyner ko‘rsatdi.
- `get_classifier` har bir `/api/health/ready` chaqiruvida yangi HTTP klient yaratib, uni yopmagan. Kodni ko‘rib chiqish buni topdi.
- Agent alohida loyihadagi tekshiruvni yiqilgan testdan keyin boshlagan va birinchi tekshiruvlar hech narsani isbotlamagan: yiqilgan yuklash 0 ta ticket qoldirgan, shuning uchun “navbat bo‘shadi” hech qanday ishsiz o‘tgan. Natija juda tez ko‘ringani logni ko‘rishga olib keldi. Skriptga qator soni va saqlangan natijalar tekshiruvi qo‘shildi.

## 2026-11-06 · Claude Code · Opus 5.5 · CI va yakuniy tekshiruv

**Muhim prompt**

- CI qo‘shish, toza Docker’da ishga tushirishni tekshirish, barcha testlar va baholashni ishga tushirish, hujjatlarni tekshirish va bajarilmagan ishni bajarilgan demasdan nima tugallanmaganini aytish.

**Natija**

- TRD 14-bo‘limga ko‘ra `.github/workflows/ci.yml` qo‘shildi. U `actionlint` dan o‘tdi va buyruqlari bo‘sh Docker daemon’da ishga tushirildi. O‘sha paytda GitHub’da ishlamagan edi. (Keyinroq: `f2e4854` commit’i uchun GitHub Actions muvaffaqiyatli o‘tdi.)
- Multipart yuklashga o‘tgandan keyin kodga mos kelmay qolgan TRD qatorlari tuzatildi va `finished_at` qayd etildi.
- Worker model kutishni boshlaganda va tugatganda log yozadi.
- Bajarilmagan va bajarilgan deyilmagan: ADR-0001 modelini ishga tushirish, 50 ta ticketli baholash, qidiruv, frontend va learning note.

**Agent qayerda xato qildi**

- Bo‘sh daemon’dagi ishga tushirish avval juda sekin bo‘ldi, keyin model yuklanishi tarmoqni band qilgani uchun `pip install` da yiqildi. Agent buni qayta takrorlab loyiha xatosidan ajratdi va oldindan build qilingan image’larni yukladi. Shuning uchun o‘sha ishga tushirish image’larni noldan build qilishni isbotlamaydi.
- Bitta skript tahriri qo‘llanmadi va agent baribir ishga tushirdi. U ishni to‘xtatib, qatorni tuzatdi va tasdiqlab, keyin qayta ishga tushirdi.

## 2026-11-06 · Claude Code · Opus 5.5 · Haqiqiy model, baholash va qolgan funksiyalar

**Muhim prompt**

- ADR-0001 modeli ishlab turgan holda 6-bosqichni davom ettirish: worker’ni kuzatish, haqiqiy pipeline va uning xatolarini tekshirish, 50 ta ticketli baholash, qolganini qurish va faqat haqiqatan bajarilganini aytish.

**Natija**

- `qwen3.6:35b-a3b` birinchi marta ishga tushirildi. Oldin worker’ning aynan o‘sha so‘rovi bilan faqat o‘qiydigan sinov qilindi, chunki 60 soniyalik timeout’dan oshgan chaqiruv har bir ticketni `llm_unavailable` ga yuborardi.
- Agent 111 ta baholanadigan va 15 ta ushlab qolinadigan ticketni model javoblarini ko‘rishdan oldin belgiladi. Belgilar agentniki, muallifniki emas, shuning uchun `eval/README.md` muallifdan ularni tekshirishni so‘raydi.
- Login va rollar, ticket ro‘yxati, tafsilot va tuzatish API’lari, statistika, outbox orqali Elasticsearch qidiruvi, retention, web ekranlar, `make` buyruqlari va `eval/` qurildi.
- Prompt `v1` ustuvorlik maqsadiga yetmadi (77.5%). `v2` PRD’dagi misollarni qo‘shib 82.9% ga chiqdi, lekin oldin ko‘rilgan to‘plamda, shuning uchun bu natija mustaqil emas.

**Agent qayerda xato qildi**

- Birinchi hisobot yo‘qolgan karta ticketini “injection’ga bo‘ysundi” deb belgiladi. Ushlab qolingan ticketlar belgilari yo‘q edi, chunki ularni yozgan buyruq agent sezmagan holda yiqilgan, tekshiruv esa bo‘sh belgini “fraud emas” deb hisoblagan. Hisobotni o‘qish buni topdi. Tekshiruvga testlar qo‘shildi.
- Prompt tahriri ikki gap ichida haqiqiy qator uzilishini qoldirgan va hech kim ko‘rmasdan ishga tushirilgan. Agent ishni to‘xtatib, qayta ishga tushirishdan oldin promptni model ko‘radigan ko‘rinishda chiqardi.
- `make bench` avval soatiga 88 ticket ko‘rsatdi, chunki vaqtga worker to‘xtab turgan soatlar ham kirgan edi. Haqiqiy qiymat ~620. Agent bu bazadagi uzluksiz oraliq bilan mos kelmasligini sezdi.
- Ikkita yiqilgan toza ishga tushirish avval buyruqni qanday ishga tushirishga bog‘landi. Haqiqiy sabab: Compose biror narsani ishga tushirishdan oldin barcha image’larni tortadi, bu 13 daqiqa 42 soniya oldi va agentning 10 daqiqalik chegarasidan oshdi.
- Ishlab turgan servislarni xato sinash uchun o‘chirish vositaning xavfsizlik tekshiruvi tomonidan rad etildi. Alohida loyihada esa agentning qo‘shimcha worker’i umumiy modelni sekinlashtirib, ishlab turgan worker’da 3 ta read timeout keltirib chiqardi (qayta urinishda tiklandi). Kompyuterda xotira tugagani uchun test to‘xtadi, shuning uchun haqiqiy model bilan o‘chirilgan worker’ning tiklanishi kuzatilmadi.

## 2026-11-07 · Claude Code · Opus 5.5 · Frontend refaktori, baholash audit’i, operatsion ishlar va muvofiqlik

Sessiya `2026-11-07_claude_c064d082`; hali tugamagan, xarajat noma’lum.

**Muhim promptlar**

- Frontend’ni Feature-Based Architecture’ga o‘tkazish (React, TypeScript, Tailwind, shadcn/ui), barcha ekran va xatti-harakatni saqlab.
- TRD’dagi frontend talablarini qator raqamlari bilan tekshirish; baholash bo‘yicha faqat o‘qiydigan audit.
- Belgilarni inson tekshirishi uchun workbook va bazadagi 2 000 ticketning ikkita eksport workbook’i.
- `llm_unavailable` va `injection_suspected` ticketlarini tekshirish; `LLM_TIMEOUT` ni 120 ga oshirish; 7 ta ticketni ketma-ket qayta tasniflash.
- Topshiriqqa to‘liq muvofiqlik bo‘yicha qat’iy audit, keyin hujjatlarni o‘zbek tilida to‘ldirish.

**Natija**

- `web/src` `app/`, `features/{auth,tickets,imports,stats}/`, `shared/` tuzilmasiga o‘tkazildi; shadcn/ui komponentlari `shared/components/ui/` da. `web` image build’i (typecheck, lint, build) keshsiz qayta ishga tushirildi va o‘tdi.
- `eval/review/labels-review.xlsx`, `eval/final-ticket-review.xlsx`, `eval/final-ticket-review-v2.xlsx` yaratildi; maskalash loyiha kodi bilan tekshirildi; belgilar va natijalar o‘zgartirilmadi.
- 7 ta `llm_unavailable` ticket mavjud reclassify endpoint’i orqali ketma-ket qayta tasniflandi; hammasi `classified`. Injection ticketlariga tegilmadi.
- Alohida Compose loyihasida backend: `ruff` toza, 601 ta test o‘tdi.
- README, AGENTS.md, learning note, ushbu log, `eval/README.md`, TRD, PRD va ADR’lar o‘zbek tilida yangilandi.

**Agent qayerda xato qildi yoki nimani o‘tkazib yubordi**

- Frontend refaktoridan keyin agent typecheck, lint va build’ni “xotira yetarli emas” deb ishga tushirmagan va buni hisobotda ochiq aytgan. Keyin `web` image’i build qilingani ko‘rildi.
- Birinchi statik tekshiruv skripti `export … from` ni hisobga olmagan va soxta “NO EXPORT” xatolarini bergan; tuzatilgan skript buzilgan nusxada har bir qasddan qo‘yilgan xatoni topdi.
- `AiResultCard` da `<p>` ichida `<div>` (Badge) qolgan — noto‘g‘ri DOM ichma-ichligi; ko‘rib chiqishda topilib tuzatildi.
- `3765a8b` commit’ida `web/src/main.tsx` yangi `@/app/App` ni import qiladi, lekin `web/src/app`, `features`, `shared` va `web/components.json` commit’ga qo‘shilmagan. Agent buni muvofiqlik ishining boshida `git status` dan topdi; GitHub Actions shu commit’da “Build all images” qadamida yiqilgani va commit’ning `web` papkasi alohida build qilinganda typecheck yiqilishi tasdiqlandi. Tuzatish (fayllarni qo‘shib commit qilish) egasiga qoldirildi, chunki agentga commit qilish taqiqlangan.

**Usage:** sessiya tugaganda `ai-usage/2026-11-07_claude_c064d082.jsonl` dagi `end` qatoriga qarang.
