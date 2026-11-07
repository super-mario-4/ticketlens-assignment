# Tasniflash sifatini baholash

`labels.csv` — etalon to‘plam, `report.md` — oxirgi sifat natijasi (prompt `v2`), `report-prompt-v1.md` — birinchi natija (prompt `v1`), `bench.md` — oxirgi tezlik natijasi. `review/labels-review.xlsx` — belgilarni muallif tekshirishi uchun workbook. `final-ticket-review.xlsx` va `final-ticket-review-v2.xlsx` — bazadagi 2 000 ticketning tekshirish uchun eksporti (baholashga ta’sir qilmaydi).

## Holat: inson tomonidan tasdiqlash KUTILMOQDA

**`labels.csv` dagi belgilarni AI agent yozgan, muallif emas.** Topshiriq “o‘zingiz belgilagan kamida 50 ta ticket” talab qiladi (PRD 9-bo‘lim, TRD 12-bo‘lim ham). Muallif kamida 50 ta belgini o‘zi tekshirib tasdiqlamaguncha bu talab **bajarilmagan** hisoblanadi va quyidagi natijalar muallifning belgilashi sifatida taqdim etilmaydi.

Belgilarni halol saqlagan choralar:

- Belgilar maskalangan matn va PRD 7-bo‘lim qoidalari asosida, model bu ticketlarga bergan javoblar ko‘rilishidan oldin yozilgan.
- Baholanadigan 111 ta belgining hash’i birinchi baholashdan oldin olingan; natijalar o‘qilgandan keyin ular o‘zgartirilmagan. (Hash qiymatining o‘zi repozitoriyda saqlanmagan.)
- Bitta istisno, hech qaysi ko‘rsatkichga ta’sir qilmaydi: 8 ta injection ticketining haqiqiy shikoyati birinchi baholashdan oldin tanlangan, lekin ularni yozadigan buyruq xato bergan. Ular avval tanlangan qiymatlar bilan birinchi baholashdan keyin faylga tushgan va faqat injection jadvalida ishlatiladi.
- Qoidalar aniq hal qilmagan belgi `ambiguous = yes` deb belgilangan; hisobot natijani ular bilan va ularsiz ham beradi.

Cheklovlar:

- Bitta belgilovchi, ikkinchi fikr va qayta belgilash yo‘q.
- Prompt qoidalarini ham, belgilarni ham bir xil model oilasi yozgan, shuning uchun umumiy ko‘r nuqtalar bo‘lishi mumkin.
- Dataset kam sonli xabar shablonlaridan tuzilgan. Bu yerdagi yuqori natija real xabarlar haqida kam narsa aytadi; xulosa faqat shu to‘plamga tegishli (TRD 12-bo‘lim).

## To‘plam

| Guruh | Ticketlar | Vazifasi |
| --- | --- | --- |
| `expected = model` | 111 | Modelga yuboriladi va baholanadi |
| `expected = no_content` | 7 | Import paytida ushlab qolinishi kerak |
| `expected = injection_suspected` | 8 | Import paytida ushlab qolinishi kerak; promptning o‘zini sinash uchun to‘g‘ridan-to‘g‘ri modelga ham yuboriladi |

Ticketlar `data/tickets.csv` dan seed bilan tanlangan noyob matnlar, kam uchraydigan kategoriyalar uchun qo‘shimcha tanlov bilan. Barcha 12 kategoriya, 4 ustuvorlik va 5 til guruhi qamrab olingan: `uz_latin`, `uz_cyrillic`, `ru`, `ru_latin` (lotin harfida ruscha) va `mixed` (ularning aralashmasi). 16 ta belgi `ambiguous = yes`.

PRD 7-bo‘lim ochiq qoldirgan holatlar uchun agent qo‘shgan qoidalar (aynan shular `ambiguous` deb belgilangan; muallif tasdiqlashi yoki rad etishi kerak):

- Komissiya nima uchun yechilgani haqidagi savol — `fees_charges`, `Low`: ma’lumot so‘ralmoqda.
- Do‘konda karta rad etilgan, pul yechilmagan — `card_issues`, `Medium`.
- Muddati tugagan karta — `card_issues`, `Medium`: kartadan foydalanishga xalaqit beradi.
- O‘z vaqtida to‘lagan bo‘lsa ham jarima — `credit_installments`, `High`.
- Qo‘pol operator — `support_complaints`, `Low`. Qo‘llab-quvvatlash ikki kundan beri javob bermasa — `Medium`.

## Prompt versiyalari

`report-prompt-v1.md` — natijalarni bilmasdan qilingan birinchi ishga tushirish. U yerda ustuvorlik aniqligi maqsaddan past bo‘lgan (77.5%), shuning uchun `v2` promptiga PRD 7-bo‘lim jadvalidagi ustuvorlik misollari qo‘shilgan (`v1` ularni tushirib qoldirgan edi). `report.md` — `v2` natijasi.

