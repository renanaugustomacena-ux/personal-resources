# Autenticazione LDAP e Active Directory in Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 5 — Operativita post-migrazione · Modulo 12.2 (segue 12.1 cert TLS, vedi `../00-SYLLABUS.md` §5)
> **Prerequisiti:** modulo 12.1 (TLS — necessario per LDAPS); modulo 09.4 (DC AD); concetti LDAP (bind, schema, filter), Kerberos basics, RFC 4511, AD specifici.
> **Obiettivi di arrivo.** Al termine del modulo lo studente sara in grado di:
> 1. configurare un **realm AD** in Proxmox: server, base DN, bind user (account di servizio dedicato), filter, sync schedule;
> 2. configurare un **realm LDAP generico** (OpenLDAP, FreeIPA, 389 Directory Server) con StartTLS o LDAPS;
> 3. implementare **LDAPS pinning**: validazione cert, anchor del CA interno, prevenzione MITM (StartTLS downgrade attack);
> 4. configurare **RADIUS 2FA fallback** per scenari dove AD MFA non e disponibile;
> 5. mappare gruppi AD/LDAP a ruoli Proxmox (sync con `realm sync` o `pveum`);
> 6. mantenere **un account locale di emergenza** in `pam` o realm `pve` per recovery quando AD non risponde;
> 7. tuning dei timeout, group cache TTL, nested-group sync;
> 8. confrontare con vSphere SSO (PSC), riconoscere feature gap (no Kerberos passthrough nativo, no SAML diretto).
> **Tempo stimato:** lettura 60-80 min · lab 240-300 min (configurazione AD test + sync + 2FA RADIUS)
> **Livello:** competent → proficient (Dreyfus 3 → 4)
> **Ultimo aggiornamento:** 2026-04-27
> **Versioni di riferimento:** Proxmox VE 8.x; AD 2019/2022/2025; OpenLDAP 2.6+; FreeIPA 4.x; FreeRADIUS 3.x.

## Mappa concettuale

```
+============================================================+
|     Realm in Proxmox: tipi e flusso autenticazione         |
+============================================================+
|                                                            |
|   TIPI DI REALM                                            |
|                                                            |
|   pve         interno Proxmox (file flat in /etc/pve)      |
|   pam         Linux PAM (utenti SO sui nodi)               |
|   ad          Active Directory (LDAP+specifiche AD)        |
|   ldap        LDAP generico (OpenLDAP, FreeIPA, 389DS)     |
|   openid      OIDC (Keycloak, Azure AD via OIDC, Google)   |
|                                                            |
|   FLUSSO LOGIN AD                                          |
|   1. Utente: john@DOMAIN.LOCAL / password                  |
|   2. Proxmox cerca realm "ad" matching DOMAIN.LOCAL        |
|   3. Bind con account servizio (svc-proxmox)               |
|      → connessione LDAPS o StartTLS                        |
|   4. Search user `(&(objectClass=user)(sAMAccountName=john))`|
|   5. Bind come john con la password fornita                |
|   6. Se OK: Proxmox emette ticket session                  |
|   7. Lookup gruppi: `(memberOf=...)` per role mapping      |
|                                                            |
|   SECURITY CHECKLIST                                       |
|   - LDAPS (port 636) o StartTLS (port 389 + STARTTLS)      |
|   - Verifica cert del DC (no `verify=0`!)                  |
|   - Account servizio dedicato, no admin privileges         |
|   - Filter restrittivo (es. solo gruppo `pve-users`)       |
|   - Audit log delle sessioni                               |
|   - Account locale break-glass in pam/pve                  |
|                                                            |
+============================================================+
```

Idee guida del modulo:

1. **Mai disabilitare verifica cert LDAPS in produzione.** "Funziona di piu" = "MITM possibile". Se cert AD non e trusted, importare CA root nel trust store di Proxmox (`/etc/pve/local/pveproxy-ssl.pem` o trust system-wide).
2. **Account locale break-glass e mandatory.** Se l'AD cade (rete, DC, password corrotta service account), serve almeno un admin che possa entrare. Account `root@pam` o `admin@pve` con password salvata in vault offline.
3. **Sync gruppi vs sync utenti: scegli cosa autorizzare.** Sync solo gruppi → assegnazione ruoli a livello gruppo (preferito, manutenzione facile). Sync utenti → ruoli per utente (solo per casi speciali).
4. **Group cache TTL e tradeoff freshness vs perf.** Default ~1h: cambi su gruppi AD si propagano fino a 1h dopo. Per aud trail compliance: TTL 5-15 min con accettazione del costo network LDAP.
5. **2FA via RADIUS funziona ma e legacy.** Per nuovi deployment: OIDC con IdP (Keycloak, Azure AD) supporta MFA nativamente. RADIUS 2FA e fallback per ambienti legacy senza upgrade path.

---

## Introduzione

L'integrazione con directory service aziendali e un requisito fondamentale per qualsiasi ambiente di virtualizzazione enterprise. In VMware vCenter, l'integrazione con Active Directory avviene attraverso il componente SSO (Single Sign-On) e supporta nativamente LDAP, Active Directory e, nelle versioni piu recenti, anche provider di identita OIDC. In Proxmox VE, l'integrazione avviene attraverso il concetto di **realm**, che permette di collegare diverse sorgenti di autenticazione al sistema di gestione degli accessi.

Questo documento fornisce una guida operativa completa per l'integrazione di Proxmox VE con Active Directory e LDAP generico, coprendo ogni fase dalla configurazione iniziale alla risoluzione dei problemi, con un confronto diretto con l'equivalente VMware.

