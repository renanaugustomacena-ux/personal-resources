# Scenario 02 — Recovery BitLocker con TPM Failure

> **Modulo di riferimento:** [07-storage-windows.md](../07-storage-windows.md), [05-sicurezza-windows.md](../05-sicurezza-windows.md), [21-group-policy-guida-completa.md](../21-group-policy-guida-completa.md)
> **Tempo stimato:** 1–1.5 ore
> **Livello:** intermediate
> **Prerequisiti:** BitLocker attivo su almeno una VM/workstation, accesso AD DS con attributi BitLocker, completamento moduli 05, 07, 21
> **Ultimo aggiornamento:** 2026-05-23

---

## Scenario

L'helpdesk riceve una chiamata urgente da un dirigente: il laptop aziendale (LAPTOP-DIR-017, Windows 11 Enterprise) non si avvia dopo un aggiornamento BIOS eseguito durante la notte da un task di manutenzione. Lo schermo mostra la richiesta di recovery key BitLocker. L'utente non ha mai salvato la recovery key personalmente. Il laptop contiene documenti critici per una presentazione al CdA prevista tra 3 ore.

Il tuo compito è:

1. Recuperare la recovery key e sbloccare il volume
2. Ripristinare la protezione BitLocker con il nuovo stato TPM
3. Implementare procedure per evitare il problema in futuro

---

## Fase 1 — Triage (15 min)

### 1.1 Comprendere il trigger del recovery

```
Cause comuni di richiesta BitLocker recovery key:
┌─────────────────────────────────────────────────────────────────────┐
│ Trigger                          │ PCR coinvolti │ Frequenza       │
├─────────────────────────────────────────────────────────────────────┤
│ Aggiornamento BIOS/UEFI         │ PCR 0, 2      │ Comune          │
│ Modifica boot order             │ PCR 4         │ Comune          │
│ Cambio hardware (scheda madre)  │ PCR 1         │ Raro            │
│ Aggiornamento Secure Boot DB    │ PCR 7         │ Occasionale     │
│ Modifica MBR/Boot Manager       │ PCR 4, 11     │ Raro            │
│ TPM cleared/reset               │ Tutti         │ Raro            │
│ Modifica partizione di recovery │ PCR 11        │ Raro            │
│ Pre-boot authentication fail    │ N/A           │ Errore utente   │
└─────────────────────────────────────────────────────────────────────┘

PCR = Platform Configuration Register (registri del TPM che misurano
lo stato del boot chain; se cambiano, BitLocker richiede recovery)
```

### 1.2 Identificare il volume e lo stato del recovery

```powershell
# Da un altro sistema con accesso AD, identificare il computer
Get-ADComputer -Identity "LAPTOP-DIR-017" -Properties * |
    Select-Object Name, DistinguishedName, OperatingSystem, LastLogonDate

# Verificare se la recovery key è salvata in AD DS
# L'attributo ms-FVE-RecoveryInformation è memorizzato sotto l'oggetto computer
$computerDN = (Get-ADComputer -Identity "LAPTOP-DIR-017").DistinguishedName
Get-ADObject -SearchBase $computerDN -Filter {objectClass -eq 'msFVE-RecoveryInformation'} -Properties * |
    Select-Object @{
        N='RecoveryPassword'; E={$_.'msFVE-RecoveryPassword'}
    }, @{
        N='KeyID'; E={$_.'msFVE-VolumeGuid'}
    }, @{
        N='DateCreated'; E={$_.Created}
    } | Format-List
```

### 1.3 Localizzare la recovery key — percorsi alternativi

```powershell
# Percorso 1: Active Directory (BitLocker AD Backup)
# Usare il tool RSAT "Active Directory Users and Computers"
# Tab "BitLocker Recovery" sull'oggetto computer

# Percorso 2: Microsoft Entra ID (se il dispositivo è Azure AD Joined o Hybrid)
# Portale Entra ID > Devices > LAPTOP-DIR-017 > BitLocker keys
# Oppure via PowerShell:
# Connect-MgGraph -Scopes "BitlockerKey.Read.All"
# Get-MgInformationProtectionBitlockerRecoveryKey -Filter "deviceId eq '<device-id>'"

# Percorso 3: MBAM (Microsoft BitLocker Administration and Monitoring) — se deployato
# Accedere al portale web MBAM: https://mbam.contoso.local/HelpDesk

# Percorso 4: File di backup utente
# L'utente potrebbe aver salvato su: account Microsoft, file .txt, stampa cartacea

# Percorso 5: Intune (se MDM managed)
# Endpoint Manager > Devices > LAPTOP-DIR-017 > Recovery keys
```

---

## Fase 2 — Recovery (20 min)

