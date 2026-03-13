from pyfatura.models import InvoiceItem, Invoice, price_to_text, _number_to_turkish


class TestNumberToTurkish:
    def test_zero(self):
        assert _number_to_turkish(0) == "SIFIR"

    def test_single_digit(self):
        assert _number_to_turkish(5) == "BES"

    def test_teens(self):
        assert _number_to_turkish(13) == "ON UC"

    def test_tens(self):
        assert _number_to_turkish(50) == "ELLI"

    def test_hundred(self):
        assert _number_to_turkish(100) == "YUZ"

    def test_hundreds(self):
        assert _number_to_turkish(350) == "UC YUZ ELLI"

    def test_thousand(self):
        assert _number_to_turkish(1000) == "BIN"

    def test_thousands(self):
        assert _number_to_turkish(1450) == "BIN DORT YUZ ELLI"

    def test_large_number(self):
        assert _number_to_turkish(2500000) == "IKI MILYON BES YUZ BIN"

    def test_negative(self):
        assert _number_to_turkish(-42) == "EKSI KIRK IKI"


class TestPriceToText:
    def test_whole_number(self):
        result = price_to_text(1450.0)
        assert result == "BIN DORT YUZ ELLI LIRA SIFIR KURUS"

    def test_with_kurus(self):
        result = price_to_text(100.50)
        assert result == "YUZ LIRA ELLI KURUS"

    def test_small_amount(self):
        result = price_to_text(1.99)
        assert result == "BIR LIRA DOKSAN DOKUZ KURUS"


class TestInvoiceItem:
    def test_price_calculation(self):
        item = InvoiceItem(name="Test", quantity=3, unit_price=100.0, vat_rate=18)
        assert item.price == 300.0
        assert item.vat_amount == 54.0

    def test_to_gib_dict(self):
        item = InvoiceItem(name="Hizmet", quantity=1, unit_price=1000.0, vat_rate=20)
        d = item.to_gib_dict()
        assert d["malHizmet"] == "Hizmet"
        assert d["miktar"] == 1
        assert d["birimFiyat"] == "1000.00"
        assert d["kdvOrani"] == "20"
        assert d["kdvTutari"] == "200.00"


class TestInvoice:
    def _make_invoice(self, **kwargs):
        defaults = {
            "date": "13/03/2026",
            "time": "12:00:00",
            "items": [
                InvoiceItem(name="Yazılım", quantity=1, unit_price=1000.0, vat_rate=20),
                InvoiceItem(name="Danışmanlık", quantity=2, unit_price=500.0, vat_rate=20),
            ],
        }
        defaults.update(kwargs)
        return Invoice(**defaults)

    def test_totals(self):
        inv = self._make_invoice()
        assert inv.calculated_grand_total == 2000.0
        assert inv.calculated_total_vat == 400.0
        assert inv.calculated_grand_total_incl_vat == 2400.0
        assert inv.calculated_payment_total == 2400.0

    def test_override_totals(self):
        inv = self._make_invoice(grand_total=1800.0, total_vat=360.0)
        assert inv.calculated_grand_total == 1800.0
        assert inv.calculated_total_vat == 360.0

    def test_to_gib_dict(self):
        inv = self._make_invoice(name="Ali", surname="Yılmaz", city="İstanbul")
        d = inv.to_gib_dict("test-uuid-123")
        assert d["faturaUuid"] == "test-uuid-123"
        assert d["aliciAdi"] == "Ali"
        assert d["aliciSoyadi"] == "Yılmaz"
        assert d["sehir"] == "İstanbul"
        assert len(d["malHizmetTable"]) == 2
        assert d["odenecekTutar"] == "2400.00"
        assert "LIRA" in d["not"]