---

## 1. Architettura dell'Autenticazione Esterna

### 1.1 Flusso di Autenticazione

```
Utente (GUI/API/CLI)
        |
        v
   Proxmox VE API
        |
        v
   Identificazione Realm (username@realm)
        |
        +---> PAM (utenti di sistema)
        |
        +---> PVE (utenti locali Proxmox)
        |
        +---> LDAP (directory LDAP generico)
        |
        +---> AD (Active Directory)
        |
        +---> OpenID Connect (provider OIDC)
        |
        v
   Autenticazione riuscita?
        |
        +---> Si: Ticket PVE emesso, verifica ACL per autorizzazione
        |
        +---> No: Errore di autenticazione
```

### 1.2 Dove Sono Memorizzate le Configurazioni

| File | Contenuto | Replicato nel Cluster |
|------|-----------|-----------------------|
| `/etc/pve/domains.cfg` | Configurazione dei realm | Si (pmxcfs) |
| `/etc/pve/user.cfg` | Utenti, gruppi, ACL | Si (pmxcfs) |
| `/etc/pve/priv/shadow.cfg` | Password utenti PVE | Si (pmxcfs) |
| `/etc/pve/priv/tfa.cfg` | Configurazioni 2FA | Si (pmxcfs) |

### 1.3 Protocolli Supportati

| Protocollo | Porta Default | Sicurezza | Uso |
|-----------|---------------|-----------|-----|
| LDAP | 389 | Testo in chiaro (non usare!) | Solo test |
| LDAPS | 636 | TLS nativo | Produzione |
| LDAP + StartTLS | 389 | TLS negoziato | Alternativa a LDAPS |
| Global Catalog | 3268 | Testo in chiaro | Multi-dominio (non sicuro) |
| Global Catalog SSL | 3269 | TLS nativo | Multi-dominio sicuro |

---

## 2. Configurazione Active Directory

### 2.1 Prerequisiti

Prima di configurare l'integrazione AD su Proxmox VE, verificare i seguenti prerequisiti:

**Sul Domain Controller:**

```powershell
# Creare un account di servizio dedicato per Proxmox
New-ADUser -Name "svc-proxmox" `
  -SamAccountName "svc-proxmox" `
  -UserPrincipalName "svc-proxmox@studio-lavoro.local" `
  -Path "OU=Service Accounts,DC=studio-lavoro,DC=local" `
  -AccountPassword (ConvertTo-SecureString "P@ssw0rd_Compl3ss@!" -AsPlainText -Force) `
  -Enabled $true `
  -PasswordNeverExpires $true `
  -CannotChangePassword $true `
  -Description "Account di servizio per autenticazione Proxmox VE"

# Creare un gruppo per gli utenti Proxmox (opzionale, per filtrare)
New-ADGroup -Name "Proxmox-Users" `
  -GroupScope Global `
  -GroupCategory Security `
  -Path "OU=Groups,DC=studio-lavoro,DC=local" `
  -Description "Utenti autorizzati ad accedere a Proxmox VE"

# Creare gruppi per i ruoli
New-ADGroup -Name "Proxmox-Admins" -GroupScope Global -GroupCategory Security -Path "OU=Groups,DC=studio-lavoro,DC=local"
New-ADGroup -Name "Proxmox-VMOperators" -GroupScope Global -GroupCategory Security -Path "OU=Groups,DC=studio-lavoro,DC=local"
New-ADGroup -Name "Proxmox-Developers" -GroupScope Global -GroupCategory Security -Path "OU=Groups,DC=studio-lavoro,DC=local"
New-ADGroup -Name "Proxmox-Auditors" -GroupScope Global -GroupCategory Security -Path "OU=Groups,DC=studio-lavoro,DC=local"

# Aggiungere utenti ai gruppi
Add-ADGroupMember -Identity "Proxmox-Admins" -Members "admin1","admin2"
Add-ADGroupMember -Identity "Proxmox-VMOperators" -Members "operatore1","operatore2"
```

**Sul nodo Proxmox VE:**

```bash
# Verificare la risoluzione DNS del dominio AD
nslookup studio-lavoro.local
nslookup dc01.studio-lavoro.local
nslookup dc02.studio-lavoro.local

# Verificare la raggiungibilita dei Domain Controller
ping -c 3 dc01.studio-lavoro.local
ping -c 3 dc02.studio-lavoro.local

# Verificare la connettivita sulle porte LDAPS
openssl s_client -connect dc01.studio-lavoro.local:636 -showcerts </dev/null 2>/dev/null | head -20

# Verificare la sincronizzazione oraria (critica per Kerberos)
timedatectl status
chronyc tracking

# Se necessario, configurare il NTP
cat > /etc/chrony/sources.d/ad-ntp.conf << 'EOF'
server dc01.studio-lavoro.local iburst
server dc02.studio-lavoro.local iburst
EOF
systemctl restart chrony
```

### 2.2 Configurazione del Realm AD tramite CLI

```bash
# Configurazione completa del realm Active Directory
pveum realm add ad-aziendale --type ad \
  --domain "studio-lavoro.local" \
  --server1 "dc01.studio-lavoro.local" \
  --server2 "dc02.studio-lavoro.local" \
  --port 636 \
  --secure 1 \
  --default 0 \
  --comment "Active Directory Aziendale - studio-lavoro.local" \
  --tfa type=totp \
  --bind_dn "CN=svc-proxmox,OU=Service Accounts,DC=studio-lavoro,DC=local" \
  --group_dn "OU=Groups,DC=studio-lavoro,DC=local" \
  --group_filter "(|(CN=Proxmox-Admins)(CN=Proxmox-VMOperators)(CN=Proxmox-Developers)(CN=Proxmox-Auditors))" \
  --sync_defaults_options "scope=subtree,enable-new=1,full=1,purge=1"

# Impostare la password di bind
pveum realm set ad-aziendale --password
# Inserire: P@ssw0rd_Compl3ss@!
```

