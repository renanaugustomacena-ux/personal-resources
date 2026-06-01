# Scenario 04 — Compromissione Root CA e Re-emissione Catena

> **Modulo di riferimento:** [11-servizi-certificati.md](../11-servizi-certificati.md), [28-pki-certificati-guida-completa.md](../28-pki-certificati-guida-completa.md), [34-disaster-recovery-ad-pki.md](../34-disaster-recovery-ad-pki.md)
> **Tempo stimato:** 2–2.5 ore
> **Livello:** expert
> **Prerequisiti:** Lab PKI a due livelli (Offline Root CA + Issuing CA), completamento moduli 11, 28, 34
> **Ultimo aggiornamento:** 2026-05-23

---

## Scenario

Il team di sicurezza fisica segnala un incidente: durante la manutenzione programmata della server room, un tecnico esterno non autorizzato ha avuto accesso non supervisionato per circa 40 minuti alla sala che ospita la Root CA offline (YOURROOT-CA01, Windows Server 2022 Datacenter, air-gapped). Le telecamere mostrano il tecnico vicino al server, ma non è chiaro se abbia interagito con la console.

La Root CA è offline e air-gapped, ma la chiave privata è protetta solo da software (CNG Key Storage Provider, senza HSM). La Issuing CA subordinata (SUB-CA01) ha emesso circa 2.400 certificati attivi per: autenticazione computer di dominio, autenticazione utente, web server interni (IIS), firma codice interno, e VPN SSTP.

Il CISO richiede di procedere con il worst-case scenario: considerare la chiave privata della Root CA come compromessa.

---

## Fase 1 — Assessment (30 min)

### 1.1 Determinare l'estensione della compromissione

```powershell
# Sulla Root CA (accenderla in ambiente isolato per l'analisi)

# Verificare i log di audit della CA
# Event ID 4886 = Certificate Services received a certificate request
# Event ID 4887 = Certificate Services approved and issued a certificate
# Event ID 4888 = Certificate Services denied a certificate request
# Event ID 4890 = Certificate manager settings changed
# Event ID 4896 = One or more rows deleted from certificate database

Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4886, 4887, 4888, 4890, 4896
    StartTime = (Get-Date).AddDays(-7)
} -ErrorAction SilentlyContinue | Select-Object TimeCreated, Id, Message | Format-List

# Verificare logon events sulla Root CA
# (dovrebbe essere sempre spenta — qualsiasi logon è sospetto)
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4624, 4625, 4648
    StartTime = (Get-Date).AddDays(-7)
} | Select-Object TimeCreated,
    @{N='LogonType'; E={$_.Properties[8].Value}},
    @{N='Account'; E={$_.Properties[5].Value}},
    @{N='SourceIP'; E={$_.Properties[18].Value}} |
    Format-Table -AutoSize

# Verificare se la chiave privata è stata esportata
# Controllare i log di CNG Key Isolation
Get-WinEvent -FilterHashtable @{
    LogName = 'System'
    ProviderName = 'Microsoft-Windows-Crypto-NCrypt'
} -ErrorAction SilentlyContinue | Format-List TimeCreated, Message
```

### 1.2 Inventario certificati emessi dalla catena

```powershell
# Sulla Issuing CA (SUB-CA01): esportare tutti i certificati attivi

# Conteggio per template
certutil -view -restrict "Disposition=20,NotAfter>$(Get-Date -Format 'MM/dd/yyyy')" `
    -out "RequestID,CommonName,CertificateTemplate,NotBefore,NotAfter" |
    Out-File C:\Incident\all-active-certs.txt

# Conteggio per tipo di template
certutil -view -restrict "Disposition=20" -out "CertificateTemplate" |
    Select-String "Certificate Template:" |
    Group-Object | Sort-Object Count -Descending |
    Select-Object Count, @{N='Template'; E={$_.Name.Trim()}} |
    Format-Table -AutoSize

