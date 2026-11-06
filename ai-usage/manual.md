# AI usage the hooks don't record

The hooks in this repository record Claude Code, Cursor, Codex CLI, Gemini CLI and
GitHub Copilot CLI by themselves, into the `.jsonl` files next to this one. Everything
else goes here, newest last:

- **any other AI agent** working in this repository: it adds its own entries, as
  `AGENTS.md` tells it to;
- **chat apps** (ChatGPT, Claude, Gemini, … in a browser or on a phone): you add them;
- **one of the tools above whose hook did not record a prompt**: you or the agent add it;
- **usage of Cursor, Gemini CLI and Copilot CLI sessions**: their hooks record prompts
  but not usage, so add a `Usage:` line per session (`## <date> · Cursor · <model>`
  heading, then the line below).

One entry per prompt:

```markdown
## 2026-11-05 14:30 · ChatGPT (web) · GPT-5

> The prompt, word for word. Every line starts with "> ".
> Replace secrets such as API keys with [REDACTED].
```

When a session or chat ends, add one line under its last entry:

```markdown
Usage: 41K tokens, $0.32 (what the tool shows; "unknown" if it shows nothing)
```

---

```markdown
## 2026-11-06 ChatGPT-5 (web)

> proyektni o'rganib chiqib hatolari bo'lsa to'g'rilashini aytib bu proyekt shunchaki menga berilgan taskligini va uni diqqat "> " .
> bilan o'qib chiqib men yaratgan narsalarimda asosan TRD, PRD va ADRlarni yaratganman holos mana shular taskka "> " .
> noto'g'ri joylangan bo'lsa uni taskka moslab to'g'rilashim kerakligini aytadigan bitta prompt yozib ber ingliz tilida "> " .
```

```markdown
## 2026-11-06 15:00 ChatGPT-5 (web)

> `README.md` faylini ushbu repository'dagi oxirgi commit holatiga (`HEAD`) to‘liq qaytar. "> " .
> Talablar: "> " .
>
> - Faqat `README.md` faylini tikla. "> " .
> - Boshqa fayllarga tegma. "> " .
> - `README.md` ichidagi barcha o‘zgarishlarni bekor qil. "> " .
> - Keyingi ishlar davomida `README.md` faylini hech qanday tarzda o‘zgartirma, tahrir qilma yoki formatlama. "> " .
> - Uni faqat o‘qish mumkin, tahrirlash taqiqlangan. "> " .
>   Avval Git orqali holatini tekshir, so‘ng faqat shu faylni tikla. Yakunda bajarilgan ishni tasdiqla. "> " .
```

```markdown
## 2026-11-06 15:11 ChatGPT-5 (web)

> Ohirgi marta tekshiraylik yuqoridagi talablar bajarilganini "> " .
```

```markdown
## 2026-11-06 15:29 ChatGPT-5 (web)

> Claude Code'ga butun backendni yozmasdan qisqa va aniq prompt berib bosqichma bosqich yaratishni so'rab promptlar yozamiz. "> " .
> avvalishlar ketma ketligini belgilab olaylik!
```

```markdown
## 2026-11-06 18:13

ChatGPT-5 (web)

> endi keyingi bosqich uchun buyruq yozamiz "> " .
```

```markdown
## 2026-11-06 18:26

ChatGPT-5 (web)

> muvaffaqiyatli bo'ldi keyingi bosqichga o'tamiz "> " .
```

```markdown
## 2026-11-06 18:57

ChatGPT-5 (web)

> menga API endpointi berdi, lekin uni fayl sifatida emas oddiy text sifatida yozsa bo'ladigan qilib berdi "> " .
```

```markdown
## 2026-11-06 19:14

ChatGPT-5 (web)

> tog'rilandi keyingi bosqichga o'tamiz "> " .
```

```markdown
## 2026-11-06 19:29

ChatGPT-5 (web)

> endi keyingi bosqich, keyingi bosqichda ADR-0001 da qaysi runtime llm aytilgan bo'lsa shuni yozsin, shuni ham qo'shib ket "> " .
```

```markdown
## 2026-11-06 20:16

ChatGPT-5 (web)

> docker compose exec postgres psql -U ticketlens -d ticketlens -c "SELECT status, COUNT(\*) FROM tickets GROUP BY status ORDER BY status;" burug'ini bergandim faqat ikkita status chiqyapti pending va needs_review pending ticket hali processing jarayonidan o'tmagan bo'lishi mumkinmi buni qanday tekshirish mumkin "> " .
```

```markdown
## 2026-11-06 20:16

ChatGPT-5 (web)

> yaxshi u to'lguncha keyingi bosqichni davom ettirib turamiz "> " .
```

```markdown
## 2026-11-06 23:00

ChatGPT-5 (web)

> keyingi bosqichga o'tamiz "> " .
```

```markdown
## 2026-11-06 01:30

ChatGPT-5 (web)

> Login va parol hato berdi "> " .
```
