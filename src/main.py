import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QDialog, QMessageBox, QTableWidgetItem
from ui.Katalog_Mainpage import Ui_MainWindow
from ui.Form_Login_Admin import Ui_LoginWindow
from ui.Admin_Page import Ui_AdminWindow
from ui.Confirmation import Ui_Dialog as Ui_ConfirmationDialog
from database import DatabaseHandler


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.db = DatabaseHandler()
        self.current_book = None

        # Connect signals - FIXED METHOD NAMES
        self.Search_Button.clicked.connect(self.search_book)
        self.Pindah_ke_Lantai_Button.clicked.connect(self.move_to_floor)
        self.Pinjam_ke_Luar_Ruangan_Button.clicked.connect(self.borrow_outside)
        self.Admin_Page_Button.clicked.connect(self.open_admin_login)

        # Load location tables
        self.load_location_tables()

    def load_location_tables(self):
        """Load books by location status"""
        self.books_on_floor = self.db.get_books_by_location("Di Lantai")
        self.books_outside = self.db.get_books_by_location("Di Luar Ruangan")
        self.books_in_rack = self.db.get_books_by_location("Di Rak")

    def search_book(self):
        nomor_kendali = self.Form_Nomor_Kendali.text().strip()

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

    # FIXED: ADDED MISSING METHODS
    def move_to_floor(self):
        """Move book to floor status"""
        if not self.current_book:
            QMessageBox.warning(self, "Peringatan", "Cari buku terlebih dahulu")
            return

        if self.db.update_location_status(self.current_book["ID_Buku"], "Di Lantai"):
            self.db.log_activity(2, self.current_book["ID_Buku"], "UPDATE",
                                 f"Status diubah ke Di Lantai")
            QMessageBox.information(self, "Berhasil", "Status lokasi diperbarui")

    def borrow_outside(self):
        """Borrow book outside the room"""
        if not self.current_book:
            QMessageBox.warning(self, "Peringatan", "Cari buku terlebih dahulu")
            return

        if self.db.update_location_status(self.current_book["ID_Buku"], "Di Luar Ruangan"):
            self.db.log_activity(2, self.current_book["ID_Buku"], "UPDATE",
                                 f"Status diubah ke Di Luar Ruangan")
            QMessageBox.information(self, "Berhasil", "Status lokasi diperbarui")

    def open_admin_login(self):
        """Open admin login window"""
        login_window = LoginWindow(self)
        if login_window.exec() == QDialog.DialogCode.Accepted:
            admin_panel = AdminPanel(login_window.user)
            admin_panel.show()

    def display_book_info(self, book):
        """Display book information in table"""
        # Implementation of display logic
        pass

    def clear_results(self):
        """Clear search results"""
        # Implementation of clear results logic
        pass


class LoginWindow(QDialog, Ui_LoginWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.db = DatabaseHandler()
        self.user = None
        self.pushButton_Login.clicked.connect(self.authenticate)

    def authenticate(self):
        """Authenticate admin credentials"""
        username = self.lineEdit_Username.text().strip()
        password = self.lineEdit_Password.text().strip()

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