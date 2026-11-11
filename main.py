"""Точка входа: консольное приложение «Банк и финансовые операции»."""

import os

from exceptions import BankError
from repository_layer import BankRepository, FileStorage
from service_layer import BankService

DEFAULT_FILE = "data/bank.json"

MENU = """
===== Банк =====
1. Список клиентов
2. Добавить клиента
3. Изменить телефон клиента
4. Удалить клиента
5. Открыть счёт
6. Счета клиента
7. Закрыть счёт
8. Пополнить счёт
9. Снять деньги
10. Перевод между счетами
11. История операций по счёту
12. Сохранить данные в файл (JSON или XML)
13. Загрузить данные из файла (JSON или XML)
0. Выход"""


class ConsoleApp:
    """Консольное приложение: показывает меню и вызывает методы сервиса."""

    def __init__(self, service: BankService) -> None:
        self.service = service

    def run(self) -> None:
        """Главный цикл программы."""
        if os.path.exists(DEFAULT_FILE):
            try:
                self.service.load(DEFAULT_FILE)
                print(f"Загружены данные из {DEFAULT_FILE}")
            except BankError as error:
                print("Не удалось загрузить данные:", error)

        while True:
            print(MENU)
            choice = input("Выберите пункт: ").strip()
            if choice == "0":
                print("До свидания!")
                break
            # Ошибки перехватываются, чтобы программа не завершалась
            try:
                self.handle(choice)
            except BankError as error:
                print("Ошибка:", error)
            except ValueError:
                print("Ошибка: нужно ввести число")
            input("\nНажмите Enter, чтобы продолжить...")

    def handle(self, choice: str) -> None:
        """Выполняет выбранный пункт меню."""
        if choice == "1":
            self.show_clients()
        elif choice == "2":
            name = input("ФИО: ")
            phone = input("Телефон (+7XXXXXXXXXX): ")
            client = self.service.add_client(name, phone)
            print("Клиент добавлен:", client)
        elif choice == "3":
            client_id = input("Номер клиента: ")
            phone = input("Новый телефон: ")
            self.service.change_phone(client_id, phone)
            print("Телефон изменён")
        elif choice == "4":
            self.service.delete_client(input("Номер клиента: "))
            print("Клиент удалён")
        elif choice == "5":
            self.open_account()
        elif choice == "6":
            self.show_accounts()
        elif choice == "7":
            self.service.close_account(input("Номер счёта: "))
            print("Счёт закрыт")
        elif choice == "8":
            number = input("Номер счёта: ")
            self.service.deposit(number, self.ask_amount())
            print("Счёт пополнен")
        elif choice == "9":
            number = input("Номер счёта: ")
            self.service.withdraw(number, self.ask_amount())
            print("Деньги сняты")
        elif choice == "10":
            from_number = input("Счёт отправителя: ")
            to_number = input("Счёт получателя: ")
            self.service.transfer(from_number, to_number, self.ask_amount())
            print("Перевод выполнен")
        elif choice == "11":
            self.show_history()
        elif choice == "12":
            path = input("Имя файла (например, data/bank.json): ")
            self.service.save(path)
            print("Данные сохранены")
        elif choice == "13":
            path = input("Имя файла (например, data/bank.xml): ")
            self.service.load(path)
            print("Данные загружены")
        else:
            print("Такого пункта нет")

    def show_clients(self) -> None:
        """Выводит список клиентов."""
        clients = self.service.get_clients()
        if len(clients) == 0:
            print("Клиентов пока нет")
        for client in clients:
            print(client)

    def open_account(self) -> None:
        """Спрашивает данные и открывает счёт."""
        client_id = input("Номер клиента: ")
        account_type = input("Тип счёта (debit / credit): ").strip()
        limit = 0.0
        if account_type == "credit":
            limit = self.ask_amount("Кредитный лимит: ")
        account = self.service.open_account(client_id, account_type, limit)
        print("Открыт счёт:", account)

    def show_accounts(self) -> None:
        """Выводит счета клиента и общую сумму."""
        client_id = input("Номер клиента: ")
        for account in self.service.get_client_accounts(client_id):
            print(account)
        total = self.service.get_total_balance(client_id)
        print(f"Всего на счетах: {total:.2f} руб.")

    def show_history(self) -> None:
        """Выводит историю операций по счёту."""
        history = self.service.get_history(input("Номер счёта: "))
        if len(history) == 0:
            print("Операций пока нет")
        for transaction in history:
            print(transaction)

    def ask_amount(self, text: str = "Сумма: ") -> float:
        """Спрашивает сумму. Если ввести не число, будет ValueError."""
        return float(input(text).replace(",", "."))


def main() -> None:
    """Собирает слои приложения и запускает его."""
    repository = BankRepository()
    storage = FileStorage()
    service = BankService(repository, storage)
    app = ConsoleApp(service)
    app.run()


if __name__ == "__main__":
    main()
