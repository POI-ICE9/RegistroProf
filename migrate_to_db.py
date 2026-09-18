#!/usr/bin/env python3
"""
Script di migrazione dai file JSON al database SQLite
Mantiene la funzionalità esistente e preserva tutti i dati
"""

import json
import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Aggiungi il percorso corrente al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importa l'app Flask e i modelli
from utenti import app, db, User, Vote, Review, Professor, Subject, School, Ticket, Report, Notice, Notification, PasswordRecovery, AuditLog, PrivacyRequest, NotificationPreference, LoginHistory, SessionLog, RegistrationRequest, StudyMaterial, ExamEvent, ProfessorFavorite

def load_json_file(filename):
    """Carica un file JSON se esiste"""
    filepath = os.path.join(os.path.dirname(__file__), filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"[✓] Caricati {len(data) if isinstance(data, list) else 1} record da {filename}")
                return data
        except Exception as e:
            print(f"[!] Errore nel caricamento di {filename}: {e}")
            return [] if filename != 'settings.json' else {}
    else:
        print(f"[ ] File {filename} non trovato, salto...")
        return [] if filename != 'settings.json' else {}

def migrate_users(users_data):
    """Migra gli utenti dal JSON al database"""
    if not users_data:
        print("[ ] Nessun utente da migrare")
        return
    
    count = 0
    for user_json in users_data:
        # Controlla se l'utente esiste già
        existing = User.query.filter_by(username=user_json.get('username')).first()
        if existing:
            print(f"[ ] Utente {user_json.get('username')} già esiste, salto...")
            continue
        
        # Crea nuovo utente
        password = user_json.get('password', '')
        # Se la password non è già hashata, hashala
        if not password.startswith('pbkdf2:'):
            password = generate_password_hash(password)
        
        # Gestisci email vuota - usa un placeholder unico per evitare conflitti
        email = user_json.get('email', '')
        if not email or email.strip() == '':
            # Crea un'email placeholder unica basata sul username
            email = f"{user_json.get('username', 'user')}@placeholder.local"
        
        user = User(
            username=user_json.get('username', ''),
            password=password,
            email=email,
            nome_cognome=user_json.get('nome_cognome', ''),
            scuola=user_json.get('scuola', ''),
            role=user_json.get('role', 'user'),
            stato=user_json.get('stato', 'attivo'),
            account_status=user_json.get('account_status', 'attivo'),
            telefono=user_json.get('telefono', ''),
            data_nascita=user_json.get('data_nascita', ''),
            indirizzo=user_json.get('indirizzo', ''),
            citta=user_json.get('citta', ''),
            cap=user_json.get('cap', ''),
            admin_note=user_json.get('admin_note', ''),
            avatar_preset=user_json.get('avatar_preset', 0),
            avatar_file=user_json.get('avatar_file', ''),
            oauth_provider=user_json.get('oauth_provider', ''),
            oauth_sub=user_json.get('oauth_sub', '')
        )
        
        # Gestisci created_at se presente
        created_at_str = user_json.get('created_at')
        if created_at_str:
            try:
                user.created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
            except:
                user.created_at = datetime.now()
        
        db.session.add(user)
        count += 1
    
    try:
        db.session.commit()
        print(f"[✓] Migrati {count} utenti")
    except Exception as e:
        db.session.rollback()
        print(f"[!] Errore nella migrazione utenti: {e}")

