import json

import httpx
import pytest

from pyfatura import EArsivClient, Invoice, InvoiceItem


@pytest.fixture
def client():
    c = EArsivClient(test_mode=True)
    yield c
    c.close()


class TestClientInit:
    def test_test_mode(self):
        c = EArsivClient(test_mode=True)
        assert "test" in c._base_url
        c.close()

    def test_prod_mode(self):
        c = EArsivClient(test_mode=False)
        assert "test" not in c._base_url
        c.close()

    def test_no_token_initially(self, client):
        assert client.token is None


class TestRunCommandRequiresLogin:
    def test_raises_without_login(self, client):
        with pytest.raises(RuntimeError, match="login"):
            client.get_user_data()


class TestLogin:
    def test_login_sets_token(self, client, httpx_mock):
        httpx_mock.add_response(
            url=f"{client._base_url}/earsiv-services/assos-login",
            json={"token": "test-token-123"},
        )
        token = client.login("user", "pass")
        assert token == "test-token-123"
        assert client.token == "test-token-123"

    def test_logout_clears_token(self, client, httpx_mock):
        # Login first
        httpx_mock.add_response(
            url=f"{client._base_url}/earsiv-services/assos-login",
            json={"token": "test-token-123"},
        )
        client.login("user", "pass")

        # Logout
        httpx_mock.add_response(
            url=f"{client._base_url}/earsiv-services/assos-login",
            json={"data": "redirect-url"},
        )
        result = client.logout()
        assert client.token is None
        assert result == "redirect-url"


class TestGetDownloadUrl:
    def test_signed(self, client):
        client._token = "tok"
        url = client.get_download_url("uuid-123", signed=True)
        assert "token=tok" in url
        assert "ettn=uuid-123" in url
        assert "Onayland" in url

    def test_unsigned(self, client):
        client._token = "tok"
        url = client.get_download_url("uuid-123", signed=False)
        assert "Onaylanmad" in url


class TestContextManager:
    def test_context_manager(self):
        with EArsivClient(test_mode=True) as client:
            assert client.token is None

class TestCreateDraftInvoice:
    def test_interaktif_fallback(self, client, httpx_mock):
        client._token = "test-token-123"
        invoice = Invoice(
            date="01/04/2026",
            time="12:00:00",
            items=[InvoiceItem(name="Test", quantity=1, unit_price=10.0, vat_rate=20)],
        )

        # Ilk istek basarisiz (Interaktif kural ihlali)
        httpx_mock.add_response(
            url=f"{client._base_url}/earsiv-services/dispatch",
            json={"data": "Bu mükellef (VKN/TCKN: 111) e-Arşiv Portal Fatura'nın ekranından fatura kesemez."},
        )

        # Ikinci istek basarili
        httpx_mock.add_response(
            url=f"{client._base_url}/earsiv-services/dispatch",
            json={"data": "Faturanız başarıyla oluşturulmuştur."},
        )

        result = client.create_draft_invoice(invoice)

        assert invoice.hangi_tip == "5000/30000"
        assert result["data"] == "Faturanız başarıyla oluşturulmuştur."
        requests = httpx_mock.get_requests()
        assert len(requests) == 2
