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

        # Connect signals
        self.Search_Button.clicked.connect(self.search_book)
        self.Pindah_ke_Lantai_Button.clicked.connect(self.move_to_floor)
        self.Pinjam_ke_Luar_Ruangan_Button.clicked.connect(self.borrow_outside)
        self.Admin_Page_Button.clicked.connect(self.open_admin_login)
        self.Kembalikan_ke_Rak_dari_Lantai_Button.clicked.connect(self.move_from_floor_to_shelf)

        # Configure tables
        self.configure_table(self.Tabel_Hasil)
        self.configure_table(self.Tabel_di_Atas_Lantai)
        self.configure_table(self.Tabel_Dipinjam)

        # Load initial data
        self.load_location_tables()

    @staticmethod
    def configure_table(table):
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

    @staticmethod
    def populate_table(table, books):
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

    @staticmethod
    def get_selected_book_id(table):
        """Get selected book ID from a table"""
        if table.model() is None:
            return None

        selection_model = table.selectionModel()
        if selection_model and selection_model.hasSelection():
            selected_indexes = selection_model.selectedRows(0)  # Get selected row in column 0 (ID_Buku)
            if selected_indexes:
                row = selected_indexes[0].row()
                return table.model().index(row, 0).data()  # Return ID_Buku
        return None

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
        else:
            QMessageBox.information(self, "Hasil Pencarian", "Buku tidak ditemukan")
            self.Tabel_Hasil.setModel(None)

    def move_to_floor(self):
        """Move selected book to floor status"""
        book_id = self.get_selected_book_id(self.Tabel_Hasil)
        if not book_id:
            QMessageBox.warning(self, "Peringatan", "Pilih buku di Tabel Hasil terlebih dahulu")
            return

        # Update status
        if self.db.update_location_status(book_id, "Di Lantai"):
            # Log activity
            self.db.log_activity(2, book_id, "UPDATE", "Status diubah ke Di Lantai")
            # Refresh tables
            self.load_location_tables()
            # Clear search results
            self.Tabel_Hasil.setModel(None)
            self.Form_Nomor_Kendali.clear()
            QMessageBox.information(self, "Berhasil", "Buku berhasil dipindahkan ke lantai")
        else:
            QMessageBox.warning(self, "Gagal", "Gagal memperbarui status buku")

    def move_from_floor_to_shelf(self):
        """Move selected book from floor back to shelf"""
        book_id = self.get_selected_book_id(self.Tabel_di_Atas_Lantai)
        if not book_id:
            QMessageBox.warning(self, "Peringatan", "Pilih buku di Tabel di Atas Lantai terlebih dahulu")
            return

        # Update status
        if self.db.update_location_status(book_id, "Di Rak"):
            # Log activity
            self.db.log_activity(2, book_id, "UPDATE", "Status diubah ke Di Rak")
            # Refresh tables
            self.load_location_tables()
            QMessageBox.information(self, "Berhasil", "Buku berhasil dikembalikan ke rak")
        else:
            QMessageBox.warning(self, "Gagal", "Gagal memperbarui status buku")

    def borrow_outside(self):
        """Borrow selected book outside the room"""
        book_id = self.get_selected_book_id(self.Tabel_Hasil)
        if not book_id:
            QMessageBox.warning(self, "Peringatan", "Pilih buku di Tabel Hasil terlebih dahulu")
            return

        # Update status
        if self.db.update_location_status(book_id, "Di Luar Ruangan"):
            # Log activity
            self.db.log_activity(2, book_id, "UPDATE", "Status diubah ke Di Luar Ruangan")
            # Refresh tables
            self.load_location_tables()
            # Clear search results
            self.Tabel_Hasil.setModel(None)
            self.Form_Nomor_Kendali.clear()
            QMessageBox.information(self, "Berhasil", "Buku berhasil dipinjam ke luar ruangan")
        else:
            QMessageBox.warning(self, "Gagal", "Gagal memperbarui status buku")

    def open_admin_login(self):
        """Open admin login window - FIXED: This shouldn't close the main window"""
        login_window = LoginWindow(self)
        login_window.exec()


class LoginWindow(QDialog, Ui_LoginWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.admin_panel = AdminPanel(self.user)
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
            # Open admin panel on successful login
            self.admin_panel.show()
            self.close()
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
        self.setWindowTitle("Panel Admin")
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