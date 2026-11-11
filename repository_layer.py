"""Слой репозитория: хранение данных и CRUD-операции, работа с файлами."""

import json
import xml.etree.ElementTree as ET

from data_layer import Account, Client
from exceptions import BankError


class BankRepository:
    """Хранит клиентов и счета в словарях (в оперативной памяти).

    Реализует CRUD: Create (add), Read (get), Update (update),
    Delete (delete).
    """

    def __init__(self) -> None:
        self.clients: dict[str, Client] = {}
        self.accounts: dict[str, Account] = {}

    # ----- Клиенты -----
    def add_client(self, client: Client) -> None:
        """Добавляет нового клиента."""
        if client.client_id in self.clients:
            raise BankError(f"Клиент {client.client_id} уже существует")
        self.clients[client.client_id] = client

    def get_client(self, client_id: str) -> Client:
        """Возвращает клиента по номеру."""
        try:
            return self.clients[client_id]
        except KeyError:
            raise BankError(f"Клиент {client_id} не найден")

    def get_all_clients(self) -> list[Client]:
        """Возвращает список всех клиентов."""
        return list(self.clients.values())

    def update_client(self, client: Client) -> None:
        """Сохраняет изменения клиента."""
        self.get_client(client.client_id)  # проверяем, что клиент есть
        self.clients[client.client_id] = client

    def delete_client(self, client_id: str) -> None:
        """Удаляет клиента."""
        self.get_client(client_id)
        del self.clients[client_id]

    # ----- Счета -----
    def add_account(self, account: Account) -> None:
        """Добавляет новый счёт."""
        if account.number in self.accounts:
            raise BankError(f"Счёт {account.number} уже существует")
        self.accounts[account.number] = account

    def get_account(self, number: str) -> Account:
        """Возвращает счёт по номеру."""
        try:
            return self.accounts[number]
        except KeyError:
            raise BankError(f"Счёт {number} не найден")

    def get_all_accounts(self) -> list[Account]:
        """Возвращает список всех счетов."""
        return list(self.accounts.values())

    def update_account(self, account: Account) -> None:
        """Сохраняет изменения счёта."""
        self.get_account(account.number)
        self.accounts[account.number] = account

    def delete_account(self, number: str) -> None:
        """Удаляет счёт."""
        self.get_account(number)
        del self.accounts[number]

    def clear(self) -> None:
        """Удаляет все данные (перед загрузкой из файла)."""
        self.clients.clear()
        self.accounts.clear()


class FileStorage:
    """Сохраняет данные репозитория в файлы JSON и XML и загружает их."""

    def save_json(self, repository: BankRepository, path: str) -> None:
        """Записывает всех клиентов и все счета в JSON-файл."""
        data = {"clients": [], "accounts": []}
        for client in repository.get_all_clients():
            data["clients"].append(client.to_dict())
        for account in repository.get_all_accounts():
            data["accounts"].append(account.to_dict())
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except OSError:
            raise BankError(f"Не удалось записать файл {path}")

    def load_json(self, repository: BankRepository, path: str) -> None:
        """Читает клиентов и счета из JSON-файла."""
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
            clients = [Client.from_dict(item) for item in data["clients"]]
            accounts = [Account.from_dict(item) for item in data["accounts"]]
        except FileNotFoundError:
            raise BankError(f"Файл {path} не найден")
        except json.JSONDecodeError:
            raise BankError(f"Файл {path} не является корректным JSON")
        except (KeyError, ValueError, TypeError):
            raise BankError(f"В файле {path} неверная структура данных")
        self._fill(repository, clients, accounts)

    def save_xml(self, repository: BankRepository, path: str) -> None:
        """Записывает всех клиентов и все счета в XML-файл."""
        root = ET.Element("bank")
        clients_element = ET.SubElement(root, "clients")
        for client in repository.get_all_clients():
            element = ET.SubElement(clients_element, "client",
                                    id=client.client_id)
            ET.SubElement(element, "name").text = client.name
            ET.SubElement(element, "phone").text = client.phone

        accounts_element = ET.SubElement(root, "accounts")
        for account in repository.get_all_accounts():
            data = account.to_dict()
            element = ET.SubElement(accounts_element, "account",
                                    type=data["type"],
                                    number=data["number"],
                                    owner_id=data["owner_id"])
            ET.SubElement(element, "balance").text = str(data["balance"])
            if "credit_limit" in data:
                limit = ET.SubElement(element, "credit_limit")
                limit.text = str(data["credit_limit"])
            history = ET.SubElement(element, "transactions")
            for item in data["transactions"]:
                ET.SubElement(history, "transaction", kind=item["kind"],
                              amount=str(item["amount"]), date=item["date"])

        ET.indent(root)
        try:
            ET.ElementTree(root).write(path, encoding="utf-8",
                                       xml_declaration=True)
        except OSError:
            raise BankError(f"Не удалось записать файл {path}")

    def load_xml(self, repository: BankRepository, path: str) -> None:
        """Читает клиентов и счета из XML-файла."""
        try:
            root = ET.parse(path).getroot()
            clients = []
            for element in root.find("clients"):
                data = {"id": element.get("id"),
                        "name": element.find("name").text,
                        "phone": element.find("phone").text}
                clients.append(Client.from_dict(data))
            accounts = []
            for element in root.find("accounts"):
                data = {"type": element.get("type"),
                        "number": element.get("number"),
                        "owner_id": element.get("owner_id"),
                        "balance": element.find("balance").text,
                        "transactions": []}
                if element.find("credit_limit") is not None:
                    data["credit_limit"] = element.find("credit_limit").text
                for item in element.find("transactions"):
                    data["transactions"].append(item.attrib)
                accounts.append(Account.from_dict(data))
        except FileNotFoundError:
            raise BankError(f"Файл {path} не найден")
        except ET.ParseError:
            raise BankError(f"Файл {path} не является корректным XML")
        except (AttributeError, KeyError, ValueError, TypeError):
            raise BankError(f"В файле {path} неверная структура данных")
        self._fill(repository, clients, accounts)

    def _fill(self, repository: BankRepository, clients: list[Client],
              accounts: list[Account]) -> None:
        """Заменяет данные в репозитории на прочитанные из файла."""
        repository.clear()
        for client in clients:
            repository.add_client(client)
        for account in accounts:
            repository.add_account(account)