### 2.1 Recuperare la recovery key da AD DS

```powershell
# Metodo PowerShell completo per estrarre la recovery key
# Richiede modulo ActiveDirectory e permessi di lettura sugli attributi BitLocker

# Cercare tutti i recovery password per il computer
$computer = Get-ADComputer -Identity "LAPTOP-DIR-017"
$recoveryKeys = Get-ADObject -SearchBase $computer.DistinguishedName `
    -Filter {objectClass -eq 'msFVE-RecoveryInformation'} `
    -Properties 'msFVE-RecoveryPassword', 'msFVE-RecoveryGuid', 'whenCreated'

foreach ($key in $recoveryKeys) {
    Write-Output "================================================"
    Write-Output "Key ID:    $($key.'msFVE-RecoveryGuid')"
    Write-Output "Password:  $($key.'msFVE-RecoveryPassword')"
    Write-Output "Creata:    $($key.whenCreated)"
    Write-Output "================================================"
}

# NOTA: la schermata BitLocker mostra i primi 8 caratteri del Key ID
# Confrontare con il Key ID per trovare la password corretta

# Esempio output:
# Key ID:    3A4B5C6D-7E8F-9A0B-C1D2-E3F4A5B6C7D8
# Password:  123456-789012-345678-901234-567890-123456-789012-345678
```

### 2.2 Sbloccare il volume

```
Sul laptop bloccato (schermata di recovery BitLocker):

1. Premere ESC se richiesto per opzioni aggiuntive
2. Inserire la recovery key di 48 cifre (8 gruppi di 6 cifre)
   Esempio: 123456-789012-345678-901234-567890-123456-789012-345678
3. Il sistema dovrebbe avviarsi normalmente

Se la recovery key non funziona:
- Verificare che il Key ID corrisponda (primi 8 char visibili sullo schermo)
- Potrebbero esserci multiple chiavi; provare quella con data più recente
- Se nessuna chiave funziona: il volume potrebbe essere corrotto (passare a recovery dati)
```

### 2.3 Verifica post-sblocco

```powershell
# Dopo l'avvio, verificare lo stato di BitLocker
manage-bde -status C:

# Output atteso dopo recovery:
# Volume C: [Windows]
#     Size:                 475.00 GB
#     BitLocker Version:    2.0
#     Conversion Status:    Fully Encrypted
#     Percentage Encrypted: 100%
#     Encryption Method:    XTS-AES 256
#     Protection Status:    Protection Off    <-- ATTENZIONE: protezione sospesa
#     Lock Status:          Unlocked
#     Key Protectors:
#         TPM
#         Numerical Password

# Verificare con cmdlet PowerShell
Get-BitLockerVolume -MountPoint C: | Select-Object MountPoint,
    EncryptionMethod, VolumeStatus, ProtectionStatus, LockStatus,
    @{N='KeyProtectors'; E={($_.KeyProtector | ForEach-Object {$_.KeyProtectorType}) -join ', '}}
```

---

## Fase 3 — Re-seal TPM e ripristino protezione (20 min)

### 3.1 Rimuovere e ricreare i protettori TPM

```powershell
# La protezione è sospesa dopo il recovery — il TPM ha PCR diversi
# Bisogna ricreare i protettori per "sigillare" al nuovo stato

# Passo 1: Verificare i protettori attuali
manage-bde -protectors -get C:
# Annotare i protettori presenti (TPM, RecoveryPassword, ecc.)

# Passo 2: Rimuovere il protettore TPM attuale (obsoleto)
$tpmProtector = (Get-BitLockerVolume -MountPoint C:).KeyProtector |
    Where-Object KeyProtectorType -eq 'Tpm'
if ($tpmProtector) {
    manage-bde -protectors -delete C: -id $tpmProtector.KeyProtectorId
    Write-Output "[+] Protettore TPM rimosso: $($tpmProtector.KeyProtectorId)"
}

# Passo 3: Aggiungere nuovo protettore TPM (sigillato ai PCR attuali)
# Opzione A: Solo TPM
manage-bde -protectors -add C: -tpm

# Opzione B: TPM + PIN (più sicuro, raccomandato per laptop)
manage-bde -protectors -add C: -tpmandpin
# Verrà richiesto di impostare un PIN numerico

# Passo 4: Riprendere la protezione
manage-bde -protectors -enable C:

# Equivalente PowerShell
Resume-BitLocker -MountPoint C:
```

### 3.2 Verificare il profilo PCR

