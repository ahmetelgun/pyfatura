from __future__ import annotations

import json
import uuid
from urllib.parse import urlencode, quote

import httpx

from pyfatura.models import Invoice

_ENV = {
    "PROD": "https://earsivportal.efatura.gov.tr",
    "TEST": "https://earsivportaltest.efatura.gov.tr",
}

_COMMANDS = {
    "create_draft_invoice": ("EARSIV_PORTAL_FATURA_OLUSTUR", "RG_BASITFATURA"),
    "get_all_invoices_by_date_range": (
        "EARSIV_PORTAL_TASLAKLARI_GETIR",
        "RG_BASITTASLAKLAR",
    ),
    "get_all_invoices_issued_to_me": (
        "EARSIV_PORTAL_ADIMA_KESILEN_BELGELERI_GETIR",
        "RG_ALICI_TASLAKLAR",
    ),
    "sign_draft_invoice": (
        "EARSIV_PORTAL_FATURA_HSM_CIHAZI_ILE_IMZALA",
        "RG_BASITTASLAKLAR",
    ),
    "get_invoice_html": ("EARSIV_PORTAL_FATURA_GOSTER", "RG_BASITTASLAKLAR"),
    "cancel_draft_invoice": ("EARSIV_PORTAL_FATURA_SIL", "RG_BASITTASLAKLAR"),
    "get_recipient_data": (
        "SICIL_VEYA_MERNISTEN_BILGILERI_GETIR",
        "RG_BASITFATURA",
    ),
    "send_sign_sms": ("EARSIV_PORTAL_SMSSIFRE_GONDER", "RG_SMSONAY"),
    "verify_sms": ("EARSIV_PORTAL_SMSSIFRE_DOGRULA", "RG_SMSONAY"),
    "get_user_data": ("EARSIV_PORTAL_KULLANICI_BILGILERI_GETIR", "RG_KULLANICI"),
    "update_user_data": ("EARSIV_PORTAL_KULLANICI_BILGILERI_KAYDET", "RG_KULLANICI"),
}

_DEFAULT_HEADERS = {
    "accept": "*/*",
    "accept-language": "tr,en-US;q=0.9,en;q=0.8",
    "cache-control": "no-cache",
    "content-type": "application/x-www-form-urlencoded;charset=UTF-8",
    "pragma": "no-cache",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}