# Esportare lista completa per il piano di sostituzione
certutil -view -restrict "Disposition=20,NotAfter>$(Get-Date -Format 'MM/dd/yyyy')" `
    -out "RequestID,RequesterName,CommonName,CertificateTemplate,NotBefore,NotAfter,SerialNumber" -csv |
    Out-File C:\Incident\cert-inventory.csv -Encoding UTF8

# PowerShell alternativo per analisi
Get-CertificationAuthority | Get-IssuedRequest -Filter "NotAfter -gt $(Get-Date)" |
    Group-Object CertificateTemplate |
    Select-Object Count, Name |
    Sort-Object Count -Descending |
    Format-Table -AutoSize
```

### 1.3 Verificare certificati non autorizzati

```powershell
# Cercare certificati emessi dalla Root CA nell'intervallo sospetto
# (la Root CA emette solo il certificato della Issuing CA — qualsiasi altro è anomalo)

# Sulla Root CA:
certutil -view -restrict "Disposition=20" `
    -out "RequestID,CommonName,RequesterName,NotBefore,NotAfter,SerialNumber" |
    Out-File C:\Incident\root-ca-issued-certs.txt

# Deve contenere SOLO:
# 1. Il certificato auto-firmato della Root CA stessa
# 2. Il certificato della Issuing CA (SUB-CA01)
# Qualsiasi altro certificato = COMPROMISSIONE CONFERMATA

# Cercare richieste di certificati rifiutate (tentativo di emissione)
certutil -view -restrict "Disposition=31" `
    -out "RequestID,CommonName,RequesterName,SubmittedWhen,DispositionMessage"
```

---

## Fase 2 — Contenimento (30 min)

### 2.1 Analisi di impatto della revoca

```
Piano di revoca — impatto per tipo di certificato:
┌────────────────────────┬──────────┬─────────────────────────────────────────────┐
│ Tipo certificato       │ Quantità │ Impatto della revoca                        │
├────────────────────────┼──────────┼─────────────────────────────────────────────┤
│ Computer Authentication│ ~1.800   │ ALTO: Kerberos PKINIT fallisce,             │
│                        │          │ 802.1X auth fallisce, IPsec interrotto      │
├────────────────────────┼──────────┼─────────────────────────────────────────────┤
│ User Authentication    │ ~400     │ ALTO: smart card logon fallisce,            │
│                        │          │ VPN cert-based auth interrotta              │
├────────────────────────┼──────────┼─────────────────────────────────────────────┤
│ Web Server (IIS)       │ ~120     │ MEDIO: siti interni HTTPS mostrano errori   │
│                        │          │ certificato fino a sostituzione             │
├────────────────────────┼──────────┼─────────────────────────────────────────────┤
│ Code Signing           │ ~30      │ MEDIO: signature su binari interni          │
│                        │          │ diventano non valide                        │
├────────────────────────┼──────────┼─────────────────────────────────────────────┤
│ VPN SSTP               │ ~50      │ ALTO: connessioni VPN remote interrotte     │
└────────────────────────┴──────────┴─────────────────────────────────────────────┘

STRATEGIA: NON revocare immediatamente la Root CA.
Costruire prima la nuova catena, poi fare il cutover coordinato.
```

### 2.2 Revocare il certificato della Root CA (dopo che la nuova catena è pronta)

```powershell
# ATTENZIONE: questa sezione viene ESEGUITA solo dopo che la Fase 3 è completata
# e la nuova catena è operativa. Documentata qui per completezza procedurale.

# Sulla Root CA compromessa (prima di spegnerla definitivamente):

# Revocare il certificato della Issuing CA (SUB-CA01)
# Questo invalida tutta la catena sotto di essa
certutil -revoke <serial-number-SUB-CA01> 1
# Reason code 1 = Key Compromise

# Pubblicare CRL aggiornata
certutil -CRL

# Esportare la CRL per distribuzione manuale (la Root CA è offline)
certutil -getcrl C:\CRL\root-ca-final.crl
# Copiare la CRL via USB alla location AIA/CDP (web server/LDAP)
```

### 2.3 Disabilitare auto-enrollment temporaneamente

