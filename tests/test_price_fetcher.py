"""
Tests para price_fetcher.py
Usamos mocks para no depender de internet ni de las APIs reales al correr los tests.
"""
from unittest.mock import patch, MagicMock

from price_fetcher import get_dolar_prices, get_crypto_prices


@patch("price_fetcher.requests.get")
def test_get_dolar_prices_parses_response(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {"casa": "oficial", "venta": 1050.5},
        {"casa": "blue", "venta": 1230.0},
    ]
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    prices = get_dolar_prices()

    assert prices["oficial"] == 1050.5
    assert prices["blue"] == 1230.0


@patch("price_fetcher.requests.get")
def test_get_dolar_prices_empty_response(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    prices = get_dolar_prices()

    assert prices == {}


@patch("price_fetcher.requests.get")
def test_get_crypto_prices_parses_response(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "bitcoin": {"usd": 65000.0},
        "ethereum": {"usd": 3400.0},
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    prices = get_crypto_prices(["bitcoin", "ethereum"], "usd")

    assert prices["bitcoin"] == 65000.0
    assert prices["ethereum"] == 3400.0


@patch("price_fetcher.requests.get")
def test_get_crypto_prices_missing_coin(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"bitcoin": {"usd": 65000.0}}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    prices = get_crypto_prices(["bitcoin", "dogecoin"], "usd")

    assert "bitcoin" in prices
    assert "dogecoin" not in prices
