import os
from collections import defaultdict
from decimal import Decimal
from typing import List, Dict

import pandas as pd


# def process_excel_files(directory):
#     for i, filename in enumerate(os.listdir(directory)):
#         if filename.endswith(".xlsx") or filename.endswith(".xls"):
#             filepath = os.path.join(directory, filename)
#             parse_excel(filepath)


def parse_excel(filepath):
    try:
        with pd.ExcelFile(filepath) as xls:
            df = pd.read_excel(xls, header=1)

        if column_full_name in df.columns:
            column_data_name = df.iloc[:, 0]
            column_data_number = df.iloc[:, 1]
            column_order = df.iloc[:, 2]
            column_order_price = df.iloc[:, 3]
            column_date_order = df.iloc[:, 4]
            column_notes = df.iloc[:, 6]

            final_full_name_from_exel = ', '.join(parse_full_name(column_data_name))
            final_number_from_exel = ', '.join(parse_number(column_data_number))
            final_full_order_from_exel = parse_order(column_order, column_order_price, column_date_order)
            final_full_order_from_exel_lists = list(final_full_order_from_exel.values())
            final_full_notes_from_exel = ', '.join(parse_notes(column_notes))

            print(f"{final_full_name_from_exel}")
            print(f"{final_number_from_exel}")
            print(final_full_order_from_exel_lists)
            print(final_full_notes_from_exel)
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
                numbers_list.append(f"{value:.0f}")
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


def parse_order(column_order, column_order_price, column_date_order) -> Dict:
    final_dict = defaultdict(list)
    columns = {
        'column_order': column_order,
        'column_order_price': column_order_price,
        'column_date_order': column_date_order
    }

    for column_name, column_data in columns.items():
        for index, value in column_data.items():
            if value != " " and not pd.isnull(value):
                if column_name == 'column_order_price':
                    try:
                        final_dict[index].append(int(value))
                    except:
                        final_dict[index].append(value)
                else:
                    final_dict[index].append(value)
            else:
                break

    return final_dict


# Указать путь к директории с файлами Excel и название столбца
directory = 'C:\\Users\\Dell\\Clients'
column_full_name = 'ФИО'
column_number = 'Телефон'
column_order = 'Заказ'
column_order_price = 'Сумма заказа'
column_date_order = 'Дата принятия'
column_notes = 'Заметки'


