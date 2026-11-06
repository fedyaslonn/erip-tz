class DealAlreadyProcessedError(Exception):
    def __init__(self, deal_id: str, status: str):
        self.deal_id = str(deal_id)
        self.status = status


class InvalidCurrencyPairError(Exception):
    def __init__(self, source: str, target: str):
        self.source = source
        self.target = target


class InvalidAmountError(Exception):
    pass
