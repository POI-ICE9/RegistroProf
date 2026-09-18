#!/usr/bin/env python3
"""
Script di migrazione dai file JSON al database SQLAlchemy
Mantiene tutti i dati esistenti e li trasferisce nel database
"""

import os
import sys
import json
from datetime import datetime
from werkzeug.security import generate_password_hash

# Aggiungi il percorso dell'app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utenti import app, db, User, Vote, Review, Professor, RegistrationRequest, Ticket, Notification, AuditLog, SessionLog

def load_json(filename):
    """Carica un file JSON se esiste e non è vuoto"""
    filepath = os.path.join(os.path.dirname(os.path.dirname(__file__)), filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, Exception) as e:
            print(f"  ! Errore nel caricare {filename}: {e}")
            return []
    return []

def migrate_users():
    """Migra gli utenti dal JSON al database"""
    print("[*] Migrazione Utenti...")
    users_data = load_json('utenti.json')
    
    for u in users_data:
        existing = User.query.filter_by(username=u.get('username')).first()
        if existing:
            print(f"  - Utente {u.get('username')} già esistente, salto.")
            continue
        
        # Assicurati che la password sia hashata
        pwd = u.get('password', '')
        if not pwd.startswith('pbkdf2:') and pwd:
            pwd = generate_password_hash(pwd)
        
        user = User(
            username=u.get('username', ''),
            password=pwd,
            email=u.get('email', ''),
            nome_cognome=u.get('nome_cognome', ''),
            scuola=u.get('scuola', ''),
            role=u.get('role', 'user'),
            stato=u.get('stato', 'attivo'),
            account_status=u.get('account_status', 'attivo'),
            telefono=u.get('telefono', ''),
            data_nascita=u.get('data_nascita', ''),
            indirizzo=u.get('indirizzo', ''),
            citta=u.get('citta', ''),
            cap=u.get('cap', ''),
            admin_note=u.get('admin_note', '')
        )
        
        # Gestisci created_at
        if u.get('created_at'):
            try:
                user.created_at = datetime.strptime(u['created_at'], '%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        db.session.add(user)
        print(f"  + Utente creato: {u.get('username')}")
    
    db.session.commit()
    print(f"[✓] Utenti migrati: {len(users_data)}")

def migrate_professors():
    """Migra i professori dal JSON al database"""
    print("[*] Migrazione Professori...")
    prof_data = load_json('professori.json')
    
    for p in prof_data:
        existing = Professor.query.filter_by(
            nome=p.get('nome', ''),
            materia=p.get('materia', ''),
            scuola=p.get('scuola', '')
        ).first()
        
        if existing:
            print(f"  - Professore {p.get('nome')} già esistente, salto.")
            continue
        
        professor = Professor(
            nome=p.get('nome', ''),
            materia=p.get('materia', ''),
            scuola=p.get('scuola', ''),
            istituto=p.get('istituto', ''),
            descrizione=p.get('descrizione', ''),
            profilo_pubblico=p.get('profilo_pubblico', False)
        )
        db.session.add(professor)
        print(f"  + Professore creato: {p.get('nome')}")
    
    db.session.commit()
    print(f"[✓] Professori migrati: {len(prof_data)}")

def migrate_reviews():
    """Migra le recensioni dal JSON al database"""
    print("[*] Migrazione Recensioni...")
    reviews_data = load_json('recensioni.json')
    
    for r in reviews_data:
        existing = Review.query.filter_by(id=r.get('id')).first()
        if existing:
            print(f"  - Recensione {r.get('id')} già esistente, salto.")
            continue
        
        review = Review(
            id=r.get('id'),
            username=r.get('user', r.get('username', '')),
            nomeProfRec=r.get('nomeProfRec', ''),
            scuola=r.get('scuola', ''),
            recensione=r.get('recensione', ''),
            likes=r.get('likes', 0),
            dislikes=r.get('dislikes', 0),
            user_likes=r.get('user_likes', []),
            user_dislikes=r.get('user_dislikes', []),
            commenti=r.get('commenti', []),
            is_anonymous=r.get('is_anonymous', False),
            professor_id=r.get('professor_id')
        )
        
        if r.get('timestamp'):
            try:
                review.timestamp = datetime.strptime(r['timestamp'], '%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        db.session.add(review)
        print(f"  + Recensione creata: ID {r.get('id')}")
    
    db.session.commit()
    print(f"[✓] Recensioni migrate: {len(reviews_data)}")

def migrate_votes():
    """Migra i voti dal JSON al database"""
    print("[*] Migrazione Voti...")
    votes_data = load_json('voti.json')
    
    for v in votes_data:
        vote = Vote(
            username=v.get('user', v.get('username', '')),
            voto=v.get('voto', ''),
            nomeProf=v.get('nomeProf', ''),
            materia=v.get('materia', ''),
            scuola=v.get('scuola', '')
        )
        
        if v.get('timestamp'):
            try:
                vote.timestamp = datetime.strptime(v['timestamp'], '%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        db.session.add(vote)
    
    db.session.commit()
    print(f"[✓] Voti migrati: {len(votes_data)}")

def migrate_tickets():
    """Migra i ticket dal JSON al database"""
    print("[*] Migrazione Ticket...")
    tickets_data = load_json('ticket.json')
    
    for t in tickets_data:
        existing = Ticket.query.filter_by(id=t.get('id')).first()
        if existing:
            print(f"  - Ticket {t.get('id')} già esistente, salto.")
            continue
        
        ticket = Ticket(
            id=t.get('id'),
            utente=t.get('utente', ''),
            oggetto=t.get('oggetto', ''),
            messaggio=t.get('messaggio', ''),
            priorita=t.get('priorita', 'media'),
            stato=t.get('stato', 'aperto'),
            admin_assegnato=t.get('admin_assegnato'),
            risposte=t.get('risposte', [])
        )
        
        if t.get('data_apertura'):
            try:
                ticket.data_apertura = datetime.strptime(t['data_apertura'], '%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        if t.get('data_chiusura'):
            try:
                ticket.data_chiusura = datetime.strptime(t['data_chiusura'], '%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        db.session.add(ticket)
        print(f"  + Ticket creato: ID {t.get('id')}")
    
    db.session.commit()
    print(f"[✓] Ticket migrati: {len(tickets_data)}")

def migrate_registrations():
    """Migra le richieste di registrazione pendenti"""
    print("[*] Migrazione Registrazioni Pendenti...")
    reg_data = load_json('registrazioni.json')
    
    for r in reg_data:
        existing = RegistrationRequest.query.filter_by(username=r.get('username')).first()
        if existing:
            print(f"  - Registrazione {r.get('username')} già esistente, salto.")
            continue
        
        req = RegistrationRequest(
            username=r.get('username', ''),
            password=r.get('password', ''),
            email=r.get('email', ''),
            nome_cognome=r.get('nome_cognome', ''),
            scuola=r.get('scuola', ''),
            stato=r.get('stato', 'in_attesa'),
            admin_note=r.get('admin_note', '')
        )
        
        if r.get('data_registrazione'):
            try:
                req.data_registrazione = datetime.strptime(r['data_registrazione'], '%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        db.session.add(req)
        print(f"  + Registrazione pendente: {r.get('username')}")
    
    db.session.commit()
    print(f"[✓] Registrazioni migrate: {len(reg_data)}")

def migrate_sessions():
    """Migra le sessioni attive"""
    print("[*] Migrazione Sessioni...")
    sessions_data = load_json('sessioni.json')
    
    for s in sessions_data:
        existing = SessionLog.query.filter_by(session_id=s.get('session_id')).first()
        if existing:
            continue
        
        session = SessionLog(
            session_id=s.get('session_id', ''),
            username=s.get('username', ''),
            ip=s.get('ip', ''),
            user_agent=s.get('user_agent', '')[:500]
        )
        
        if s.get('login_time'):
            try:
                session.login_time = datetime.strptime(s['login_time'], '%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        if s.get('last_activity'):
            try:
                session.last_activity = datetime.strptime(s['last_activity'], '%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        db.session.add(session)
    
    db.session.commit()
    print(f"[✓] Sessioni migrate: {len(sessions_data)}")

def migrate_audit_log():
    """Migra il log di audit"""
    print("[*] Migrazione Audit Log...")
    audit_data = load_json('audit_log.json')
    
    for a in audit_data:
        existing = AuditLog.query.filter_by(id=a.get('id')).first()
        if existing:
            continue
        
        log = AuditLog(
            id=a.get('id'),
            azione=a.get('azione', ''),
            esito=a.get('esito', ''),
            attore=a.get('attore', ''),
            target=a.get('target', ''),
            ip=a.get('ip', ''),
            user_agent=a.get('user_agent', '')[:500],
            dettagli=a.get('dettagli', {})
        )
        
        if a.get('timestamp'):
            try:
                log.timestamp = datetime.strptime(a['timestamp'], '%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        db.session.add(log)
    
    db.session.commit()
    print(f"[✓] Audit Log migrati: {len(audit_data)}")

def migrate_notifications():
    """Migra le notifiche"""
    print("[*] Migrazione Notifiche...")
    notif_data = load_json('notifiche.json')
    
    for n in notif_data:
        existing = Notification.query.filter_by(id=n.get('id')).first()
        if existing:
            continue
        
        notif = Notification(
            id=n.get('id'),
            utente=n.get('utente', ''),
            tipo=n.get('tipo', ''),
            titolo=n.get('titolo', ''),
            messaggio=n.get('messaggio', ''),
            link=n.get('link', ''),
            letta=n.get('letta', False)
        )
        
        if n.get('data'):
            try:
                notif.data = datetime.strptime(n['data'], '%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        if n.get('data_lettura'):
            try:
                notif.data_lettura = datetime.strptime(n['data_lettura'], '%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        db.session.add(notif)
    
    db.session.commit()
    print(f"[✓] Notifiche migrate: {len(notif_data)}")

def main():
    """Esegue tutte le migrazioni"""
    print("=" * 60)
    print("MIGRAZIONE DATI DA JSON A DATABASE SQLALCHEMY")
    print("=" * 60)
    
    with app.app_context():
        # Crea le tabelle se non esistono
        print("\n[*] Creazione tabelle database...")
        db.create_all()
        print("[✓] Tabelle create/verificate\n")
        
        # Esegui migrazioni
        migrate_users()
        migrate_professors()
        migrate_reviews()
        migrate_votes()
        migrate_tickets()
        migrate_registrations()
        migrate_sessions()
        migrate_audit_log()
        migrate_notifications()
        
        print("\n" + "=" * 60)
        print("[✓✓✓] MIGRAZIONE COMPLETATA CON SUCCESSO!")
        print("=" * 60)
        print("\nI dati sono stati trasferiti dal formato JSON al database SQLite/PostgreSQL.")
        print("I file JSON originali sono stati mantenuti come backup.")
        print("\nOra puoi utilizzare l'applicazione con il database.")

if __name__ == '__main__':
    main()