```powershell
# Disabilitare auto-enrollment via GPO per evitare che i client
# richiedano certificati dalla catena compromessa durante la transizione

# Opzione rapida: disabilitare i template sulla Issuing CA
$issuingCA = "SUB-CA01.contoso.local\Contoso-SubCA"

# Rimuovere i template dalla CA (non li elimina, solo li rende non disponibili)
$templates = @("Machine", "User", "WebServer", "CodeSigning", "IPSec")
foreach ($template in $templates) {
    certutil -setcatemplates -$template
    Write-Output "[-] Template $template rimosso dalla CA"
}

# Verificare template rimanenti
certutil -catemplates

# Alternativa: impostare la CA in stato "non emette certificati"
# certutil -setreg ca\InterfaceFlags +IF_LOCKICERTREQUEST
# net stop certsvc && net start certsvc
```

### 2.4 Notificare stakeholder

```
Comunicazione necessaria:

1. CISO / Management — decisione formale di procedere con la sostituzione
2. Team Infrastruttura — pianificazione downtime per servizi certificate-dependent
3. Team Applicazioni — inventario applicazioni con certificate pinning
4. Team Security — monitoraggio per certificati emessi dalla vecchia catena
5. Help Desk — preparazione per ticket relativi a errori certificato
6. Utenti VPN — notifica di interruzione temporanea con tempistica
```

---

## Fase 3 — Rebuild della catena PKI (40 min)

### 3.1 Generare nuova Root CA

```powershell
# Su un nuovo server air-gapped (NEWROOT-CA01, installazione pulita)
# Prerequisiti: Windows Server 2022 Datacenter, nessuna connessione di rete

# Installare il ruolo
Install-WindowsFeature ADCS-Cert-Authority -IncludeManagementTools

# Configurare la nuova Root CA
Install-AdcsCertificationAuthority `
    -CAType StandaloneRootCA `
    -CACommonName "Contoso Root CA v2" `
    -KeyLength 4096 `
    -HashAlgorithmName SHA384 `
    -CryptoProviderName "RSA#Microsoft Software Key Storage Provider" `
    -ValidityPeriod Years `
    -ValidityPeriodUnits 20 `
    -DatabaseDirectory "D:\CertDB" `
    -LogDirectory "D:\CertLog" `
    -Force

# CRITICO: usare RSA 4096 + SHA384 (o superiore) per la nuova Root
# La vecchia usava RSA 2048 + SHA256 — aggiornare la baseline

# Configurare AIA e CDP per la nuova Root
certutil -setreg CA\CACertPublicationURLs "1:C:\Windows\system32\CertSrv\CertEnroll\%1_%3%4.crt\n2:ldap:///CN=%7,CN=AIA,CN=Public Key Services,CN=Services,%6%11\n2:http://pki.contoso.local/CertEnroll/%1_%3%4.crt"

certutil -setreg CA\CRLPublicationURLs "65:C:\Windows\system32\CertSrv\CertEnroll\%3%8%9.crl\n79:ldap:///CN=%7%8,CN=%2,CN=CDP,CN=Public Key Services,CN=Services,%6%10\n6:http://pki.contoso.local/CertEnroll/%3%8%9.crl"

# Configurare validità CRL (più lunga per Root offline)
certutil -setreg CA\CRLPeriodUnits 6
certutil -setreg CA\CRLPeriod "Months"
certutil -setreg CA\CRLDeltaPeriodUnits 0
certutil -setreg CA\CRLDeltaPeriod "Days"

# Riavviare il servizio
Restart-Service certsvc

# Pubblicare la CRL
certutil -CRL

# Esportare il certificato Root per distribuzione
certutil -ca.cert C:\RootCA\contoso-root-ca-v2.cer

# Esportare la CRL
Copy-Item C:\Windows\system32\CertSrv\CertEnroll\*.crl C:\RootCA\
```

### 3.2 Creare la nuova Issuing CA subordinata

