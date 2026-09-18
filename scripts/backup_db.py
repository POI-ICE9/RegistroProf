#!/usr/bin/env python3
"""
Script di backup automatico del database
Crea copie del database con timestamp e gestisce la rotazione dei backup vecchi
"""

import os
import sys
import shutil
from datetime import datetime, timedelta

# Aggiungi il percorso dell'app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utenti import app, db

# Configurazione
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backups')
MAX_BACKUPS = 10  # Numero massimo di backup da mantenere
DAYS_TO_KEEP = 30  # Giorni per cui mantenere i backup

def ensure_backup_dir():
    """Assicura che la cartella dei backup esista"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    print(f"[✓] Cartella backup: {BACKUP_DIR}")

def get_database_path():
    """Ottiene il percorso del database attuale"""
    uri = str(app.config.get('SQLALCHEMY_DATABASE_URI', ''))
    
    if uri.startswith('sqlite:///'):
        # Percorso relativo o assoluto
        db_path = uri.replace('sqlite:///', '')
        if not os.path.isabs(db_path):
            # Prova prima nella cartella instance (Flask default)
            instance_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', db_path)
            if os.path.exists(instance_path):
                return instance_path
            # Altrimenti nella root dell'app
            db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), db_path)
        return db_path
    elif uri.startswith('postgresql://'):
        # Per PostgreSQL, crea un dump
        return None  # Gestito separatamente
    
    return None

def backup_sqlite():
    """Crea un backup del database SQLite"""
    db_path = get_database_path()
    
    if not db_path or not os.path.exists(db_path):
        print("[!] Database SQLite non trovato o non configurato")
        return False
    
    # Crea nome file con timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'registro_backup_{timestamp}.db'
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    # Copia il file del database
    try:
        shutil.copy2(db_path, backup_path)
        print(f"[✓] Backup creato: {backup_filename}")
        
        # Crea anche un file di metadati
        metadata_path = backup_path.replace('.db', '.txt')
        with open(metadata_path, 'w', encoding='utf-8') as f:
            f.write(f"Backup del: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Database originale: {db_path}\n")
            f.write(f"Dimensione: {os.path.getsize(backup_path)} bytes\n")
        
        print(f"[✓] Metadati creati: {os.path.basename(metadata_path)}")
        return True
        
    except Exception as e:
        print(f"[!] Errore durante il backup: {e}")
        return False

def backup_postgresql():
    """Crea un dump del database PostgreSQL (se pg_dump è disponibile)"""
    uri = str(app.config.get('SQLALCHEMY_DATABASE_URI', ''))
    
    if not uri.startswith('postgresql://'):
        return False
    
    print("[*] Backup PostgreSQL richiesto...")
    print("[!] Nota: Per PostgreSQL è necessario installare pg_dump e configurare le variabili d'ambiente")
    
    # Estrai informazioni dal URI
    # Formato: postgresql://user:password@host:port/dbname
    try:
        from urllib.parse import urlparse
        parsed = urlparse(uri.replace('postgresql://', ''))
        
        dbname = parsed.path.strip('/')
        user = parsed.username
        password = parsed.password
        host = parsed.hostname
        port = parsed.port or 5432
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'registro_backup_{timestamp}.sql'
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # Comando pg_dump
        import subprocess
        env = os.environ.copy()
        env['PGPASSWORD'] = password
        
        cmd = [
            'pg_dump',
            '-h', host,
            '-p', str(port),
            '-U', user,
            '-d', dbname,
            '-f', backup_path
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"[✓] Dump PostgreSQL creato: {backup_filename}")
            
            # Comprimi il file SQL
            import gzip
            compressed_path = backup_path + '.gz'
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            os.remove(backup_path)  # Rimuovi file non compresso
            print(f"[✓] File compresso: {os.path.basename(compressed_path)}")
            return True
        else:
            print(f"[!] Errore pg_dump: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("[!] pg_dump non trovato. Installa PostgreSQL tools.")
        return False
    except Exception as e:
        print(f"[!] Errore durante il backup PostgreSQL: {e}")
        return False

def cleanup_old_backups():
    """Rimuove i backup più vecchi del limite configurato"""
    print("[*] Pulizia backup vecchi...")
    
    if not os.path.exists(BACKUP_DIR):
        return
    
    # Ottieni tutti i file di backup
    backup_files = []
    for f in os.listdir(BACKUP_DIR):
        if f.startswith('registro_backup_') and (f.endswith('.db') or f.endswith('.sql.gz') or f.endswith('.txt')):
            filepath = os.path.join(BACKUP_DIR, f)
            backup_files.append((filepath, os.path.getmtime(filepath)))
    
    # Ordina per data (più recenti primi)
    backup_files.sort(key=lambda x: x[1], reverse=True)
    
    removed_count = 0
    
    # Mantieni solo MAX_BACKUPS
    if len(backup_files) > MAX_BACKUPS:
        for filepath, _ in backup_files[MAX_BACKUPS:]:
            try:
                os.remove(filepath)
                print(f"  - Rimosso: {os.path.basename(filepath)}")
                removed_count += 1
            except Exception as e:
                print(f"  ! Errore nella rimozione di {filepath}: {e}")
    
    # Rimuovi backup più vecchi di DAYS_TO_KEEP giorni
    cutoff_date = datetime.now() - timedelta(days=DAYS_TO_KEEP)
    for filepath, mtime in backup_files[:MAX_BACKUPS]:  # Controlla solo quelli mantenuti
        file_date = datetime.fromtimestamp(mtime)
        if file_date < cutoff_date:
            try:
                os.remove(filepath)
                print(f"  - Rimosso (scaduto): {os.path.basename(filepath)}")
                removed_count += 1
            except Exception as e:
                print(f"  ! Errore nella rimozione di {filepath}: {e}")
    
    print(f"[✓] Backup rimossi: {removed_count}")

def list_backups():
    """Mostra l'elenco dei backup disponibili"""
    print("\n" + "=" * 60)
    print("BACKUP DISPONIBILI")
    print("=" * 60)
    
    if not os.path.exists(BACKUP_DIR):
        print("Nessun backup trovato.")
        return
    
    backup_files = []
    for f in os.listdir(BACKUP_DIR):
        if f.startswith('registro_backup_'):
            filepath = os.path.join(BACKUP_DIR, f)
            size = os.path.getsize(filepath)
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            backup_files.append((f, size, mtime))
    
    if not backup_files:
        print("Nessun backup trovato.")
        return
    
    backup_files.sort(key=lambda x: x[2], reverse=True)
    
    for filename, size, date in backup_files[:20]:  # Mostra solo i 20 più recenti
        size_kb = size / 1024
        print(f"  {date.strftime('%Y-%m-%d %H:%M')}  |  {filename:<40}  |  {size_kb:>8.1f} KB")
    
    if len(backup_files) > 20:
        print(f"  ... e altri {len(backup_files) - 20} backup")

