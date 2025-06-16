import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QDialog
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt
from ui.Katalog_Mainpage import Ui_MainWindow
from ui.Form_Login_Admin import Ui_LoginAdmin
from ui.Admin_Page import Ui_AdminPage
from ui.Confirmation import ConfirmationDialog
import database as db


class MainPage(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.db = db.DatabaseHandler()
        self.current_user = None

        # Connect signals to slots
        self.btnCari.clicked.connect(self.search_book)
        self.btnPindahLantai.clicked.connect(lambda: self.update_status("Di Lantai"))
        self.btnPinjamLuar.clicked.connect(lambda: self.update_status("Di Luar Ruangan"))
        self.btnAdmin.clicked.connect(self.open_admin_login)

        # Initialize UI
        self.load_location_tables()

    def load_location_tables(self):
        """Populate tables with books based on their location status"""
        headers = ["ID Buku", "Kategori", "Tahun Cetak", "No. Min", "No. Max", "Rak"]

        # Populate 'Di Lantai' table
        self.populate_table(
            self.Tabel_di_Atas_Lantai,
            self.db.get_books_by_location("Di Lantai"),
            headers
        )

        # Populate 'Di Luar Ruangan' table
        self.populate_table(
            self.Tabel_di_Luar_Ruangan,
            self.db.get_books_by_location("Di Luar Ruangan"),
            headers
        )

        # Populate 'Di Rak' table
        self.populate_table(
            self.Tabel_di_Rak,
            self.db.get_books_by_location("Di Rak"),
            headers
        )

    def populate_table(self, table, data, headers):
        """Populate QTableWidget with data"""
        table.clear()
        table.setRowCount(len(data))
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)

        # Populate table data
        for row_idx, row_data in enumerate(data):
            for col_idx, col_data in enumerate(row_data):
                item = QTableWidgetItem(str(col_data))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)

        # Resize columns to contents
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def search_book(self):
        """Search for a book by control number"""
        try:
            control_num = int(self.inputNomorKendali.text())
            result = self.db.search_book(control_num)

            if result:
                self.display_search_result(result)
            else:
                QMessageBox.warning(self, "Tidak Ditemukan",
                                    "Buku tidak ditemukan untuk nomor kendali tersebut")
        except ValueError:
            QMessageBox.critical(self, "Input Error",
                                 "Nomor kendali harus berupa angka")

    def display_search_result(self, result):
        """Display search result in the UI"""
        # Format location information
        location_info = (
            f"Rak: {result['Nama_Rak']}\n"
            f"Kategori: {result['Nama_Kategori']}\n"
            f"Status: {result['Status_Lokasi']}"
        )
        self.labelHasilPencarian.setText(location_info)

        # Highlight in appropriate table
        if result['Status_Lokasi'] == "Di Lantai":
            self.highlight_book_in_table(self.Tabel_di_Atas_Lantai, result['ID_Buku'])
        elif result['Status_Lokasi'] == "Di Luar Ruangan":
            self.highlight_book_in_table(self.Tabel_di_Luar_Ruangan, result['ID_Buku'])
        else:
            self.highlight_book_in_table(self.Tabel_di_Rak, result['ID_Buku'])

    def highlight_book_in_table(self, table, book_id):
        """Highlight a specific book in the given table"""
        for row in range(table.rowCount()):
            if table.item(row, 0).text() == book_id:
                for col in range(table.columnCount()):
                    table.item(row, col).setBackground(QColor('#FFFF00'))  # Yellow highlight
                table.selectRow(row)
                return

    def update_status(self, new_status):
        """Update the location status of a book"""
        if not self.inputNomorKendali.text():
            QMessageBox.warning(self, "Peringatan", "Masukkan nomor kendali terlebih dahulu")
            return

        try:
            control_num = int(self.inputNomorKendali.text())
            book_data = self.db.search_book(control_num)

            if not book_data:
                QMessageBox.warning(self, "Tidak Ditemukan",
                                    "Buku tidak ditemukan untuk nomor kendali tersebut")
                return

            # Show confirmation dialog
            dialog = ConfirmationDialog(
                self,
                f"Apakah Anda yakin ingin mengubah status buku menjadi '{new_status}'?",
                "Konfirmasi Perubahan Status"
            )

            if dialog.exec() == QDialog.DialogCode.Accepted:
                # Get current status before update
                old_status = book_data['Status_Lokasi']

                # Update status in database
                self.db.update_location_status(book_data['ID_Buku'], new_status)

                # Log the activity
                self.db.log_activity(
                    self.current_user['ID_Pengguna'] if self.current_user else None,
                    book_data['ID_Buku'],
                    "UPDATE_STATUS",
                    f"Status lokasi diubah dari {old_status} menjadi {new_status}",
                    old_status,
                    new_status
                )

                # Refresh UI
                self.load_location_tables()
                self.search_book()  # Refresh search result

                QMessageBox.information(self, "Berhasil", "Status buku berhasil diperbarui")

        except ValueError:
            QMessageBox.critical(self, "Input Error",
                                 "Nomor kendali harus berupa angka")

    def open_admin_login(self):
        """Open the admin login dialog"""
        self.login_dialog = LoginDialog(self)
        self.login_dialog.exec()


class LoginDialog(QDialog, Ui_LoginAdmin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.btnLogin.clicked.connect(self.authenticate)

    def authenticate(self):
        """Authenticate user credentials"""
        username = self.inputUsername.text()
        password = self.inputPassword.text()

        db_handler = db.DatabaseHandler()
        user = db_handler.authenticate_user(username, password)

        if user and user['Role'] == 'Admin':
            self.parent.current_user = user
            self.parent.statusbar.showMessage(f"Masuk sebagai: {user['Username']}", 5000)
            self.accept()
        else:
            QMessageBox.warning(self, "Login Gagal",
                                "Username atau password salah, atau Anda bukan admin")


class AdminPage(QMainWindow, Ui_AdminPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.parent = parent
        self.db = db.DatabaseHandler()

        # Connect signals
        self.btnBack.clicked.connect(self.close)
        self.btnAddBook.clicked.connect(self.add_book)
        self.btnEditBook.clicked.connect(self.edit_book)
        self.btnDeleteBook.clicked.connect(self.delete_book)
        self.btnRefresh.clicked.connect(self.load_books)

        # Initialize UI
        self.load_books()

    def load_books(self):
        """Load all books into the table"""
        books = self.db.get_all_books()
        self.tableBooks.setRowCount(len(books))

        for row_idx, book in enumerate(books):
            for col_idx, col in enumerate([
                'ID_Buku', 'ID_Kategori', 'Tahun_Cetak',
                'No_Kendali_Min', 'No_Kendali_Max', 'Status_Lokasi'
            ]):
                item = QTableWidgetItem(str(book[col]))
                item.setFlags(item.flags() ^ Qt.ItemFlag.ItemIsEditable)
                self.tableBooks.setItem(row_idx, col_idx, item)

        # Set column headers
        headers = ["ID Buku", "Kategori", "Tahun Cetak", "No. Min", "No. Max", "Status Lokasi"]
        self.tableBooks.setHorizontalHeaderLabels(headers)
        self.tableBooks.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def add_book(self):
        # Implement book addition logic
        pass

    def edit_book(self):
        # Implement book editing logic
        pass

    def delete_book(self):
        # Implement book deletion logic
        pass

def main():
    app = QApplication(sys.argv)

    # Create data directory if not exists
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)

    # Initialize database
    db_handler = db.DatabaseHandler()
    db_handler.initialize_database()

    window = MainPage()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()