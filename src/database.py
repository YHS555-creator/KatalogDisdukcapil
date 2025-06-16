import sqlite3
import os
from pathlib import Path
from datetime import datetime


class DatabaseHandler:
    def __init__(self, db_path=None):
        if db_path is None:
            base_dir = Path(__file__).resolve().parent.parent
            db_path = os.path.join(base_dir, "data", "arsip.sqlite")
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def search_book(self, nomor_kendali):
        """Search book by control number"""
        query = """
        SELECT B.*, R.Nama_Rak, K.Nama_Kategori 
        FROM BUKU B
        JOIN RAK R ON B.ID_Rak = R.ID_Rak
        JOIN KATEGORI K ON B.ID_Kategori = K.ID_Kategori
        WHERE ? BETWEEN B.No_Kendali_Min AND B.No_Kendali_Max
        """
        return self.execute_query(query, (nomor_kendali,), fetch_one=True)

    def execute_query(self, query, params=(), fetch_one=False):
        """Execute SQL query with error handling"""
        try:
            cur = self.conn.cursor()
            cur.execute(query, params)
            self.conn.commit()
            return cur.fetchone() if fetch_one else cur.fetchall()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    def update_location_status(self, book_id, new_status):
        """Update book location status"""
        query = "UPDATE BUKU SET Status_Lokasi = ? WHERE ID_Buku = ?"
        return self.execute_query(query, (new_status, book_id))

    def log_activity(self, user_id, book_id, action_type, details):
        """Log user activity"""
        query = """
        INSERT INTO LOG_AKTIVITAS 
        (ID_Pengguna, ID_Buku, Jenis_Aksi, Detail_Perubahan, Waktu)
        VALUES (?, ?, ?, ?, ?)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.execute_query(query, (user_id, book_id, action_type, details, timestamp))

    def authenticate_user(self, username, password):
        """Authenticate user credentials"""
        query = "SELECT * FROM PENGGUNA WHERE Username = ? AND Password = ?"
        return self.execute_query(query, (username, password), fetch_one=True)

    # ADD THIS MISSING METHOD
    def get_books_by_location(self, status):
        """Get books by location status"""
        query = """
        SELECT B.ID_Buku, R.Nama_Rak, K.Nama_Kategori, B.Tahun_Cetak,
               B.No_Kendali_Min, B.No_Kendali_Max, B.Status_Lokasi
        FROM BUKU B
        JOIN RAK R ON B.ID_Rak = R.ID_Rak
        JOIN KATEGORI K ON B.ID_Kategori = K.ID_Kategori
        WHERE B.Status_Lokasi = ?
        """
        return self.execute_query(query, (status,))