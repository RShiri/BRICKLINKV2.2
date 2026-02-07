import requests
import streamlit as st
from datetime import datetime, timedelta
import logging

# Fallback rates if API fails
FALLBACK_RATES = {
    'ILS': 1.00,
    'USD': 3.20,
    'EUR': 3.95,
    'GBP': 4.65,
    'CAD': 2.60,
    'AUD': 2.35
}

class CurrencyConverter:
    """
    Singleton Currency Converter with session state caching.
    Fetches live rates from exchangerate-api.com (free tier: 1,500 requests/month).
    Caches rates for 24 hours to prevent quota burn.
    """
    
    @staticmethod
    def get_rates():
        """
        Gets currency rates (cached in session state).
        Only makes API call once per 24 hours.
        """
        # Initialize session state if needed
        if 'currency_rates' not in st.session_state:
            st.session_state.currency_rates = None
            st.session_state.currency_rates_timestamp = None
        
        # Check if cache is valid (24 hours)
        now = datetime.now()
        cache_valid = False
        
        if st.session_state.currency_rates and st.session_state.currency_rates_timestamp:
            age = (now - st.session_state.currency_rates_timestamp).total_seconds()
            cache_valid = age < 86400  # 24 hours in seconds
        
        # Return cached rates if valid
        if cache_valid:
            return st.session_state.currency_rates
        
        # Fetch fresh rates from API
        try:
            logging.info("Fetching live currency rates from API...")
            response = requests.get(
                'https://api.exchangerate-api.com/v4/latest/USD',
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            
            # Convert to ILS-based rates (API gives USD-based)
            usd_to_ils = data['rates'].get('ILS', 3.60)
            
            rates = {
                'ILS': 1.00,
                'USD': usd_to_ils,
                'EUR': data['rates'].get('EUR', 0.95) * usd_to_ils,
                'GBP': data['rates'].get('GBP', 0.82) * usd_to_ils,
                'CAD': data['rates'].get('CAD', 1.35) * usd_to_ils,
                'AUD': data['rates'].get('AUD', 1.52) * usd_to_ils
            }
            
            # Cache the rates
            st.session_state.currency_rates = rates
            st.session_state.currency_rates_timestamp = now
            
            logging.info(f"✅ Live rates fetched: USD={rates['USD']:.2f} ILS")
            return rates
            
        except Exception as e:
            logging.warning(f"⚠️ Currency API failed: {e}. Using fallback rates.")
            
            # Use fallback rates and cache them
            st.session_state.currency_rates = FALLBACK_RATES
            st.session_state.currency_rates_timestamp = now
            
            return FALLBACK_RATES
    
    @staticmethod
    def get_rate(currency_code):
        """Gets the conversion rate for a specific currency to ILS."""
        rates = CurrencyConverter.get_rates()
        return rates.get(currency_code.upper(), 1.0)
    
    @staticmethod
    def convert_to_ils(amount, currency_code):
        """Converts an amount from any currency to ILS."""
        rate = CurrencyConverter.get_rate(currency_code)
        return round(amount * rate, 2)
