import os
import pandas as pd


def process_excel_files(directory, column_full_name, column_number):
    for filename in os.listdir(directory):
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            filepath = os.path.join(directory, filename)
            # print(f"Processing file: {filepath}")
            parse_excel(filepath, column_full_name, column_number)


def parse_excel(filepath, column_full_name, column_number):
    try:
        df = pd.read_excel(filepath, header=1)
        if column_full_name in df.columns:
            column_data_name = df[column_full_name]
            column_data_number = df[column_number]

            for index, value in column_data_name.items():
                if value and not pd.isnull(value):
                    print(value)
                else:
                    break
            for index, value in column_data_number.items():
                if value and not pd.isnull(value):
                    if str(value)[0:2] == "80":
                        print(f"{value:.0f}")
                    else:
                        print(f"+375({str(value)[0:2]}){str(value)[2:5]}-{str(value)[5:7]}-{str(value)[7:9]}\n")
                else:
                    break
        else:
            print(f"Column '{column_full_name}' not found in file: {filepath}")
    except Exception as e:
        print(f"Error processing file {filepath}: {str(e)}")


# Указать путь к директории с файлами Excel и название столбца
directory = 'C:\\Users\\Dell\\Clients'
column_full_name = 'ФИО'
column_number = 'Телефон'

process_excel_files(directory, column_full_name, column_number)

def column_letter_to_index_1(column_letter):
    """
    Функция преобразует буквенный индекс столбца Excel в числовой индекс.
    Например, column_letter_to_index('A') вернет 0, column_letter_to_index('B') вернет 1 и т.д.
    """
    index = 0
    for letter in column_letter:
        index = index * 26 + (ord(letter.upper()) - ord('A')) + 1
    return index - 1


def process_excel_files_1(directory, start_column_letter, end_column_letter):
    start_column_index = column_letter_to_index_1(start_column_letter)
    end_column_index = column_letter_to_index_1(end_column_letter)

    for filename in os.listdir(directory):
        if filename.endswith(".xlsx") or filename.endswith(".xls"):
            filepath = os.path.join(directory, filename)
            parse_excel_1(filepath, start_column_index, end_column_index)


def parse_excel_1(filepath, start_column_index, end_column_index):
    try:
        df = pd.read_excel(filepath, header=1)

        # Читаем данные построчно из заданного числового диапазона столбцов
        for _, row in df.iterrows():
            output_line = ""  # Переменная для накопления данных в одной строке
            for i in range(start_column_index, end_column_index + 1):
                value = row.iloc[i]  # Используем метод .iloc[] для доступа к элементам по позиции
                if pd.notnull(value):
                    output_line += str(value)  # Накапливаем данные в одну строку
                else:
                    break

            print(output_line)  # Выводим строку после обработки всех данных в строке

    except Exception as e:
        print(f"Error processing file {filepath}: {str(e)}")


# Пример использования
process_excel_files_1("C:\\Users\\Dell\\Clients", 'C', 'G')  # Например, для столбцов с индексами от 0 до 2 (включительно)


