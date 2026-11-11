"""Слой сервиса: бизнес-логика банка."""

from data_layer import Account, Client, CreditAccount, DebitAccount
from data_layer import Transaction
from exceptions import BankError
from repository_layer import BankRepository, FileStorage


class BankService:
    """Бизнес-логика: проверки данных, открытие счетов, переводы.

    Репозиторий и файловое хранилище передаются в конструктор снаружи,
    поэтому сервис не зависит от того, где хранятся данные.
    """

    def __init__(self, repository: BankRepository,
                 storage: FileStorage) -> None:
        self.repository = repository
        self.storage = storage

    # ----- Клиенты -----
    def add_client(self, name: str, phone: str) -> Client:
        """Регистрирует нового клиента."""
        name = name.strip()
        if name == "":
            raise BankError("Имя клиента не может быть пустым")
        self._check_phone(phone)
        client_id = self._next_client_id()
        client = Client(client_id, name, phone)
        self.repository.add_client(client)
        return client

    def get_clients(self) -> list[Client]:
        """Возвращает всех клиентов."""
        return self.repository.get_all_clients()

    def change_phone(self, client_id: str, phone: str) -> None:
        """Меняет телефон клиента."""
        self._check_phone(phone)
        client = self.repository.get_client(client_id)
        client.phone = phone
        self.repository.update_client(client)

    def delete_client(self, client_id: str) -> None:
        """Удаляет клиента и его счета, если на них нет денег и долгов."""
        accounts = self.get_client_accounts(client_id)
        for account in accounts:
            if account.balance != 0:
                raise BankError("Нельзя удалить клиента: на его счетах "
                                "есть деньги или долг")
        for account in accounts:
            self.repository.delete_account(account.number)
        self.repository.delete_client(client_id)

    # ----- Счета -----
    def open_account(self, client_id: str, account_type: str,
                     credit_limit: float = 0.0) -> Account:
        """Открывает клиенту дебетовый или кредитный счёт."""
        self.repository.get_client(client_id)  # проверяем, что клиент есть
        number = self._next_account_number()
        if account_type == "debit":
            account = DebitAccount(number, client_id)
        elif account_type == "credit":
            account = CreditAccount(number, client_id, credit_limit)
        else:
            raise BankError("Тип счёта должен быть debit или credit")
        self.repository.add_account(account)
        return account

    def get_client_accounts(self, client_id: str) -> list[Account]:
        """Возвращает все счета клиента."""
        self.repository.get_client(client_id)
        result = []
        for account in self.repository.get_all_accounts():
            if account.owner_id == client_id:
                result.append(account)
        return result

    def close_account(self, number: str) -> None:
        """Закрывает счёт, если его баланс равен нулю."""
        account = self.repository.get_account(number)
        if account.balance != 0:
            raise BankError("Можно закрыть только счёт с нулевым балансом")
        self.repository.delete_account(number)

    def get_history(self, number: str) -> list[Transaction]:
        """Возвращает историю операций по счёту."""
        return self.repository.get_account(number).transactions

    def get_total_balance(self, client_id: str) -> float:
        """Сумма денег на всех счетах клиента."""
        total = 0.0
        for account in self.get_client_accounts(client_id):
            total += account.balance
        return total

    # ----- Операции с деньгами -----
    def deposit(self, number: str, amount: float) -> None:
        """Пополняет счёт."""
        account = self.repository.get_account(number)
        account.deposit(amount)
        self.repository.update_account(account)

    def withdraw(self, number: str, amount: float) -> None:
        """Снимает деньги со счёта."""
        account = self.repository.get_account(number)
        account.withdraw(amount)
        self.repository.update_account(account)

    def transfer(self, from_number: str, to_number: str,
                 amount: float) -> None:
        """Переводит деньги с одного счёта на другой."""
        if from_number == to_number:
            raise BankError("Нельзя перевести деньги на тот же счёт")
        source = self.repository.get_account(from_number)
        target = self.repository.get_account(to_number)
        source.withdraw(amount, f"Перевод на счёт {to_number}")
        target.deposit(amount, f"Перевод со счёта {from_number}")
        self.repository.update_account(source)
        self.repository.update_account(target)

    # ----- Файлы -----
    def save(self, path: str) -> None:
        """Сохраняет данные в файл .json или .xml."""
        if path.endswith(".json"):
            self.storage.save_json(self.repository, path)
        elif path.endswith(".xml"):
            self.storage.save_xml(self.repository, path)
        else:
            raise BankError("Файл должен иметь расширение .json или .xml")

    def load(self, path: str) -> None:
        """Загружает данные из файла .json или .xml."""
        if path.endswith(".json"):
            self.storage.load_json(self.repository, path)
        elif path.endswith(".xml"):
            self.storage.load_xml(self.repository, path)
        else:
            raise BankError("Файл должен иметь расширение .json или .xml")

    # ----- Вспомогательные методы -----
    def _check_phone(self, phone: str) -> None:
        """Проверяет, что телефон записан в формате +7XXXXXXXXXX."""
        if not (phone.startswith("+7") and len(phone) == 12
                and phone[1:].isdigit()):
            raise BankError("Телефон должен быть в формате +7XXXXXXXXXX")

    def _next_client_id(self) -> str:
        """Новый номер клиента: C1, C2, C3..."""
        biggest = 0
        for client in self.repository.get_all_clients():
            number = int(client.client_id[1:])
            if number > biggest:
                biggest = number
        return "C" + str(biggest + 1)

    def _next_account_number(self) -> str:
        """Новый номер счёта из 20 цифр."""
        biggest = 0
        for account in self.repository.get_all_accounts():
            number = int(account.number[8:])
            if number > biggest:
                biggest = number
        return "40817810" + str(biggest + 1).zfill(12)