```powershell
# Su un nuovo server (NEWSUB-CA01), membro del dominio

# Installare il ruolo
Install-WindowsFeature ADCS-Cert-Authority, ADCS-Web-Enrollment -IncludeManagementTools

# Generare la richiesta di certificato per la Issuing CA
Install-AdcsCertificationAuthority `
    -CAType EnterpriseSubordinateCA `
    -CACommonName "Contoso Issuing CA v2" `
    -KeyLength 4096 `
    -HashAlgorithmName SHA256 `
    -CryptoProviderName "RSA#Microsoft Software Key Storage Provider" `
    -DatabaseDirectory "D:\CertDB" `
    -LogDirectory "D:\CertLog" `
    -OutputCertRequestFile "C:\CertReq\NEWSUB-CA01.req" `
    -Force

# Trasferire il file .req alla Root CA via USB
# Sulla Root CA:
certreq -submit -attrib "CertificateTemplate:" C:\CertReq\NEWSUB-CA01.req C:\CertReq\NEWSUB-CA01.cer

# Trasferire il certificato emesso (.cer) di nuovo alla Issuing CA via USB

# Sulla Issuing CA: installare il certificato
certutil -installcert C:\CertReq\NEWSUB-CA01.cer

# Avviare il servizio CA
Start-Service certsvc

# Configurare AIA e CDP per la Issuing CA
certutil -setreg CA\CACertPublicationURLs "1:C:\Windows\system32\CertSrv\CertEnroll\%1_%3%4.crt\n2:ldap:///CN=%7,CN=AIA,CN=Public Key Services,CN=Services,%6%11\n2:http://pki.contoso.local/CertEnroll/%1_%3%4.crt"

certutil -setreg CA\CRLPublicationURLs "65:C:\Windows\system32\CertSrv\CertEnroll\%3%8%9.crl\n79:ldap:///CN=%7%8,CN=%2,CN=CDP,CN=Public Key Services,CN=Services,%6%10\n6:http://pki.contoso.local/CertEnroll/%3%8%9.crl"

# CRL più frequente per Issuing CA
certutil -setreg CA\CRLPeriodUnits 7
certutil -setreg CA\CRLPeriod "Days"
certutil -setreg CA\CRLDeltaPeriodUnits 1
certutil -setreg CA\CRLDeltaPeriod "Days"

Restart-Service certsvc
certutil -CRL
```

### 3.3 Configurare i template di certificato

```powershell
# Sulla nuova Issuing CA: aggiungere i template necessari

# Duplicare e configurare i template standard
# (i template vengono gestiti a livello di AD — verificare che esistano già)

$templatesToAdd = @(
    "Machine"              # Computer Authentication
    "User"                 # User Authentication
    "WebServer"            # Web Server SSL
    "SubCA"                # Subordinate CA (per future sub-CA)
    "CodeSigning"          # Code Signing
    "IPSec"                # IPSec
    "SmartcardLogon"       # Smartcard Logon
)

foreach ($template in $templatesToAdd) {
    try {
        Add-CATemplate -Name $template -Force -ErrorAction Stop
        Write-Output "[+] Template aggiunto: $template"
    } catch {
        Write-Output "[-] Errore per $template : $($_.Exception.Message)"
    }
}

# Verificare template disponibili sulla nuova CA
certutil -catemplates

# Verificare con PowerShell
Get-CATemplate | Select-Object Name | Sort-Object Name
```

---

## Fase 4 — Rollout sostituzione certificati (30 min)

### 4.1 Pubblicare il nuovo certificato Root in AD e GPO

```powershell
# Pubblicare il certificato della nuova Root CA in AD
# Questo lo distribuisce a tutti i computer del dominio via GPO

# Pubblicare nel contenitore Trusted Root Certification Authorities di AD
certutil -dspublish -f C:\RootCA\contoso-root-ca-v2.cer RootCA

# Pubblicare nell'NTAuthCertificates (necessario per smart card logon e auto-enrollment)
certutil -dspublish -f C:\RootCA\contoso-root-ca-v2.cer NTAuthCA

# Pubblicare il certificato della Issuing CA
certutil -dspublish -f C:\CertReq\NEWSUB-CA01.cer SubCA

