# pyfatura

GİB e-Arşiv Portal üzerinden **e-Arşiv fatura** oluşturma, imzalama, sorgulama ve iptal işlemleri için Python istemcisi.

> **Uyarı**: Bu paket **vergi mükellefiyeti doğuran** belgeler oluşturur. Oluşturulan faturaların hukuki sorumluluğu tamamen kullanıcıya aittir. Test ortamında (`test_mode=True`) geliştirme yapmanız önerilir.

Bu paket, [f/fatura](https://github.com/f/fatura) (Node.js) projesinin Python portudur.

## Kurulum

```bash
pip install pyfatura
```

## Hızlı Başlangıç

```python
from pyfatura import EArsivClient, Invoice, InvoiceItem

# Test ortamında istemci oluştur
client = EArsivClient(test_mode=True)

# Giriş yap
client.login("kullanici_adi", "sifre")

# Fatura kalemleri
items = [
    InvoiceItem(
        name="Yazılım Geliştirme Hizmeti",
        quantity=1,
        unit_price=5000.00,
        vat_rate=20,
    ),
    InvoiceItem(
        name="Danışmanlık Hizmeti",
        quantity=3,
        unit_price=1000.00,
        vat_rate=20,
    ),
]

# Fatura oluştur
invoice = Invoice(
    date="13/03/2026",
    time="14:30:00",
    name="Ali",
    surname="Yılmaz",
    tax_id_or_tr_id="11111111111",
    full_address="Örnek Mah. Test Sok. No:1",
    district="Kadıköy",
    city="İstanbul",
    items=items,
)

# Faturayı oluştur ve imzala
result = client.create_invoice(invoice, sign=True)
print(f"Fatura UUID: {result['uuid']}")

# İndirme URL'si al
url = client.get_download_url(result["uuid"], signed=True)
print(f"İndirme URL: {url}")

# Çıkış yap
client.logout()
client.close()
```

## Context Manager Kullanımı

```python
with EArsivClient(test_mode=True) as client:
    client.login("kullanici", "sifre")
    # ... işlemler ...
    client.logout()
```

## API Referansı

### `EArsivClient(test_mode=False)`

Ana istemci sınıfı.

| Parametre | Tip | Varsayılan | Açıklama |
|-----------|-----|------------|----------|
| `test_mode` | `bool` | `False` | `True` ise GİB test ortamını kullanır |

### Kimlik Doğrulama

#### `client.login(username, password) -> str`
e-Arşiv portalına giriş yapar. Oturum token'ı döner.

#### `client.logout() -> str | None`
Oturumu kapatır.

### Fatura İşlemleri

#### `client.create_draft_invoice(invoice) -> dict`
Taslak fatura oluşturur.

```python
result = client.create_draft_invoice(invoice)
# {"date": "13/03/2026", "uuid": "...", ...}
```

#### `client.get_all_invoices_by_date_range(start_date, end_date) -> list[dict]`
Tarih aralığında kesilen faturaları listeler.

```python
invoices = client.get_all_invoices_by_date_range("01/03/2026", "31/03/2026")
```

#### `client.get_all_invoices_issued_to_me(start_date, end_date) -> list[dict]`
Tarih aralığında adınıza kesilen faturaları listeler.

#### `client.find_invoice(date, invoice_uuid) -> dict | None`
UUID ile belirli bir faturayı bulur.

#### `client.sign_draft_invoice(draft_invoice) -> dict`
Taslak faturayı imzalar/onaylar.

```python
draft = client.find_invoice("13/03/2026", "fatura-uuid")
client.sign_draft_invoice(draft)
```

#### `client.get_invoice_html(invoice_uuid, signed=True) -> str`
Faturanın HTML içeriğini döner.

#### `client.get_download_url(invoice_uuid, signed=True) -> str`
Fatura indirme URL'si oluşturur (ZIP formatında).

#### `client.cancel_draft_invoice(reason, draft_invoice) -> dict`
Taslak faturayı iptal eder.

```python
draft = client.find_invoice("13/03/2026", "fatura-uuid")
client.cancel_draft_invoice("Yanlış kesildi", draft)
```

### Toplu İşlemler

#### `client.create_invoice(invoice, sign=True) -> dict`
Fatura oluşturur ve opsiyonel olarak imzalar. Tüm adımları otomatik yapar.

#### `client.create_invoice_and_get_download_url(invoice, sign=True) -> str`
Fatura oluşturur ve indirme URL'si döner.

#### `client.create_invoice_and_get_html(invoice, sign=True) -> str`
Fatura oluşturur ve HTML içeriğini döner.

### Alıcı Sorgulama

#### `client.get_recipient_data(tax_id_or_tr_id) -> dict`
VKN veya TCKN ile alıcı bilgilerini sorgular.

```python
data = client.get_recipient_data("1234567890")
```

### SMS İmza Doğrulama

#### `client.send_sign_sms_code(phone) -> str`
İmza için SMS doğrulama kodu gönderir. İşlem ID'si döner.

#### `client.verify_sign_sms_code(sms_code, operation_id) -> str`
SMS kodunu doğrular.

```python
oid = client.send_sign_sms_code("05551234567")
client.verify_sign_sms_code("123456", oid)
```

### Kullanıcı Bilgileri

#### `client.get_user_data() -> dict`
Kullanıcı profil bilgilerini getirir.

#### `client.update_user_data(user_data) -> dict`
Kullanıcı profil bilgilerini günceller.

```python
data = client.get_user_data()
data["email"] = "yeni@email.com"
client.update_user_data(data)
```

## Modeller

### `InvoiceItem`

| Alan | Tip | Varsayılan | Açıklama |
|------|-----|------------|----------|
| `name` | `str` | *zorunlu* | Mal/hizmet adı |
| `quantity` | `int \| float` | `1` | Miktar |
| `unit_price` | `float` | `0.0` | Birim fiyat |
| `vat_rate` | `int` | `18` | KDV oranı (%) |
| `unit_type` | `str` | `"C62"` | Birim tipi (C62=Adet) |
| `discount_rate` | `int` | `0` | İskonto oranı (%) |
| `discount_amount` | `float` | `0.0` | İskonto tutarı |

### `Invoice`

| Alan | Tip | Varsayılan | Açıklama |
|------|-----|------------|----------|
| `date` | `str` | *zorunlu* | Fatura tarihi (GG/AA/YYYY) |
| `time` | `str` | *zorunlu* | Fatura saati (SS:DD:SS) |
| `items` | `list[InvoiceItem]` | *zorunlu* | Fatura kalemleri |
| `name` | `str` | `""` | Alıcı adı |
| `surname` | `str` | `""` | Alıcı soyadı |
| `title` | `str` | `""` | Alıcı unvanı |
| `tax_id_or_tr_id` | `str` | `"11111111111"` | VKN veya TCKN |
| `tax_office` | `str` | `""` | Vergi dairesi |
| `full_address` | `str` | `""` | Açık adres |
| `district` | `str` | `""` | İlçe |
| `city` | `str` | `" "` | Şehir |
| `country` | `str` | `"Türkiye"` | Ülke |
| `currency` | `str` | `"TRY"` | Para birimi |

Toplamlar (`grand_total`, `total_vat`, `grand_total_incl_vat`, `payment_total`) otomatik hesaplanır. İsterseniz manuel olarak geçersiz kılabilirsiniz.

## Geliştirme

```bash
git clone https://github.com/ahmetelgun/pyfatura.git
cd pyfatura
pip install -e ".[dev]"
pytest
```

## Lisans

MIT
