# ConstructSmart - Multi-language Construction Project Management System

## 👷 مقدمة | Introduction | Introducción

نظام إدارة مشاريع البناء الذكي، يدعم العربية، الإنجليزية، والإسبانية.  
Smart construction project management system supporting Arabic, English, and Spanish.  
Sistema inteligente de gestión de proyectos de construcción con soporte para árabe, inglés y español.

---

## 🗂️ الهيكل | Structure | Estructura

- **backend/** — Node.js + Express + Sequelize + PostgreSQL
- **frontend/** — React.js + i18next (AR/EN/ES)

---

## 🚀 طريقة التشغيل | How to Run | Cómo Ejecutar

### 1. إعداد قاعدة البيانات | Setup PostgreSQL

- أنشئ قاعدة بيانات باسم `constructsmart`.
- عدّل ملف `.env` في مجلد backend وضع بيانات الاتصال بقاعدة البيانات الخاصة بك.

### 2. تشغيل الباك اند | Start Backend

```bash
cd backend
cp .env.example .env
npm install
npm run start
```
سوف يعمل السيرفر على المنفذ 5000 أو حسب ما تحدد في .env

---

### 3. تشغيل الواجهة الأمامية | Start Frontend

```bash
cd frontend
npm install
npm start
```
ستعمل الواجهة على `http://localhost:3000`

---

## 🌐 تغيير اللغة | Change Language | Cambiar Idioma

استعمل أزرار اللغة في أعلى الصفحة (EN | عربي | ES)  
Use the language switcher at the top (EN | عربي | ES)  
Utiliza el selector de idioma arriba (EN | عربي | ES)

---

## 📦 رفع المشروع إلى GitHub وVercel/Render

1. ارفع المجلدين `backend` و`frontend` إلى مستودع GitHub خاص بك.
2. استخدم [Render](https://render.com/) أو [Railway](https://railway.app/) لتشغيل الباك اند.
3. استخدم [Vercel](https://vercel.com/) أو [Netlify](https://netlify.com/) لتشغيل الواجهة الأمامية.
4. حدّث رابط الـAPI داخل الواجهة الأمامية إذا كان الباك اند يعمل على رابط غير محلي.

---

## 📨 الدعم | Support

لأي استفسار أو تطوير إضافي، تواصل معي عبر Issues أو Discussions في المستودع الخاص بك بعد الرفع.

---

**بالتوفيق في مشاريعك!**