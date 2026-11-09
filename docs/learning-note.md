# TicketLens — Learning Note

## 1. Loyiha davomida nimalarni o‘rgandim?

TicketLens loyihasi davomida backend arxitekturasi, ma’lumotlar bazalari, qidiruv tizimlari va sun’iy intellektni real dasturiy mahsulotga integratsiya qilish bo‘yicha amaliy bilim va ko‘nikmalarimni rivojlantirdim.

Loyiha davomida quyidagi texnologiyalar bilan ishladim:

- **FastAPI** — REST API yaratish va backend xizmatlarini tashkil qilish.
- **PostgreSQL** — ma’lumotlarni saqlash, boshqarish va ular bilan ishlash.
- **Elasticsearch** — ma’lumotlarni indekslash va qidiruv infratuzilmasini yaratish.
- **Ollama** — mahalliy AI modelini ishga tushirish va tizimga integratsiya qilish.
- **React** — foydalanuvchi interfeysini ishlab chiqish.
- **Docker Compose** — barcha xizmatlarni yagona muhitda ishga tushirish.
- **GitHub Actions** — CI jarayonlarini avtomatlashtirish va testlarni bajarish.

Eng muhimi, ushbu texnologiyalarni alohida ishlatishdan tashqari, ularni yagona tizim sifatida birlashtirish tajribasiga ega bo‘ldim.

## 2. Men uchun eng muhim texnologik o‘rganish — Elasticsearch

TicketLens loyihasida men uchun eng muhim yangi texnologiyalardan biri Elasticsearch bo‘ldi. Uni aynan shu loyiha davomida birinchi marta amaliy o‘rgandim.

Ishlash jarayonida Elasticsearch ma’lumotlarni indekslash, qidiruv so‘rovlarini bajarish va katta hajmdagi ma’lumotlar bilan ishlash imkoniyatlarini o‘rgandim.

Shuningdek, Elasticsearch oddiy ma’lumotlar bazasining o‘rnini to‘liq bosmasligini, balki PostgreSQL bilan birgalikda turli vazifalarni bajarishi mumkinligini tushundim.

Bu tajriba menga texnologiyani shunchaki tanlash emas, balki uning loyihadagi aniq vazifasi va boshqa komponentlar bilan o‘zaro aloqasini to‘g‘ri belgilash muhimligini ko‘rsatdi.

## 3. Loyihadagi eng katta qiyinchiliklar

Loyiha davomida eng katta qiyinchiliklardan biri mahalliy AI modelini tizimga integratsiya qilish va uning barqaror ishlashini ta’minlash bo‘ldi.

Qwen modelining resurs talablari yuqori bo‘lgani sababli quyidagi masalalarga alohida e’tibor qaratishimga to‘g‘ri keldi:

- Operativ xotira (RAM) sarfini nazorat qilish.
- Model javobini kutish vaqtini to‘g‘ri belgilash.
- Background worker jarayonlarini boshqarish.
- Qayta ishlash jarayonida yuzaga keladigan xatolarni aniqlash va qayd etish.

Bundan tashqari, 2 000 ta murojaatni qayta ishlash, natijalarni tekshirish, muammoli murojaatlarni aniqlash va ularni inson tekshiruviga yuborish mexanizmlarini tashkil qilish ham muhim amaliy tajriba bo‘ldi.

Bu jarayon menga AI bilan ishlaydigan tizimlarda faqat modelning javob berishi emas, balki butun qayta ishlash jarayonini nazorat qilish ham muhimligini o‘rgatdi.

## 4. Sun’iy intellektdan foydalanish bo‘yicha xulosalar

Loyihani ishlab chiqishda AI coding agentlaridan faol foydalandim. Ulardan arxitekturani tahlil qilish, kod yozish, xatolarni aniqlash, testlar yaratish va texnik hujjatlarni tayyorlashda yordamchi vosita sifatida foydalandim.

Bu jarayonda bir muhim xulosaga keldim: AI agent tomonidan berilgan natijani avtomatik ravishda to‘g‘ri deb qabul qilish mumkin emas.

Har bir muhim o‘zgarishni kodni ko‘rib chiqish, testlarni bajarish va amaliy natijalarni tekshirish orqali tasdiqlash zarur.

AI coding agentlar ishlab chiqish jarayonini tezlashtiradi, biroq arxitektura bo‘yicha qarorlar, kod sifatini nazorat qilish va yakuniy natija uchun mas’uliyat ishlab chiquvchining o‘zida qoladi.

## 5. Arxitektura bo‘yicha o‘rganganlarim

TicketLens arxitekturasida AI modeli murojaatning kategoriyasi, ustuvorligi va qisqacha mazmunini aniqlashda foydalaniladi.

Mas’ul jamoani tanlash esa AI modeliga topshirilmagan. Bu vazifa backend tomonidan `config/routing.yaml` konfiguratsiyasi asosida bajariladi.

Bunday yondashuv biznes qoidalarini AI modelidan ajratish imkonini beradi. Natijada jamoalar taqsimotini o‘zgartirish uchun modelni qayta o‘qitish talab qilinmaydi.

Shuningdek, PostgreSQL, Elasticsearch, API va background worker vazifalarini ajratish tizimning modulliligini, boshqarilishini va kelajakda kengaytirish imkoniyatini yaxshilashini amalda tushundim.

## 6. Yakuniy xulosa

TicketLens loyihasi menga real dasturiy mahsulotni ishlab chiqish jarayoni faqat kod yozishdan iborat emasligini ko‘rsatdi.

Texnologiyalarni to‘g‘ri tanlash, ularni o‘zaro integratsiya qilish, tizimni testlash, xatolarni tahlil qilish, xavfsizlikni hisobga olish va texnik hujjatlarni yuritish ham mahsulot sifatining muhim qismlaridir.

Men uchun ushbu loyihaning eng katta natijasi — yangi texnologiyani, xususan Elasticsearch'ni amaliy o‘rganish, mahalliy AI modelini real tizimga integratsiya qilish va bir nechta mustaqil komponentlardan iborat yagona mahsulot yaratish tajribasiga ega bo‘lganimdir.

Asosiy xulosam: **yaxshi dasturiy mahsulot nafaqat ishlashi, balki uning natijalari tekshiriladigan, cheklovlari tushunarli, xavfsiz va kelajakda rivojlantirishga tayyor bo‘lishi kerak.**