### 2.3 Configurazione tramite GUI

Procedura dalla web GUI:

1. Navigare a **Datacenter -> Permissions -> Realms**
2. Cliccare su **Add -> Active Directory Server**
3. Compilare i campi:

| Campo | Valore | Note |
|-------|--------|------|
| Realm | `ad-aziendale` | Identificativo univoco |
| Domain | `studio-lavoro.local` | FQDN del dominio AD |
| Server | `dc01.studio-lavoro.local` | Domain Controller primario |
| Fallback Server | `dc02.studio-lavoro.local` | Domain Controller secondario |
| Port | `636` | LDAPS |
| SSL | `checked` | Abilitare per LDAPS |
| Bind User | `CN=svc-proxmox,OU=Service Accounts,DC=studio-lavoro,DC=local` | Distinguished Name completo |
| Bind Password | `***` | Password dell'account di servizio |
| Base Domain DN | (vuoto, usa domain) | Compilare se diverso dal domain |
| User Attribute Name | `sAMAccountName` | Attributo di login |
| Default | `unchecked` | Non impostare come default all'inizio |
| TFA | `TOTP` | Opzionale, per richiedere 2FA |
| Comment | `Active Directory Aziendale` | Descrizione |

4. Tab **Sync Options**:

| Campo | Valore |
|-------|--------|
| Bind User | (come sopra) |
| Group DN | `OU=Groups,DC=studio-lavoro,DC=local` |
| Group Name Attribute | `cn` |
| Group Filter | `(objectClass=group)` |
| User Filter | `(&(objectClass=user)(memberOf=CN=Proxmox-Users,OU=Groups,DC=studio-lavoro,DC=local))` |
| Scope | `subtree` |
| Enable New | `checked` |
| Full | `checked` |

### 2.4 Configurazione del File domains.cfg Direttamente

```bash
# Il file /etc/pve/domains.cfg contiene la configurazione dei realm
# Visualizzare la configurazione attuale
cat /etc/pve/domains.cfg
```

Esempio di configurazione completa:

```
ad: ad-aziendale
    bind_dn CN=svc-proxmox,OU=Service Accounts,DC=studio-lavoro,DC=local
    comment Active Directory Aziendale
    default 0
    domain studio-lavoro.local
    group_dn OU=Groups,DC=studio-lavoro,DC=local
    group_filter (|(CN=Proxmox-Admins)(CN=Proxmox-VMOperators)(CN=Proxmox-Developers)(CN=Proxmox-Auditors))
    port 636
    secure 1
    server1 dc01.studio-lavoro.local
    server2 dc02.studio-lavoro.local
    sync_defaults_options scope=subtree,enable-new=1,full=1,purge=1
    tfa type=totp

ldap: ldap-openldap
    base_dn dc=studio-lavoro,dc=local
    bind_dn cn=proxmox-bind,ou=service-accounts,dc=studio-lavoro,dc=local
    comment OpenLDAP Server
    port 636
    secure 1
    server1 ldap.studio-lavoro.local
    user_attr uid
```

---

## 3. Configurazione LDAP Generico

### 3.1 OpenLDAP / FreeIPA

```bash
# Configurare un realm LDAP generico
pveum realm add ldap-openldap --type ldap \
  --base_dn "dc=studio-lavoro,dc=local" \
  --user_attr "uid" \
  --server1 "ldap01.studio-lavoro.local" \
  --server2 "ldap02.studio-lavoro.local" \
  --port 636 \
  --secure 1 \
  --default 0 \
  --comment "OpenLDAP Server" \
  --bind_dn "cn=proxmox-bind,ou=service-accounts,dc=studio-lavoro,dc=local" \
  --group_dn "ou=groups,dc=studio-lavoro,dc=local" \
  --group_filter "(objectClass=posixGroup)" \
  --group_name_attr "cn" \
  --sync_defaults_options "scope=subtree,enable-new=1"

# Impostare la password di bind
pveum realm set ldap-openldap --password
```

### 3.2 Differenze tra LDAP e AD in Proxmox

| Aspetto | Realm AD | Realm LDAP |
|---------|----------|------------|
| Tipo | `ad` | `ldap` |
| User attribute default | `sAMAccountName` | Deve essere specificato (`uid`, `cn`) |
| Group filter | `(objectClass=group)` | `(objectClass=posixGroup)` o `(objectClass=groupOfNames)` |
| Domain | FQDN del dominio AD | Non applicabile |
| Base DN | Derivato dal domain | Deve essere specificato |
| Supporto UPN | Si (`user@domain`) | No |
| Nested groups | Si | Dipende dal server LDAP |
| Global Catalog | Si (porta 3268/3269) | No |

### 3.3 Configurazione per FreeIPA

```bash
pveum realm add freeipa --type ldap \
  --base_dn "cn=users,cn=accounts,dc=ipa,dc=studio-lavoro,dc=local" \
  --user_attr "uid" \
  --server1 "ipa01.studio-lavoro.local" \
  --port 636 \
  --secure 1 \
  --bind_dn "uid=proxmox-bind,cn=users,cn=accounts,dc=ipa,dc=studio-lavoro,dc=local" \
  --group_dn "cn=groups,cn=accounts,dc=ipa,dc=studio-lavoro,dc=local" \
  --group_filter "(objectClass=posixGroup)" \
  --group_name_attr "cn" \
  --comment "FreeIPA Server"
```