def migrate_professors(prof_data):
    """Migra i professori dal JSON al database"""
    if not prof_data:
        print("[ ] Nessun professore da migrare")
        return
    
    count = 0
    for prof_json in prof_data:
        # Controlla se il professore esiste già (basato su nome, materia, scuola)
        existing = Professor.query.filter_by(
            nome=prof_json.get('nome', ''),
            materia=prof_json.get('materia', ''),
            scuola=prof_json.get('scuola', '')
        ).first()
        
        if existing:
            print(f"[ ] Professore {prof_json.get('nome')} già esiste, salto...")
            continue
        
        prof = Professor(
            nome=prof_json.get('nome', ''),
            materia=prof_json.get('materia', ''),
            scuola=prof_json.get('scuola', ''),
            istituto=prof_json.get('istituto', ''),
            descrizione=prof_json.get('descrizione', ''),
            profilo_pubblico=prof_json.get('profilo_pubblico', False),
            avatar_file=prof_json.get('avatar_file', ''),
            materie_extra=json.dumps(prof_json.get('materie_extra', []))
        )
        db.session.add(prof)
        count += 1
    
    try:
        db.session.commit()
        print(f"[✓] Migrati {count} professori")
    except Exception as e:
        db.session.rollback()
        print(f"[!] Errore nella migrazione professori: {e}")

def migrate_reviews(reviews_data):
    """Migra le recensioni dal JSON al database"""
    if not reviews_data:
        print("[ ] Nessuna recensione da migrare")
        return
    
    count = 0
    for review_json in reviews_data:
        # Evita duplicati basati su id o combinazione username+prof+timestamp
        existing = None
        if review_json.get('id'):
            existing = Review.query.filter_by(id=review_json['id']).first()
        
        if not existing and review_json.get('username') and review_json.get('nomeProfRec'):
            existing = Review.query.filter_by(
                username=review_json['username'],
                nomeProfRec=review_json['nomeProfRec']
            ).first()
        
        if existing:
            print(f"[ ] Recensione {review_json.get('id')} già esiste, salto...")
            continue
        
        review = Review(
            id=review_json.get('id'),
            username=review_json.get('username', ''),
            nomeProfRec=review_json.get('nomeProfRec', ''),
            scuola=review_json.get('scuola', ''),
            recensione=review_json.get('recensione', ''),
            likes=review_json.get('likes', 0),
            dislikes=review_json.get('dislikes', 0),
            user_likes=review_json.get('user_likes', []),
            user_dislikes=review_json.get('user_dislikes', []),
            commenti=review_json.get('commenti', []),
            is_anonymous=review_json.get('is_anonymous', False),
            professor_id=review_json.get('professor_id')
        )
        
        # Gestisci timestamp
        timestamp_str = review_json.get('timestamp')
        if timestamp_str:
            try:
                review.timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            except:
                review.timestamp = datetime.now()
        else:
            review.timestamp = datetime.now()
        
        db.session.add(review)
        count += 1
    
    try:
        db.session.commit()
        print(f"[✓] Migrati {count} recensioni")
    except Exception as e:
        db.session.rollback()
        print(f"[!] Errore nella migrazione recensioni: {e}")

def migrate_votes(votes_data):
    """Migra i voti dal JSON al database"""
    if not votes_data:
        print("[ ] Nessun voto da migrare")
        return
    
    count = 0
    for vote_json in votes_data:
        vote = Vote(
            username=vote_json.get('username', ''),
            voto=vote_json.get('voto', ''),
            nomeProf=vote_json.get('nomeProf', ''),
            materia=vote_json.get('materia', ''),
            scuola=vote_json.get('scuola', '')
        )
        
        # Gestisci timestamp
        timestamp_str = vote_json.get('timestamp')
        if timestamp_str:
            try:
                vote.timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            except:
                vote.timestamp = datetime.now()
        
        db.session.add(vote)
        count += 1
    
    try:
        db.session.commit()
        print(f"[✓] Migrati {count} voti")
    except Exception as e:
        db.session.rollback()
        print(f"[!] Errore nella migrazione voti: {e}")

