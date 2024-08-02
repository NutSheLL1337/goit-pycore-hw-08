from collections import UserDict
from datetime import datetime, timedelta
import pickle

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    # Name: Клас для зберігання імені контакту. Обов'язкове поле.
    pass

class Phone(Field):
    # Phone: Клас для зберігання номера телефону. Має валідацію формату (10 цифр).
    def __init__(self, value):
        if self._validate_phone(value):
            super().__init__(value)
        else:
            raise ValueError("Phone number must be exactly 10 digits.")

    def _validate_phone(self, phone):
        return phone.isdigit() and len(phone) == 10

class Birthday(Field):
    def __init__(self, value):
        try:
            datetime_value = datetime.strptime(value, '%d.%m.%Y')
            super().__init__(datetime_value)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        phone_obj = self.find_phone(phone)
        if phone_obj:
            self.phones.remove(phone_obj)

    def edit_phone(self, old_phone, new_phone):
        phone_obj = self.find_phone(old_phone)
        if phone_obj:
            self.phones.remove(phone_obj)
            self.add_phone(new_phone)

    def find_phone(self, phone):
        for phone_obj in self.phones:
            if phone_obj.value == phone:
                return phone_obj
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}, birthday: {self.birthday.value.strftime('%d.%m.%Y') if self.birthday else 'N/A'}"


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    # Реалізація отримання днів народження та прорахунку днів народжень в найближчі 7 днів
    def get_upcoming_birthdays(self, days=7):
        today = datetime.today().date()
        upcoming_birthdays = []

        for record in self.data.values():
            if record.birthday:
                birthday = record.birthday.value.date()
                birthday_this_year = birthday.replace(year=today.year)

                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year=today.year + 1)

                days_until_birthday = (birthday_this_year - today).days

                if 0 <= days_until_birthday <= days:
                    if birthday_this_year.weekday() == 5:  # Saturday
                        congratulation_date = birthday_this_year + timedelta(days=1)
                    elif birthday_this_year.weekday() == 6:  # Sunday
                        congratulation_date = birthday_this_year + timedelta(days=1)
                    else:
                        congratulation_date = birthday_this_year

                    upcoming_birthdays.append({
                        "name": record.name.value,
                        "congratulation_date": congratulation_date.strftime("%Y.%m.%d")
                    })

        return upcoming_birthdays

# Реалізація перехоплювача помилок який буде використовуватись як декоратор
def input_error(handler):
    def wrapper(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except IndexError:
            return "Not enough arguments"
        except ValueError as e:
            return str(e)
        except KeyError:
            return "No such contact"
    return wrapper

# Реалізація роботи з контактами, додавання, пошук, зміна контакту. 
@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        return "Such contact is not found"
    record.edit_phone(old_phone, new_phone)
    return "Contact changed."

@input_error
def find_contact(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record is None:
        return "Such contact is not found"
    return f"{record.name.value}: {'; '.join(phone.value for phone in record.phones)}"

# Реалізація функцій збереження та відображення днів народжень 
@input_error
def add_birthday(args, book: AddressBook):
    name, birthday, *_ = args
    record = book.find(name)
    if record is None:
        return "Such contact is not found"
    record.add_birthday(birthday)
    return "Birthday added."


@input_error
def show_birthday(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record is None:
        return "Such contact is not found"
    return f"{record.name.value}'s birthday is {record.birthday.value.strftime('%d.%m.%Y') if record.birthday else 'not set'}"

@input_error
def birthdays(args, book: AddressBook):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if not upcoming_birthdays:
        return "No birthdays in the next week."
    return "\n".join(f"{b['name']} has a birthday on {b['congratulation_date']}" for b in upcoming_birthdays)

def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, args

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено

# Запуск основної програми та збереження її у файл
def main():
    book = AddressBook()
    print("Welcome to the assistant bot!")
    book = load_data()
    # Основний цикл програми
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            save_data(book)  # Викликати перед виходом з програми
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(find_contact(args, book))

        elif command == "all":
            for record in book.data.values():
                print(record)

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")

if __name__ == "__main__":
    main()
