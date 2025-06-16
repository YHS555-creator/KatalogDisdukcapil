# database.py
import sqlite3
import os
from pathlib import Path
from datetime import datetime
from typing import Any


class DatabaseHandler:
    def __init__(self, db_path=None):
        if db_path is None:
            base_dir = Path(__file__).resolve().parent.parent
            self.db_path = base_dir / "data" / "arsip.sqlite"
        else:
            self.db_path = Path(db_path)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        print(f"Connected to database: {self.db_path}")

    def execute_query(self, query, params=(), fetch_one=False):
        """Execute SQL query and return results as dictionaries"""
        try:
            cur = self.conn.cursor()
            cur.execute(query, params)
            self.conn.commit()

            if fetch_one:
                row = cur.fetchone()
                return dict(row) if row else None
            else:
                return [dict(row) for row in cur.fetchall()]
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    def get_books_by_location(self, status, full_attributes=False):
        """Get books by location status with all attributes"""
        if full_attributes:
            query = """
            SELECT B.*, R.Nama_Rak, K.Nama_Kategori 
            FROM BUKU B
            JOIN RAK R ON B.ID_Rak = R.ID_Rak
            JOIN KATEGORI K ON B.ID_Kategori = K.ID_Kategori
            WHERE B.Status_Lokasi = ?
            """
        else:
            query = """
            SELECT B.ID_Buku, R.Nama_Rak, K.Nama_Kategori, B.Tahun_Cetak,
                   B.No_Kendali_Min, B.No_Kendali_Max, B.Status_Lokasi
            FROM BUKU B
            JOIN RAK R ON B.ID_Rak = R.ID_Rak
            JOIN KATEGORI K ON B.ID_Kategori = K.ID_Kategori
            WHERE B.Status_Lokasi = ?
            """
        return self.execute_query(query, (status,))

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

    def update_location_status(self, book_id, new_status):
        """Update book location status"""
        query = "UPDATE BUKU SET Status_Lokasi = ? WHERE ID_Buku = ?"
        try:
            cur = self.conn.cursor()
            cur.execute(query, (new_status, book_id))
            self.conn.commit()
            return cur.rowcount > 0
        except sqlite3.Error as e:
            print(f"Update error: {e}")
            return False

    def log_activity(self, user_id, book_id, action_type, details):
        """Log user activity"""
        query = """
        INSERT INTO LOG_AKTIVITAS 
        (ID_Pengguna, ID_Buku, Jenis_Aksi, Detail_Perubahan, Waktu)
        VALUES (?, ?, ?, ?, ?)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.execute_query(query, (user_id, book_id, action_type, details, timestamp))

    def authenticate_user(self, username: object, password: object) -> dict[Any, Any] | dict[str, Any] | dict[str, str] | dict[bytes, bytes] | None | list[dict[Any, Any] | dict[str, Any] | dict[str, str] | dict[bytes, bytes]]:
        """Authenticate user credentials"""
        query = "SELECT * FROM PENGGUNA WHERE Username = ? AND Password = ?"
        return self.execute_query(query, (username, password), fetch_one=True)