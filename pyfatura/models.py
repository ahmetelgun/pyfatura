from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class InvoiceItem:
    """Fatura kalemi."""

    name: str
    quantity: int | float = 1
    unit_price: float = 0.0
    vat_rate: int = 18
    unit_type: str = "C62"
    discount_rate: int = 0
    discount_amount: float = 0.0
    discount_reason: str = ""
    tax_rate: int = 0
    vat_amount_of_tax: float = 0.0

    @property
    def price(self) -> float:
        return round(self.quantity * self.unit_price, 2)

    @property
    def vat_amount(self) -> float:
        return round(self.price * self.vat_rate / 100, 2)

    def to_gib_dict(self) -> dict:
        return {
            "iskontoArttm": "İskonto",
            "malHizmet": self.name,
            "miktar": self.quantity,
            "birim": self.unit_type,
            "birimFiyat": f"{self.unit_price:.2f}",
            "fiyat": f"{self.price:.2f}",
            "iskontoOrani": self.discount_rate,
            "iskontoTutari": f"{self.discount_amount:.2f}",
            "iskontoNedeni": self.discount_reason,
            "malHizmetTutari": f"{self.price:.2f}",
            "kdvOrani": f"{self.vat_rate}",
            "vergiOrani": self.tax_rate,
            "kdvTutari": f"{self.vat_amount:.2f}",
            "vergininKdvTutari": f"{self.vat_amount_of_tax:.2f}",
        }