# Pubblicare la CRL della Root in AD
certutil -dspublish -f C:\RootCA\contoso-root-ca-v2.crl

# Verificare la pubblicazione
certutil -viewstore "ldap:///CN=Contoso Root CA v2,CN=Certification Authorities,CN=Public Key Services,CN=Services,CN=Configuration,DC=contoso,DC=local?cACertificate"

# Forzare aggiornamento GPO su un client di test
gpupdate /force

# Verificare che il certificato Root sia nel trust store della macchina
certutil -store Root "Contoso Root CA v2"
# Deve mostrare il certificato con la nuova chiave
```

### 4.2 Triggerare auto-enrollment per certificati di dominio

```powershell
# Abilitare auto-enrollment nella GPO (se era stato disabilitato nella Fase 2)
# Computer Configuration > Windows Settings > Security Settings >
#   Public Key Policies > Certificate Services Client - Auto-Enrollment
#   = Enabled, check "Renew expired certificates" e "Update certificates that use templates"

# Forzare auto-enrollment su un client di test
certutil -pulse

# Verificare che il nuovo certificato sia stato emesso
certutil -store My

# Monitorare l'enrollment sulla nuova CA
Get-WinEvent -FilterHashtable @{
    LogName = 'Application'
    ProviderName = 'Microsoft-Windows-CertificateServicesClient-AutoEnrollment'
} -MaxEvents 20 | Select-Object TimeCreated, Message | Format-List

# Sulla Issuing CA: monitorare le richieste in arrivo
certutil -view -restrict "Disposition=20,NotBefore>$(Get-Date -Format 'MM/dd/yyyy')" `
    -out "RequestID,CommonName,CertificateTemplate,NotBefore" |
    Select-Object -Last 20
```

### 4.3 Sostituire certificati web server e code signing (manuali)

```powershell
# I certificati Web Server e Code Signing richiedono sostituzione manuale
# (non auto-enrolled tipicamente)

# Generare nuova richiesta per un web server
# Sul web server:
$inf = @"
[Version]
Signature = "`$Windows NT`$"

[NewRequest]
Subject = "CN=intranet.contoso.local"
KeyLength = 2048
KeySpec = 1
KeyUsage = 0xA0
MachineKeySet = TRUE
ProviderName = "Microsoft RSA SChannel Cryptographic Provider"
RequestType = PKCS10
HashAlgorithm = SHA256

[EnhancedKeyUsageExtension]
OID = 1.3.6.1.5.5.7.3.1

[Extensions]
2.5.29.17 = "{text}"
_continue_ = "dns=intranet.contoso.local&"
_continue_ = "dns=intranet&"
_continue_ = "dns=portal.contoso.local"
"@

$inf | Out-File C:\CertReq\webserver.inf -Encoding ASCII
certreq -new C:\CertReq\webserver.inf C:\CertReq\webserver.req

# Sottomettere alla nuova Issuing CA
certreq -submit -config "NEWSUB-CA01.contoso.local\Contoso Issuing CA v2" `
    C:\CertReq\webserver.req C:\CertReq\webserver.cer

# Installare il certificato
certreq -accept C:\CertReq\webserver.cer

# Aggiornare il binding IIS
Import-Module WebAdministration
$newCert = Get-ChildItem Cert:\LocalMachine\My |
    Where-Object { $_.Subject -match "intranet.contoso.local" -and $_.NotBefore -gt (Get-Date).AddDays(-1) }

# Aggiornare il binding HTTPS
Set-ItemProperty "IIS:\Sites\Default Web Site" -Name "bindings" -Value @{
    protocol = "https"
    bindingInformation = "*:443:"
    certificateHash = $newCert.Thumbprint
    certificateStoreName = "MY"
}

# Verificare
Get-ChildItem IIS:\SslBindings | Format-Table Port, Host, @{
    N='CertSubject'; E={(Get-ChildItem "Cert:\LocalMachine\My\$($_.Thumbprint)").Subject}
}
```

### 4.4 Verificare la catena di trust

```powershell
# Verificare la catena completa su un client
certutil -verify -urlfetch C:\test-cert.cer

