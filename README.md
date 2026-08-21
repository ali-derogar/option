# TSETMC Options Data Pipeline

پروژه Python برای دریافت داده‌های اختیار معامله از **وب‌سرویس رسمی** شرکت مدیریت فناوری بورس تهران (`api.tsetmc.com`).

## قابلیت‌ها

1. **موقعیت‌های باز هر اپشن** — `BuyOP`, `SellOP`, `YesterdayOP`
2. **ورود/خروج پول حقیقی و حقوقی** — محاسبه خالص از ارزش خرید و فروش
3. **اطلاعات عددی خرید/فروش حقیقی و حقوقی** — تعداد، حجم، ارزش
4. **همه اطلاعات قراردادها** — مشخصات کامل + داده معاملاتی
5. **تحلیل سنتیمنت اختیار معامله** — تجمیع Call/Put، ITM/OTM، تغییرات OI و برچسب صعودی/نزولی/خنثی

خروجی: SQLite + CSV + داشبورد Streamlit + **فرانت وب**

## پیش‌نیاز

- Python 3.10+
- یوزرنیم و پسورد رسمی وب‌سرویس TSETMC

## نصب

```bash
cd /home/darklord/Desktop/darush
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# ویرایش .env و قرار دادن TSETMC_USERNAME و TSETMC_PASSWORD
```

## اجرای Pipeline

```bash
# دریافت همه داده‌ها
python -m src.pipeline

# تست با محدودیت (۵ قرارداد)
python -m src.pipeline --limit 5

# بدون client type (سریع‌تر)
python -m src.pipeline --skip-client-type
```

داده‌ها در `data/tsetmc_options.db` ذخیره و CSV در `data/exports/` خروجی می‌گیرد.

## فرانت وب (پیشنهادی)

```bash
python main.py
```

مرورگر: **http://localhost:8080** (به‌صورت خودکار باز می‌شود)

یک دستور — هم **API (بک‌اند)** هم **داشبورد (فرانت)**:

| مسیر | کار |
|------|-----|
| `/` | فرانت وب |
| `/api/*` | API بک‌اند |
| `/static/*` | CSS و JS |
| `/api/sentiment` | تحلیل سنتیمنت گروهی اختیار معامله |

ویژگی‌ها:
- UI فارسی RTL، تیره و مدرن
- ۵ تب: قراردادها، موقعیت باز، جریان پول، حقیقی/حقوقی، سنتیمنت
- جستجو، مرتب‌سازی، جزئیات قرارداد، نمودار موقعیت باز
- تحلیل گروهی بر اساس دارایی پایه و سررسید، همراه با دلایل و هشدارهای تفسیری
- به‌روزرسانی داده از داخل UI
- خروجی CSV

## داشبورد Streamlit (قدیمی)

```bash
streamlit run dashboard.py
```

پنج تب:
- همه قراردادها
- موقعیت‌های باز (+ نمودار روند)
- ورود/خروج پول (رنگ‌بندی مثبت/منفی)
- خرید/فروش حقیقی و حقوقی (جزئیات عددی)
- سنتیمنت اختیار معامله

## ساختار پروژه

```
src/
  client.py          # احراز هویت و فراخوانی API
  schema.py          # مسیر endpointها و فیلدها
  storage.py         # SQLite + CSV
  pipeline.py        # pipeline اصلی
  services/
    options.py       # داده اختیار معامله
    client_type.py   # حقیقی/حقوقی
    instruments.py   # فهرست نمادها
dashboard.py         # داشبورد Streamlit
run_web.py           # همان main.py
main.py              # اجرای فرانت + بک‌اند
web/                 # HTML, CSS, JS
  index.html
  static/
src/api/             # FastAPI backend
```

## API Endpoints استفاده‌شده

| سرویس | مسیر |
|--------|------|
| Login | `POST /Account/Login` |
| Option | `POST /Derivative/Option` |
| Instrument | `POST /Instrument/Instrument` |
| ClientTypeByIns | `POST /ClientType/ClientTypeByInsCode` |

مستندات کامل: https://api.tsetmc.com/docs/

## بررسی اتصال

```bash
python scripts/check_login.py
```

اگر کد **-102** دیدید: یوزر/پسورد اشتباه یا حساب مسدود است.  
اگر کد **107** دیدید: ابتدا رمز را تغییر دهید:

```bash
python scripts/change_password.py رمز_جدید_شما
```

## نکات

- `TSETMC_FLOW=3` برای بازار مشتقه (ATI) تنظیم شده است.
- اولین ورود ممکن است کد ۱۰۷ (تغییر رمز) برگرداند؛ از `ChangePassword` در client استفاده کنید.
- فراخوانی `ClientTypeByIns` برای هر قرارداد زمان‌بر است؛ `--delay` برای تنظیم فاصله بین درخواست‌ها.

## امنیت

فایل `.env` را در git کامیت نکنید.
