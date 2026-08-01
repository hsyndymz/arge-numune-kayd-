import sqlite3

# Zemin iznini tüm kullanıcılara ekle (zaten varsa tekrar ekleme)
conn = sqlite3.connect('data/kesif_sistemi.db')
rows = conn.execute('SELECT id, username, permissions FROM users').fetchall()

for row in rows:
    uid, uname, perms = row
    perm_list = [p.strip() for p in perms.split(',') if p.strip()]
    zemin_perm = '🌍 ZEMİN KARAR SİSTEMİ'
    if zemin_perm not in perm_list:
        perm_list.append(zemin_perm)
        new_perms = ','.join(perm_list)
        conn.execute('UPDATE users SET permissions=? WHERE id=?', (new_perms, uid))
        print(f"✅ '{uname}' kullanıcısına Zemin izni eklendi.")
    else:
        print(f"ℹ️  '{uname}' zaten Zemin iznine sahip.")

conn.commit()
conn.close()
print("\nTüm kullanıcılar güncellendi. Lütfen uygulamayı yeniden başlatın.")
