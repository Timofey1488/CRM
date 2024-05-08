import re
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List

import pandas as pd
from sympy import sympify

# Указать путь к директории с файлами Excel и название столбца
directory = 'C:\\Users\\Dell\\Clients'
column_full_name = 'ФИО'
column_number = 'Телефон'
column_order = 'Заказ'
column_order_price = 'Сумма заказа'
column_date_order = 'Дата принятия'
column_notes = 'Заметки'


def parse_excel(filepath):
    try:
        with pd.ExcelFile(filepath) as xls:
            df = pd.read_excel(xls, header=1)

        if column_full_name in df.columns:
            offset = 0
            if df.columns[0] == '№' or df.columns[1] == '№':
                offset += 1
            column_data_name = df.iloc[:, 0+offset]
            column_data_number = df.iloc[:, 1+offset]
            column_order = df.iloc[:, 2+offset]
            column_order_price = df.iloc[:, 3+offset]
            column_date_order = df.iloc[:, 4+offset]
            try:
                column_notes = df.iloc[:, 6 + offset]
                final_full_notes_from_exel = ', '.join(parse_notes(column_notes))
            except Exception:
                final_full_notes_from_exel = ''

            final_full_name_from_exel = ', '.join(parse_full_name(column_data_name))
            final_number_from_exel = ', '.join(parse_number(column_data_number))
            final_full_order_from_exel = parse_order(column_order, column_order_price, column_date_order)
            final_full_order_from_exel_lists = list(final_full_order_from_exel.values())


            # print(f"{final_full_name_from_exel}")
            # print(f"{final_number_from_exel}")
            # print(final_full_order_from_exel_lists)
            # print(final_full_notes_from_exel)

            # for client_orders in final_full_order_from_exel_lists:
            #     if client_orders != ['  ']:
            #         print(client_orders)
            return [final_full_name_from_exel, final_number_from_exel, final_full_order_from_exel_lists,
                    final_full_notes_from_exel]

    except Exception as e:
        print(f"Error processing file {filepath}: {str(e)}")


def parse_full_name(column_data_name) -> List:
    full_names_list = []
    for index, value in column_data_name.items():
        if value != " " and not pd.isnull(value):

            full_names_list.append(value)
        else:
            break
    return full_names_list


def parse_number(column_data_number) -> List:
    numbers_list = []
    for index, value in column_data_number.items():
        if value != " " and not pd.isnull(value):
            if str(value)[0:2] == "80":
                numbers_list.append(f"+375({str(value)[2:4]}){str(value)[4:7]}-{str(value)[7:9]}-{str(value)[9:11]}")
            elif type(value) == float or type(value) == int:
                numbers_list.append(f"+375({str(value)[0:2]}){str(value)[2:5]}-{str(value)[5:7]}-{str(value)[7:9]}")
            else:
                numbers_list.append(f"Не указан")
        else:
            break
    return numbers_list


def parse_notes(column_data_notes) -> List:
    notes_list = []
    for index, value in column_data_notes.items():
        if value != " " and not pd.isnull(value):
            notes_list.append(f"{value}")
        else:
            break
    return notes_list


def parse_order(column_order, column_order_price, column_date_order) -> dict:
    final_dict = defaultdict(list)
    columns = {
        'column_order': column_order,
        'column_order_price': column_order_price,
        'column_date_order': column_date_order
    }

    for column_name, column_data in columns.items():
        for index, value in column_data.items():
            if value != "" and not pd.isnull(value):
                if column_name == 'column_order_price':
                    if re.search(r'[*/+=-]', str(value)):
                        final_dict[index].append(plus_pair_partition(value))
                        continue
                    if not re.search(r'\d', str(value)):
                        final_dict[index].append(0)
                        continue
                    try:
                        final_dict[index].append(int(value.split()[0]))
                    except:
                        final_dict[index].append(value)
                elif column_name == 'column_date_order':
                    value = validate_date(value)
                    final_dict[index].append(value)
                else:
                    final_dict[index].append(value)
            else:
                if column_name == 'column_order_price' and len(final_dict[index]) > 0:
                    final_dict[index].append(0)
                    continue
                if column_name == 'column_date_order' and len(final_dict[index]) > 0:
                    final_dict[index].append(None)
                    continue
                break
    final_dict_filtered = {key: value for key, value in final_dict.items() if value != ['  ', 0, None] and value != []}
    return final_dict_filtered


def validate_date(date_str):
    try:
        if isinstance(date_str, datetime):
            return date_str.strftime("%d %m %Y")
        elif isinstance(date_str, str):
            return datetime.strptime(date_str, "%d %m %Y")
        elif isinstance(date_str, (int, float)):
            # Если передано целое число или число с плавающей запятой,
            # преобразуем в строку, а затем в datetime
            date_str = str(int(date_str))  # преобразуем в строку, убирая возможную десятичную часть
            return datetime.strptime(date_str, "%d %m %Y")
        else:
            return None
    except (ValueError, TypeError):
        return None


def plus_pair_partition(value) -> Decimal:
    try:
        # Разбиваем строку до знака "="
        value = value.split('=')[0]
        value = value.replace('%', '/100')
        value = value.replace(',', '.')
        value = re.sub(r'[^\d+*/-]', '', value)
        if re.search(r'[-+*/]$', value):
            # Если есть, убираем эту операцию
            value = value.rstrip('+-*/')
        # Вычисляем значение выражения
        result = sympify(value).evalf()
        # Преобразуем результат в Decimal
        rounded_value = Decimal(str(result)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        return rounded_value
    except Exception as e:
        print(f"Error processing value {value}: {e}")
        return value
