"""
Intelligence Extractor
Scammer ke messages se important data nikalta hai:
- UPI IDs (jaise name@paytm)
- Bank Account Numbers
- Phone Numbers
- Phishing URLs/Links
"""

import re
from typing import Dict, List


class IntelligenceExtractor:

    @staticmethod
    def extract_upi_ids(text: str) -> List[str]:
        """UPI IDs dhundho"""
        pattern = r'\b[a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\b'
        matches = re.findall(pattern, text)

        # Sirf real UPI providers rakhenge
        upi_providers = [
            'paytm', 'phonepe', 'googlepay', 'ybl',
            'axl', 'oksbi', 'okicici', 'okhdfc',
            'gpay', 'bhim', 'upi'
        ]

        upi_ids = []
        for match in matches:
            if any(provider in match.lower() for provider in upi_providers):
                upi_ids.append(match)

        return upi_ids

    @staticmethod
    def extract_bank_accounts(text: str) -> List[str]:
        """Bank account numbers dhundho (9-18 digits)"""
        # Sirf extract karo agar 'account' word hai
        if any(word in text.lower() for word in ['account', 'acc', 'ifsc', 'bank']):
            pattern = r'\b\d{9,18}\b'
            return re.findall(pattern, text)
        return []

    @staticmethod
    def extract_ifsc_codes(text: str) -> List[str]:
        """IFSC codes dhundho — format: UTIB0000001"""
        pattern = r'\b[A-Z]{4}0[A-Z0-9]{6}\b'
        return re.findall(pattern, text)

    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """Indian phone numbers dhundho (10 digits, 6-9 se shuru)"""
        pattern = r'\b[6-9]\d{9}\b'
        return re.findall(pattern, text)

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """URLs dhundho"""
        pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(pattern, text)

    @staticmethod
    def is_suspicious_url(url: str) -> bool:
        """URL suspicious hai ya nahi"""
        bad_signs = [
            'bit.ly', 'tinyurl', 'goo.gl',
            'login', 'verify', 'confirm',
            '.tk', '.ml', '.ga', '.cf',
            'http://'
        ]
        return any(sign in url.lower() for sign in bad_signs)

    @staticmethod
    def extract_all(text: str) -> Dict:
        """
        Ek call mein sab kuch extract karo — YEH MAIN FUNCTION HAI
        """
        upi_ids = IntelligenceExtractor.extract_upi_ids(text)
        bank_accounts = IntelligenceExtractor.extract_bank_accounts(text)
        ifsc_codes = IntelligenceExtractor.extract_ifsc_codes(text)
        phone_numbers = IntelligenceExtractor.extract_phone_numbers(text)
        urls = IntelligenceExtractor.extract_urls(text)
        suspicious_urls = [u for u in urls if IntelligenceExtractor.is_suspicious_url(u)]

        # Print karo kya mila
        if upi_ids:
            print(f"  ✅ UPI IDs: {upi_ids}")
        if phone_numbers:
            print(f"  ✅ Phones: {phone_numbers}")
        if bank_accounts:
            print(f"  ✅ Accounts: {bank_accounts}")
        if urls:
            print(f"  ✅ URLs: {urls}")

        return {
            'upi_ids': upi_ids,
            'bank_accounts': bank_accounts,
            'ifsc_codes': ifsc_codes,
            'phone_numbers': phone_numbers,
            'urls': urls,
            'suspicious_urls': suspicious_urls
        }