class EArsivClient:
    """GİB e-Arşiv Portal istemcisi.

    Türkiye Gelir İdaresi Başkanlığı e-Arşiv portalı ile iletişim kurar.
    Fatura oluşturma, imzalama, sorgulama ve iptal işlemlerini destekler.

    Örnek kullanım::

        client = EArsivClient(test_mode=True)

        # Giriş yap
        client.login("kullanici", "sifre")

        # Fatura oluştur
        invoice = Invoice(
            date="13/03/2026",
            time="12:00:00",
            items=[InvoiceItem(name="Yazılım Hizmeti", quantity=1, unit_price=1000, vat_rate=20)],
            name="Ali",
            surname="Yılmaz",
        )
        result = client.create_draft_invoice(invoice)

        # Çıkış yap
        client.logout()
    """

    def __init__(self, test_mode: bool = False) -> None:
        self._env = "TEST" if test_mode else "PROD"
        self._base_url = _ENV[self._env]
        self._token: str | None = None
        self._client = httpx.Client(headers=_DEFAULT_HEADERS, timeout=30.0)

    @property
    def token(self) -> str | None:
        return self._token

    def _run_command(self, command: str, page_name: str, data: dict | None = None) -> dict:
        if self._token is None:
            raise RuntimeError("Önce login() ile giriş yapmalısınız.")

        body = (
            f"cmd={command}"
            f"&callid={uuid.uuid1()}"
            f"&pageName={page_name}"
            f"&token={self._token}"
            f"&jp={quote(json.dumps(data or {}))}"
        )
        response = self._client.post(
            f"{self._base_url}/earsiv-services/dispatch",
            content=body,
            headers={
                **_DEFAULT_HEADERS,
                "referrer": f"{self._base_url}/login.jsp",
            },
        )
        response.raise_for_status()
        return response.json()

    # --- Auth ---

    def login(self, username: str, password: str) -> str:
        """e-Arşiv portalına giriş yapar ve token döner."""
        assoscmd = "anologin" if self._env == "PROD" else "login"
        body = (
            f"assoscmd={assoscmd}"
            f"&rtype=json"
            f"&userid={username}"
            f"&sifre={password}"
            f"&sifre2={password}"
            f"&parola=1&"
        )
        response = self._client.post(
            f"{self._base_url}/earsiv-services/assos-login",
            content=body,
            headers={
                **_DEFAULT_HEADERS,
                "referrer": f"{self._base_url}/intragiris.html",
            },
        )
        response.raise_for_status()
        result = response.json()
        self._token = result["token"]
        return self._token

    def logout(self) -> str | None:
        """Oturumu kapatır."""
        if self._token is None:
            return None
        assoscmd = "anologin" if self._env == "PROD" else "logout"
        body = f"assoscmd={assoscmd}&rtype=json&token={self._token}&"
        response = self._client.post(
            f"{self._base_url}/earsiv-services/assos-login",
            content=body,
            headers={
                **_DEFAULT_HEADERS,
                "referrer": f"{self._base_url}/intragiris.html",
            },
        )
        response.raise_for_status()
        result = response.json()
        self._token = None
        return result.get("data")

    # --- Fatura İşlemleri ---

    def create_draft_invoice(self, invoice: Invoice) -> dict:
        """Taslak fatura oluşturur.

        Returns:
            ``{"date": "...", "uuid": "...", ...}`` şeklinde sözlük.
        """
        invoice_uuid = str(uuid.uuid1())
        data = invoice.to_gib_dict(invoice_uuid)
        cmd, page = _COMMANDS["create_draft_invoice"]
        result = self._run_command(cmd, page, data)
        return {"date": invoice.date, "uuid": invoice_uuid, **result}

    def get_all_invoices_by_date_range(
        self, start_date: str, end_date: str
    ) -> list[dict]:
        """Tarih aralığına göre kesilen faturaları getirir.

        Args:
            start_date: Başlangıç tarihi (GG/AA/YYYY).
            end_date: Bitiş tarihi (GG/AA/YYYY).
        """
        cmd, page = _COMMANDS["get_all_invoices_by_date_range"]
        result = self._run_command(
            cmd,
            page,
            {
                "baslangic": start_date,
                "bitis": end_date,
                "hangiTip": "5000/30000",
                "table": [],
            },
        )
        return result.get("data", [])

    def get_all_invoices_issued_to_me(
        self, start_date: str, end_date: str
    ) -> list[dict]:
        """Tarih aralığına göre adınıza kesilen faturaları getirir."""
        cmd, page = _COMMANDS["get_all_invoices_issued_to_me"]
        result = self._run_command(
            cmd,
            page,
            {
                "baslangic": start_date,
                "bitis": end_date,
                "hangiTip": "5000/30000",
                "table": [],
            },
        )
        return result.get("data", [])

    def find_invoice(self, date: str, invoice_uuid: str) -> dict | None:
        """Belirli bir taslak faturayı UUID ile bulur."""
        invoices = self.get_all_invoices_by_date_range(date, date)
        for inv in invoices:
            if inv.get("ettn") == invoice_uuid:
                return inv
        return None

    def sign_draft_invoice(self, draft_invoice: dict) -> dict:
        """Taslak faturayı imzalar/onaylar."""
        cmd, page = _COMMANDS["sign_draft_invoice"]
        return self._run_command(cmd, page, {"imzalanacaklar": [draft_invoice]})

    def get_invoice_html(self, invoice_uuid: str, signed: bool = True) -> str:
        """Faturanın HTML içeriğini döner."""
        cmd, page = _COMMANDS["get_invoice_html"]
        result = self._run_command(
            cmd,
            page,
            {
                "ettn": invoice_uuid,
                "onayDurumu": "Onaylandı" if signed else "Onaylanmadı",
            },
        )
        return result.get("data", "")

    def get_download_url(self, invoice_uuid: str, signed: bool = True) -> str:
        """Fatura indirme URL'si oluşturur."""
        onay = quote("Onaylandı" if signed else "Onaylanmadı")
        return (
            f"{self._base_url}/earsiv-services/download"
            f"?token={self._token}"
            f"&ettn={invoice_uuid}"
            f"&belgeTip=FATURA"
            f"&onayDurumu={onay}"
            f"&cmd=downloadResource&"
        )

    def cancel_draft_invoice(self, reason: str, draft_invoice: dict) -> dict:
        """Taslak faturayı iptal eder."""
        cmd, page = _COMMANDS["cancel_draft_invoice"]
        result = self._run_command(
            cmd, page, {"silinecekler": [draft_invoice], "aciklama": reason}
        )
        return result.get("data", {})

    # --- Alıcı Sorgulama ---

    def get_recipient_data(self, tax_id_or_tr_id: str) -> dict:
        """Vergi kimlik numarası veya TC kimlik numarası ile alıcı bilgilerini sorgular."""
        cmd, page = _COMMANDS["get_recipient_data"]
        result = self._run_command(cmd, page, {"vknTcknn": tax_id_or_tr_id})
        return result.get("data", {})

    # --- SMS İmza ---

    def send_sign_sms_code(self, phone: str) -> str:
        """İmza SMS doğrulama kodu gönderir."""
        cmd, page = _COMMANDS["send_sign_sms"]
        result = self._run_command(
            cmd, page, {"CEPTEL": phone, "KCEPTEL": False, "TIP": ""}
        )
        return result.get("oid", "")

    def verify_sign_sms_code(self, sms_code: str, operation_id: str) -> str:
        """SMS doğrulama kodunu onaylar."""
        cmd, page = _COMMANDS["verify_sms"]
        result = self._run_command(
            cmd, page, {"SIFRE": sms_code, "OID": operation_id}
        )
        return result.get("oid", "")

    # --- Kullanıcı Bilgileri ---

    def get_user_data(self) -> dict:
        """Kullanıcı profil bilgilerini getirir."""
        cmd, page = _COMMANDS["get_user_data"]
        result = self._run_command(cmd, page)
        data = result.get("data", {})
        return {
            "tax_id_or_tr_id": data.get("vknTckn", ""),
            "title": data.get("unvan", ""),
            "name": data.get("ad", ""),
            "surname": data.get("soyad", ""),
            "registry_no": data.get("sicilNo", ""),
            "mersis_no": data.get("mersisNo", ""),
            "tax_office": data.get("vergiDairesi", ""),
            "full_address": data.get("cadde", ""),
            "building_name": data.get("apartmanAdi", ""),
            "building_number": data.get("apartmanNo", ""),
            "door_number": data.get("kapiNo", ""),
            "town": data.get("kasaba", ""),
            "district": data.get("ilce", ""),
            "city": data.get("il", ""),
            "zip_code": data.get("postaKodu", ""),
            "country": data.get("ulke", ""),
            "phone_number": data.get("telNo", ""),
            "fax_number": data.get("faksNo", ""),
            "email": data.get("ePostaAdresi", ""),
            "website": data.get("webSitesiAdresi", ""),
            "business_center": data.get("isMerkezi", ""),
        }

    def update_user_data(self, user_data: dict) -> dict:
        """Kullanıcı profil bilgilerini günceller."""
        cmd, page = _COMMANDS["update_user_data"]
        gib_data = {
            "vknTckn": user_data.get("tax_id_or_tr_id", ""),
            "unvan": user_data.get("title", ""),
            "ad": user_data.get("name", ""),
            "soyad": user_data.get("surname", ""),
            "sicilNo": user_data.get("registry_no", ""),
            "mersisNo": user_data.get("mersis_no", ""),
            "vergiDairesi": user_data.get("tax_office", ""),
            "cadde": user_data.get("full_address", ""),
            "apartmanAdi": user_data.get("building_name", ""),
            "apartmanNo": user_data.get("building_number", ""),
            "kapiNo": user_data.get("door_number", ""),
            "kasaba": user_data.get("town", ""),
            "ilce": user_data.get("district", ""),
            "il": user_data.get("city", ""),
            "postaKodu": user_data.get("zip_code", ""),
            "ulke": user_data.get("country", ""),
            "telNo": user_data.get("phone_number", ""),
            "faksNo": user_data.get("fax_number", ""),
            "ePostaAdresi": user_data.get("email", ""),
            "webSitesiAdresi": user_data.get("website", ""),
            "isMerkezi": user_data.get("business_center", ""),
        }
        result = self._run_command(cmd, page, gib_data)
        return result.get("data", {})

    # --- Toplu İşlemler ---

    def create_invoice(
        self, invoice: Invoice, sign: bool = True
    ) -> dict:
        """Fatura oluşturur, opsiyonel olarak imzalar.

        Returns:
            ``{"uuid": "...", "signed": bool}`` şeklinde sözlük.
        """
        draft = self.create_draft_invoice(invoice)
        draft_details = self.find_invoice(draft["date"], draft["uuid"])
        if sign and draft_details:
            self.sign_draft_invoice(draft_details)
        return {"uuid": draft["uuid"], "signed": sign}

    def create_invoice_and_get_download_url(
        self, invoice: Invoice, sign: bool = True
    ) -> str:
        """Fatura oluşturur ve indirme URL'si döner."""
        result = self.create_invoice(invoice, sign=sign)
        return self.get_download_url(result["uuid"], signed=result["signed"])

    def create_invoice_and_get_html(
        self, invoice: Invoice, sign: bool = True
    ) -> str:
        """Fatura oluşturur ve HTML içeriğini döner."""
        result = self.create_invoice(invoice, sign=sign)
        return self.get_invoice_html(result["uuid"], signed=result["signed"])

    # --- Context Manager ---

    def __enter__(self) -> EArsivClient:
        return self

    def __exit__(self, *args: object) -> None:
        self._client.close()

    def close(self) -> None:
        """HTTP istemcisini kapatır."""
        self._client.close()
