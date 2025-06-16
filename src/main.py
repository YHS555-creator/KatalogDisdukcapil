# main.py
import sys

from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import (QApplication, QMainWindow, QDialog, QMessageBox,
                             QTableView, QAbstractItemView)

from database import DatabaseHandler
from ui.Admin_Page import Ui_AdminWindow
from ui.Confirmation import Ui_Dialog as Ui_ConfirmationDialog
from ui.Form_Login_Admin import Ui_LoginWindow
from ui.Katalog_Mainpage import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.db = DatabaseHandler()
        self.current_book = None

        # Connect signals
        self.Search_Button.clicked.connect(self.search_book)
        self.Pindah_ke_Lantai_Button.clicked.connect(self.move_to_floor)
        self.Pinjam_ke_Luar_Ruangan_Button.clicked.connect(self.borrow_outside)
        self.Admin_Page_Button.clicked.connect(self.open_admin_login)

        # Configure tables
        self.configure_table(self.Tabel_Hasil)
        self.configure_table(self.Tabel_di_Atas_Lantai)
        self.configure_table(self.Tabel_Dipinjam)

        # Load initial data
        self.load_location_tables()

    def configure_table(self, table):
        """Configure table settings for consistent behavior"""
        table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def load_location_tables(self):
        """Load books by location status into tables"""
        # Load books on floor
        books_on_floor = self.db.get_books_by_location("Di Lantai", full_attributes=True)
        if books_on_floor is not None:
            self.populate_table(self.Tabel_di_Atas_Lantai, books_on_floor)

        # Load borrowed books
        books_outside = self.db.get_books_by_location("Di Luar Ruangan", full_attributes=True)
        if books_outside is not None:
            self.populate_table(self.Tabel_Dipinjam, books_outside)

    def populate_table(self, table, books):
        """Populate table with book data"""
        if not books:
            table.setModel(None)
            return

        # Create model with headers
        model = QStandardItemModel(len(books), 10)
        model.setHorizontalHeaderLabels([
            "ID Buku", "Rak", "Kategori", "Tahun Cetak",
            "Min No", "Max No", "Warna Sampul", "Subkategori",
            "Status Kondisi", "Status Lokasi"
        ])

        # Populate model with data
        for row, book in enumerate(books):
            # Use safer dictionary access
            model.setItem(row, 0, QStandardItem(book.get("ID_Buku", "")))
            model.setItem(row, 1, QStandardItem(book.get("Nama_Rak", "")))
            model.setItem(row, 2, QStandardItem(book.get("Nama_Kategori", "")))
            model.setItem(row, 3, QStandardItem(str(book.get("Tahun_Cetak", ""))))
            model.setItem(row, 4, QStandardItem(str(book.get("No_Kendali_Min", ""))))
            model.setItem(row, 5, QStandardItem(str(book.get("No_Kendali_Max", ""))))
            model.setItem(row, 6, QStandardItem(book.get("Warna_Sampul", "")))
            model.setItem(row, 7, QStandardItem(book.get("Subkategori", "")))
            model.setItem(row, 8, QStandardItem(book.get("Status_Kondisi", "")))
            model.setItem(row, 9, QStandardItem(book.get("Status_Lokasi", "")))

        # Set model to table
        table.setModel(model)

        # Resize columns to content
        for column in range(10):
            table.resizeColumnToContents(column)

    def search_book(self):
        """Search book by control number and display results"""
        # Get input text
        nomor_kendali = self.Form_Nomor_Kendali.toPlainText().strip()

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
            # Create a list with a single book for the table
            books = [book]
            self.populate_table(self.Tabel_Hasil, books)
            self.current_book = book
        else:
            QMessageBox.information(self, "Hasil Pencarian", "Buku tidak ditemukan")
            self.Tabel_Hasil.setModel(None)
            self.current_book = None

    def move_to_floor(self):
        """Move selected book to floor status"""
        if not self.current_book:
            QMessageBox.warning(self, "Peringatan", "Cari buku terlebih dahulu")
            return

        # Update status
        if self.db.update_location_status(self.current_book["ID_Buku"], "Di Lantai"):
            # Log activity
            self.db.log_activity(2, self.current_book["ID_Buku"], "UPDATE",
                                 f"Status diubah ke Di Lantai")
            # Refresh tables
            self.load_location_tables()
            QMessageBox.information(self, "Berhasil", "Status lokasi diperbarui")

    def borrow_outside(self):
        """Borrow selected book outside the room"""
        if not self.current_book:
            QMessageBox.warning(self, "Peringatan", "Cari buku terlebih dahulu")
            return

        # Update status
        if self.db.update_location_status(self.current_book["ID_Buku"], "Di Luar Ruangan"):
            # Log activity
            self.db.log_activity(2, self.current_book["ID_Buku"], "UPDATE",
                                 f"Status diubah ke Di Luar Ruangan")
            # Refresh tables
            self.load_location_tables()
            QMessageBox.information(self, "Berhasil", "Status lokasi diperbarui")

    def open_admin_login(self):
        """Open admin login window"""
        login_window = LoginWindow(self)
        if login_window.exec() == QDialog.DialogCode.Accepted:
            admin_panel = AdminPanel(login_window.user)
            admin_panel.show()


class LoginWindow(QDialog, Ui_LoginWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.db = DatabaseHandler()
        self.user = None
        self.Login_Button.clicked.connect(self.authenticate)

    def authenticate(self):
        """Authenticate admin credentials"""
        username = self.Form_Username.text().strip()
        password = self.Form_Password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Username dan password harus diisi")
            return

        self.user = self.db.authenticate_user(username, password)

        if self.user and self.user["Role"] == "Admin":
            self.accept()
        else:
            QMessageBox.warning(self, "Login Gagal", "Username atau password salah")
            self.user = None


class AdminPanel(QMainWindow, Ui_AdminWindow):
    def __init__(self, user):
        super().__init__()
        self.setupUi(self)
        self.user = user
        self.db = DatabaseHandler()
        # Add admin functionality here


class ConfirmationDialog(QDialog, Ui_ConfirmationDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        # Add confirmation dialog functionality here


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()