---

## 4. Sincronizzazione Utenti e Gruppi

### 4.1 Sincronizzazione Manuale

```bash
# Sincronizzazione completa (aggiunge nuovi utenti, aggiorna esistenti)
pveum realm sync ad-aziendale --scope full --enable-new 1

# Sincronizzazione solo degli utenti esistenti in Proxmox
pveum realm sync ad-aziendale --scope existing

# Sincronizzazione con eliminazione degli utenti rimossi da AD
pveum realm sync ad-aziendale --scope full --enable-new 1 --purge 1

# Dry-run (mostra cosa verrebbe fatto senza applicare)
pveum realm sync ad-aziendale --scope full --enable-new 1 --dry-run 1
```

### 4.2 Sincronizzazione Automatica (Scheduled)

```bash
# Configurare un job di sincronizzazione automatica dalla GUI:
# Datacenter -> Permissions -> Realms -> [realm] -> Sync Jobs

# Oppure tramite CLI, creare un cron job:
cat > /etc/cron.d/proxmox-ad-sync << 'EOF'
# Sincronizzazione AD ogni 4 ore
0 */4 * * * root /usr/sbin/pveum realm sync ad-aziendale --scope full --enable-new 1 2>&1 | logger -t pve-ad-sync
EOF

# Oppure usare il sistema di sync job integrato di Proxmox
# Dalla GUI: Datacenter -> Permissions -> Realms -> ad-aziendale -> Sync Jobs -> Add
# Schedule: */4:00 (ogni 4 ore)
```

### 4.3 Mappatura Gruppi AD ai Ruoli Proxmox

Dopo la sincronizzazione, i gruppi AD appaiono come gruppi Proxmox. E necessario assegnare i ruoli:

```bash
# Prima, verificare i gruppi sincronizzati
pveum group list

# Mappare i gruppi AD ai ruoli Proxmox
# Gruppo Proxmox-Admins -> Ruolo Administrator su tutto
pveum aclmod / -group Proxmox-Admins -role Administrator

# Gruppo Proxmox-VMOperators -> Ruolo PVEVMAdmin sulle VM
pveum aclmod /vms -group Proxmox-VMOperators -role PVEVMAdmin

# Gruppo Proxmox-Developers -> Ruolo Developer sui pool sviluppo/test
pveum aclmod /pool/sviluppo -group Proxmox-Developers -role Developer
pveum aclmod /pool/test -group Proxmox-Developers -role PVEVMAdmin

# Gruppo Proxmox-Auditors -> Ruolo PVEAuditor su tutto
pveum aclmod / -group Proxmox-Auditors -role PVEAuditor

# Verificare le ACL
pveum acl list
```

### 4.4 Filtraggio Utenti con LDAP Filter

```bash
# Filtrare solo gli utenti membri di un gruppo specifico
pveum realm set ad-aziendale \
  --filter "(&(objectClass=user)(memberOf=CN=Proxmox-Users,OU=Groups,DC=studio-lavoro,DC=local))"

# Filtrare per OU specifica
pveum realm set ad-aziendale \
  --filter "(&(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))"
# L'ultimo filtro esclude gli account disabilitati in AD

# Filtrare utenti di gruppi multipli (OR)
pveum realm set ad-aziendale \
  --filter "(&(objectClass=user)(|(memberOf=CN=Proxmox-Admins,OU=Groups,DC=studio-lavoro,DC=local)(memberOf=CN=Proxmox-VMOperators,OU=Groups,DC=studio-lavoro,DC=local)(memberOf=CN=Proxmox-Developers,OU=Groups,DC=studio-lavoro,DC=local)))"
```

---

## 5. Verifica del Certificato per LDAPS

### 5.1 Importare il Certificato CA di Active Directory

```bash
# Scaricare il certificato CA root del dominio AD
# Metodo 1: Dal Domain Controller via browser
# https://dc01.studio-lavoro.local/certsrv

# Metodo 2: Estrarre il certificato con openssl
openssl s_client -connect dc01.studio-lavoro.local:636 -showcerts </dev/null 2>/dev/null | \
  openssl x509 -outform PEM > /usr/local/share/ca-certificates/ad-ca.crt

# Metodo 3: Se si ha accesso al DC, esportare il certificato
# certutil -ca.cert ad-root-ca.cer (sul Domain Controller)
# Copiare il file .cer sul nodo Proxmox e convertire:
openssl x509 -inform DER -in ad-root-ca.cer -out /usr/local/share/ca-certificates/ad-ca.crt

# Aggiornare il trust store di sistema
update-ca-certificates

# Verificare che il certificato sia stato aggiunto
ls -la /etc/ssl/certs/ | grep ad-ca

# Testare la connessione LDAPS con verifica del certificato
openssl s_client -connect dc01.studio-lavoro.local:636 -CApath /etc/ssl/certs/ </dev/null 2>&1 | grep "Verify return code"
# Output atteso: Verify return code: 0 (ok)
```

### 5.2 Verificare il Certificato del Domain Controller

```bash
# Verificare il certificato LDAPS del DC
openssl s_client -connect dc01.studio-lavoro.local:636 </dev/null 2>/dev/null | openssl x509 -noout -text | grep -A2 "Validity"

# Verificare la catena di certificazione completa
openssl s_client -connect dc01.studio-lavoro.local:636 -showcerts </dev/null 2>/dev/null

# Verificare il Subject Alternative Name (deve includere il FQDN del DC)
openssl s_client -connect dc01.studio-lavoro.local:636 </dev/null 2>/dev/null | openssl x509 -noout -ext subjectAltName
```

