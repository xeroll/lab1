"""Слой данных: сущности предметной области «Банк»."""

from abc import ABC, abstractmethod
from datetime import datetime

from exceptions import BankError, InsufficientFundsError


class Transaction:
    """Операция по счёту: пополнение, снятие или перевод."""

    def __init__(self, kind: str, amount: float, date: str = "") -> None:
        self.kind = kind
        self.amount = amount
        # Если дата не передана, берём текущие дату и время
        if date == "":
            date = datetime.now().strftime("%d.%m.%Y %H:%M")
        self.date = date

    def to_dict(self) -> dict:
        """Превращает операцию в словарь для сохранения в файл."""
        return {"kind": self.kind, "amount": self.amount, "date": self.date}

    @staticmethod
    def from_dict(data: dict) -> "Transaction":
        """Создаёт операцию из словаря, прочитанного из файла."""
        return Transaction(data["kind"], float(data["amount"]), data["date"])

    def __str__(self) -> str:
        return f"{self.date}  {self.kind}: {self.amount:.2f} руб."


class Account(ABC):
    """Банковский счёт. Абстрактный класс: создать можно только наследника."""

    def __init__(self, number: str, owner_id: str,
                 balance: float = 0.0) -> None:
        self.number = number
        self.owner_id = owner_id
        self._balance = balance  # защищённое поле: меняем только через методы
        self.transactions: list[Transaction] = []

    @property
    def balance(self) -> float:
        """Текущий баланс (можно только прочитать)."""
        return self._balance

    @abstractmethod
    def get_type(self) -> str:
        """Тип счёта для сохранения в файл: "debit" или "credit"."""

    @abstractmethod
    def get_title(self) -> str:
        """Название типа счёта для вывода на экран."""

    @abstractmethod
    def get_available(self) -> float:
        """Сколько денег можно снять со счёта прямо сейчас."""

    def deposit(self, amount: float, kind: str = "Пополнение") -> None:
        """Зачисляет деньги на счёт."""
        if amount <= 0:
            raise BankError("Сумма должна быть больше нуля")
        self._balance += amount
        self.transactions.append(Transaction(kind, amount))

    def withdraw(self, amount: float, kind: str = "Снятие") -> None:
        """Списывает деньги со счёта, если их достаточно."""
        if amount <= 0:
            raise BankError("Сумма должна быть больше нуля")
        if amount > self.get_available():
            raise InsufficientFundsError(self.number, amount,
                                         self.get_available())
        self._balance -= amount
        self.transactions.append(Transaction(kind, amount))

    def to_dict(self) -> dict:
        """Превращает счёт в словарь для сохранения в файл."""
        transactions = []
        for transaction in self.transactions:
            transactions.append(transaction.to_dict())
        return {
            "type": self.get_type(),
            "number": self.number,
            "owner_id": self.owner_id,
            "balance": self._balance,
            "transactions": transactions,
        }

    @staticmethod
    def from_dict(data: dict) -> "Account":
        """Создаёт счёт нужного типа из словаря, прочитанного из файла."""
        balance = float(data["balance"])
        if data["type"] == "credit":
            limit = float(data["credit_limit"])
            account = CreditAccount(data["number"], data["owner_id"], limit,
                                    balance)
        elif data["type"] == "debit":
            account = DebitAccount(data["number"], data["owner_id"], balance)
        else:
            raise BankError(f"Неизвестный тип счёта: {data['type']}")
        for item in data["transactions"]:
            account.transactions.append(Transaction.from_dict(item))
        return account

    def __str__(self) -> str:
        return (f"{self.get_title()} счёт {self.number}: "
                f"{self._balance:.2f} руб.")


class DebitAccount(Account):
    """Дебетовый счёт: можно тратить только свои деньги."""

    def get_type(self) -> str:
        return "debit"

    def get_title(self) -> str:
        return "Дебетовый"

    def get_available(self) -> float:
        return self._balance


class CreditAccount(Account):
    """Кредитный счёт: можно уйти в минус в пределах кредитного лимита."""

    def __init__(self, number: str, owner_id: str, credit_limit: float,
                 balance: float = 0.0) -> None:
        super().__init__(number, owner_id, balance)
        if credit_limit < 0:
            raise BankError("Кредитный лимит не может быть отрицательным")
        self.credit_limit = credit_limit

    def get_type(self) -> str:
        return "credit"

    def get_title(self) -> str:
        return "Кредитный"

    def get_available(self) -> float:
        return self._balance + self.credit_limit

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["credit_limit"] = self.credit_limit
        return data

    def __str__(self) -> str:
        return super().__str__() + f" (лимит {self.credit_limit:.2f} руб.)"


class Client:
    """Клиент банка."""

    def __init__(self, client_id: str, name: str, phone: str) -> None:
        self.client_id = client_id
        self.name = name
        self.phone = phone

    def to_dict(self) -> dict:
        """Превращает клиента в словарь для сохранения в файл."""
        return {"id": self.client_id, "name": self.name, "phone": self.phone}

    @staticmethod
    def from_dict(data: dict) -> "Client":
        """Создаёт клиента из словаря, прочитанного из файла."""
        return Client(data["id"], data["name"], data["phone"])

    def __str__(self) -> str:
        return f"{self.client_id}  {self.name}  {self.phone}"