**`v2` natijalari agent oldin ko‘rgan to‘plamdan olingan, shuning uchun ular mustaqil emas.** O‘zgarish faqat PRD matnidan olingan va alohida ticketlarga moslanmagan, lekin yangi ticketlarda ishlashini faqat yangi to‘plam ko‘rsata oladi. Shu sababli endi promptni bu to‘plam natijalariga qarab o‘zgartirmang. `v1` fayli injection belgilaridan oldin yozilgan, shuning uchun uning injection jadvali qo‘lda tuzatilgan (faylning boshida izoh bor).

## Joriy natijalar (agent belgilari bilan)

| Ko‘rsatkich | `v1` | `v2` (`report.md`) | Maqsad |
| --- | --- | --- | --- |
| Kategoriya aniqligi | 107/111 = 96.4% | 107/111 = 96.4% | ≥ 85% |
| Ustuvorlik aniqligi | 86/111 = 77.5% | 92/111 = 82.9% | ≥ 80% |
| Critical recall | 8/8 = 100% | 8/8 = 100% | ≥ 95% |
| Qo‘lda tekshirishga tushgan | 4/111 = 3.6% | 3/111 = 2.7% | ≤ 15% |
| To‘g‘ri JSON (har bir chaqiruv) | 120/120 | 119/119 | ≥ 98% |
| Kechikish, bittadan so‘rov | p50 8.9 s, p95 10.6 s | p50 9.7 s, p95 11.0 s | — |

Ehtiyot bo‘lish kerak bo‘lgan joylar:

- Critical faqat 8 ta: 100% natijaning 95% Wilson oralig‘i 67.6–100%. Ustuvorlik `v2` uchun oraliq 74.8–88.8%.
- Til bo‘yicha ustuvorlik: `ru_latin` 6/11 = 54.5%, `mixed` 17/22 = 77.3% — eng zaif joylar.
- Model `confidence` qiymati kalibrlanmagan (barcha javoblar 0.85–1.0), shuning uchun “qo‘lda tekshirishga tushgan” ko‘rsatkichi asosan `other` kategoriyasidan keladi.
- Bu kechikish bittadan so‘rovda o‘lchangan. Ishlab turgan `worker` 3 parallel so‘rov bilan ishlaganda kechikish yuqoriroq: `bench.md` da p50 17.0 s, p95 25.4 s.

## Muallif uchun: belgilarni tekshirish va tasdiqlash tartibi

1. `eval/review/labels-review.xlsx` ni oching va **Guide** varag‘ini o‘qing. Faqat **Review** varag‘idagi och ko‘k L–O ustunlarini to‘ldiring.
2. Avval 27 ta rangli qatorni ko‘ring: 16 ta oltin rangli (`ambiguous`) va audit qo‘shgan 11 ta to‘q sariq. Keyin oddiy qatorlarni: jami kamida 50 ta, imkon bo‘lsa barcha 126 tasi.
3. Har bir qatorda avval matnni o‘qib kategoriya va ustuvorlikni **o‘zingiz** hal qiling, keyin belgilangan qiymat bilan solishtiring:
   - rozi bo‘lsangiz — `approved`;
   - rozi bo‘lmasangiz — `changed` va faqat farq qiladigan `reviewed_category` / `reviewed_priority`;
   - hal qila olmasangiz — `unsure` va `reviewer_note` ga sabab.
4. Bir xil holatlarga (masalan, bankomat kartani yutgan 4 ta ticket) bir xil qaror bering. Agent yozgan 5 ta qoidani tasdiqlang yoki o‘zgartiring.
5. **Progress** varag‘ida “Yes: ready to apply” chiqquncha davom eting.
6. Qarorlaringizni `eval/labels.csv` ga o‘zingiz kiriting (yoki agentdan workbook’ni aynan ko‘chirishni so‘rang). Qoida hal qilingan bo‘lsa, `ambiguous` ni ham yangilang. Prompt va `report.md` ga tegmang.
7. Baholashni qayta ishga tushiring (stack ishlab turgan, ticketlar import qilingan bo‘lishi kerak):

   ```bash
   docker compose stop worker
   make eval
   docker compose start worker
   ```

   `make eval` `eval/report.md` ni qayta yozadi; eski versiya git tarixida qoladi.
8. Shu faylning “Holat” bo‘limini, TRD 16-bo‘limdagi belgilovchi haqidagi qatorni va README’dagi baholash bo‘limini yangilang: nechta belgi tekshirilgani, nechtasi o‘zgargani va sanasini yozing.
9. Workbook’ni ham commit qiling: u har bir qarorning yozuvi bo‘ladi.

## Ishga tushirish

Stack ishlab turgan va `data/tickets.csv` import qilingan bo‘lishi kerak:

```bash
docker compose stop worker   # Model bir vaqtda ikkalasiga sekinlashmasdan xizmat qila olmaydi.
make eval                    # Har bir ticket uchun modelni bir marta chaqiradi. Bazaga hech narsa yozmaydi.
docker compose start worker
make bench                   # Saqlangan natijalarni o‘qiydi. Model kerak emas.
```