### 5.3 Configurazione Proxmox per la Verifica del Certificato

```bash
# Proxmox VE rispetta le CA di sistema (/etc/ssl/certs/)
# Se il certificato CA e stato importato correttamente, la verifica e automatica

# Per disabilitare la verifica del certificato (SOLO PER TEST!)
pveum realm set ad-aziendale --verify 0

# Riabilitare la verifica per produzione
pveum realm set ad-aziendale --verify 1

# Verificare l'impostazione
grep -A20 "ad: ad-aziendale" /etc/pve/domains.cfg
```

> **Importante per la sicurezza:** In produzione, la verifica del certificato LDAPS deve SEMPRE essere abilitata (`--verify 1` o non specificato, che e il default). Disabilitare la verifica espone a attacchi man-in-the-middle.

---

## 6. Test dell'Autenticazione

### 6.1 Test dalla CLI

```bash
# Testare l'autenticazione di un utente AD
pveum user list | grep "@ad-aziendale"

# Tentare il login via API
curl -k -d "username=mario.rossi@ad-aziendale" -d "password=LaPasswordDiMario" \
  https://localhost:8006/api2/json/access/ticket

# Se l'autenticazione ha successo, la risposta conterra un ticket PVE
# Esempio di risposta positiva:
# {"data":{"ticket":"PVE:mario.rossi@ad-aziendale:...","username":"mario.rossi@ad-aziendale",...}}

# Se fallisce:
# {"data":null}
```

### 6.2 Test dalla GUI

1. Aprire la GUI Proxmox: `https://pve-node01:8006`
2. Nel campo **Username**, inserire: `mario.rossi`
3. Nel campo **Password**, inserire la password AD
4. Nel menu a tendina **Realm**, selezionare: `ad-aziendale`
5. Se 2FA e attivo, inserire il codice TOTP
6. Cliccare **Login**

### 6.3 Verifica dei Log

```bash
# Verificare i log di autenticazione
journalctl -u pvedaemon --since "10 minutes ago" | grep -i "auth"

# Log dettagliati delle connessioni LDAP
journalctl -u pvedaemon --since "10 minutes ago" | grep -iE "(ldap|auth|realm)"

# Verificare i tentativi falliti
journalctl -u pvedaemon | grep "authentication failure"
```

---

## 7. Fallback all'Autenticazione Locale

### 7.1 Strategia di Fallback

E fondamentale mantenere sempre un metodo di accesso alternativo in caso di indisponibilita di Active Directory.

```bash
# Creare un account di emergenza nel realm PVE
pveum useradd emergency-admin@pve \
  -comment "Account di emergenza - Usare solo se AD non disponibile" \
  -email "admin@studio-lavoro.local"

pveum passwd emergency-admin@pve
# Impostare una password complessa e conservarla in un luogo sicuro

# Assegnare permessi di amministratore
pveum aclmod / -user emergency-admin@pve -role Administrator

# Configurare 2FA per l'account di emergenza
# (Dalla GUI, configurare TOTP e generare recovery keys)
```

### 7.2 Procedura di Accesso di Emergenza

| Passo | Azione | Note |
|-------|--------|------|
| 1 | Verificare che AD sia realmente non disponibile | `nslookup dc01.studio-lavoro.local` |
| 2 | Accedere alla GUI Proxmox | `https://pve-node01:8006` |
| 3 | Selezionare il realm **Proxmox VE authentication server** | Non selezionare AD |
| 4 | Inserire `emergency-admin` come username | Senza @pve |
| 5 | Inserire la password e il codice 2FA | |
| 6 | Documentare l'uso dell'account | Log nel sistema di ticketing |

### 7.3 Test Periodico del Fallback

```bash
# Creare un cron job per testare periodicamente l'accesso locale
cat > /usr/local/bin/test-local-auth.sh << 'SCRIPT'
#!/bin/bash
# Test autenticazione locale - eseguire settimanalmente

RESULT=$(curl -sk -d "username=emergency-admin@pve" -d "password=TEST_PLACEHOLDER" \
  https://localhost:8006/api2/json/access/ticket 2>&1)

if echo "$RESULT" | grep -q "ticket"; then
    echo "$(date): Autenticazione locale OK" >> /var/log/pve-auth-test.log
else
    echo "$(date): ERRORE - Autenticazione locale FALLITA!" >> /var/log/pve-auth-test.log
    # Inviare allarme
    echo "ALLARME: Autenticazione locale Proxmox fallita su $(hostname)" | \
      mail -s "PVE Auth Alert" admin@studio-lavoro.local
fi
SCRIPT

chmod +x /usr/local/bin/test-local-auth.sh
```

> **Nota:** Non memorizzare password reali negli script. Questo e un esempio concettuale. In produzione, usare un sistema di secrets management.

---

## 8. Troubleshooting Problemi AD

### 8.1 Problemi Comuni e Soluzioni

| Problema | Causa Probabile | Soluzione |
|----------|----------------|-----------|
| "authentication failure" | Password errata, account bloccato | Verificare credenziali, controllare AD |
| "connection refused" | DC non raggiungibile | Verificare rete, firewall, DNS |
| "certificate verify failed" | CA non importata o certificato scaduto | Importare CA, verificare date certificato |
| "invalid credentials" | Bind DN errato | Verificare il Distinguished Name completo |
| Utenti non sincronizzati | Filtro LDAP troppo restrittivo | Verificare e testare il filtro |
| Gruppi non visibili | Group DN errato | Verificare il percorso OU dei gruppi |
| Timeout di connessione | Problemi di rete o DNS | Testare connettivita e risoluzione DNS |
| "realm not found" | Realm non configurato o typo nel nome | Verificare `pveum realm list` |

