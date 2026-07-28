"""ISO 3166-1 alpha-2 -> display name, for the countries that actually show
up as major players in oil trade data. Falls back to the raw code if a
country isn't in this map rather than failing.
"""

ISO2_NAMES = {
    "US": "United States", "CA": "Canada", "MX": "Mexico", "BR": "Brazil",
    "AR": "Argentina", "VE": "Venezuela", "CO": "Colombia", "EC": "Ecuador",
    "GB": "United Kingdom", "NO": "Norway", "NL": "Netherlands", "DE": "Germany",
    "FR": "France", "IT": "Italy", "ES": "Spain", "RU": "Russia", "KZ": "Kazakhstan",
    "AZ": "Azerbaijan", "SA": "Saudi Arabia", "IQ": "Iraq", "IR": "Iran",
    "AE": "United Arab Emirates", "KW": "Kuwait", "QA": "Qatar", "OM": "Oman",
    "DZ": "Algeria", "LY": "Libya", "NG": "Nigeria", "AO": "Angola", "EG": "Egypt",
    "CN": "China", "IN": "India", "JP": "Japan", "KR": "South Korea",
    "SG": "Singapore", "ID": "Indonesia", "MY": "Malaysia", "TH": "Thailand",
    "AU": "Australia", "ZA": "South Africa",
}


def country_name(code: str) -> str:
    return ISO2_NAMES.get(code, code)