# Output atteso:
# -------- CERT 0 --------
# ...
# Issuer: CN=Contoso Issuing CA v2
# -------- CERT 1 --------
# ...
# Issuer: CN=Contoso Root CA v2
# ...
# CertUtil: -verify command completed successfully.

# Verificare AIA e CDP accessibili
certutil -verify -urlfetch C:\test-cert.cer 2>&1 | Select-String "Verified|Error|FAILED"

# Verificare il trust store della macchina
certutil -store Root | Select-String "Contoso Root CA"
# Deve mostrare SOLO "Contoso Root CA v2"
# Se appare ancora "Contoso Root CA" (v1), rimuoverlo:
# certutil -delstore Root "Contoso Root CA"

# Test pratico: connessione HTTPS a un sito con il nuovo certificato
$uri = "https://intranet.contoso.local"
try {
    $response = Invoke-WebRequest -Uri $uri -UseBasicParsing
    Write-Output "[+] Connessione riuscita: $($response.StatusCode)"
} catch {
    Write-Output "[-] Errore: $($_.Exception.Message)"
}

# Verificare il certificato presentato
$tcpClient = [System.Net.Sockets.TcpClient]::new("intranet.contoso.local", 443)
$sslStream = [System.Net.Security.SslStream]::new($tcpClient.GetStream(), $false)
$sslStream.AuthenticateAsClient("intranet.contoso.local")
$cert = $sslStream.RemoteCertificate
Write-Output "Subject: $($cert.Subject)"
Write-Output "Issuer: $($cert.Issuer)"
Write-Output "Valid: $($cert.GetEffectiveDateString()) - $($cert.GetExpirationDateString())"
$sslStream.Dispose()
$tcpClient.Dispose()
```

---

## Fase 5 — Post-incident (20 min)

### 5.1 Sicurezza fisica della CA

```
Misure da implementare:
┌────────────────────────────────────────────────────────────────────────┐
│ Controllo                       │ Priorità │ Implementazione          │
├────────────────────────────────────────────────────────────────────────┤
│ HSM per chiave privata Root CA  │ CRITICA  │ FIPS 140-2 Level 3+     │
│ Accesso biometrico alla sala    │ ALTA     │ Lettore impronte + badge │
│ Videosorveglianza con retention │ ALTA     │ 90 giorni, tamper-proof  │
│ Dual-person access (two-man)    │ ALTA     │ Due badge per aprire     │
│ Inventory log per accessi       │ MEDIA    │ Registro cartaceo + dig. │
│ Sensori tamper sul server       │ MEDIA    │ Chassis intrusion detect │
│ Audit periodico accessi fisici  │ MEDIA    │ Trimestrale              │
└────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Implementare HSM per la nuova Root CA

```powershell
# Configurare la nuova Root CA per usare HSM (esempio con nCipher/Thales)
# Il provider crittografico cambia da Software KSP a HSM KSP

# Verificare i provider disponibili
certutil -csplist

# Se HSM è installato, apparirà il provider specifico
# Esempio: "nCipher Security World Key Storage Provider"

# Per migrare la chiave a HSM (richiede riconfigurazione CA):
# 1. Esportare la chiave (se il software provider lo permette)
# 2. Importare nell'HSM
# 3. Riconfigurare la CA per usare il provider HSM

# Per una nuova CA con HSM fin dall'inizio:
# Install-AdcsCertificationAuthority `
#     -CAType StandaloneRootCA `
#     -CACommonName "Contoso Root CA v3" `
#     -CryptoProviderName "nCipher Security World Key Storage Provider" `
#     -KeyLength 4096 `
#     -HashAlgorithmName SHA384 `
#     ...
```

### 5.3 Aggiornare il piano di Disaster Recovery

```
Aggiornamenti al piano DR per la PKI:

1. BACKUP
   - Backup HSM key material in cassaforte secondaria (sito diverso)
   - Backup database CA settimanale (su media crittografato)
   - Export CRL e AIA su storage ridondante
   - Documentare serial number e thumbprint di ogni CA

