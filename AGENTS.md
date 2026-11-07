# AGENTS.md

## AI usage logging (required by the assignment, do not change this section)

Every prompt the user gives an AI tool in this repository must be recorded in `ai-usage/`.

- **Claude Code, Cursor, Codex CLI, Gemini CLI and GitHub Copilot CLI** record prompts
  through hooks (`.claude/`, `.cursor/`, `.codex/`, `.gemini/`, `.github/hooks/`) into
  `ai-usage/<date>_<tool>_<session>.jsonl`. If you are one of these and such a file for
  your tool already holds the user's latest message, do nothing more.
- **Any other AI agent, or one of the above whose file does not hold that message:**
  before you act on each message from the user, append an entry for it to
  `ai-usage/manual.md` in the format shown there (the message word for word, every line
  prefixed with `> `, secrets replaced with `[REDACTED]`). When the session ends, add a
  `Usage:` line with the tokens or cost your tool reports, or `unknown`. Then run
  `git add ai-usage/manual.md`.
- Never edit or delete existing entries or files in `ai-usage/`.

<!-- Your own instructions for agents go below this line. -->

## Loyiha haqida

TicketLens fintech murojaatlarini (o‘zbek lotin/kirill, rus, aralash) lokal LLM bilan tasniflaydi, ustuvorlik va qisqa xulosa beradi, jamoaga `config/routing.yaml` bo‘yicha yo‘naltiradi. Talablar manbasi: `TicketLens_Task.md`; mahsulot va texnik qarorlar: `docs/PRD.md`, `docs/TRD.md`, `docs/adr/`. Kod va hujjat zid kelsa, ishni to‘xtatib egasiga xabar bering.

Servislar (`docker-compose.yml`): `web` (React + nginx), `api` (FastAPI), `worker` (tasniflash, ES outbox, retention), `postgres`, `elasticsearch`, `llm` (Ollama, `qwen3.6:35b-a3b`).

## Backend (`backend/app/`)

Qatlamlar, yuqoridan pastga; pastki qatlam yuqorisini import qilmaydi:

- `api/routes/` — HTTP: so‘rovni tekshirish, rol (`require_operator`, `require_lead`), xatoni HTTP kodga aylantirish. Biznes mantiq bu yerda emas.
- `services/` — biznes mantiq va tranzaksiya (`commit`) shu yerda.
- `repositories/` — SQLAlchemy so‘rovlari; `commit` qilmaydi.
- `models/` (ORM, `enums.py`), `schemas/` (Pydantic), `core/config.py` (sozlamalar), `db/`.
- `preprocess/` — normalizatsiya, tozalash, maskalash, injection evristikasi. `classification/` — prompt, sxema, LLM klient, routing. `search/` — Elasticsearch.

Qoidalar:

- API yo‘llari `/api/...`; ro‘yxat qiymatlari (kategoriya, ustuvorlik, jamoa) faqat `models/enums.py` va `config/routing.yaml` da, UI ularni `GET /api/meta` dan oladi.
- Amaldagi kategoriya/ustuvorlik/jamoa: eng so‘nggi `corrections`, u bo‘lmasa eng so‘nggi `classifications`. AI natijasi va tuzatishlar o‘chirilmaydi, faqat qo‘shiladi.
- Sxema o‘zgarishi faqat yangi Alembic migratsiyasi bilan (`backend/migrations/versions/`); mavjud migratsiyani tahrirlamang.

## Frontend (`web/src/`) — Feature-Based Architecture

