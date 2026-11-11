"""Собственные исключения программы."""


class BankError(Exception):
    """Ошибка в работе банка: неверные данные, счёт не найден и т. п."""


class InsufficientFundsError(BankError):
    """Недостаточно денег на счёте для снятия или перевода."""

    def __init__(self, number: str, amount: float, available: float) -> None:
        self.number = number
        self.amount = amount
        self.available = available
        message = (f"На счёте {number} недостаточно средств: "
                   f"нужно {amount:.2f}, доступно {available:.2f}")
        super().__init__(message)