### 8.2 Comandi Diagnostici

```bash
# --- Verifica DNS ---
# Risolvere il dominio AD
dig studio-lavoro.local
dig _ldap._tcp.studio-lavoro.local SRV

# Risolvere i Domain Controller
dig dc01.studio-lavoro.local
dig dc02.studio-lavoro.local

# --- Verifica Connettivita ---
# Testare la porta LDAPS
nc -zv dc01.studio-lavoro.local 636

# Testare con timeout
timeout 5 bash -c 'echo > /dev/tcp/dc01.studio-lavoro.local/636' && echo "OK" || echo "FAIL"

# --- Verifica LDAP ---
# Testare una ricerca LDAP con ldapsearch
apt install -y ldap-utils

# Ricerca con bind DN
ldapsearch -x -H ldaps://dc01.studio-lavoro.local:636 \
  -D "CN=svc-proxmox,OU=Service Accounts,DC=studio-lavoro,DC=local" \
  -W \
  -b "DC=studio-lavoro,DC=local" \
  "(sAMAccountName=mario.rossi)" \
  dn sAMAccountName memberOf

# Ricerca dei gruppi
ldapsearch -x -H ldaps://dc01.studio-lavoro.local:636 \
  -D "CN=svc-proxmox,OU=Service Accounts,DC=studio-lavoro,DC=local" \
  -W \
  -b "OU=Groups,DC=studio-lavoro,DC=local" \
  "(objectClass=group)" \
  dn cn member

# Verificare il bind dell'account di servizio
ldapwhoami -x -H ldaps://dc01.studio-lavoro.local:636 \
  -D "CN=svc-proxmox,OU=Service Accounts,DC=studio-lavoro,DC=local" \
  -W

# --- Verifica Certificati ---
# Visualizzare il certificato del DC
echo | openssl s_client -connect dc01.studio-lavoro.local:636 2>/dev/null | openssl x509 -noout -dates -subject -issuer

# Verificare la catena di certificazione
echo | openssl s_client -connect dc01.studio-lavoro.local:636 -CApath /etc/ssl/certs/ 2>&1 | grep -E "(Verify|Certificate chain)"

# --- Verifica Sincronizzazione Oraria ---
# La differenza oraria massima per Kerberos e 5 minuti
chronyc tracking
date
# Confrontare con il DC:
# net time /domain:studio-lavoro.local (su Windows)

# --- Log Proxmox ---
# Log di autenticazione dettagliati
journalctl -u pvedaemon -f --no-pager | grep -iE "(ldap|auth|ad-aziendale|realm)"

# Log del proxy web
journalctl -u pveproxy -f --no-pager | grep -i auth

# Tutti i log relativi ad un utente specifico
journalctl | grep "mario.rossi"
```

### 8.3 Debug Avanzato

```bash
# Abilitare il debug LDAP in Proxmox (temporaneo)
# Modificare /etc/default/pvedaemon
echo 'PVE_LOG_LEVEL=debug' >> /etc/default/pvedaemon
systemctl restart pvedaemon

# Monitorare i log in tempo reale
journalctl -u pvedaemon -f

# IMPORTANTE: Rimuovere il debug dopo la diagnosi
sed -i '/PVE_LOG_LEVEL=debug/d' /etc/default/pvedaemon
systemctl restart pvedaemon
```

### 8.4 Problemi con Active Directory Specifici

**Problema: Nested Groups non funzionano**

```bash
# AD supporta nested groups con il filtro LDAP_MATCHING_RULE_IN_CHAIN
# Proxmox potrebbe non risolvere automaticamente i gruppi innestati

# Soluzione: Usare gruppi flat (non innestati) per i permessi Proxmox
# Oppure: Creare un filtro esplicito che includa tutti i gruppi rilevanti
pveum realm set ad-aziendale \
  --group_filter "(|(CN=Proxmox-Admins)(CN=Proxmox-VMOperators)(CN=Proxmox-Developers))"
```

**Problema: Utenti di domini multipli in una foresta AD**

```bash
# Se si ha una foresta AD con piu domini:
# - studio-lavoro.local (root domain)
# - roma.studio-lavoro.local (child domain)
# - milano.studio-lavoro.local (child domain)

# Opzione 1: Configurare un realm per ogni dominio
pveum realm add ad-roma --type ad --domain "roma.studio-lavoro.local" --server1 "dc01.roma.studio-lavoro.local" --port 636 --secure 1
pveum realm add ad-milano --type ad --domain "milano.studio-lavoro.local" --server1 "dc01.milano.studio-lavoro.local" --port 636 --secure 1

# Opzione 2: Usare il Global Catalog (porta 3269 per SSL)
pveum realm add ad-foresta --type ad \
  --domain "studio-lavoro.local" \
  --server1 "dc01.studio-lavoro.local" \
  --port 3269 \
  --secure 1 \
  --comment "AD Forest - Global Catalog"
```

**Problema: Account di servizio bloccato o scaduto**

