import sys

from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QDialog, QMessageBox,
    QTableView, QAbstractItemView
)

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
        self.Kembalikan_ke_Rak_dari_Luar_Button.clicked.connect(self.return_from_borrowed)

        # Configure tables
        self.configure_table(self.Tabel_Hasil)
        self.configure_table(self.Tabel_di_Atas_Lantai)
        self.configure_table(self.Tabel_Dipinjam)

        # Load initial data
        self.load_location_tables()

    def configure_table(self, table):
        table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def load_location_tables(self):
        books_on_floor = self.db.get_books_by_location("Di Lantai", full_attributes=True)
        if books_on_floor is not None:
            self.populate_table(self.Tabel_di_Atas_Lantai, books_on_floor)
        books_outside = self.db.get_books_by_location("Dipinjam", full_attributes=True)
        if books_outside is not None:
            self.populate_table(self.Tabel_Dipinjam, books_outside)

    def populate_table(self, table, books):
        if not books:
            table.setModel(None)
            return
        model = QStandardItemModel(len(books), 10)
        model.setHorizontalHeaderLabels([
            "ID Buku", "Rak", "Kategori", "Tahun Cetak",
            "Min No", "Max No", "Warna Sampul", "Subkategori",
            "Status Kondisi", "Status Lokasi"
        ])
        for row, book in enumerate(books):
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
        table.setModel(model)
        for column in range(10):
            table.resizeColumnToContents(column)

    def get_selected_book_id(self, table):
        if table.model() is None:
            return None
        sel = table.selectionModel()
        if not sel or not sel.hasSelection():
            return None
        rows = sel.selectedRows()
        if not rows:
            return None
        return table.model().index(rows[0].row(), 0).data()

    def search_book(self):
        nomor = self.Form_Nomor_Kendali.toPlainText().strip()
        if not nomor:
            QMessageBox.warning(self, "Peringatan", "Masukkan nomor kendali arsip")
            return
        try:
            nomor = int(nomor)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Nomor kendali harus berupa angka")
            return
        book = self.db.search_book(nomor)
        if book:
            self.populate_table(self.Tabel_Hasil, [book])
        else:
            QMessageBox.information(self, "Hasil Pencarian", "Buku tidak ditemukan")
            self.Tabel_Hasil.setModel(None)

    def move_to_floor(self):
        book_id = self.get_selected_book_id(self.Tabel_Hasil)
        if not book_id:
            QMessageBox.warning(self, "Peringatan", "Pilih buku di Tabel Hasil terlebih dahulu")
            return
        if self.db.update_location_status(book_id, "Di Lantai"):
            self.db.log_activity(2, book_id, "Pinjam", "Status diubah ke Di Lantai")
            self.load_location_tables()
            self.Tabel_Hasil.setModel(None)
            self.Form_Nomor_Kendali.clear()
            QMessageBox.information(self, "Berhasil", "Buku berhasil dipindahkan ke lantai")

    def move_from_floor_to_shelf(self):
        book_id = self.get_selected_book_id(self.Tabel_di_Atas_Lantai)
        if not book_id:
            QMessageBox.warning(self, "Peringatan", "Pilih buku di Tabel di Atas Lantai terlebih dahulu")
            return
        if self.db.update_location_status(book_id, "Di Rak"):
            self.db.log_activity(2, book_id, "Kembalikan", "Status diubah ke Di Rak")
            self.load_location_tables()
            QMessageBox.information(self, "Berhasil", "Buku berhasil dikembalikan ke rak")

    def borrow_outside(self):
        book_id = self.get_selected_book_id(self.Tabel_Hasil)
        if not book_id:
            QMessageBox.warning(self, "Peringatan", "Pilih buku di Tabel Hasil terlebih dahulu")
            return
        if self.db.update_location_status(book_id, "Dipinjam"):
            self.db.log_activity(2, book_id, "Pinjam", "Status diubah ke Dipinjam")
            self.load_location_tables()
            self.Tabel_Hasil.setModel(None)
            self.Form_Nomor_Kendali.clear()
            QMessageBox.information(self, "Berhasil", "Buku berhasil dipinjam ke luar ruangan")

    def return_from_borrowed(self):
        book_id = self.get_selected_book_id(self.Tabel_Dipinjam)
        if not book_id:
            QMessageBox.warning(self, "Peringatan", "Pilih buku di Tabel Dipinjam terlebih dahulu")
            return
        if self.db.update_location_status(book_id, "Di Rak"):
            self.db.log_activity(2, book_id, "Kembalikan", "Status diubah ke Di Rak")
            self.load_location_tables()
            QMessageBox.information(self, "Berhasil", "Buku berhasil dikembalikan ke rak")

    def open_admin_login(self):
        self.login_window = LoginWindow(self)
        self.login_window.show()


