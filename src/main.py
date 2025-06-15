# File: src/main.py
import sys, os, sqlite3, shutil
from datetime import datetime
from PyQt6 import QtWidgets, QtCore
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import QFileDialog
from src.ui.Katalog_Mainpage import Ui_MainWindow as MainPageUI
from src.ui.Form_Login_Admin import Ui_MainWindow as LoginUI
from src.ui.Admin_Page import Ui_MainWindow as AdminUI

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
DB_DIR      = os.path.join(PROJECT_DIR, "data")
DB_PATH     = os.path.join(DB_DIR, "arsip.sqlite")

class DatabaseHandler:
    def __init__(self, db_path=DB_PATH):
        if not os.path.isfile(db_path):
            raise FileNotFoundError(f"DB not found at {db_path!r}")
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def search_book(self, nomor_kendali, tahun=None, kategori=None):
        sql = """
            SELECT b.ID_Buku, b.ID_Rak, r.Nama_Rak, b.ID_Kategori, k.Nama_Kategori,
                   b.Tahun_Cetak, b.No_Kendali_Min, b.No_Kendali_Max,
                   b.Warna_Sampul, b.Subkategori, b.Status_Kondisi, b.Status_Lokasi
            FROM BUKU b
            JOIN RAK r ON b.ID_Rak = r.ID_Rak
            JOIN KATEGORI k ON b.ID_Kategori = k.ID_Kategori
            WHERE ? BETWEEN b.No_Kendali_Min AND b.No_Kendali_Max
        """
        params = [nomor_kendali]
        if tahun:
            sql += " AND b.Tahun_Cetak = ?"
            params.append(tahun)
        if kategori:
            sql += " AND k.Nama_Kategori = ?"
            params.append(kategori)
        self.cursor.execute(sql, tuple(params))
        return self.cursor.fetchall()

    def get_books_by_location(self, lokasi):
        sql = """
            SELECT b.ID_Buku, b.ID_Rak, r.Nama_Rak, b.ID_Kategori, k.Nama_Kategori,
                   b.Tahun_Cetak, b.No_Kendali_Min, b.No_Kendali_Max,
                   b.Warna_Sampul, b.Subkategori, b.Status_Kondisi, b.Status_Lokasi
            FROM BUKU b
            JOIN RAK r ON b.ID_Rak = r.ID_Rak
            JOIN KATEGORI k ON b.ID_Kategori = k.ID_Kategori
            WHERE b.Status_Lokasi = ?
        """
        self.cursor.execute(sql, (lokasi,))
        return self.cursor.fetchall()

    def authenticate_user(self, username, password):
        sql = "SELECT ID_Pengguna, Role FROM PENGGUNA WHERE Username=? AND Password=?"
        self.cursor.execute(sql, (username, password))
        return self.cursor.fetchone()

    def update_location_status(self, book_id, new_status):
        sql = "UPDATE BUKU SET Status_Lokasi = ? WHERE ID_Buku = ?"
        self.cursor.execute(sql, (new_status, book_id))
        self.conn.commit()

    def close(self):
        self.conn.close()