def migrate_tickets(tickets_data):
    """Migra i ticket dal JSON al database"""
    if not tickets_data:
        print("[ ] Nessun ticket da migrare")
        return
    
    count = 0
    for ticket_json in tickets_data:
        # Controlla se il ticket esiste già
        existing = None
        if ticket_json.get('id'):
            existing = Ticket.query.filter_by(id=ticket_json['id']).first()
        
        if existing:
            print(f"[ ] Ticket {ticket_json.get('id')} già esiste, salto...")
            continue
        
        ticket = Ticket(
            id=ticket_json.get('id'),
            utente=ticket_json.get('utente', ''),
            oggetto=ticket_json.get('oggetto', ''),
            messaggio=ticket_json.get('messaggio', ''),
            priorita=ticket_json.get('priorita', 'media'),
            stato=ticket_json.get('stato', 'aperto'),
            admin_assegnato=ticket_json.get('admin_assegnato', ''),
            risposte=ticket_json.get('risposte', [])
        )
        
        # Gestisci data_apertura
        ts_str = ticket_json.get('data_apertura')
        if ts_str:
            try:
                ticket.data_apertura = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            except:
                ticket.data_apertura = datetime.now()
        
        # Gestisci data_chiusura
        ts_str = ticket_json.get('data_chiusura')
        if ts_str:
            try:
                ticket.data_chiusura = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            except:
                pass
        
        db.session.add(ticket)
        count += 1
    
    try:
        db.session.commit()
        print(f"[✓] Migrati {count} ticket")
    except Exception as e:
        db.session.rollback()
        print(f"[!] Errore nella migrazione ticket: {e}")

def migrate_reports(reports_data):
    """Migra le segnalazioni dal JSON al database"""
    if not reports_data:
        print("[ ] Nessuna segnalazione da migrare")
        return
    
    count = 0
    for report_json in reports_data:
        report = Report(
            id=report_json.get('id'),
            reporter_username=report_json.get('reporter_username', ''),
            content_type=report_json.get('content_type', ''),
            content_id=report_json.get('content_id'),
            reason=report_json.get('reason', ''),
            status=report_json.get('status', 'pending')
        )
        
        # Gestisci timestamp
        ts_str = report_json.get('timestamp')
        if ts_str:
            try:
                report.timestamp = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            except:
                report.timestamp = datetime.now()
        
        db.session.add(report)
        count += 1
    
    try:
        db.session.commit()
        print(f"[✓] Migrati {count} segnalazioni")
    except Exception as e:
        db.session.rollback()
        print(f"[!] Errore nella migrazione segnalazioni: {e}")

def migrate_notices(notices_data):
    """Migra gli avvisi dal JSON al database"""
    if not notices_data:
        print("[ ] Nessun avviso da migrare")
        return
    
    count = 0
    for notice_json in notices_data:
        notice = Notice(
            id=notice_json.get('id'),
            title=notice_json.get('title', ''),
            content=notice_json.get('content', ''),
            type=notice_json.get('type', 'info'),
            active=notice_json.get('active', True)
        )
        
        # Gestisci expires_at
        expires_str = notice_json.get('expires_at')
        if expires_str:
            try:
                notice.expires_at = datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S")
            except:
                pass
        
        db.session.add(notice)
        count += 1
    
    try:
        db.session.commit()
        print(f"[✓] Migrati {count} avvisi")
    except Exception as e:
        db.session.rollback()
        print(f"[!] Errore nella migrazione avvisi: {e}")

def migrate_notifications(notif_data):
    """Migra le notifiche dal JSON al database"""
    if not notif_data:
        print("[ ] Nessuna notifica da migrare")
        return
    
    count = 0
    for notif_json in notif_data:
        # Controlla se la notifica esiste già
        existing = None
        if notif_json.get('id'):
            existing = Notification.query.filter_by(id=notif_json['id']).first()
        
        if existing:
            print(f"[ ] Notifica {notif_json.get('id')} già esiste, salto...")
            continue
        
        notification = Notification(
            id=notif_json.get('id'),
            utente=notif_json.get('utente', ''),
            tipo=notif_json.get('tipo', ''),
            titolo=notif_json.get('titolo', ''),
            messaggio=notif_json.get('messaggio', ''),
            link=notif_json.get('link', ''),
            letta=notif_json.get('letta', False)
        )
        
        # Gestisci data
        ts_str = notif_json.get('data')
        if ts_str:
            try:
                notification.data = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            except:
                notification.data = datetime.now()
        
        # Gestisci data_lettura
        ts_str = notif_json.get('data_lettura')
        if ts_str:
            try:
                notification.data_lettura = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            except:
                pass
        
        db.session.add(notification)
        count += 1
    
    try:
        db.session.commit()
        print(f"[✓] Migrati {count} notifiche")
    except Exception as e:
        db.session.rollback()
        print(f"[!] Errore nella migrazione notifiche: {e}")

