import sqlite3
from src.database import create_database

if __name__ == '__main__':
    print('Initializing database...')
    conn = create_database()
    conn.execute('CREATE INDEX IF NOT EXISTS idx_buku_tahun ON BUKU(Tahun_Cetak)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_buku_kategori ON BUKU(ID_Kategori)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_log_waktu ON LOG_AKTIVITAS(Waktu)')
    print('Database created with indexes!')
    conn.close()