class MainPage(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.ui = MainPageUI()
        self.ui.setupUi(self)
        self.db = DatabaseHandler()
        self.login_win = None
        self.admin_win = None

        # Connect signals
        self.ui.Search_Button.clicked.connect(self.search_archive)
        self.ui.Admin_Page_Button.clicked.connect(self.open_admin_login)
        self.ui.Pindah_ke_Lantai_Button.clicked.connect(self.move_to_floor)
        self.ui.Pinjam_ke_Luar_Ruangan_Button.clicked.connect(self.borrow_outside)

        self.load_location_tables()

    def _create_model(self, rows):
        headers = [
            "ID_Buku","ID_Rak","Nama_Rak","ID_Kategori","Nama_Kategori",
            "Tahun_Cetak","No_Kendali_Min","No_Kendali_Max",
            "Warna_Sampul","Subkategori","Status_Kondisi","Status_Lokasi"
        ]
        model = QStandardItemModel(len(rows), len(headers), self)
        model.setHorizontalHeaderLabels(headers)
        for i, row in enumerate(rows):
            for j, field in enumerate(headers):
                model.setItem(i, j, QStandardItem(str(row[field])))
        return model

    def load_location_tables(self):
        self.ui.Tabel_di_Atas_Lantai.setModel(
            self._create_model(self.db.get_books_by_location("Di Lantai"))
        )
        self.ui.Tabel_Dipinjam_di_Luar_Ruangan.setModel(
            self._create_model(self.db.get_books_by_location("Di Luar Ruangan"))
        )

    def search_archive(self):
        raw = self.ui.Form_Nomor_Kendali.toPlainText().strip()
        if not raw.isdigit():
            QtWidgets.QMessageBox.warning(self, "Input Salah", "Masukkan nomor kendali numerik.")
            return
        nomor = int(raw)
        tahun = int(self.ui.Tahun_ComboBox.currentText())
        kategori = self.ui.Kategori_ComboBox.currentText()
        results = self.db.search_book(nomor, tahun, kategori)
        if not results:
            QtWidgets.QMessageBox.information(self, "Tidak Ditemukan", "Arsip tidak ada.")
            self.ui.Tabel_Hasil.setModel(None)
            return
        self.ui.Tabel_Hasil.setModel(self._create_model(results))

    def move_to_floor(self):
        bid = self.ui.Form_Nomor_Kendali.toPlainText().strip()
        if bid:
            self.db.update_location_status(bid, "Di Lantai")
            QtWidgets.QMessageBox.information(self, "Sukses", "Buku dipindah ke lantai.")
            self.load_location_tables()

    def borrow_outside(self):
        bid = self.ui.Form_Nomor_Kendali.toPlainText().strip()
        if bid:
            self.db.update_location_status(bid, "Di Luar Ruangan")
            QtWidgets.QMessageBox.information(self, "Sukses", "Buku dipinjam ke luar ruangan.")
            self.load_location_tables()

    def open_admin_login(self):
        # hide staff UI, open login UI
        self.hide()
        self.login_win = LoginWindow(self.db, self)
        self.login_win.show()

    def open_admin_page(self, user_id):
        # called by login
        self.login_win.close()
        self.admin_win = AdminPage(self.db, user_id)
        self.admin_win.show()

class LoginWindow(QtWidgets.QMainWindow):
    def __init__(self, db, main_win):
        super().__init__()
        self.ui = LoginUI()
        self.ui.setupUi(self)
        self.db = db
        self.main_win = main_win

        # Connect signals
        self.ui.Login_Button.clicked.connect(self.authenticate)
        self.ui.Staff_Page_Button.clicked.connect(self.back_to_staff)
        self.ui.Search_Button.clicked.connect(self.search_archive)
        self.ui.Pindah_ke_Lantai_Button.clicked.connect(self.move_to_floor)
        self.ui.Pinjam_ke_Luar_Ruangan_Button.clicked.connect(self.borrow_outside)

    def back_to_staff(self):
        # close login and show staff UI
        self.close()
        self.main_win.show()

    def authenticate(self):
        user = self.ui.Form_Username.toPlainText().strip()
        pwd  = self.ui.Form_Password.toPlainText().strip()
        res  = self.db.authenticate_user(user, pwd)
        if res and res[1] == "Admin":
            self.main_win.open_admin_page(res[0])
        else:
            QtWidgets.QMessageBox.warning(self, "Gagal", "Username atau password salah.")

    def _create_model(self, rows):
        headers = [
            "ID_Buku","ID_Rak","Nama_Rak","ID_Kategori","Nama_Kategori",
            "Tahun_Cetak","No_Kendali_Min","No_Kendali_Max",
            "Warna_Sampul","Subkategori","Status_Kondisi","Status_Lokasi"
        ]
        model = QStandardItemModel(len(rows), len(headers), self)
        model.setHorizontalHeaderLabels(headers)
        for i, r in enumerate(rows):
            for j, f in enumerate(headers):
                model.setItem(i, j, QStandardItem(str(r[f])))
        return model

    def search_archive(self):
        raw = self.ui.Form_Nomor_Kendali.toPlainText().strip()
        if not raw.isdigit():
            QtWidgets.QMessageBox.warning(self, "Input Salah", "Masukkan nomor kendali numerik.")
            return
        nomor = int(raw)
        tahun = int(self.ui.Tahun_ComboBox.currentText())
        kategori = self.ui.Kategori_ComboBox.currentText()
        results = self.db.search_book(nomor, tahun, kategori)
        self.ui.Tabel_Hasil.setModel(self._create_model(results))

    def move_to_floor(self):
        bid = self.ui.Form_Nomor_Kendali.toPlainText().strip()
        if bid:
            self.db.update_location_status(bid, "Di Lantai")
            QtWidgets.QMessageBox.information(self, "Sukses", "Buku dipindah ke lantai.")
            self.search_archive()

    def borrow_outside(self):
        bid = self.ui.Form_Nomor_Kendali.toPlainText().strip()
        if bid:
            self.db.update_location_status(bid, "Di Luar Ruangan")
            QtWidgets.QMessageBox.information(self, "Sukses", "Buku dipinjam ke luar ruangan.")
            self.search_archive()

class AdminPage(QtWidgets.QMainWindow):
    def __init__(self, db, user_id):
        super().__init__()
        self.ui = AdminUI()
        self.ui.setupUi(self)
        self.db = db
        self.user_id = user_id

        # Connect signals
        self.ui.Search_Button.clicked.connect(self.search_archive)
        self.ui.Staff_Page_Button.clicked.connect(self.back_to_staff)
        self.ui.Impor_Button.clicked.connect(self.import_backup)
        self.ui.Expor_Button.clicked.connect(self.export_backup)

    def back_to_staff(self):
        # close admin and show main page
        self.close()
        # maintain reference to prevent garbage collection
        self.main_win = MainPage()
        self.main_win.show()

    def import_backup(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Pilih File Backup .sqlite", "", "SQLite Files (*.sqlite)")
        if fname:
            try:
                shutil.copy(fname, DB_PATH)
                QtWidgets.QMessageBox.information(self, "Sukses", "Backup diimpor ke database.")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def export_backup(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Simpan File Backup .sqlite", "arsip_backup.sqlite", "SQLite Files (*.sqlite)")
        if fname:
            try:
                shutil.copy(DB_PATH, fname)
                QtWidgets.QMessageBox.information(self, "Sukses", "Backup disimpan.")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def _create_model(self, rows):
        headers = [
            "ID_Buku","ID_Rak","Nama_Rak","ID_Kategori","Nama_Kategori",
            "Tahun_Cetak","No_Kendali_Min","No_Kendali_Max",
            "Warna_Sampul","Subkategori","Status_Kondisi","Status_Lokasi"
        ]
        model = QStandardItemModel(len(rows), len(headers), self)
        model.setHorizontalHeaderLabels(headers)
        for i, row in enumerate(rows):
            for j, field in enumerate(headers):
                model.setItem(i, j, QStandardItem(str(row[field])))
        return model

    def search_archive(self):
        raw = self.ui.Form_Nomor_Kendali.toPlainText().strip()
        if not raw.isdigit():
            QtWidgets.QMessageBox.warning(self, "Input Salah", "Masukkan nomor kendali numerik.")
            return
        nomor = int(raw)
        tahun = int(self.ui.Tahun_ComboBox.currentText())
        kategori = self.ui.Kategori_ComboBox.currentText()
        results = self.db.search_book(nomor, tahun, kategori)
        self.ui.Tabel_Hasil.setModel(self._create_model(results))

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main = MainPage()
    main.show()
    sys.exit(app.exec())