def migrate_audit_logs(audit_data):
    """Migra i log di audit dal JSON al database"""
    if not audit_data:
        print("[ ] Nessun log audit da migrare")
        return
    
    count = 0
    for audit_json in audit_data:
        # Controlla se il log esiste già
        existing = None
        if audit_json.get('id'):
            existing = AuditLog.query.filter_by(id=audit_json['id']).first()
        
        if existing:
            print(f"[ ] Log audit {audit_json.get('id')} già esiste, salto...")
            continue
        
        audit = AuditLog(
            id=audit_json.get('id'),
            azione=audit_json.get('azione', ''),
            esito=audit_json.get('esito', 'ok'),
            attore=audit_json.get('attore', ''),
            target=audit_json.get('target', ''),
            ip=audit_json.get('ip', ''),
            user_agent=audit_json.get('user_agent', ''),
            dettagli=audit_json.get('dettagli', {})
        )
        
        # Gestisci timestamp
        ts_str = audit_json.get('timestamp')
        if ts_str:
            try:
                audit.timestamp = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            except:
                audit.timestamp = datetime.now()
        
        db.session.add(audit)
        count += 1
    
    try:
        db.session.commit()
        print(f"[✓] Migrati {count} log audit")
    except Exception as e:
        db.session.rollback()
        print(f"[!] Errore nella migrazione log audit: {e}")

def migrate_password_recovery(recovery_data):
    """Migra le richieste di recupero password dal JSON al database"""
    if not recovery_data:
        print("[ ] Nessuna richiesta di recupero password da migrare")
        return
    
    count = 0
    for recovery_json in recovery_data:
        # Controlla se la richiesta esiste già
        existing = None
        if recovery_json.get('id'):
            existing = PasswordRecovery.query.filter_by(id=recovery_json['id']).first()
        
        if existing:
            print(f"[ ] Recupero password {recovery_json.get('id')} già esiste, salto...")
            continue
        
        recovery = PasswordRecovery(
            id=recovery_json.get('id'),
            username=recovery_json.get('username', ''),
            codice=recovery_json.get('codice', ''),
            attempts=recovery_json.get('attempts', 0),
            usato=recovery_json.get('usato', False)
        )
        
        # Gestisci data_richiesta
        ts_str = recovery_json.get('data_richiesta')
        if ts_str:
            try:
                recovery.data_richiesta = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            except:
                recovery.data_richiesta = datetime.now()
        
        # Gestisci expires_at
        expires_str = recovery_json.get('expires_at')
        if expires_str:
            try:
                recovery.expires_at = datetime.strptime(expires_str, "%Y-%m-%d %H:%M:%S")
            except:
                pass
        
        db.session.add(recovery)
        count += 1
    
    try:
        db.session.commit()
        print(f"[✓] Migrati {count} recuperi password")
    except Exception as e:
        db.session.rollback()
        print(f"[!] Errore nella migrazione recuperi password: {e}")

