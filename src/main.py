import sys
import os
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem, QHeaderView
from PyQt6.QtSql import QSqlDatabase, QSqlQuery, QSqlTableModel
from PyQt6.QtCore import Qt, QDate
import sqlite3
from datetime import datetime

from src.ui.Katalog_Mainpage import Ui_MainWindow


class DatabaseHandler:
    def __init__(self, db_path='../data/arsip.sqlite'):
        self.db_path = os.path.abspath(db_path)
        self.conn = None
        self.connect()

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"Connected to database at {self.db_path}")
        except sqlite3.Error as e:
            print(f"Database connection error: {e}")

    def search_book(self, nomor_kendali):
        query = """
        SELECT B.*, R.Nama_Rak, K.Nama_Kategori 
        FROM BUKU B
        JOIN RAK R ON B.ID_Rak = R.ID_Rak
        JOIN KATEGORI K ON B.ID_Kategori = K.ID_Kategori
        WHERE ? BETWEEN B.No_Kendali_Min AND B.No_Kendali_Max
        """
        cur = self.conn.cursor()
        cur.execute(query, (nomor_kendali,))
        return cur.fetchone()

    def get_books_by_location(self, location):
        query = """
        SELECT B.ID_Buku, R.Nama_Rak, K.Nama_Kategori, B.Tahun_Cetak, 
               B.No_Kendali_Min, B.No_Kendali_Max 
        FROM BUKU B
        JOIN RAK R ON B.ID_Rak = R.ID_Rak
        JOIN KATEGORI K ON B.ID_Kategori = K.ID_Kategori
        WHERE B.Status_Lokasi = ?
        """
        cur = self.conn.cursor()
        cur.execute(query, (location,))
        return cur.fetchall()

    def update_location_status(self, book_id, new_status):
        query = "UPDATE BUKU SET Status_Lokasi = ? WHERE ID_Buku = ?"
        cur = self.conn.cursor()
        cur.execute(query, (new_status, book_id))
        self.conn.commit()
        return True

    def log_activity(self, user_id, book_id, action_type, details):
        query = """
        INSERT INTO LOG_AKTIVITAS 
        (ID_Pengguna, ID_Buku, Jenis_Aksi, Detail_Perubahan, Waktu)
        VALUES (?, ?, ?, ?, ?)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur = self.conn.cursor()
        cur.execute(query, (user_id, book_id, action_type, details, timestamp))
        self.conn.commit()
        return True

    def authenticate_user(self, username, password):
        query = "SELECT * FROM PENGGUNA WHERE Username = ? AND Password = ?"
        cur = self.conn.cursor()
        cur.execute(query, (username, password))
        return cur.fetchone()


class MainPage(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.db = DatabaseHandler()
        self.current_book = None
        self.setup_connections()
        self.load_location_tables()

    def setup_connections(self):
        self.ui.Search_Button.clicked.connect(self.search_book)
        self.ui.Pindah_ke_Lantai_Button.clicked.connect(lambda: self.update_status("Di Lantai"))
        self.ui.Pinjam_ke_Luar_Ruangan_Button.clicked.connect(lambda: self.update_status("Di Luar Ruangan"))
        self.ui.Admin_Page_Button.clicked.connect(self.open_admin_login)

    def load_location_tables(self):
        # Fixed method: Using manual table population instead of setModel()
        books_di_lantai = self.db.get_books_by_location("Di Lantai")
        self.populate_table(self.ui.Tabel_di_Atas_Lantai, books_di_lantai)

        books_di_luar = self.db.get_books_by_location("Di Luar Ruangan")
        self.populate_table(self.ui.Tabel_Dipinjam, books_di_luar)

    def populate_table(self, table, data):
        table.setRowCount(0)

        if not data:
            return

        table.setRowCount(len(data))
        table.setColumnCount(6)
        headers = ["ID Buku", "Rak", "Kategori", "Tahun Cetak", "No. Min", "No. Max"]
        table.setHorizontalHeaderLabels(headers)

        for row, book in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(book[0]))  # ID_Buku
            table.setItem(row, 1, QTableWidgetItem(book[1]))  # Nama_Rak
            table.setItem(row, 2, QTableWidgetItem(book[2]))  # Nama_Kategori
            table.setItem(row, 3, QTableWidgetItem(str(book[3])))  # Tahun_Cetak
            table.setItem(row, 4, QTableWidgetItem(str(book[4])))  # No_Kendali_Min
            table.setItem(row, 5, QTableWidgetItem(str(book[5])))  # No_Kendali_Max

        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def search_book(self):
        nomor_kendali = self.ui.Input_Nomor.text().strip()

        if not nomor_kendali:
            QMessageBox.warning(self, "Peringatan", "Masukkan nomor kendali arsip")
            return

        try:
            nomor = int(nomor_kendali)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Nomor kendali harus berupa angka")
            return

        book = self.db.search_book(nomor)

        if book:
            self.display_book_info(book)
            self.current_book = book
        else:
            QMessageBox.information(self, "Hasil Pencarian", "Buku tidak ditemukan")
            self.clear_results()

    def display_book_info(self, book):
        self.ui.Label_ID_Buku.setText(book[0])  # ID_Buku
        self.ui.Label_Rak.setText(book[10])  # Nama_Rak
        self.ui.Label_Kategori.setText(book[11])  # Nama_Kategori
        self.ui.Label_Tahun.setText(str(book[3]))  # Tahun_Cetak
        self.ui.Label_No_Min.setText(str(book[4]))  # No_Kendali_Min
        self.ui.Label_No_Max.setText(str(book[5]))  # No_Kendali_Max
        self.ui.Label_Status_Lokasi.setText(book[9])  # Status_Lokasi

    def clear_results(self):
        self.ui.Label_ID_Buku.setText("")
        self.ui.Label_Rak.setText("")
        self.ui.Label_Kategori.setText("")
        self.ui.Label_Tahun.setText("")
        self.ui.Label_No_Min.setText("")
        self.ui.Label_No_Max.setText("")
        self.ui.Label_Status_Lokasi.setText("")
        self.current_book = None

    def update_status(self, new_status):
        if not self.current_book:
            QMessageBox.warning(self, "Peringatan", "Cari buku terlebih dahulu")
            return

        book_id = self.current_book[0]
        if self.db.update_location_status(book_id, new_status):
            self.db.log_activity(2, book_id, "UPDATE", f"Status lokasi diubah menjadi {new_status}")
            QMessageBox.information(self, "Berhasil", "Status lokasi diperbarui")
            self.load_location_tables()
            self.clear_results()
        else:
            QMessageBox.warning(self, "Error", "Gagal memperbarui status")

    def open_admin_login(self):
        from ui.Form_Login_Admin import LoginWindow
        self.login_window = LoginWindow(self)
        self.login_window.show()


class Ui_LoginWindow:
    pass


class LoginWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_LoginWindow()
        self.ui.setupUi(self)
        self.db = DatabaseHandler()
        self.ui.Button_Login.clicked.connect(self.authenticate)

    def authenticate(self):
        username = self.ui.Input_Username.text().strip()
        password = self.ui.Input_Password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Username dan password harus diisi")
            return

        user = self.db.authenticate_user(username, password)

        if user and user[3] == "Admin":  # Role check
            self.open_admin_panel()
        else:
            QMessageBox.warning(self, "Login Gagal", "Username atau password salah")

    def open_admin_panel(self):
        from ui.Admin_Page import AdminPage
        self.admin_panel = AdminPage(self)
        self.admin_panel.show()
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main = MainPage()
    main.show()
    sys.exit(app.exec())