```powershell
# Verificare quali PCR sono usati per la validazione
manage-bde -protectors -get C: -type tpm

# Output atteso:
#     TPM:
#       ID: {GUID}
#       PCR Validation Profile:
#         7, 11
#         (Uses Secure Boot for integrity validation)
#
# PCR 7 = Secure Boot policy
# PCR 11 = BitLocker access control

# Verificare lo stato del TPM
Get-Tpm | Select-Object TpmPresent, TpmReady, TpmEnabled, TpmActivated,
    ManufacturerId, ManufacturerVersion

# Verificare i valori PCR attuali (per documentazione)
# Richiede modulo TrustedPlatformModule
$pcrs = @(0, 2, 4, 7, 11)
foreach ($pcr in $pcrs) {
    $value = (Get-TpmEndorsementKeyInfo -ErrorAction SilentlyContinue)
    Write-Output "PCR $pcr — Usato per: $(switch($pcr) {
        0 {'BIOS/UEFI firmware'}
        2 {'Option ROM code'}
        4 {'MBR/Boot Manager'}
        7 {'Secure Boot policy'}
        11 {'BitLocker access control'}
    })"
}
```

### 3.3 Verificare che la recovery key sia ancora in backup

```powershell
# Dopo il re-seal, eseguire backup della nuova recovery key in AD DS
# (la recovery key numerica non cambia, ma è buona pratica verificare)

# Verificare backup in AD
$bitlockerVolume = Get-BitLockerVolume -MountPoint C:
$recoveryProtector = $bitlockerVolume.KeyProtector |
    Where-Object KeyProtectorType -eq 'RecoveryPassword'

Write-Output "Recovery Key ID: $($recoveryProtector.KeyProtectorId)"
Write-Output "Recovery Password: $($recoveryProtector.RecoveryPassword)"

# Forzare backup in AD DS
Backup-BitLockerKeyProtector -MountPoint C: -KeyProtectorId $recoveryProtector.KeyProtectorId

# Verificare che il backup sia presente in AD
$computerDN = (Get-ADComputer -Identity $env:COMPUTERNAME).DistinguishedName
Get-ADObject -SearchBase $computerDN `
    -Filter {objectClass -eq 'msFVE-RecoveryInformation'} `
    -Properties 'msFVE-RecoveryPassword' | Measure-Object
# Count deve essere >= 1

# Backup aggiuntivo in Entra ID (se hybrid joined)
# BackupToAAD-BitLockerKeyProtector -MountPoint C: -KeyProtectorId $recoveryProtector.KeyProtectorId
```

### 3.4 Stato finale

```powershell
# Verifica completa dello stato finale
manage-bde -status C:

# Output atteso:
#     Protection Status:    Protection On     <-- CORRETTO
#     Key Protectors:
#         TPM And PIN                         <-- Aggiornato
#         Numerical Password                  <-- Backup recovery key

# Test: simulare un reboot per verificare che il TPM sblocchi senza recovery
# shutdown /r /t 0
# Il sistema deve avviarsi normalmente (con richiesta PIN se TPM+PIN)
```

---

## Fase 4 — Prevenzione (15 min)

### 4.1 Configurare GPO per backup automatico recovery key in AD DS

```powershell
# GPO Path:
# Computer Configuration > Administrative Templates > Windows Components >
#   BitLocker Drive Encryption > Operating System Drives

# Impostazioni critiche:
# 1. "Choose how BitLocker-protected operating system drives can be recovered"
#    = Enabled
#    - Allow data recovery agent: True
#    - Configure storage of BitLocker recovery information to AD DS: Enabled
#    - "Store recovery passwords and key packages"
#    - "Do not enable BitLocker until recovery information is stored to AD DS"
#      ^^^ CRITICO: impedisce attivazione BitLocker senza backup in AD

# 2. "Configure TPM platform validation profile for native UEFI firmware"
#    = Enabled
#    - PCR 7 (Secure Boot)
#    - PCR 11 (BitLocker)
#    - NOTA: NON includere PCR 0 e PCR 2 se si prevedono aggiornamenti BIOS frequenti

# Verificare GPO applicata
gpresult /h C:\Temp\gpresult.html
# Cercare "BitLocker Drive Encryption" nella sezione Computer Configuration
```

### 4.2 Procedura aggiornamento BIOS (documentare per IT)