def migrate_registrations(reg_data):
    """Migra le registrazioni dal JSON al database"""
    if not reg_data:
        print("[ ] Nessuna registrazione da migrare")
        return
    
    count = 0
    for reg_json in reg_data:
        # Controlla se la registrazione esiste già
        existing = None
        if reg_json.get('id'):
            existing = RegistrationRequest.query.filter_by(id=reg_json['id']).first()
        
        if existing:
            print(f"[ ] Registrazione {reg_json.get('id')} già esiste, salto...")
            continue
        
        reg = RegistrationRequest(
            id=reg_json.get('id'),
            username=reg_json.get('username', ''),
            password=reg_json.get('password', ''),
            email=reg_json.get('email', ''),
            nome_cognome=reg_json.get('nome_cognome', ''),
            scuola=reg_json.get('scuola', ''),
            stato=reg_json.get('stato', 'in_attesa'),
            admin_note=reg_json.get('admin_note', '')
        )
        
        # Gestisci data_registrazione
        ts_str = reg_json.get('data_registrazione')
        if ts_str:
            try:
                reg.data_registrazione = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            except:
                reg.data_registrazione = datetime.now()
        
        # Gestisci data_approvazione
        ts_str = reg_json.get('data_approvazione')
        if ts_str:
            try:
                reg.data_approvazione = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            except:
                pass
        
        db.session.add(reg)
        count += 1
    
    try:
        db.session.commit()
        print(f"[✓] Migrati {count} registrazioni")
    except Exception as e:
        db.session.rollback()
        print(f"[!] Errore nella migrazione registrazioni: {e}")

def migrate_sessions(session_data):
    """Migra le sessioni dal JSON al database"""
    if not session_data:
        print("[ ] Nessuna sessione da migrare")
        return
    
    count = 0
    for session_json in session_data:
        # Controlla se la sessione esiste già (per session_id)
        existing = None
        if session_json.get('session_id'):
            existing = SessionLog.query.filter_by(session_id=session_json['session_id']).first()
        
        if existing:
            print(f"[ ] Sessione {session_json.get('session_id')[:20]}... già esiste, salto...")
            continue
        
        sess = SessionLog(
            id=session_json.get('id'),
            session_id=session_json.get('session_id', ''),
            username=session_json.get('username', ''),
            ip=session_json.get('ip', ''),
            user_agent=session_json.get('user_agent', '')
        )
        
        # Gestisci login_time
        ts_str = session_json.get('login_time')
        if ts_str:
            try:
                sess.login_time = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            except:
                sess.login_time = datetime.now()
        
        # Gestisci last_activity
        ts_str = session_json.get('last_activity')
        if ts_str:
            try:
                sess.last_activity = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            except:
                sess.last_activity = datetime.now()
        
        db.session.add(sess)
        count += 1
    
    try:
        db.session.commit()
        print(f"[✓] Migrati {count} sessioni")
    except Exception as e:
        db.session.rollback()
        print(f"[!] Errore nella migrazione sessioni: {e}")

def migrate_chat(chat_data):
    """Migra la chat dal JSON - Nota: la chat potrebbe richiedere una struttura speciale"""
    if not chat_data:
        print("[ ] Nessun messaggio chat da migrare")
        return
    
    print("[!] La migrazione della chat richiede una tabella dedicata - saltata per ora")
    # Qui si potrebbe implementare una tabella ChatMessage se necessaria

def migrate_preferenze_notifiche(pref_data):
    """Migra le preferenze di notifica dal JSON al database"""
    if not pref_data:
        print("[ ] Nessuna preferenza notifica da migrare")
        return
    
    count = 0
    for pref_json in pref_data:
        # Controlla se la preferenza esiste già
        existing = None
        if pref_json.get('username'):
            existing = NotificationPreference.query.filter_by(username=pref_json['username']).first()
        
        if existing:
            print(f"[ ] Preferenza per {pref_json.get('username')} già esiste, salto...")
            continue
        
        pref = NotificationPreference(
            id=pref_json.get('id'),
            username=pref_json.get('username', ''),
            canale_in_app=pref_json.get('canale_in_app', True),
            canale_email=pref_json.get('canale_email', False),
            tipi=pref_json.get('tipi', {'ticket': True, 'registrazione': True, 'segnalazione': True, 'sistema': True, 'comment_reply': True, 'preferiti': True})
        )
        db.session.add(pref)
        count += 1
    
    try:
        db.session.commit()
        print(f"[✓] Migrati {count} preferenze notifica")
    except Exception as e:
        db.session.rollback()
        print(f"[!] Errore nella migrazione preferenze notifica: {e}")