```bash
# Verificare lo stato dell'account sul DC (PowerShell)
# Get-ADUser -Identity svc-proxmox -Properties LockedOut,Enabled,PasswordExpired,PasswordLastSet

# Dal nodo Proxmox, testare il bind
ldapwhoami -x -H ldaps://dc01.studio-lavoro.local:636 \
  -D "CN=svc-proxmox,OU=Service Accounts,DC=studio-lavoro,DC=local" \
  -W

# Se l'account e bloccato, sbloccarlo dal DC:
# Unlock-ADAccount -Identity svc-proxmox

# Se la password e scaduta, reimpostarla:
# Sul DC: Set-ADAccountPassword -Identity svc-proxmox
# Su Proxmox: pveum realm set ad-aziendale --password
```

---

## 9. Confronto con VMware vCenter AD Integration

### 9.1 Tabella Comparativa

| Aspetto | VMware vCenter | Proxmox VE |
|---------|---------------|------------|
| Metodo di integrazione | vCenter SSO Identity Source | Realm configuration |
| Protocollo | LDAP, LDAPS | LDAP, LDAPS |
| Kerberos | Supportato nativamente | Non supportato direttamente |
| SAML | Supportato (SSO) | Non supportato (usare OIDC) |
| OIDC | Supportato (vSphere 7+) | Supportato |
| Multi-dominio | Si, tramite identity sources multipli | Si, tramite realm multipli |
| Global Catalog | Supportato | Supportato |
| Sincronizzazione gruppi | Automatica con schedule | Manuale o con cron/sync job |
| Nested groups | Supportato | Supporto limitato |
| Account lockout policy | Configurabile in SSO | Gestito da AD + fail2ban |
| Password policy | SSO policy + AD policy | AD policy (autenticazione esterna) |
| Session timeout | Configurabile per client | Configurabile (ticket timeout) |
| API authentication | SSO token, API session | API token con privilege separation |
| Certificate auth | Supportato (smart card) | Non supportato nativamente |

### 9.2 Migrazione dei Permessi da vCenter a Proxmox

| Passo | Azione | Dettaglio |
|-------|--------|-----------|
| 1 | Inventariare gli identity source vCenter | Elencare tutti i domini AD configurati |
| 2 | Elencare utenti e gruppi con permessi | Esportare da vCenter i permessi per ogni oggetto |
| 3 | Mappare i gruppi AD ai gruppi Proxmox | Creare i gruppi corrispondenti in AD se non esistono |
| 4 | Configurare i realm in Proxmox | Un realm per ogni dominio AD usato |
| 5 | Sincronizzare utenti e gruppi | `pveum realm sync` |
| 6 | Mappare i permessi vCenter ai permessi Proxmox | Usare la tabella di mappatura ruoli |
| 7 | Testare l'accesso per ogni profilo utente | Verificare tutti i gruppi |
| 8 | Configurare 2FA | Implementare per tutti gli utenti privilegiati |
| 9 | Documentare la nuova struttura | Aggiornare la documentazione di sicurezza |

---

## 10. OpenID Connect (Alternativa Moderna)

### 10.1 Quando Usare OIDC

OpenID Connect e l'alternativa moderna a LDAP/AD per scenari specifici:

- Integrazione con Azure AD (Entra ID)
- Integrazione con Keycloak
- Integrazione con Okta, Auth0, Google Workspace
- Quando si vuole SSO reale tra piu applicazioni

### 10.2 Configurazione OIDC con Azure AD

```bash
# Configurare il realm OIDC per Azure AD (Entra ID)
pveum realm add azure-ad --type openid \
  --issuer-url "https://login.microsoftonline.com/TENANT_ID/v2.0" \
  --client-id "APPLICATION_ID" \
  --client-key "CLIENT_SECRET" \
  --username-claim "preferred_username" \
  --scopes "openid profile email" \
  --default 0 \
  --autocreate 1 \
  --comment "Azure AD via OpenID Connect"
```

### 10.3 Configurazione OIDC con Keycloak

```bash
pveum realm add keycloak --type openid \
  --issuer-url "https://keycloak.studio-lavoro.local/realms/proxmox" \
  --client-id "proxmox-ve" \
  --client-key "CLIENT_SECRET_HERE" \
  --username-claim "preferred_username" \
  --scopes "openid profile email groups" \
  --default 0 \
  --autocreate 1 \
  --comment "Keycloak SSO"
```

---

## 11. Checklist Implementazione Completa

### Pre-Implementazione

| # | Verifica | Stato |
|---|---------|-------|
| 1 | Account di servizio AD creato e testato | [ ] |
| 2 | Gruppi AD per Proxmox creati | [ ] |
| 3 | Utenti AD aggiunti ai gruppi appropriati | [ ] |
| 4 | Risoluzione DNS dei DC verificata da tutti i nodi PVE | [ ] |
| 5 | Connettivita LDAPS (porta 636) verificata | [ ] |
| 6 | Certificato CA AD importato su tutti i nodi PVE | [ ] |
| 7 | Sincronizzazione oraria verificata | [ ] |
| 8 | Account locale di emergenza creato e testato | [ ] |

### Implementazione

| # | Azione | Stato |
|---|--------|-------|
| 9 | Realm AD configurato | [ ] |
| 10 | Password di bind impostata | [ ] |
| 11 | Filtri utente configurati | [ ] |
| 12 | Filtri gruppo configurati | [ ] |
| 13 | Prima sincronizzazione eseguita con successo | [ ] |
| 14 | Ruoli assegnati ai gruppi sincronizzati | [ ] |
| 15 | Test di login per ogni profilo utente | [ ] |
| 16 | 2FA configurato per utenti privilegiati | [ ] |

### Post-Implementazione

| # | Verifica | Stato |
|---|---------|-------|
| 17 | Sincronizzazione automatica configurata | [ ] |
| 18 | Monitoraggio dei log di autenticazione attivo | [ ] |
| 19 | Procedura di fallback documentata e testata | [ ] |
| 20 | Failover al DC secondario verificato | [ ] |
| 21 | Documentazione aggiornata | [ ] |
| 22 | Team informato e formato sulla nuova procedura di login | [ ] |