```powershell
# PROCEDURA STANDARD: Sospendere BitLocker PRIMA dell'aggiornamento BIOS

# Passo 1: Sospendere la protezione per un singolo reboot
Suspend-BitLocker -MountPoint C: -RebootCount 1
# -RebootCount 1 = la protezione si riattiva automaticamente dopo 1 reboot

# Passo 2: Verificare sospensione
Get-BitLockerVolume -MountPoint C: | Select-Object MountPoint, ProtectionStatus
# Deve mostrare: Protection Off

# Passo 3: Eseguire aggiornamento BIOS
# ... aggiornamento BIOS/UEFI ...

# Passo 4: Dopo il reboot, BitLocker si riattiva automaticamente
# Verificare:
Get-BitLockerVolume -MountPoint C: | Select-Object MountPoint, ProtectionStatus
# Deve mostrare: Protection On

# Per aggiornamenti che richiedono più reboot:
Suspend-BitLocker -MountPoint C: -RebootCount 3
# La protezione si riattiva dopo 3 reboot

# AUTOMAZIONE: Script per task di manutenzione BIOS (da deployare via SCCM/Intune)
# Suspend-BitLocker -MountPoint C: -RebootCount 2
# Start-Process -FilePath "BIOSUpdate.exe" -ArgumentList "/silent /reboot" -Wait
```

### 4.3 Configurare profilo PCR ottimale

```powershell
# GPO per evitare recovery trigger inutili:
# Computer Configuration > Administrative Templates > Windows Components >
#   BitLocker Drive Encryption > Operating System Drives >
#   "Configure TPM platform validation profile for native UEFI firmware configurations"

# Profilo raccomandato per ambienti con aggiornamenti BIOS frequenti:
# PCR 7 (Secure Boot State) — sufficiente per integrità boot
# PCR 11 (BitLocker access control)

# NON includere (causano recovery trigger con aggiornamenti firmware):
# PCR 0 (Core Root of Trust Measurement) — cambia con update BIOS
# PCR 2 (Extended/Pluggable code) — cambia con Option ROM update
# PCR 4 (Boot Manager) — cambia con update boot manager

# Via registry (per test, preferire GPO in produzione):
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\FVE" `
    -Name "OSPlatformValidation_UEFI" -Value 0x00000880 -Type DWord
# 0x00000880 = PCR 7 + PCR 11
```

---

## Domande di Valutazione

<details>
<summary>1. Perché un aggiornamento BIOS causa la richiesta della recovery key?</summary>

BitLocker usa il TPM per "sigillare" (seal) la chiave di crittografia del volume. Il TPM la rilascia solo se i Platform Configuration Registers (PCR) selezionati contengono gli stessi valori misurati al momento del seal. Un aggiornamento BIOS modifica il firmware, che cambia la misurazione registrata in PCR 0 (Core Root of Trust — il primo codice eseguito dopo il reset del CPU) e potenzialmente PCR 2 (codice Option ROM). Dato che i valori PCR non corrispondono più a quelli attesi, il TPM rifiuta di rilasciare la chiave (unseal fallisce) e BitLocker richiede la recovery key come fallback.
</details>

<details>
<summary>2. Qual è la differenza tra "Suspend" e "Disable" per BitLocker?</summary>

`Suspend-BitLocker` (manage-bde -protectors -disable) sospende temporaneamente la protezione: la chiave di crittografia viene salvata in chiaro sul disco, permettendo il boot senza TPM/PIN. Il volume resta crittografato. Con `-RebootCount`, la protezione si riattiva automaticamente. `Disable-BitLocker` (manage-bde -off) avvia la decrittazione completa del volume: tutti i dati vengono scritti in chiaro. Questa operazione è irreversibile senza re-crittografare l'intero disco. Per aggiornamenti BIOS, usare sempre Suspend, mai Disable.
</details>

<details>
<summary>3. Perché è critico il flag "Do not enable BitLocker until recovery information is stored to AD DS"?</summary>

Senza questo flag, un utente o un deployment automatico potrebbe abilitare BitLocker senza che la recovery key venga salvata in un luogo centralizzato. Se il TPM fallisce o l'utente dimentica il PIN, e la recovery key non è in AD/Entra/MBAM, i dati sul volume sono irrecuperabili. Il flag rende il backup della recovery key un prerequisito obbligatorio: BitLocker non si attiva finché AD DS non conferma la ricezione. Questo elimina il rischio di "BitLocker senza rete di sicurezza".
</details>

---

## Riferimenti

- [07-storage-windows.md](../07-storage-windows.md)
- [05-sicurezza-windows.md](../05-sicurezza-windows.md)
- [21-group-policy-guida-completa.md](../21-group-policy-guida-completa.md)
- Microsoft Learn — [BitLocker recovery overview](https://learn.microsoft.com/en-us/windows/security/operating-system-security/data-protection/bitlocker/recovery-overview)
- Microsoft Learn — [BitLocker Group Policy settings](https://learn.microsoft.com/en-us/windows/security/operating-system-security/data-protection/bitlocker/policy-settings)
- Microsoft Learn — [TPM fundamentals](https://learn.microsoft.com/en-us/windows/security/hardware-security/tpm/tpm-fundamentals)