def migrate_privacy_requests(priv_data):
    """Migra le richieste privacy dal JSON al database"""
    if not priv_data:
        print("[ ] Nessuna richiesta privacy da migrare")
        return
    
    count = 0
    for priv_json in priv_data:
        # Controlla se la richiesta esiste già
        existing = None
        if priv_json.get('id'):
            existing = PrivacyRequest.query.filter_by(id=priv_json['id']).first()
        
        if existing:
            print(f"[ ] Richiesta privacy {priv_json.get('id')} già esiste, salto...")
            continue
        
        priv = PrivacyRequest(
            id=priv_json.get('id'),
            username=priv_json.get('username', ''),
            motivo=priv_json.get('motivo', ''),
            stato=priv_json.get('stato', 'pending'),
            admin_note=priv_json.get('admin_note', '')
        )
        
        # Gestisci data_richiesta
        ts_str = priv_json.get('data_richiesta')
        if ts_str:
            try:
                priv.data_richiesta = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            except:
                priv.data_richiesta = datetime.now()
        
        # Gestisci data_chiusura
        ts_str = priv_json.get('data_chiusura')
        if ts_str:
            try:
                priv.data_chiusura = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            except:
                pass
        
        db.session.add(priv)
        count += 1
    
    try:
        db.session.commit()
        print(f"[✓] Migrati {count} richieste privacy")
    except Exception as e:
        db.session.rollback()
        print(f"[!] Errore nella migrazione richieste privacy: {e}")

def main():
    """Funzione principale di migrazione"""
    print("=" * 60)
    print("MIGRAZIONE DATI DA JSON A DATABASE SQLITE")
    print("=" * 60)
    
    # Inizializza il database
    with app.app_context():
        print("\n[1] Inizializzazione database...")
        db.create_all()
        print("[✓] Database inizializzato")
        
        print("\n[2] Caricamento dati dai file JSON...")
        
        # Carica tutti i file JSON
        utenti_data = load_json_file('utenti.json')
        professori_data = load_json_file('professori.json')
        recensioni_data = load_json_file('recensioni.json')
        voti_data = load_json_file('voti.json')
        ticket_data = load_json_file('ticket.json')
        segnalazioni_data = load_json_file('segnalazioni.json')
        avvisi_data = load_json_file('avvisi.json')
        notifiche_data = load_json_file('notifiche.json')
        audit_data = load_json_file('audit_log.json')
        recupero_data = load_json_file('recupero_password.json')
        registrazioni_data = load_json_file('registrazioni.json')
        sessioni_data = load_json_file('sessioni.json')
        chat_data = load_json_file('chat.json')
        preferenze_data = load_json_file('preferenze_notifiche.json')
        privacy_data = load_json_file('privacy_requests.json')
        
        print("\n[3] Migrazione dati nel database...")
        
        # Esegue le migrazioni
        migrate_users(utenti_data)
        migrate_professors(professori_data)
        migrate_reviews(recensioni_data)
        migrate_votes(voti_data)
        migrate_tickets(ticket_data)
        migrate_reports(segnalazioni_data)
        migrate_notices(avvisi_data)
        migrate_notifications(notifiche_data)
        migrate_audit_logs(audit_data)
        migrate_password_recovery(recupero_data)
        migrate_registrations(registrazioni_data)
        migrate_sessions(sessioni_data)
        migrate_chat(chat_data)
        migrate_preferenze_notifiche(preferenze_data)
        migrate_privacy_requests(privacy_data)
        
        print("\n" + "=" * 60)
        print("MIGRAZIONE COMPLETATA CON SUCCESSO!")
        print("=" * 60)
        print("\nProssimi passi:")
        print("1. Verifica che tutti i dati siano stati migrati correttamente")
        print("2. Testa l'applicazione per assicurarti che funzioni con il database")
        print("3. Una volta confermato, puoi eliminare i file JSON")
        print("\nNota: I file JSON sono stati mantenuti come backup.")
        print("      Puoi eliminarli manualmente dopo aver verificato la migrazione.")

if __name__ == '__main__':
    main()