2. RECOVERY
   - Procedura step-by-step per rebuild Root CA da HSM backup
   - Procedura per re-issue Issuing CA da nuova Root
   - Template di comunicazione per stakeholder
   - Runbook per rollout certificati (ordinato per criticità)

3. TEST
   - DR drill annuale per PKI (compreso rebuild completo)
   - Verifica trimestrale accessibilità CRL/AIA
   - Verifica semestrale backup chiavi HSM
```

### 5.4 Verificare rimozione della vecchia catena

```powershell
# Rimuovere il vecchio certificato Root da AD
# (dopo che tutti i certificati della vecchia catena sono stati sostituiti)

# Rimuovere dal trust store di AD
certutil -dsdelete "Contoso Root CA" RootCA

# Rimuovere dal NTAuthCertificates
certutil -dsdelete "Contoso Root CA" NTAuthCA

# Verificare che i client non abbiano più la vecchia Root nel trust store
# (dopo il prossimo gpupdate)
Invoke-Command -ComputerName "WKS-TEST-001" -ScriptBlock {
    certutil -store Root | Select-String "Contoso Root CA"
}
# Deve mostrare SOLO "Contoso Root CA v2"

# Rimuovere la vecchia CRL dal CDP
# (se pubblicata in AD o su web server)

# Verifica finale: nessun certificato della vecchia catena ancora in uso
$oldRootThumbprint = "<thumbprint-della-vecchia-root>"
Invoke-Command -ComputerName (Get-ADComputer -Filter * | Select-Object -First 10 -ExpandProperty Name) -ScriptBlock {
    Get-ChildItem Cert:\LocalMachine\My | Where-Object {
        $chain = New-Object Security.Cryptography.X509Certificates.X509Chain
        $chain.Build($_) | Out-Null
        $chain.ChainElements | Where-Object {
            $_.Certificate.Thumbprint -eq $using:oldRootThumbprint
        }
    } | Select-Object Subject, Thumbprint, NotAfter
} | Format-Table PSComputerName, Subject, NotAfter
```

### 5.5 Revisione permessi template

```powershell
# Audit dei permessi sui template di certificato
# Verificare che solo i gruppi autorizzati possano richiedere certificati