def main():
    """Esegue il backup completo"""
    print("=" * 60)
    print("BACKUP AUTOMATICO DATABASE")
    print("=" * 60)
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with app.app_context():
        ensure_backup_dir()
        
        # Determina il tipo di database ed esegui il backup appropriato
        uri = str(app.config.get('SQLALCHEMY_DATABASE_URI', ''))
        
        success = False
        if uri.startswith('sqlite'):
            success = backup_sqlite()
        elif uri.startswith('postgresql'):
            success = backup_postgresql()
        else:
            print("[!] Tipo di database non supportato per il backup automatico")
        
        if success:
            cleanup_old_backups()
            print("\n" + "=" * 60)
            print("[✓✓✓] BACKUP COMPLETATO CON SUCCESSO!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("[!] BACKUP FALLITO O NON ESEGUITO")
            print("=" * 60)
            sys.exit(1)

if __name__ == '__main__':
    # Supporto per argomenti da riga di comando
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == 'list':
            with app.app_context():
                ensure_backup_dir()
                list_backups()
        elif arg == 'help':
            print("Utilizzo: python backup_db.py [list|help]")
            print("  list  - Mostra l'elenco dei backup disponibili")
            print("  help  - Mostra questo messaggio")
            print("  (nessun argomento) - Esegue un nuovo backup")
        else:
            main()
    else:
        main()
