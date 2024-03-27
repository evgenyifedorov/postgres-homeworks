import json

import psycopg2

from config import config


def main():
    script_file = 'fill_db.sql'
    json_file = 'suppliers.json'
    db_name = 'my_new_db'

    params = config()
    conn = None

    create_database(params, db_name)
    print(f"БД {db_name} успешно создана")

    params.update({'dbname': db_name})
    try:
        with psycopg2.connect(**params) as conn:
            with conn.cursor() as cur:
                execute_sql_script(cur, script_file)
                print(f"БД {db_name} успешно заполнена")

                create_suppliers_table(cur)
                print("Таблица suppliers успешно создана")

                suppliers = get_suppliers_data(json_file)
                insert_suppliers_data(cur, suppliers)
                print("Данные в suppliers успешно добавлены")

                add_foreign_keys(cur, json_file)
                print(f"FOREIGN KEY успешно добавлены")

    except(Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()


def create_database(params, db_name) -> None:
    """Создает новую базу данных."""
    conn = psycopg2.connect(dbname='postgres', **params)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(f"DROP DATABASE {db_name}")
    cur.execute(f"CREATE DATABASE {db_name}")

    conn.close()


def execute_sql_script(cur, script_file) -> None:
    """Выполняет скрипт из файла для заполнения БД данными."""

    fd = open(script_file, 'r')
    sql_file = fd.read()
    cur.execute(sql_file)
    cur.execute(
        """
        ALTER TABLE products ADD COLUMN supplier_id integer
        """
    )
    fd.close()


def create_suppliers_table(cur) -> None:
    """Создает таблицу suppliers."""

    cur.execute("""CREATE TABLE suppliers (
        supplier_id SERIAL PRIMARY KEY,
        company_name varchar(40) NOT NULL,
        contact_name varchar(50),
        address varchar(100),
        phone varchar(24),
        fax varchar(24)
        )
    """)


def get_suppliers_data(json_file: str) -> list[dict]:
    """Извлекает данные о поставщиках из JSON-файла и возвращает список словарей с соответствующей информацией."""
    with open('suppliers.json', 'r', encoding='utf8') as file:
        data = json.load(file)
    return data


def insert_suppliers_data(cur, suppliers: list[dict]) -> None:
    """Добавляет данные из suppliers.json в таблицу suppliers."""

    for data_suppliers in suppliers:
        cur.execute(
            """
            INSERT INTO suppliers (company_name, contact_name, address, phone, fax)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING supplier_id
             """,
            (data_suppliers['company_name'], data_suppliers['contact'], data_suppliers['address'],
             data_suppliers['phone'], data_suppliers['fax'])
        )


def add_foreign_keys(cur, json_file) -> None:
    """Добавляет foreign key со ссылкой на supplier_id в таблицу products."""
    cur.execute(
        """ALTER TABLE ONLY products
    ADD CONSTRAINT fk_products_suppliers FOREIGN KEY (supplier_id) REFERENCES suppliers; """
    )


if __name__ == '__main__':
    main()
