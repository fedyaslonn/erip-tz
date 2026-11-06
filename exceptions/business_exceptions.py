class CurrencyNotFoundError(Exception):
    def __init__(self, currency_code: str):
        self.currency_code = currency_code


class DealNotFoundError(Exception):
    def __init__(self, deal_id: str):
        self.deal_id = str(deal_id)


class ExternalAPIError(Exception):
    def __init__(self, message: str = "External service unavailable"):
        self.message = message