$templates = Get-CATemplate
foreach ($t in $templates) {
    $templateObj = Get-ADObject -SearchBase "CN=Certificate Templates,CN=Public Key Services,CN=Services,CN=Configuration,DC=contoso,DC=local" `
        -Filter {Name -eq $t.Name} -Properties *

    Write-Output "=== Template: $($t.Name) ==="

    # Verificare chi ha permesso di Enroll e AutoEnroll
    $acl = Get-Acl "AD:$($templateObj.DistinguishedName)"
    $acl.Access | Where-Object {
        $_.ActiveDirectoryRights -match 'ExtendedRight' -and
        $_.ObjectType -in @(
            '0e10c968-78fb-11d2-90d4-00c04f79dc55', # Enroll
            'a05b8cc2-17bc-4802-a710-e7c15ab866a2'  # AutoEnroll
        )
    } | Select-Object IdentityReference, ActiveDirectoryRights, AccessControlType |
        Format-Table -AutoSize
}

# Rimuovere permessi non autorizzati (esempio)
# $acl = Get-Acl "AD:CN=WebServer,CN=Certificate Templates,..."
# $acl.RemoveAccessRule($unauthorizedRule)
# Set-Acl -Path "AD:CN=WebServer,CN=Certificate Templates,..." -AclObject $acl
```

---

## Domande di Valutazione

<details>
<summary>1. Perché non si revoca immediatamente la Root CA al primo sospetto di compromissione?</summary>

La revoca immediata della Root CA invaliderebbe istantaneamente tutti i ~2.400 certificati emessi dalla catena subordinata. Questo causerebbe: interruzione di Kerberos PKINIT (logon computer), fallimento 802.1X (accesso rete), errori HTTPS su tutti i siti interni, fallimento VPN, e invalidazione delle firme sul codice interno. L'impatto operativo sarebbe catastrofico. La strategia corretta è "build before burn": costruire la nuova catena PKI, emettere nuovi certificati, completare il rollout, e solo dopo revocare la vecchia Root e pubblicare la CRL finale. Il periodo di transizione è un rischio accettato e gestito (monitoraggio intensificato per certificati anomali dalla vecchia catena).
</details>

<details>
<summary>2. Qual è la differenza tra certutil -dspublish RootCA e NTAuthCA?</summary>

`certutil -dspublish <cert> RootCA` pubblica il certificato nel container "Certification Authorities" in AD (CN=Certification Authorities,CN=Public Key Services,CN=Services,CN=Configuration). Questo lo aggiunge al trust store "Trusted Root Certification Authorities" di tutti i domain members via auto-enrollment/GPO. I client si fidano di qualsiasi catena che termina con questa Root. `certutil -dspublish <cert> NTAuthCA` pubblica nel container "NTAuth" (CN=NTAuthCertificates,CN=Public Key Services,CN=Services,CN=Configuration). Questo è un requisito aggiuntivo per funzionalità specifiche di AD: smart card logon, EFS, e certificate-based authentication richiedono che la CA emittente (o la sua Root) sia in NTAuth. Senza NTAuth, i certificati sono trusted per TLS ma non per autenticazione AD.
</details>

<details>
<summary>3. Perché un HSM FIPS 140-2 Level 3+ è critico per una Root CA?</summary>

FIPS 140-2 Level 3 richiede: (1) tamper-evidence fisica (il modulo mostra segni visibili di manipolazione), (2) identity-based authentication (operatori autenticati, non solo ruoli), (3) separazione fisica delle interfacce per input/output di parametri critici, (4) la chiave privata non lascia mai l'HSM in chiaro — tutte le operazioni crittografiche avvengono dentro il modulo. Per una Root CA, questo significa che anche con accesso fisico al server, un attaccante non può estrarre la chiave privata. Nel nostro scenario, se la Root CA avesse usato un HSM Level 3, l'accesso non autorizzato alla sala non avrebbe compromesso la chiave, e l'intero incidente sarebbe stato declassato a "accesso fisico non autorizzato senza impatto crittografico".
</details>

<details>
<summary>4. Come gestisci i certificati con certificate pinning durante il cutover?</summary>

Le applicazioni che fanno certificate pinning (HPKP, pinning nel codice, o configurazione specifica) rifiuteranno i nuovi certificati perché il pin (hash della chiave pubblica o del certificato) non corrisponde. Per gestire il cutover: (1) inventariare tutte le applicazioni con pinning attivo, (2) aggiornare la configurazione di pinning per includere sia il vecchio che il nuovo pin (dual-pin) prima di emettere nuovi certificati, (3) emettere i nuovi certificati, (4) verificare che le applicazioni accettino i nuovi certificati, (5) rimuovere il vecchio pin solo dopo che tutti i certificati sono stati sostituiti. Per HPKP (deprecato ma ancora in uso), i pin hanno un max-age: attendere la scadenza prima di rimuovere il vecchio pin. Per pinning nel codice, serve un rilascio software coordinato.
</details>

---

## Riferimenti

- [11-servizi-certificati.md](../11-servizi-certificati.md)
- [28-pki-certificati-guida-completa.md](../28-pki-certificati-guida-completa.md)
- [34-disaster-recovery-ad-pki.md](../34-disaster-recovery-ad-pki.md)
- [05-sicurezza-windows.md](../05-sicurezza-windows.md)
- Microsoft Learn — [AD CS migration and upgrade](https://learn.microsoft.com/en-us/windows-server/identity/ad-cs/deploy/upgrade-migration)
- Microsoft Learn — [Certutil command reference](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/certutil)
- Microsoft Learn — [Certificate template management](https://learn.microsoft.com/en-us/windows-server/identity/ad-cs/certificate-template-concepts)
- NIST SP 800-57 — [Recommendation for Key Management](https://csrc.nist.gov/pubs/sp/800-57-pt1/rev5/final)