- `app/` — router (`HashRouter`), layout, provider’lar. `features/<nom>/` — `auth`, `tickets`, `imports`, `stats`; har birida `api/`, `components/`, `hooks/`, `pages/`, `types/` va tashqi API sifatida `index.ts`.
- `shared/` — umumiy kod: `api/` (klient, sessiya, 401), `components/`, `hooks/`, `lib/`; `shared/components/ui/` — shadcn/ui komponentlari (`web/components.json`).
- Feature boshqa feature’ni import qilmaydi; `app/` feature’ni faqat uning `index.ts` orqali oladi; `shared/` `features/` yoki `app/` ni import qilmaydi.
- Uslub: Tailwind CSS va shadcn/ui; oddiy `<button>`, `<input>`, `<table>` o‘rniga `shared/components/ui/` dagi komponentlar. `dangerouslySetInnerHTML` ishlatilmaydi: ticket matni va xulosa faqat matn sifatida chiqadi.
- Yangi papka yoki fayl qo‘shsangiz, uni git’ga ham qo‘shing: `main.tsx` import qiladigan fayl commit’da bo‘lmasa, CI’dagi `web` build yiqiladi.

## Buyruqlar (faqat Docker orqali; host’ga paket o‘rnatmang)

- Ishga tushirish: `docker compose up --build`.
- Backend lint va testlar: `docker compose -p tlverify --profile test run --rm --build tests`, keyin `docker compose -p tlverify --profile test down -v`.
- Frontend typecheck, lint, build: `docker compose -p tlverify build web`.
- Baholash: `docker compose stop worker`, `make eval`, `docker compose start worker`. Faqat egasi so‘raganda.
- Og‘ir ishdan oldin `docker stats --no-stream` bilan xotirani tekshiring: model yuklanganda ~22 GB egallaydi.

## Ma’lumot va xavfsizlik qoidalari

- Ishlab turgan `ticketlens` bazasiga test yozmang va undan o‘chirmang; tekshiruvlar uchun alohida Compose loyihasi (`-p tlverify`) ishlating. Bazani o‘qish faqat `BEGIN READ ONLY` bilan.
- Xom ticket matni bazaga, Elasticsearch’ga, LLM’ga, logga yoki hujjatga tushmasin. Har qanday yangi chiqish yo‘li `preprocess/mask.py` dagi maskalashdan o‘tadi va `contains_sensitive_data` bilan tekshiriladi.
- Logga ticket matnini, model javobini yoki xato matnini yozmang: faqat ticket `id`, holat va xato turi.
- Sirlar faqat `.env` da; ularni chiqarmang, commit qilmang, hujjatga yozmang.

## LLM va prompt injection

- Injection himoyasini (`preprocess/injection.py`, prompt’dagi `<ticket>` bloki, JSON sxema) zaiflashtirmang. `injection_suspected` ticketni modelga yubormang va qayta navbatga qo‘ymang.
- Jamoani model tanlamaydi (ADR-0004). Model javobi har doim backend’da sxema bo‘yicha tekshiriladi.
- Model, prompt yoki chegara qiymatini o‘zgartirish egasining tasdig‘ini talab qiladi. Promptni `eval/labels.csv` natijalariga moslab sozlamang.

## Taqiqlangan ishlar (egasining aniq ruxsatisiz)

- `data/tickets.csv`, `TicketLens_Task.md`, `eval/labels.csv`, `eval/report*.md`, `eval/bench.md` va `eval/` dagi workbook’larni o‘zgartirish; AI yozgan belgilarni inson tekshirgandek ko‘rsatish.
- `README.md` ni tahrirlash, ADR qarorini o‘zgartirish.
- `commit`, `push`, `reset`, `rebase`, `git add -A` / `git add .`.
- Ishlab turgan `worker` yoki `llm` ni to‘xtatish, ticketlarni qayta tasniflash.

## Hujjat tili

Loyiha hujjatlari (README, `docs/`, `eval/README.md`, shu fayl) o‘zbek tilida (lotin) yoziladi. API yo‘llari, buyruqlar, sozlama nomlari, kod va maydon nomlari asl ko‘rinishida qoladi. Taxmin, o‘lchangan qiymat va maqsadni aniq ajrating; tekshirilmagan narsani bajarilgan deb yozmang.