---

## Conclusione

L'integrazione di Proxmox VE con Active Directory e LDAP e un processo strutturato che richiede attenzione ai dettagli nella configurazione del bind DN, dei filtri LDAP e nella gestione dei certificati. Rispetto a VMware vCenter, la configurazione e piu diretta e trasparente, con un controllo maggiore sui filtri e sulla sincronizzazione, ma manca di alcune funzionalita avanzate come il supporto nativo Kerberos e SAML.

La strategia consigliata e utilizzare il realm AD come metodo di autenticazione primario, mantenere sempre un account locale di emergenza nel realm PVE, e considerare OIDC (con Azure AD/Keycloak) per scenari che richiedono vero SSO. La sicurezza della configurazione dipende criticamente dalla verifica dei certificati LDAPS e dalla protezione dell'account di servizio utilizzato per il bind.

---

## Approfondimenti — note del 2026-04-27

> **Errore comune — `verify=0` sul realm AD.** Sintomo: il login funziona, ma cambiando il certificato del DC con uno self-signed di un attaccante MITM, il login funziona ancora. Causa: `verify=0` disabilita la validazione del cert LDAPS — qualsiasi cert e accettato. Soluzione: `pveum realm modify <realm> --verify 1`, importare il CA root del DC in `/etc/ssl/certs/` (system trust store) o nel `cert` field del realm. Validare con `openssl s_client -connect dc.example.com:636 -CAfile <ca.pem>`. Fonte: [Proxmox VE — User Management LDAP](https://pve.proxmox.com/pve-docs/chapter-pveum.html#pveum_ldap_auth), retrieved 2026-04-27.

> **Approfondimento — RADIUS 2FA fallback con FreeRADIUS + TOTP.** Configurazione: (1) FreeRADIUS server con modulo `eap` + `pam_oath`; (2) ogni utente ha un secret TOTP nel database (es. `~/.google_authenticator`); (3) Proxmox configurato come RADIUS client; (4) flow login: utente inserisce `password+TOTP`, Proxmox forward a RADIUS, RADIUS valida; (5) audit log su RADIUS. Comodo per ambienti dove AD non ha MFA nativa (Server 2016 senza Azure AD Connect). Fonte: [FreeRADIUS — eap-otp module](https://wiki.freeradius.org/), retrieved 2026-04-27.

---

## Esercizi

1. **Concettuale — break-glass account.** Argomenta in 8-10 righe la strategia per account "break-glass" admin Proxmox: dove conservare la password, chi puo accedervi, quanto frequentemente ruotarla, come auditare l'uso.

2. **Lab — realm AD + LDAPS + sync.** (a) Configurare un realm AD per un dominio test; (b) aggiungere account servizio dedicato con `Read all user info`; (c) configurare LDAPS con cert validato; (d) sync gruppi con schedule; (e) mappare gruppo `pve-admins` a ruolo `Administrator`; (f) test login e logout.

3. **Stretch — RADIUS 2FA setup completo.** Deploy FreeRADIUS in lab, configurare 2FA TOTP per 3 utenti test, integrare con Proxmox come fallback dopo AD.

## Auto-valutazione

1. Differenza fra realm `pve`, `pam`, `ad`, `ldap`, `openid`.
2. LDAPS vs StartTLS: differenza pratica.
3. Cosa rischia un realm AD con `verify=0`?
4. Account servizio AD per Proxmox: quali permessi minimi richiede?
5. Sync gruppi vs sync utenti: quale e quando?
6. Group cache TTL: trade-off?
7. Account break-glass: dove gestirlo se AD cade?

## Letture primarie consigliate

- Proxmox VE Admin Guide — User Management. https://pve.proxmox.com/pve-docs/chapter-pveum.html (retrieved 2026-04-27).
- RFC 4511 — Lightweight Directory Access Protocol (LDAP). https://datatracker.ietf.org/doc/html/rfc4511 (retrieved 2026-04-27).
- Microsoft — Active Directory LDAP Security. https://learn.microsoft.com/en-us/troubleshoot/windows-server/identity/enable-ldap-over-ssl-3rd-certification-authority (retrieved 2026-04-27).
- FreeRADIUS — Documentation. https://wiki.freeradius.org/ (retrieved 2026-04-27).

## Collegamenti incrociati

- Modulo 12.1 — `certificati-ssl-tls-proxmox.md`: TLS prerequisito per LDAPS.
- Modulo 09.4 — `../09-SCENARI-MIGRAZIONE-SPECIFICI/migrazione-windows-server-vm.md`: AD/DC migration.

## Glossario locale

| Termine | Definizione |
|---|---|
| **Realm** | Sorgente di autenticazione in Proxmox (pve, pam, ad, ldap, openid). |
| **Bind DN** | DN dell'account servizio per query LDAP. |
| **LDAP filter** | Query per identificare utenti/gruppi candidati. |
| **LDAPS** | LDAP over TLS (port 636 default). |
| **StartTLS** | Upgrade da LDAP cleartext a TLS (port 389). |
| **Group sync** | Importazione gruppi da AD/LDAP a Proxmox. |
| **Break-glass account** | Account locale di emergenza per recovery senza AD. |
| **`pveum`** | CLI Proxmox per user management. |
| **2FA RADIUS** | Two-factor via RADIUS (legacy ma valido). |
| **OIDC** | OpenID Connect; auth standard moderno. |
