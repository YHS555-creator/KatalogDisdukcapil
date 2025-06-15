import sqlite3
import os
from PyQt6 import QtWidgets
from datetime import datetime


class DatabaseHandler:
    # File: src/database.py
    def __init__(self, db_path="data/arsip.sqlite"):
        # 1) Compute absolute path to data/arsip.sqlite
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        full_db_path = os.path.normpath(os.path.join(base_dir, db_path))
        print(f"Normalized Path: {full_db_path}")

        # 2) Connect and set up cursor
        try:
            self.conn = sqlite3.connect(full_db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()       # ← **This line was missing**
            print("Database connection successful!")
        except Exception as e:
            print(f"Connection failed: {str(e)}")
            raise

        # 3) (Optional) Ensure indexes exist
        self._initialize_indexes()


    def _initialize_indexes(self):
        """Create indexes for optimization (idempotent)."""
        try:
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_buku_tahun 
                ON BUKU(Tahun_Cetak)
            """)
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_buku_kategori 
                ON BUKU(ID_Kategori)
            """)
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_log_waktu 
                ON LOG_AKTIVITAS(Waktu)
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(None, "Index Error", f"Could not create indexes: {e}")


    # ----------------------------
    # Core CRUD Operations for BUKU
    # ----------------------------
    def search_book(self, nomor_kendali):
        """Search buku by nomor kendali."""
        query = """
            SELECT 
                BUKU.ID_Buku, BUKU.Tahun_Cetak, KATEGORI.Nama_Kategori, 
                RAK.Nama_Rak, BUKU.No_Kendali_Min, BUKU.No_Kendali_Max, 
                BUKU.Status_Lokasi
            FROM BUKU
            JOIN RAK ON BUKU.ID_Rak = RAK.ID_Rak
            JOIN KATEGORI ON BUKU.ID_Kategori = KATEGORI.ID_Kategori
            WHERE ? BETWEEN BUKU.No_Kendali_Min AND BUKU.No_Kendali_Max
        """
        return self._safe_execute(query, (nomor_kendali,))


    def add_book(self, buku_data):
        """Insert new buku."""
        query = """
            INSERT INTO BUKU (
                ID_Buku, ID_Rak, ID_Kategori, Tahun_Cetak, 
                No_Kendali_Min, No_Kendali_Max, Warna_Sampul, 
                Subkategori, Status_Kondisi, Status_Lokasi
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        return self._safe_execute(query, buku_data, commit=True)


    # ----------------------------
    # User Authentication
    # ----------------------------
    def authenticate_user(self, username, password):
        """Validate admin credentials."""
        query = """
            SELECT ID_Pengguna, Role 
            FROM PENGGUNA 
            WHERE Username = ? AND Password = ?
        """
        result = self._safe_execute(query, (username, password))
        return result[0] if result else None


    # ----------------------------
    # Location Management
    # ----------------------------
    def update_location_status(self, book_id, new_status):
        """Update Status_Lokasi."""
        query = """
            UPDATE BUKU 
            SET Status_Lokasi = ? 
            WHERE ID_Buku = ?
        """
        return self._safe_execute(query, (new_status, book_id), commit=True)


    # ----------------------------
    # Activity Logging
    # ----------------------------
    def log_activity(self, user_id, book_id, action_type, details):
        """Insert log entry."""
        query = """
            INSERT INTO LOG_AKTIVITAS (
                ID_Pengguna, ID_Buku, Waktu, 
                Jenis_Aksi, Detail_Perubahan
            ) VALUES (?, ?, ?, ?, ?)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self._safe_execute(
            query, (user_id, book_id, timestamp, action_type, details),
            commit=True
        )


    # ----------------------------
    # Generic Helper Method
    # ----------------------------
    def _safe_execute(self, query, params=(), commit=False):
        """Execute SQL safely, show dialog on error."""
        try:
            self.cursor.execute(query, params)
            if commit:
                self.conn.commit()
            # For SELECT, return fetched rows; for others, return True
            return self.cursor.fetchall() if not commit else True
        except sqlite3.Error as e:
            QtWidgets.QMessageBox.critical(
                None, "Database Error", f"SQL Error: {str(e)}"
            )
            if commit:
                self.conn.rollback()
            return False


    def close(self):
        """Close database connection."""
        self.conn.close()


# --- Testing block (optional) ---
if __name__ == "__main__":
    db = DatabaseHandler()
    print(db.search_book("12345"))             # Test search
    user = db.authenticate_user("Admin", "Admin")
    print("Admin ID:", user[0] if user else "Invalid credentials")
    db.close()