class LoginWindow(QMainWindow, Ui_LoginWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.db = DatabaseHandler()
        self.setWindowTitle("Login Admin")

        # Configure table for search results
        self.configure_table(self.Tabel_Hasil)

        # Connect signals
        self.Search_Button.clicked.connect(self.search_book)
        self.Pindah_ke_Lantai_Button.clicked.connect(self.move_to_floor)
        self.Pinjam_ke_Luar_Ruangan_Button.clicked.connect(self.borrow_outside)
        self.Login_Button.clicked.connect(self.authenticate)
        self.Staff_Page_Button.clicked.connect(self.open_staff_page)

    def configure_table(self, table):
        """Configure table settings"""
        table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

    def get_selected_book_id(self, table):
        """Get selected book ID from a table"""
        if table.model() is None:
            return None
        sel = table.selectionModel()
        if not sel or not sel.hasSelection():
            return None
        rows = sel.selectedRows()
        if not rows:
            return None
        return table.model().index(rows[0].row(), 0).data()

    def search_book(self):
        """Search book by control number"""
        nomor = self.Form_Nomor_Kendali.toPlainText().strip()
        if not nomor:
            QMessageBox.warning(self, "Peringatan", "Masukkan nomor kendali arsip")
            return
        try:
            nomor = int(nomor)
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Nomor kendali harus berupa angka")
            return
        book = self.db.search_book(nomor)
        if book:
            # Create model with headers
            model = QStandardItemModel(1, 10)
            model.setHorizontalHeaderLabels([
                "ID Buku", "Rak", "Kategori", "Tahun Cetak",
                "Min No", "Max No", "Warna Sampul", "Subkategori",
                "Status Kondisi", "Status Lokasi"
            ])

            # Populate model with data
            model.setItem(0, 0, QStandardItem(book.get("ID_Buku", "")))
            model.setItem(0, 1, QStandardItem(book.get("Nama_Rak", "")))
            model.setItem(0, 2, QStandardItem(book.get("Nama_Kategori", "")))
            model.setItem(0, 3, QStandardItem(str(book.get("Tahun_Cetak", ""))))
            model.setItem(0, 4, QStandardItem(str(book.get("No_Kendali_Min", ""))))
            model.setItem(0, 5, QStandardItem(str(book.get("No_Kendali_Max", ""))))
            model.setItem(0, 6, QStandardItem(book.get("Warna_Sampul", "")))
            model.setItem(0, 7, QStandardItem(book.get("Subkategori", "")))
            model.setItem(0, 8, QStandardItem(book.get("Status_Kondisi", "")))
            model.setItem(0, 9, QStandardItem(book.get("Status_Lokasi", "")))

            # Set model to table
            self.Tabel_Hasil.setModel(model)

            # Resize columns to content
            for column in range(10):
                self.Tabel_Hasil.resizeColumnToContents(column)
        else:
            QMessageBox.information(self, "Hasil Pencarian", "Buku tidak ditemukan")
            self.Tabel_Hasil.setModel(None)

    def move_to_floor(self):
        """Move selected book to floor status"""
        book_id = self.get_selected_book_id(self.Tabel_Hasil)
        if not book_id:
            QMessageBox.warning(self, "Peringatan", "Pilih buku di Tabel Hasil terlebih dahulu")
            return
        if self.db.update_location_status(book_id, "Di Lantai"):
            self.db.log_activity(2, book_id, "Pinjam", "Status diubah ke Di Lantai")
            self.Tabel_Hasil.setModel(None)
            self.Form_Nomor_Kendali.clear()
            QMessageBox.information(self, "Berhasil", "Buku berhasil dipindahkan ke lantai")

    def borrow_outside(self):
        """Borrow selected book outside"""
        book_id = self.get_selected_book_id(self.Tabel_Hasil)
        if not book_id:
            QMessageBox.warning(self, "Peringatan", "Pilih buku di Tabel Hasil terlebih dahulu")
            return
        if self.db.update_location_status(book_id, "Dipinjam"):
            self.db.log_activity(2, book_id, "Pinjam", "Status diubah ke Dipinjam")
            self.Tabel_Hasil.setModel(None)
            self.Form_Nomor_Kendali.clear()
            QMessageBox.information(self, "Berhasil", "Buku berhasil dipinjam ke luar ruangan")

    def authenticate(self):
        """Authenticate admin credentials"""
        username = self.Form_Username.text().strip()
        password = self.Form_Password.text().strip()

        # Validate fields are not empty
        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Username dan password harus diisi")
            return

        # Authenticate user
        user = self.db.authenticate_user(username, password)
        if user and user["Role"] == "Admin":
            # Close login window and open admin panel
            self.admin_panel = AdminPanel(user)
            self.admin_panel.show()
            self.close()
        else:
            QMessageBox.warning(self, "Login Gagal", "Username atau password salah")

    def open_staff_page(self):
        """Open staff main window"""
        self.main_window = MainWindow()
        self.main_window.show()
        self.close()


class AdminPanel(QMainWindow, Ui_AdminWindow):
    def __init__(self, user):
        super().__init__()
        self.setupUi(self)
        self.user = user
        self.db = DatabaseHandler()
        self.setWindowTitle("Panel Admin")

        # Add admin functionality here
        # For example:
        # self.btnAdd.clicked.connect(self.add_book)
        # self.btnEdit.clicked.connect(self.edit_book)
        # self.btnDelete.clicked.connect(self.delete_book)
        # self.btnImport.clicked.connect(self.import_data)
        # self.btnExport.clicked.connect(self.export_data)


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