@dataclass
class Invoice:
    """e-Arşiv fatura modeli."""

    date: str  # GG/AA/YYYY
    time: str  # SS:DD:SS
    items: list[InvoiceItem]

    # Alıcı bilgileri
    tax_id_or_tr_id: str = "11111111111"
    title: str = ""
    name: str = ""
    surname: str = ""
    full_address: str = ""
    building_name: str = ""
    building_number: str = ""
    door_number: str = ""
    town: str = ""
    district: str = ""
    city: str = " "
    country: str = "Türkiye"
    zip_code: str = ""
    phone_number: str = ""
    fax_number: str = ""
    email: str = ""
    website: str = ""
    tax_office: str = ""

    # Fatura bilgileri
    currency: str = "TRY"
    currency_rate: str = "0"
    invoice_type: str = "5000/30000"
    hangi_tip: str = "Buyuk"
    document_number: str = ""
    order_number: str = ""
    order_date: str = ""
    dispatch_number: str = ""
    dispatch_date: str = ""
    slip_number: str = ""
    slip_date: str = ""
    slip_time: str = " "
    slip_type: str = " "
    z_report_number: str = ""
    okc_serial_number: str = ""

    # Masraf oranları
    commission_rate: int = 0
    freight_rate: int = 0
    hammaliye_rate: int = 0
    nakliye_rate: int = 0
    commission_amount: str = "0"
    freight_amount: str = "0"
    hammaliye_amount: str = "0"
    nakliye_amount: str = "0"
    commission_vat_rate: int = 0
    freight_vat_rate: int = 0
    hammaliye_vat_rate: int = 0
    nakliye_vat_rate: int = 0
    commission_vat_amount: str = "0"
    freight_vat_amount: str = "0"
    hammaliye_vat_amount: str = "0"
    nakliye_vat_amount: str = "0"

    # Vergi/Kesinti oranları
    income_tax_rate: int = 0
    bagkur_deduction_rate: int = 0
    income_tax_deduction_amount: str = "0"
    bagkur_deduction_amount: str = "0"
    hal_rusum_rate: int = 0
    trade_exchange_rate: int = 0
    national_defense_fund_rate: int = 0
    other_rate: int = 0
    hal_rusum_amount: str = "0"
    trade_exchange_amount: str = "0"
    national_defense_fund_amount: str = "0"
    other_amount: str = "0"
    hal_rusum_vat_rate: int = 0
    trade_exchange_vat_rate: int = 0
    national_defense_fund_vat_rate: int = 0
    other_vat_rate: int = 0
    hal_rusum_vat_amount: str = "0"
    trade_exchange_vat_amount: str = "0"
    national_defense_fund_vat_amount: str = "0"
    other_vat_amount: str = "0"

    # Özel matrah
    special_tax_base_amount: str = "0"
    special_tax_base_rate: int = 0
    special_tax_base_tax_amount: str = "0.00"
    tax_type: str = " "

    # İade
    return_items: list = field(default_factory=list)

    # Toplam masraflar
    total_expenses: str = "0"

    # Override totals (None = auto-calculate)
    grand_total: float | None = None
    total_vat: float | None = None
    grand_total_incl_vat: float | None = None
    total_discount: float = 0.0
    payment_total: float | None = None

    @property
    def calculated_grand_total(self) -> float:
        if self.grand_total is not None:
            return self.grand_total
        return round(sum(item.price for item in self.items), 2)

    @property
    def calculated_total_vat(self) -> float:
        if self.total_vat is not None:
            return self.total_vat
        return round(sum(item.vat_amount for item in self.items), 2)

    @property
    def calculated_grand_total_incl_vat(self) -> float:
        if self.grand_total_incl_vat is not None:
            return self.grand_total_incl_vat
        return round(self.calculated_grand_total + self.calculated_total_vat, 2)

    @property
    def calculated_payment_total(self) -> float:
        if self.payment_total is not None:
            return self.payment_total
        return self.calculated_grand_total_incl_vat

    def to_gib_dict(self, uuid: str) -> dict:
        return {
            "faturaUuid": uuid,
            "belgeNumarasi": self.document_number,
            "faturaTarihi": self.date,
            "saat": self.time,
            "paraBirimi": self.currency,
            "dovzTLkur": self.currency_rate,
            "faturaTipi": self.invoice_type,
            "hangiTip": self.hangi_tip,
            "siparisNumarasi": self.order_number,
            "siparisTarihi": self.order_date,
            "irsaliyeNumarasi": self.dispatch_number,
            "irsaliyeTarihi": self.dispatch_date,
            "fisNo": self.slip_number,
            "fisTarihi": self.slip_date,
            "fisSaati": self.slip_time,
            "fisTipi": self.slip_type,
            "zRaporNo": self.z_report_number,
            "okcSeriNo": self.okc_serial_number,
            "vknTckn": self.tax_id_or_tr_id,
            "aliciUnvan": self.title,
            "aliciAdi": self.name,
            "aliciSoyadi": self.surname,
            "bulvarcaddesokak": self.full_address,
            "binaAdi": self.building_name,
            "binaNo": self.building_number,
            "kapiNo": self.door_number,
            "kasabaKoy": self.town,
            "mahalleSemtIlce": self.district,
            "sehir": self.city,
            "ulke": self.country,
            "postaKodu": self.zip_code,
            "tel": self.phone_number,
            "fax": self.fax_number,
            "eposta": self.email,
            "websitesi": self.website,
            "vergiDairesi": self.tax_office,
            "komisyonOrani": self.commission_rate,
            "navlunOrani": self.freight_rate,
            "hammaliyeOrani": self.hammaliye_rate,
            "nakliyeOrani": self.nakliye_rate,
            "komisyonTutari": self.commission_amount,
            "navlunTutari": self.freight_amount,
            "hammaliyeTutari": self.hammaliye_amount,
            "nakliyeTutari": self.nakliye_amount,
            "komisyonKDVOrani": self.commission_vat_rate,
            "navlunKDVOrani": self.freight_vat_rate,
            "hammaliyeKDVOrani": self.hammaliye_vat_rate,
            "nakliyeKDVOrani": self.nakliye_vat_rate,
            "komisyonKDVTutari": self.commission_vat_amount,
            "navlunKDVTutari": self.freight_vat_amount,
            "hammaliyeKDVTutari": self.hammaliye_vat_amount,
            "nakliyeKDVTutari": self.nakliye_vat_amount,
            "gelirVergisiOrani": self.income_tax_rate,
            "bagkurTevkifatiOrani": self.bagkur_deduction_rate,
            "gelirVergisiTevkifatiTutari": self.income_tax_deduction_amount,
            "bagkurTevkifatiTutari": self.bagkur_deduction_amount,
            "halRusumuOrani": self.hal_rusum_rate,
            "ticaretBorsasiOrani": self.trade_exchange_rate,
            "milliSavunmaFonuOrani": self.national_defense_fund_rate,
            "digerOrani": self.other_rate,
            "halRusumuTutari": self.hal_rusum_amount,
            "ticaretBorsasiTutari": self.trade_exchange_amount,
            "milliSavunmaFonuTutari": self.national_defense_fund_amount,
            "digerTutari": self.other_amount,
            "halRusumuKDVOrani": self.hal_rusum_vat_rate,
            "ticaretBorsasiKDVOrani": self.trade_exchange_vat_rate,
            "milliSavunmaFonuKDVOrani": self.national_defense_fund_vat_rate,
            "digerKDVOrani": self.other_vat_rate,
            "halRusumuKDVTutari": self.hal_rusum_vat_amount,
            "ticaretBorsasiKDVTutari": self.trade_exchange_vat_amount,
            "milliSavunmaFonuKDVTutari": self.national_defense_fund_vat_amount,
            "digerKDVTutari": self.other_vat_amount,
            "iadeTable": [{} for _ in self.return_items],
            "ozelMatrahTutari": self.special_tax_base_amount,
            "ozelMatrahOrani": self.special_tax_base_rate,
            "ozelMatrahVergiTutari": self.special_tax_base_tax_amount,
            "vergiCesidi": self.tax_type,
            "malHizmetTable": [item.to_gib_dict() for item in self.items],
            "tip": "İskonto",
            "matrah": f"{self.calculated_grand_total:.2f}",
            "malhizmetToplamTutari": f"{self.calculated_grand_total:.2f}",
            "toplamIskonto": f"{self.total_discount:.2f}",
            "hesaplanankdv": f"{self.calculated_total_vat:.2f}",
            "vergilerToplami": f"{self.calculated_total_vat:.2f}",
            "vergilerDahilToplamTutar": f"{self.calculated_grand_total_incl_vat:.2f}",
            "toplamMasraflar": self.total_expenses,
            "odenecekTutar": f"{self.calculated_payment_total:.2f}",
            "not": price_to_text(self.calculated_payment_total),
        }


