import datetime
import sqlite3

from settings import DATABASE_PATH


class DatabaseManager:
    def __init__(self):

        self.sql_connection = sqlite3.connect(DATABASE_PATH)
        self.cursor = self.sql_connection.cursor()

    def save_face_encoding_to_db(self, encoding, statue):

        sql_query = "INSERT INTO face_encoding_table (date, statue, encoding) VALUES (?, ?, ?)"
        date = str(datetime.datetime.now().date())
        face_encoding_string = " ".join(str(x) for x in encoding)
        insert_tuple = (date, statue, face_encoding_string)
        self.cursor.execute(sql_query, insert_tuple)
        self.sql_connection.commit()
        print(" Save face encoding to db successfully ")

    def select_info_from_db(self):

        sql_select_query = "SELECT * FROM face_encoding_table"

        self.cursor.execute(sql_select_query)
        records = self.cursor.fetchall()

        return records


if __name__ == '__main__':

    DatabaseManager().save_face_encoding_to_db(encoding="", statue="")