def price_to_text(price: float) -> str:
    """Fiyatı Türkçe yazıya çevirir (fatura notu için)."""
    main, sub = f"{price:.2f}".split(".")
    if sub == "00":
        sub = "0"
    return f"{_number_to_turkish(int(main))} LIRA {_number_to_turkish(int(sub))} KURUS"


def _number_to_turkish(n: int) -> str:
    """Sayıyı Türkçe yazıya çevirir."""
    if n == 0:
        return "SIFIR"

    ones = ["", "BIR", "IKI", "UC", "DORT", "BES", "ALTI", "YEDI", "SEKIZ", "DOKUZ"]
    tens = [
        "",
        "ON",
        "YIRMI",
        "OTUZ",
        "KIRK",
        "ELLI",
        "ALTMIS",
        "YETMIS",
        "SEKSEN",
        "DOKSAN",
    ]

    if n < 0:
        return "EKSI " + _number_to_turkish(-n)

    parts: list[str] = []

    if n >= 1_000_000_000:
        q, n = divmod(n, 1_000_000_000)
        parts.append(_number_to_turkish(q) + " MILYAR")

    if n >= 1_000_000:
        q, n = divmod(n, 1_000_000)
        parts.append(_number_to_turkish(q) + " MILYON")

    if n >= 1000:
        q, n = divmod(n, 1000)
        if q == 1:
            parts.append("BIN")
        else:
            parts.append(_number_to_turkish(q) + " BIN")

    if n >= 100:
        q, n = divmod(n, 100)
        if q == 1:
            parts.append("YUZ")
        else:
            parts.append(ones[q] + " YUZ")

    if n >= 10:
        q, n = divmod(n, 10)
        parts.append(tens[q])

    if n > 0:
        parts.append(ones[n])

    return " ".join(parts)
