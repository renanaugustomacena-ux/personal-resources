# Batch Scripting — Guida Completa

> **Modulo 14** · **Aggiornamento:** 2026-05-22

> **Modulo del corso:** Amministrazione Windows enterprise
> **Prerequisiti:** [PowerShell](02-powershell.md) · [Registry](04-registry.md)
> **Obiettivi di apprendimento:**
> 1. Padroneggiare la sintassi CMD e le variabili d'ambiente, inclusa la delayed expansion
> 2. Scrivere script batch strutturati con gestione errori, logging e subroutine
> 3. Utilizzare Robocopy per operazioni avanzate di copia e sincronizzazione file
> 4. Automatizzare operazioni su registry, rete e task schedulati tramite batch
> 5. Integrare script batch con PowerShell per una migrazione graduale
> **Tempo stimato:** lettura 80 min · lab 50 min
> **Livello:** competent
> **Ultimo aggiornamento:** 2026-05-23

## Idee guida
1. **Batch (`.bat`/`.cmd`) e legacy.** PowerShell preferito.
2. **`@echo off` + `setlocal enabledelayedexpansion` standard.**
3. **`%errorlevel%` per check exit code.**
4. **Batch utile per scenario base / compatibility old systems.**


## Indice

- [Panoramica](#panoramica)
- [Fondamenti CMD](#fondamenti-cmd)
- [Command Parsing e Architettura CMD](#command-parsing-e-architettura-cmd)
- [Variabili e Operatori](#variabili-e-operatori)
- [Manipolazione Stringhe](#manipolazione-stringhe)
- [Control Flow](#control-flow)
- [Operazioni su File](#operazioni-su-file)
- [Operazioni su Directory](#operazioni-su-directory)
- [Robocopy — Approfondimento](#robocopy--approfondimento)
- [Elaborazione Testo](#elaborazione-testo)
- [Gestione Errori e Pattern di Logging](#gestione-errori-e-pattern-di-logging)
- [Scheduled Tasks (schtasks)](#scheduled-tasks-schtasks)
- [Operazioni sul Registry](#operazioni-sul-registry)
- [Comandi di Rete](#comandi-di-rete)
- [WMI da Batch (WMIC)](#wmi-da-batch-wmic)
- [Sicurezza negli Script Batch](#sicurezza-negli-script-batch)
- [Hardening Avanzato e Superficie di Attacco](#hardening-avanzato-e-superficie-di-attacco)
- [Interoperabilità con PowerShell](#interoperabilità-con-powershell)
- [Script Ibridi Batch+PowerShell Avanzati](#script-ibridi-batchpowershell-avanzati)
- [Script Pratici](#script-pratici)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Guida Migrazione Batch → PowerShell](#guida-migrazione-batch--powershell)
- [Ottimizzazione delle Prestazioni](#ottimizzazione-delle-prestazioni)
- [Best Practices](#best-practices)

---

## Panoramica

Batch scripting (`.bat` / `.cmd`) è il linguaggio di scripting legacy di Windows basato su CMD.exe. Nonostante PowerShell sia lo strumento moderno, batch rimane utile per: script di login GPO, task rapidi, compatibilità con sistemi legacy, WinPE/WinRE, e ambienti dove PowerShell non è disponibile. Conoscerlo è essenziale per manutenere infrastrutture esistenti.

### Differenze `.bat` vs `.cmd`

| Aspetto | `.bat` | `.cmd` |
|---------|--------|--------|
| Origine | MS-DOS, compatibilità 16-bit | Windows NT+ |
| ERRORLEVEL | Impostato solo da alcuni comandi | Impostato da ogni comando |
| Comportamento | Mantiene compatibilità COMMAND.COM | Usa solo CMD.exe |
| Raccomandazione | Solo per retrocompatibilità estrema | Preferito per script moderni |

In pratica: usare `.cmd` per script nuovi. CMD.exe tratta entrambi identicamente nella maggior parte dei casi, ma `.cmd` imposta `ERRORLEVEL` in modo più prevedibile.

### Quando usare batch nel 2026

- **WinPE / WinRE**: PowerShell non sempre disponibile.
- **Login script GPO**: supporto universale senza dipendenze.
- **Bootstrap**: avvio rapido prima di invocare PowerShell o Python.
- **Sistemi legacy**: Windows Server 2008/2012 senza PowerShell 5+.
- **Task one-liner**: operazioni triviali dove un `.bat` è più veloce di uno script `.ps1`.

---

## Fondamenti CMD

### Struttura Base

```batch
@echo off
:: Questo è un commento
REM Anche questo è un commento

echo Script iniziato
echo Data: %date% Ora: %time%

:: Pausa per leggere output
pause

:: Uscita con codice
exit /b 0
```

### `@echo off` — Anatomia

- `echo off` disabilita l'eco dei comandi (CMD non stampa ogni riga prima di eseguirla).
- `@` sopprime l'eco del comando `echo off` stesso.
- Senza `@echo off`, ogni riga dello script viene stampata a schermo prima dell'esecuzione — rumore inutile in produzione.

### Comandi Essenziali

```batch
:: Navigazione
cd /d D:\Shares                    :: Cambia drive e directory
pushd \\server\share               :: Entra in UNC path (mappa drive temporaneo)
popd                               :: Torna alla directory precedente

:: File e Directory
dir /a /s                          :: Elenco ricorsivo con attributi
mkdir "C:\Nuova Cartella"
rmdir /s /q "C:\Temp\old"         :: Rimuovi ricorsivo senza conferma
copy source.txt dest.txt
xcopy /e /i /h source\ dest\      :: Copia ricorsiva con hidden files
move file.txt D:\Archive\
del /f /q *.tmp                    :: Elimina forzato senza conferma
ren oldname.txt newname.txt
attrib +r +h file.txt              :: Imposta attributi read-only e hidden

:: Redirezione output
command > file.txt                 :: Sovrascrive
command >> file.txt                :: Appende
command 2> errors.txt              :: Solo stderr
command > output.txt 2>&1          :: Tutto (stdout + stderr)
command > nul 2>&1                 :: Scarta tutto l'output

:: Pipe
dir | find "txt"
type file.txt | sort
netstat -an | findstr "LISTENING"
```

### Command Extensions

Le command extensions sono abilitate di default su Windows 2000+ e aggiungono funzionalità a comandi come `IF`, `FOR`, `SET`, `CALL`. Verificare e controllare:

```batch
:: Verificare se abilitate
echo %CMDEXTVERSION%

:: Abilitare esplicitamente (raramente necessario)
cmd /e:on

:: Disabilitare (quasi mai utile)
cmd /e:off

:: Dentro uno script
setlocal enableextensions
:: ... comandi con extensions ...
endlocal
```

Senza extensions, `IF /I`, `IF DEFINED`, `SET /A`, `FOR /F` e molti altri non funzionano. In pratica, lasciarle sempre abilitate.

---

## Command Parsing e Architettura CMD

### Come CMD.exe processa una riga

CMD.exe esegue il parsing in fasi ordinate. Comprendere l'ordine è critico per evitare bug sottili:

1. **Espansione variabili `%VAR%`** — prima di tutto, le variabili tra `%` vengono sostituite col loro valore corrente.
2. **Espansione `FOR` `%%var`** — le variabili di iterazione del `FOR` vengono sostituite.
3. **Analisi della riga** — CMD identifica comandi, operatori, pipe, redirezioni.
4. **Delayed expansion `!VAR!`** — se abilitata, le variabili tra `!` vengono espanse ora (dopo il parsing).
5. **Esecuzione** — il comando viene eseguito.

Questo spiega perché `%VAR%` non funziona correttamente dentro un blocco `FOR` o `IF`: il valore viene fissato al passo 1, prima che il loop o il blocco venga effettivamente iterato. Serve `!VAR!` con delayed expansion.

### Escape e caratteri speciali

```batch
:: Caratteri speciali che richiedono escape con ^
echo Prezzo ^> 100         :: > è operatore redirect, ^ lo escapa
echo A ^& B                :: & è operatore AND
echo Percentuale: 50%%     :: % si escapa con %%
echo Pipe ^| test           :: | è operatore pipe
echo Parentesi ^( ^)       :: ( ) sono delimitatori di blocco

:: Dentro stringhe con apici doppi, meno escape necessari
echo "Prezzo > 100 & sconto"

:: Newline con ^ (continuazione su riga successiva)
robocopy "D:\Source" "E:\Dest" /MIR ^
    /R:3 /W:5 ^
    /LOG:backup.log
```

### Separatori di comandi

```batch
:: & esegue il secondo comando indipendentemente dal primo
dir C:\Temp & echo Fatto

:: && esegue il secondo solo se il primo ha successo (ERRORLEVEL 0)
mkdir C:\NuovaDir && echo Directory creata

:: || esegue il secondo solo se il primo fallisce (ERRORLEVEL != 0)
ping -n 1 10.0.0.1 >nul || echo Host irraggiungibile

:: Combinazione (pattern try/catch)
robocopy src dest /MIR && echo OK || echo FALLITO
```

---

## Variabili e Operatori

### SET — Assegnazione base

```batch
:: Impostare variabile (NIENTE spazi intorno a =)
set NOME=Mario
set COGNOME=Rossi

:: ERRORE COMUNE: spazio prima di =
set NOME =Mario          :: crea variabile "NOME " (con spazio!)

:: ERRORE COMUNE: spazio dopo =
set NOME= Mario          :: valore è " Mario" (con spazio iniziale!)

:: Usare variabile
echo %NOME%
echo Risultato: %RESULT%

:: Cancellare variabile
set NOME=
:: oppure
set "NOME="

:: Elencare tutte le variabili che iniziano con...
set N                    :: mostra tutte le variabili che iniziano con N
set                      :: mostra TUTTE le variabili d'ambiente
```

### SET /A — Aritmetica

```batch
:: Operazioni aritmetiche
set /a COUNTER=0
set /a RESULT=5+3
set /a RESULT=10-4
set /a RESULT=6*7
set /a RESULT=100/3        :: divisione intera = 33
set /a RESULT=100%%3       :: modulo = 1 (nota: %% in batch file, % al prompt)

:: Operatori compound
set /a COUNTER+=1          :: incremento
set /a COUNTER-=1          :: decremento
set /a VALUE*=2            :: moltiplica per 2
set /a VALUE/=4            :: dividi per 4

:: Operazioni bitwise
set /a RESULT=0xFF         :: esadecimale → 255
set /a RESULT=0377         :: ottale → 255
set /a RESULT=5^&3         :: AND bitwise = 1
set /a RESULT=5^|3         :: OR bitwise = 7
set /a RESULT=5^^3         :: XOR bitwise = 6
set /a RESULT=^~5          :: NOT bitwise
set /a RESULT=1^<^<4       :: shift left = 16
set /a RESULT=16^>^>2      :: shift right = 4

:: Espressioni multiple
set /a "X=5, Y=10, Z=X+Y"
echo %Z%                   :: 15

:: Parentesi
set /a RESULT=(5+3)*2      :: 16

:: LIMITAZIONE: solo aritmetica intera a 32 bit (-2147483648 a 2147483647)
:: Nessun supporto floating point
```

### SET /P — Input utente

```batch
:: Input utente
set /p RISPOSTA=Inserisci il tuo nome:
echo Ciao %RISPOSTA%

:: Con valore default (validazione manuale)
set "SCELTA=N"
set /p SCELTA=Continuare? [S/N] (default N):
if /i "%SCELTA%"=="S" echo Proseguiamo...

:: Leggere da file (primo riga)
set /p PRIMA_RIGA=<input.txt

:: ATTENZIONE SICUREZZA: set /p è vulnerabile a injection
:: Vedere sezione "Sicurezza negli Script Batch"
```

### Variabili d'ambiente predefinite

```batch
:: Sistema
echo Computer: %COMPUTERNAME%
echo Utente: %USERNAME%
echo Dominio: %USERDOMAIN%
echo Home: %USERPROFILE%
echo Temp: %TEMP%
echo OS: %OS%
echo Path: %PATH%
echo Data: %DATE%
echo Ora: %TIME%
echo Random: %RANDOM%            :: numero casuale 0-32767
echo CD: %CD%                    :: directory corrente
echo Arch: %PROCESSOR_ARCHITECTURE%

:: Locazioni
echo AppData: %APPDATA%
echo LocalAppData: %LOCALAPPDATA%
echo ProgramFiles: %ProgramFiles%
echo ProgramFiles(x86): %ProgramFiles(x86)%
echo SystemRoot: %SystemRoot%
echo WinDir: %WINDIR%
echo SystemDrive: %SystemDrive%
echo Public: %PUBLIC%

:: Script-specific
echo Script: %~f0                :: percorso completo dello script
echo ScriptDir: %~dp0           :: directory dello script
echo ScriptName: %~nx0          :: nome + estensione dello script
```

### Scope e `setlocal` / `endlocal`

```batch
:: Variabili con scope locale
setlocal
set LOCAL_VAR=valore
echo Dentro: %LOCAL_VAR%
endlocal
:: LOCAL_VAR non esiste più qui

:: Passare un valore oltre endlocal (trick)
setlocal
set "RISULTATO=42"
endlocal & set "RISULTATO=%RISULTATO%"
:: RISULTATO è ancora disponibile (espanso prima di endlocal)

:: Nesting di setlocal
setlocal
set A=1
    setlocal
    set B=2
    echo A=%A% B=%B%
    endlocal
:: B non esiste più, A ancora sì
endlocal
:: Neanche A esiste più
```

### Delayed Expansion

```batch
:: PROBLEMA: %VAR% viene espansa PRIMA dell'esecuzione del blocco
set COUNT=0
for %%f in (*.txt) do (
    set /a COUNT+=1
    echo File %COUNT%: %%f     :: stampa SEMPRE 0!
)

:: SOLUZIONE: delayed expansion con !VAR!
setlocal enabledelayedexpansion
set COUNT=0
for %%f in (*.txt) do (
    set /a COUNT+=1
    echo File !COUNT!: %%f     :: stampa il valore aggiornato
)
echo Totale file: !COUNT!
endlocal

:: Delayed expansion in blocchi IF
setlocal enabledelayedexpansion
set STATO=iniziale
if 1==1 (
    set STATO=modificato
    echo Con %%: %STATO%       :: stampa "iniziale"
    echo Con !!: !STATO!       :: stampa "modificato"
)
endlocal
```

### Sostituzione variabili `%VAR:old=new%`

```batch
set PATH_UNIX=/home/user/docs
echo %PATH_UNIX:/=\%          :: \home\user\docs

set FRASE=il gatto mangia il pesce
echo %FRASE:gatto=cane%       :: il cane mangia il pesce

:: Rimuovere testo (sostituire con nulla)
set STR=   spazi   iniziali
echo %STR: =%                 :: spaziiniziali (rimuove TUTTI gli spazi)

:: Case-insensitive
set MSG=Hello World
echo %MSG:hello=CIAO%         :: CIAO World (funziona indipendente dal case)
```

### Parametri Script

```batch
:: %0 = nome script, %1-%9 = parametri posizionali
:: %* = tutti i parametri

@echo off
echo Script: %~nx0
echo Parametro 1: %1
echo Parametro 2: %2
echo Tutti: %*

:: Modificatori parametri:
:: %~f1  = Full path
:: %~d1  = Drive letter
:: %~p1  = Path senza drive
:: %~n1  = Nome file senza estensione
:: %~x1  = Solo estensione
:: %~s1  = Short name (8.3)
:: %~a1  = Attributi file
:: %~t1  = Data/ora modifica
:: %~z1  = Dimensione file
:: %~dp1 = Drive + path (directory del file)
:: %~nx1 = Nome + estensione

:: Combinazioni utili
echo Directory del parametro 1: %~dp1
echo Nome completo: %~nx1
echo Path completo: %~f1

:: Shift per accedere a parametri oltre %9
:loop
if "%1"=="" goto :end
echo Param: %1
shift
goto :loop
:end
```

---

## Manipolazione Stringhe

### Substring `%VAR:~start,length%`

```batch
set STR=Hello World

:: Estrazione con posizione e lunghezza
echo %STR:~0,5%          :: Hello (primi 5 caratteri)
echo %STR:~6%            :: World (dal carattere 6 in poi)
echo %STR:~6,3%          :: Wor (3 caratteri a partire dal 6)

:: Indici negativi (dalla fine)
echo %STR:~-5%           :: World (ultimi 5 caratteri)
echo %STR:~-5,3%         :: Wor (3 caratteri, partendo da -5)
echo %STR:~0,-3%         :: Hello Wo (tutto tranne ultimi 3)

:: Estrarre data formattata (dipende dal locale!)
set TODAY=%DATE%
:: Formato italiano tipico: gg/mm/aaaa
set ANNO=%DATE:~-4%
set MESE=%DATE:~3,2%
set GIORNO=%DATE:~0,2%
echo %ANNO%-%MESE%-%GIORNO%     :: 2026-05-22

:: Estrarre ora
set ORA=%TIME:~0,2%
set MINUTI=%TIME:~3,2%
set SECONDI=%TIME:~6,2%
echo %ORA%:%MINUTI%:%SECONDI%
```

### Sostituzione e Rimozione

```batch
set STR=Hello World
echo %STR:World=Mondo%   :: Hello Mondo (sostituzione)

:: Rimuovere spazi iniziali (trick con for)
set "VAR=   testo con spazi"
for /f "tokens=*" %%a in ("%VAR%") do set "VAR=%%a"

:: Rimuovere virgolette
set STR="testo tra virgolette"
set STR=%STR:"=%
echo %STR%                :: testo tra virgolette

:: Rimuovere estensione
set FILE=documento.txt
set NOME=%FILE:.txt=%
echo %NOME%               :: documento
```

### Concatenazione

```batch
:: Concatenazione diretta
set A=Hello
set B=World
set C=%A% %B%
echo %C%                  :: Hello World

:: Costruire path
set BASE=C:\Users
set USER=Mario
set FULLPATH=%BASE%\%USER%\Documents
echo %FULLPATH%

:: Costruire stringhe in loop
setlocal enabledelayedexpansion
set LISTA=
for %%f in (*.txt) do (
    set "LISTA=!LISTA! %%f"
)
echo File trovati:%LISTA%
endlocal
```

### Lunghezza stringa (workaround — batch non ha funzione nativa)

```batch
@echo off
setlocal enabledelayedexpansion

set "STR=Hello World"
set "LEN=0"
set "TMP=%STR%"

:strlen_loop
if defined TMP (
    set "TMP=!TMP:~1!"
    set /a LEN+=1
    goto :strlen_loop
)
echo Lunghezza: %LEN%     :: 11
endlocal
```

### Conversione maiuscolo/minuscolo (workaround)

Batch non ha conversione case nativa. Workaround con `FOR /F`:

```batch
@echo off
:: Uppercase tramite sostituzione manuale
set "STR=hello world"
set "UPPER=%STR%"
for %%a in (a b c d e f g h i j k l m n o p q r s t u v w x y z) do (
    call set "UPPER=%%UPPER:%%a=%%a%%"
)
:: Questo richiede una tabella di mapping completa
:: Alternativa più pratica: usare PowerShell per la conversione
for /f "delims=" %%a in ('powershell -c "'%STR%'.ToUpper()"') do set "UPPER=%%a"
echo %UPPER%              :: HELLO WORLD
```

---

## Control Flow

### IF / ELSE

```batch
:: IF base
if "%1"=="" (
    echo Uso: %~nx0 ^<parametro^>
    exit /b 1
)

:: IF EXIST — verifica esistenza file o directory
if exist "C:\file.txt" (
    echo File trovato
) else (
    echo File non trovato
)

:: IF EXIST su directory (deve terminare con \)
if exist "C:\Users\Mario\" (
    echo Directory esiste
)

:: IF DEFINED — verifica se variabile è definita
if defined JAVA_HOME (
    echo Java trovato: %JAVA_HOME%
) else (
    echo JAVA_HOME non configurato
)

:: IF NOT — negazione
if not exist "C:\file.txt" echo File mancante
if not defined MYVAR echo Variabile non definita
if not "%1"=="" echo Parametro fornito: %1

:: Confronto numerico
if %ERRORLEVEL% equ 0 echo Successo
if %ERRORLEVEL% neq 0 echo Errore: %ERRORLEVEL%
:: EQU=uguale, NEQ=diverso, LSS=minore, LEQ=minore-uguale
:: GTR=maggiore, GEQ=maggiore-uguale

:: Confronto stringhe (case-insensitive con /i)
if /i "%RISPOSTA%"=="si" echo Confermato
if /i "%RISPOSTA%"=="yes" echo Confirmed

:: ERRORLEVEL — due sintassi
ping -n 1 192.168.10.1 > nul
if %ERRORLEVEL% equ 0 (echo Host raggiungibile) else (echo Host non raggiungibile)

:: Sintassi legacy (vera se ERRORLEVEL >= valore)
if errorlevel 1 echo Errore (livello >= 1)
:: ATTENZIONE: "if errorlevel 1" è TRUE anche per errorlevel 2, 3, ecc.

:: Operatori logici con IF (AND simulato con IF nidificati)
if exist "file1.txt" if exist "file2.txt" echo Entrambi esistono

:: OR simulato (più complesso)
set FOUND=0
if exist "file1.txt" set FOUND=1
if exist "file2.txt" set FOUND=1
if %FOUND%==1 echo Almeno uno esiste
```

### IF ERRORLEVEL — Pattern comuni

```batch
:: Pattern 1: check esplicito dopo ogni comando critico
net stop wuauserv
if %ERRORLEVEL% neq 0 (
    echo ERRORE: impossibile fermare il servizio
    exit /b %ERRORLEVEL%
)

:: Pattern 2: condizionale inline
net start wuauserv && echo Servizio avviato || echo Avvio fallito

:: Pattern 3: gestione multi-livello
xcopy source dest /e /i /h
if %ERRORLEVEL% equ 0 echo Copia completata senza errori
if %ERRORLEVEL% equ 1 echo Nessun file da copiare
if %ERRORLEVEL% equ 2 echo Interrotto dall'utente (CTRL+C)
if %ERRORLEVEL% equ 4 echo Errore di inizializzazione
if %ERRORLEVEL% equ 5 echo Errore di scrittura disco
```

### FOR Loops

```batch
:: File in directory
for %%f in (C:\Logs\*.log) do echo %%f

:: Ricorsivo (/R) — cerca in tutte le sottodirectory
for /r "C:\Logs" %%f in (*.log) do echo %%f

:: Solo in una directory specifica
for /r "C:\Logs" %%f in (*.log) do (
    echo File: %%~nxf
    echo Dimensione: %%~zf bytes
    echo Data: %%~tf
)

:: Directory (/D) — solo directory
for /d %%d in (C:\Users\*) do echo Directory: %%d

:: Ricorsivo su directory
for /d /r "C:\Projects" %%d in (*) do echo %%d

:: Numerico (/L) — for (start, step, end)
for /l %%i in (1,1,10) do echo Numero %%i
for /l %%i in (10,-1,1) do echo Countdown: %%i
for /l %%i in (0,2,20) do echo Pari: %%i

:: Parsing file (/F)
for /f "tokens=1,2 delims=," %%a in (data.csv) do echo Nome: %%a Cognome: %%b

:: Parsing con skip e eol
for /f "skip=1 eol=# tokens=1-3 delims=;" %%a in (config.ini) do (
    echo Chiave: %%a  Valore: %%b  Commento: %%c
)

:: Parsing output comando (usebackq per comandi tra backtick)
for /f "tokens=*" %%a in ('dir /b *.txt') do echo %%a

:: usebackq permette di usare "..." per nomi file con spazi
for /f "usebackq tokens=*" %%a in ("file con spazi.txt") do echo %%a

:: Variabili FOR: %%a, %%b, %%c sono consecutive
:: tokens=1,3,5 → %%a=token1, %%b=token3, %%c=token5
:: tokens=2-4 → %%a=token2, %%b=token3, %%c=token4
:: tokens=1* → %%a=token1, %%b=resto della riga
```

### GOTO, CALL e Label

```batch
:: GOTO — salto incondizionato
goto :sezione_due

:sezione_due
echo Sezione due
call :funzione "parametro"
goto :eof

:: CALL — invoca subroutine (ritorna al chiamante)
:funzione
echo Funzione chiamata con: %1
exit /b 0

:: CALL con ritorno di valore
call :somma 5 3 RISULTATO
echo Somma: %RISULTATO%
goto :eof

:somma
set /a %3=%1+%2
exit /b 0

:: CALL ad altro batch (il controllo torna dopo)
call altro_script.bat arg1 arg2
echo Ritorno da altro_script, ERRORLEVEL=%ERRORLEVEL%

:: Senza CALL, il controllo NON torna:
:: another.bat arg1    ← esecuzione non torna mai!
:: call another.bat    ← esecuzione torna dopo another.bat

:: Menu con GOTO
:menu
echo 1. Opzione A
echo 2. Opzione B
echo 3. Esci
set /p SCELTA=Seleziona:
if "%SCELTA%"=="1" goto :opzione_a
if "%SCELTA%"=="2" goto :opzione_b
if "%SCELTA%"=="3" goto :eof
echo Scelta non valida
goto :menu

:opzione_a
echo Hai scelto A
goto :menu

:opzione_b
echo Hai scelto B
goto :menu
```

### Loop con contatore e condizione di uscita

```batch
@echo off
setlocal enabledelayedexpansion

:: Retry loop con timeout
set MAX_RETRY=5
set RETRY=0

:retry_loop
set /a RETRY+=1
echo Tentativo !RETRY! di %MAX_RETRY%...

ping -n 1 192.168.1.1 >nul 2>&1
if !ERRORLEVEL! equ 0 (
    echo Connessione riuscita al tentativo !RETRY!
    goto :retry_done
)

if !RETRY! geq %MAX_RETRY% (
    echo ERRORE: tutti i tentativi falliti
    exit /b 1
)

:: Attendi 5 secondi prima del retry
timeout /t 5 /nobreak >nul
goto :retry_loop

:retry_done
echo Operazione completata
endlocal
```

---

## Operazioni su File

### COPY

```batch
:: Copia base
copy source.txt dest.txt

:: Copia con conferma sovrascrittura (default)
copy file.txt C:\Backup\

:: Copia senza conferma
copy /y file.txt C:\Backup\

:: Copia binaria
copy /b image.jpg C:\Backup\image.jpg

:: Unire file
copy /b file1.txt + file2.txt merged.txt

:: Copia con verifica
copy /v source.txt dest.txt
```

### XCOPY

```batch
:: Copia ricorsiva con directory vuote
xcopy /e /i /h "C:\Source" "D:\Dest"

:: Opzioni principali
:: /E   → Include subdirectory vuote
:: /S   → Subdirectory (escluse vuote)
:: /I   → Se destinazione non esiste, assume directory
:: /H   → Include file hidden e system
:: /Y   → Non chiedere conferma sovrascrittura
:: /D   → Solo file più recenti della destinazione
:: /R   → Sovrascrive file read-only
:: /K   → Mantiene attributi
:: /C   → Continua anche dopo errori
:: /Q   → Non mostra nomi file durante la copia
:: /L   → Lista file senza copiare (dry-run)

:: Esempio: copia incrementale solo file modificati
xcopy /e /i /h /y /d "C:\Projects" "D:\Backup\Projects"
```

### MKLINK — Link simbolici e hard link

```batch
:: Link simbolico a file (richiede privilegi elevati)
mklink "C:\link.txt" "D:\target.txt"

:: Link simbolico a directory
mklink /d "C:\LinkDir" "D:\TargetDir"

:: Hard link (solo file, stessa partizione)
mklink /h "C:\hardlink.txt" "D:\target.txt"

:: Junction (directory, stessa macchina)
mklink /j "C:\Junction" "D:\TargetDir"

:: Verificare link
dir /al     :: lista tutti i link
```

### ATTRIB — Attributi file

```batch
:: Mostrare attributi
attrib file.txt

:: Attributi disponibili:
:: R = Read-only
:: A = Archive
:: S = System
:: H = Hidden
:: I = Not Content Indexed

:: Impostare attributi
attrib +r +h file.txt           :: read-only e hidden
attrib -r -h file.txt           :: rimuovi read-only e hidden

:: Ricorsivo
attrib +r /s /d "C:\Protetti\*.*"

:: Rimuovere hidden da tutti i file in una directory
attrib -h -s /s /d "D:\USBDrive\*.*"
```

### FORFILES — Operazioni basate su data

```batch
:: Elimina file più vecchi di 30 giorni
forfiles /p "C:\Logs" /s /m *.log /d -30 /c "cmd /c del @path"

:: Lista file modificati negli ultimi 7 giorni
forfiles /p "C:\Projects" /s /d +7 /c "cmd /c echo @path @fdate"

:: Variabili FORFILES:
:: @path  = percorso completo
:: @fname = nome file con apici
:: @fdate = data modifica
:: @fsize = dimensione
:: @isdir = TRUE se directory
:: @ext   = estensione

:: Archivia file vecchi prima di eliminarli
forfiles /p "C:\Logs" /s /m *.log /d -90 /c "cmd /c move @path C:\Archive\"
```

---

## Operazioni su Directory

### DIR — Elenco directory

```batch
:: Elenco base
dir

:: Opzioni utili
dir /a                :: mostra file hidden e system
dir /ad               :: solo directory
dir /ah               :: solo file hidden
dir /a-d              :: solo file (no directory)
dir /s                :: ricorsivo
dir /b                :: solo nomi (bare format, per pipe)
dir /o:n              :: ordinato per nome
dir /o:d              :: ordinato per data
dir /o:s              :: ordinato per dimensione
dir /o:-d             :: ordinato per data decrescente
dir /q                :: mostra proprietario
dir /r                :: mostra alternate data streams
dir /x                :: mostra nomi 8.3

:: Cercare file ricorsivamente
dir /s /b "C:\*.config"

:: Dimensione totale directory
dir /s "C:\Users\Mario\Documents" | findstr "File(s)"
```

### MD / MKDIR — Creazione directory

```batch
:: Crea directory (e parent se non esistono)
md "C:\Projects\2026\Q1\Reports"
:: Crea tutto il percorso senza errore se già esiste

:: Verificare prima di creare (buona pratica)
if not exist "C:\Logs" md "C:\Logs"
```

### RD / RMDIR — Rimozione directory

```batch
:: Rimuovi directory vuota
rd "C:\Temp\old"

:: Rimuovi directory con contenuto (ATTENZIONE: irreversibile!)
rd /s /q "C:\Temp\old"
:: /s = ricorsivo (include sottodirectory e file)
:: /q = quiet (nessuna conferma)
```

### PUSHD / POPD — Stack di directory

```batch
:: Salva directory corrente e cambia
pushd "C:\Projects\webapp"
echo Ora siamo in: %CD%

:: Funziona anche con UNC path (mappa drive temporaneo)
pushd \\server\share
echo Mappato come: %CD%

:: Torna alla directory precedente
popd

:: Nesting multiplo
pushd C:\Dir1
pushd C:\Dir2
pushd C:\Dir3
echo In Dir3
popd
echo In Dir2
popd
echo In Dir1
popd
echo Tornati alla directory originale
```

### TREE — Visualizzazione struttura

```batch
:: Albero directory
tree C:\Projects

:: Con file
tree /f C:\Projects

:: Output su file
tree /f /a C:\Projects > struttura.txt
:: /a = usa caratteri ASCII (non Unicode)
```

---

## Robocopy — Approfondimento

### Sintassi e uso base

```batch
:: Robocopy è lo strumento di copia file più potente in Windows

:: Sintassi: robocopy <source> <dest> [file] [opzioni]

:: Mirror (copia esatta — cancella file extra nella destinazione)
robocopy "D:\Source" "E:\Backup" /MIR /R:3 /W:5 /LOG:C:\Logs\robocopy.log

:: Copia ricorsiva senza cancellare
robocopy "D:\Source" "E:\Backup" /E /R:3 /W:5

:: Con permessi NTFS
robocopy "D:\Source" "E:\Backup" /E /COPYALL /R:3 /W:5
:: /COPY:DAT = Data, Attributes, Timestamps (default)
:: /COPYALL = /COPY:DATSOU (Data, Attributes, Timestamps, Security, Owner, aUditing)
:: /SEC = /COPY:DATS (include Security/NTFS permissions)
```

### Flag completi

```batch
:: === SELEZIONE FILE ===
:: /E          → Include subdirectory vuote
:: /S          → Subdirectory (escluse vuote)
:: /MIR        → Mirror (come /E /PURGE — cancella extra nella dest)
:: /PURGE      → Cancella file nella dest che non esistono nella source
:: /XF file    → Escludi file (wildcard supportati)
:: /XD dir     → Escludi directory
:: /XC         → Escludi file Changed
:: /XN         → Escludi file Newer
:: /XO         → Escludi file Older
:: /XX         → Escludi file eXtra (presenti solo in dest)
:: /XL         → Escludi file Lonely (presenti solo in source)
:: /MAXAGE:n   → Solo file modificati negli ultimi n giorni (o data YYYYMMDD)
:: /MINAGE:n   → Solo file più vecchi di n giorni
:: /MAXLAD:n   → Solo file con ultimo accesso < n giorni
:: /MINLAD:n   → Solo file con ultimo accesso > n giorni
:: /MAX:n      → Solo file con dimensione <= n byte
:: /MIN:n      → Solo file con dimensione >= n byte
:: /IS         → Include Same files
:: /IT         → Include Tweaked files (stessi dati, timestamp diversi)
:: /A          → Solo file con attributo Archive
:: /M          → Come /A ma resetta attributo Archive dopo copia

:: === COPIA ===
:: /COPY:flags → Cosa copiare (D=data, A=attrib, T=timestamp, S=security, O=owner, U=audit)
:: /COPYALL    → /COPY:DATSOU
:: /SEC        → /COPY:DATS
:: /DCOPY:T    → Copia timestamp directory
:: /DCOPY:DAT  → Copia Data, Attrib, Timestamp directory

:: === PERFORMANCE ===
:: /MT:n       → Multi-thread (n thread, default 8 se /MT senza numero)
:: /IPG:ms     → Inter-packet gap (limita banda, ms tra pacchetti)
:: /J          → Copia usando unbuffered I/O (file grandi)
:: /NOOFFLOAD  → Disabilita offloaded data transfer

:: === RETRY E ATTESA ===
:: /R:n        → Retry n volte per file falliti (default 1000000!)
:: /W:n        → Wait n secondi tra retry (default 30)
:: /REG        → Salva /R:n e /W:n nel registry come default
:: /TBD        → Wait for sharenames To Be Defined (retry se share offline)

:: === MONITOR ===
:: /MON:n      → Monitora: riesegui dopo n cambiamenti
:: /MOT:m      → Monitora: riesegui ogni m minuti
:: /RH:hhmm-hhmm → Ore di esecuzione (es. /RH:0200-0600)

:: === RESUME E BACKUP ===
:: /Z          → Restartable mode (riprendi transfer interrotti, più lento)
:: /B          → Backup mode (usa SeBackupPrivilege, ignora ACL)
:: /ZB         → Restartable + Backup fallback
:: /EFSRAW     → Copia file EFS in raw mode

:: === LOGGING ===
:: /LOG:file   → Log su file (sovrascrive)
:: /LOG+:file  → Appende al log
:: /TEE        → Output su console E log file
:: /NP         → Non mostrare percentuale
:: /NFL        → Non listare file
:: /NDL        → Non listare directory
:: /NJH        → Non mostrare header
:: /NJS        → Non mostrare summary
:: /V          → Verbose output
:: /FP         → Include Full Pathname nel log
:: /BYTES      → Mostra dimensioni in bytes
:: /TS         → Mostra timestamp nel log
:: /UNICODE    → Output in Unicode
:: /UNILOG:file → Log Unicode
```

### Exit code robocopy

```batch
:: Exit codes robocopy (DIVERSI dagli standard!):
:: 0 = Nessun file copiato, nessun errore, nessun mismatch, source e dest sincronizzati
:: 1 = File copiati con successo
:: 2 = File extra nella destinazione rilevati (con /PURGE o /MIR sarebbero eliminati)
:: 3 = 1+2 — file copiati e extra rilevati
:: 4 = File o directory mismatched rilevati
:: 5 = 1+4
:: 6 = 2+4
:: 7 = 1+2+4
:: 8 = Errore durante la copia (almeno un file non copiato)
:: 16 = Errore fatale (nessun file copiato, errore di sintassi o permessi)
:: NOTA: exit code 1-7 sono SUCCESSI. Solo >= 8 sono errori.

:: In batch, verificare correttamente:
robocopy "source" "dest" /MIR
if %ERRORLEVEL% GEQ 8 (
    echo ERRORE nel backup [exit code %ERRORLEVEL%]
    exit /b 1
) else (
    echo Backup OK [exit code %ERRORLEVEL%]
    exit /b 0
)
```

### Pattern di backup avanzati

```batch
:: Backup notturno con esclusioni e log datato
robocopy "D:\Shares" "E:\Backup\Shares" /MIR /SEC /MT:8 /R:3 /W:10 ^
    /XD "D:\Shares\Temp" "D:\Shares\Cache" ^
    /XF *.tmp *.bak *.log thumbs.db desktop.ini ^
    /LOG:"C:\Logs\backup-%date:~-4%-%date:~3,2%-%date:~0,2%.log" /TEE /NP

:: Backup incrementale (solo file nuovi/modificati)
robocopy "D:\Source" "E:\Backup" /E /XO /R:3 /W:5 /MT:16 /NP ^
    /LOG+:"C:\Logs\incremental.log"

:: Replica con banda limitata (utile per WAN)
robocopy "D:\Source" "\\RemoteServer\Backup" /MIR /Z /IPG:100 ^
    /R:5 /W:30 /LOG:"C:\Logs\wan-backup.log" /TEE

:: Solo durante ore non lavorative
robocopy "D:\Source" "E:\Backup" /MIR /RH:2200-0600 ^
    /LOG:"C:\Logs\offhours.log" /TEE

:: Monitoring continuo (riesegui ogni 60 minuti)
robocopy "D:\Source" "E:\Backup" /MIR /MOT:60 ^
    /LOG:"C:\Logs\monitor.log" /TEE
```

---

## Elaborazione Testo

### FIND — Ricerca semplice

```batch
:: Cerca stringa in un file
find "errore" logfile.txt

:: Case-insensitive
find /i "warning" logfile.txt

:: Conta occorrenze
find /c "ERROR" logfile.txt

:: Inverso (righe che NON contengono)
find /v "DEBUG" logfile.txt

:: Numera le righe
find /n "CRITICAL" logfile.txt

:: Da pipe
type logfile.txt | find "timeout"
```

### FINDSTR — Ricerca con regex

```batch
:: Ricerca regex base
findstr "^Error" logfile.txt                :: righe che iniziano con Error

:: Case-insensitive
findstr /i "warning" logfile.txt

:: Regex completa
findstr /r "^[0-9][0-9]*\." logfile.txt     :: righe che iniziano con numeri

:: Ricorsivo in tutti i file
findstr /s /i "password" "C:\Scripts\*.bat"  :: ATTENZIONE: solo per audit!

:: Stringa letterale (no regex)
findstr /l /c:"parola esatta" file.txt
:: /c: permette spazi nella stringa di ricerca

:: Classe di regex FINDSTR (limitata):
:: .     → qualsiasi carattere
:: *     → zero o più ripetizioni del precedente
:: ^     → inizio riga
:: $     → fine riga
:: [abc] → classe di caratteri
:: [a-z] → range
:: [^abc]→ negazione classe
:: \<    → inizio parola
:: \>    → fine parola

:: Più stringhe (OR)
findstr "errore warning critico" logfile.txt

:: Più file
findstr /i "TODO FIXME HACK" *.bat *.cmd

:: Output su file
findstr /i /s "Exception" "C:\Logs\*.log" > eccezioni_trovate.txt

:: Contesto: mostrare numero riga
findstr /n /i "error" logfile.txt
```

### SORT

```batch
:: Ordinamento base
sort file.txt

:: Inverso
sort /r file.txt

:: Da colonna specifica (offset carattere)
sort /+10 file.txt     :: ordina dal carattere 10

:: Pipe
dir /b | sort
dir /b | sort /r

:: Output su file
sort input.txt /o output.txt
```

### MORE — Paginazione

```batch
:: Mostra file pagina per pagina
more file.txt

:: Da pipe
dir /s | more
type longfile.txt | more

:: Opzioni
more /e /c /p file.txt
:: /e = comandi estesi (spazio, invio, Q, =, P, S, F)
:: /c = pulisce schermo prima di ogni pagina
:: /p = espande form feed
```

### FOR /F — Parsing file e output comandi

```batch
:: Parsing CSV
for /f "tokens=1-4 delims=," %%a in (utenti.csv) do (
    echo Nome: %%a Email: %%b Ruolo: %%c Stato: %%d
)

:: Parsing output comando
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr "IPv4"') do (
    set IP=%%a
    echo IP trovato: !IP!
)

:: Parsing con skip di header
for /f "skip=2 tokens=1-3" %%a in ('netstat -an') do (
    echo Proto: %%a  Locale: %%b  Remoto: %%c
)

:: Leggere file riga per riga
for /f "delims=" %%a in (config.txt) do (
    echo Riga: %%a
)

:: Ignorare righe di commento
for /f "eol=# delims=" %%a in (config.ini) do (
    echo %%a
)

:: Leggere da file con spazi nel nome (usebackq)
for /f "usebackq delims=" %%a in ("file con spazi.txt") do echo %%a

:: Contare righe in un file
set LINES=0
for /f %%a in ('type file.txt ^| find /c /v ""') do set LINES=%%a
echo Righe: %LINES%
```

---

## Gestione Errori e Pattern di Logging

### ERRORLEVEL — Meccanismo centrale

```batch
:: Ogni comando esterno imposta %ERRORLEVEL%
:: 0 = successo, != 0 = errore (convenzione, non regola assoluta)

:: Cattura e verifica
xcopy source dest /e /i /y
set XCOPY_RESULT=%ERRORLEVEL%
echo XCopy terminato con codice: %XCOPY_RESULT%

:: TRAPPOLA: "if errorlevel N" è TRUE per ERRORLEVEL >= N
:: Preferire la sintassi esplicita:
if %ERRORLEVEL% equ 0 echo OK
if %ERRORLEVEL% neq 0 echo ERRORE
```

### Esecuzione condizionale `&&` e `||`

```batch
:: && = esegui se precedente ha successo
mkdir C:\NuovaDir && echo Creata con successo

:: || = esegui se precedente fallisce
mkdir C:\NuovaDir || echo Creazione fallita

:: Combinazione (pattern try/catch minimo)
ping -n 1 server01 >nul && (
    echo Server raggiungibile
    net use Z: \\server01\share
) || (
    echo Server NON raggiungibile - skip
)
```

### Pattern di logging strutturato

```batch
@echo off
setlocal enabledelayedexpansion

:: Configurazione log
set LOGFILE=C:\Logs\script_%date:~-4%%date:~3,2%%date:~0,2%.log
set LOGLEVEL=INFO

:: Funzione di log
call :log "INFO" "Script avviato"
call :log "INFO" "Utente: %USERNAME% su %COMPUTERNAME%"

:: ... operazioni ...
robocopy src dest /mir >nul 2>&1
if !ERRORLEVEL! geq 8 (
    call :log "ERROR" "Backup fallito con codice !ERRORLEVEL!"
) else (
    call :log "INFO" "Backup completato [code=!ERRORLEVEL!]"
)

call :log "INFO" "Script terminato"
goto :eof

:log
:: Parametri: %1=livello, %2=messaggio
set "TIMESTAMP=%date% %time:~0,8%"
echo [%TIMESTAMP%] [%~1] %~2
echo [%TIMESTAMP%] [%~1] %~2 >> "%LOGFILE%"
exit /b 0
```

### Framework di logging avanzato

Il logging di base con timestamp derivato da `%date%` e `%time%` soffre di un problema critico: il formato dipende dalle impostazioni regionali del sistema. Su un PC italiano `%date%` restituisce `gg/mm/aaaa`, su uno americano `mm/dd/yyyy`. Per script eseguiti in ambienti multi-locale o schedulati su server con locale mista, il timestamp diventa inaffidabile. La soluzione è ricavare un timestamp ISO 8601 deterministico tramite WMIC:

```batch
:log_iso
:: Genera timestamp ISO 8601 locale-independent
for /f "tokens=2 delims==" %%a in ('wmic os get localdatetime /value 2^>nul') do set "DT=%%a"
set "ISO_TS=%DT:~0,4%-%DT:~4,2%-%DT:~6,2%T%DT:~8,2%:%DT:~10,2%:%DT:~12,2%"
echo [%ISO_TS%] [%~1] %~2
echo [%ISO_TS%] [%~1] %~2 >> "%LOGFILE%"
exit /b 0
```

#### Logging multi-livello con filtraggio

Negli ambienti di produzione serve filtrare i messaggi per severità. Il pattern seguente implementa livelli DEBUG, INFO, WARN, ERROR con soglia configurabile:

```batch
@echo off
setlocal enabledelayedexpansion

:: Livelli: 0=DEBUG 1=INFO 2=WARN 3=ERROR
set LOG_LEVEL=1
set LOGFILE=C:\Logs\app_%date:~-4%%date:~3,2%%date:~0,2%.log
if not exist "C:\Logs" mkdir "C:\Logs"

call :logmsg 0 "DEBUG" "Variabili di ambiente caricate"
call :logmsg 1 "INFO"  "Avvio elaborazione"
call :logmsg 2 "WARN"  "Directory temp piena al 85%%"
call :logmsg 3 "ERROR" "Connessione database fallita"
goto :eof

:logmsg
:: %1=livello numerico, %2=etichetta, %3=messaggio
if %~1 LSS %LOG_LEVEL% exit /b 0
for /f "tokens=2 delims==" %%a in ('wmic os get localdatetime /value 2^>nul') do set "DT=%%a"
set "TS=%DT:~0,4%-%DT:~4,2%-%DT:~6,2% %DT:~8,2%:%DT:~10,2%:%DT:~12,2%"
set "MSG=[%TS%] [%~2] %~3"
echo !MSG!
echo !MSG! >> "%LOGFILE%"
exit /b 0
```

Impostando `LOG_LEVEL=2` si escludono automaticamente DEBUG e INFO, riducendo il rumore nei log di produzione senza modificare il codice.

#### Rotazione log per dimensione

I file di log non ruotati crescono indefinitamente, consumando spazio disco e rendendo difficile la diagnostica. Il pattern seguente implementa rotazione per dimensione e pulizia automatica dei log vecchi:

```batch
:rotate_log
:: Rotazione quando il log supera 5 MB (5242880 byte)
set MAX_SIZE=5242880
if not exist "%LOGFILE%" exit /b 0

for %%F in ("%LOGFILE%") do set FILE_SIZE=%%~zF
if !FILE_SIZE! GEQ %MAX_SIZE% (
    for /f "tokens=2 delims==" %%a in ('wmic os get localdatetime /value 2^>nul') do set "DT=%%a"
    set "ROTATED=%LOGFILE%.!DT:~0,8!_!DT:~8,6!"
    move "%LOGFILE%" "!ROTATED!" >nul 2>&1
    echo [Rotazione] Log ruotato: !ROTATED! > "%LOGFILE%"
)
exit /b 0

:cleanup_old_logs
:: Eliminare log più vecchi di 30 giorni
forfiles /p "C:\Logs" /m "*.log.*" /d -30 /c "cmd /c del @path" 2>nul
exit /b 0
```

La rotazione va invocata all'inizio dello script con `call :rotate_log` prima di qualsiasi scrittura. `forfiles` con `/d -30` elimina i file ruotati con più di 30 giorni, implementando una retention policy automatica. Per ambienti critici, considerare la compressione dei log ruotati con `compact /c` (NTFS) o l'invio a un collector centralizzato via `wevtutil` o syslog relay.

### Pattern di cleanup e EXIT

```batch
@echo off
setlocal

:: Crea file temporanei
set TMPFILE=%TEMP%\script_%RANDOM%.tmp

:: Trap: assicurarsi di pulire in ogni caso
echo Dati temporanei > "%TMPFILE%"

:: ... operazioni ...
if %ERRORLEVEL% neq 0 goto :cleanup_error

:cleanup_ok
call :cleanup
echo Operazione completata con successo
exit /b 0

:cleanup_error
call :cleanup
echo Operazione fallita
exit /b 1

:cleanup
if exist "%TMPFILE%" del /f /q "%TMPFILE%"
exit /b 0
```

### Validazione prerequisiti all'avvio

```batch
@echo off
setlocal

:: Verifica privilegi admin
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERRORE: questo script richiede privilegi di amministratore
    exit /b 1
)

:: Verifica esistenza tool richiesti
where robocopy >nul 2>&1 || (echo ERRORE: robocopy non trovato & exit /b 1)
where findstr >nul 2>&1 || (echo ERRORE: findstr non trovato & exit /b 1)

:: Verifica parametri obbligatori
if "%1"=="" (
    echo Uso: %~nx0 ^<source^> ^<dest^>
    exit /b 1
)
if "%2"=="" (
    echo Uso: %~nx0 ^<source^> ^<dest^>
    exit /b 1
)

:: Verifica path source
if not exist "%~1" (
    echo ERRORE: directory source non trovata: %~1
    exit /b 1
)

echo Prerequisiti verificati, procedo...
```

### Emulazione try/catch/finally con CALL e GOTO

CMD.exe non ha gestione strutturata delle eccezioni. Tuttavia, combinando `call`, `goto` e codici di uscita, si può emulare un pattern try/catch/finally che offre recupero controllato dagli errori:

```batch
@echo off
setlocal enabledelayedexpansion

call :try_operation
echo Codice finale: %ERRORLEVEL%
goto :eof

:try_operation
:: === TRY ===
call :step_connect_db
if !ERRORLEVEL! neq 0 (
    set "ERR_CODE=!ERRORLEVEL!"
    set "ERR_MSG=Connessione DB fallita"
    goto :catch
)

call :step_process_data
if !ERRORLEVEL! neq 0 (
    set "ERR_CODE=!ERRORLEVEL!"
    set "ERR_MSG=Elaborazione dati fallita"
    goto :catch
)

:: === FINALLY (successo) ===
call :finally
exit /b 0

:catch
:: === CATCH ===
echo ERRORE [%ERR_CODE%]: %ERR_MSG% >&2
call :logmsg 3 "ERROR" "%ERR_MSG% [code=%ERR_CODE%]"

:: Retry con backoff per errori transitori (codice 2 = timeout)
if %ERR_CODE% equ 2 (
    call :retry_with_backoff
    if !ERRORLEVEL! equ 0 (
        call :finally
        exit /b 0
    )
)

:: === FINALLY (errore) ===
call :finally
exit /b %ERR_CODE%

:finally
:: Cleanup garantito in ogni percorso di uscita
if exist "%TMPFILE%" del "%TMPFILE%" >nul 2>&1
if defined DB_CONN call :step_disconnect_db
exit /b 0
```

Il `:finally` viene invocato sia nel percorso di successo sia in quello di errore, garantendo che le risorse vengano sempre rilasciate. Questo pattern è fondamentale per script che aprono connessioni, creano file temporanei, o acquisiscono lock.

#### Propagazione errori attraverso chiamate nidificate

Quando gli script batch crescono in complessità, le subroutine chiamano altre subroutine. Un errore profondo deve propagarsi fino al chiamante principale. Il pattern standard usa `exit /b` con codici stratificati:

```batch
:main
call :level1
if !ERRORLEVEL! neq 0 (
    echo Operazione fallita al livello: !ERRORLEVEL! >&2
    exit /b !ERRORLEVEL!
)
exit /b 0

:level1
call :level2
:: Propagazione esplicita — NON ignorare ERRORLEVEL
if !ERRORLEVEL! neq 0 exit /b !ERRORLEVEL!
exit /b 0

:level2
:: Codici di uscita strutturati:
:: 1=errore generico, 2=timeout, 3=permessi, 4=risorsa mancante
some_command
if !ERRORLEVEL! neq 0 exit /b 4
exit /b 0
```

Ogni livello verifica e rilancia `ERRORLEVEL`. Senza questa propagazione esplicita, un errore in `:level2` verrebbe silenziosamente ignorato da `:level1`, producendo risultati corrotti senza alcuna segnalazione.

#### Retry con backoff esponenziale

Per operazioni di rete o I/O che possono fallire per cause transitorie (rete instabile, file lock temporaneo), il retry con backoff esponenziale evita di sovraccaricare il servizio remoto:

```batch
:retry_with_backoff
set RETRY_MAX=4
set RETRY_DELAY=2
for /L %%i in (1,1,%RETRY_MAX%) do (
    echo Tentativo %%i di %RETRY_MAX% (attesa %RETRY_DELAY%s)...
    timeout /t %RETRY_DELAY% /nobreak >nul
    call :step_connect_db
    if !ERRORLEVEL! equ 0 exit /b 0
    set /a "RETRY_DELAY*=2"
)
echo Tutti i tentativi esauriti >&2
exit /b 2
```

Il delay raddoppia ad ogni tentativo (2s → 4s → 8s → 16s), rispettando il servizio di destinazione. In produzione, aggiungere un jitter casuale con `%RANDOM%` per evitare che più script schedulati alla stessa ora riprovino in sincrono (thundering herd).

---

## Scheduled Tasks (schtasks)

### Creazione task

```batch
:: Creare task schedulato
schtasks /create /tn "BackupNightly" /tr "C:\Scripts\backup.bat" ^
    /sc daily /st 02:00 /ru SYSTEM /rl HIGHEST

:: Ogni lunedì alle 06:00
schtasks /create /tn "WeeklyReport" /tr "C:\Scripts\report.bat" ^
    /sc weekly /d MON /st 06:00 /ru DOMAIN\svc-task /rp "Password"

:: Ogni 4 ore
schtasks /create /tn "HealthCheck" /tr "C:\Scripts\check.bat" ^
    /sc hourly /mo 4 /ru SYSTEM

:: Al boot del sistema
schtasks /create /tn "StartupScript" /tr "C:\Scripts\startup.bat" ^
    /sc onstart /ru SYSTEM /rl HIGHEST

:: Al logon dell'utente
schtasks /create /tn "UserSetup" /tr "C:\Scripts\setup.bat" ^
    /sc onlogon /ru %USERNAME%

:: A un evento specifico del log
schtasks /create /tn "OnDiskFull" ^
    /tr "C:\Scripts\disk-alert.bat" ^
    /sc onevent /ec System /mo "*[System[EventID=2013]]" ^
    /ru SYSTEM /rl HIGHEST
```

### Schedule types completi

```batch
:: /sc MINUTE /mo N        → ogni N minuti
:: /sc HOURLY /mo N        → ogni N ore
:: /sc DAILY /mo N         → ogni N giorni
:: /sc WEEKLY /d MON,WED   → giorni specifici
:: /sc MONTHLY /d 1,15     → giorni del mese
:: /sc MONTHLY /mo FIRST /d MON  → primo lunedì del mese
:: /sc ONCE /st HH:MM /sd MM/DD/YYYY  → una volta sola
:: /sc ONSTART             → al boot
:: /sc ONLOGON             → al logon
:: /sc ONIDLE /i MM        → dopo MM minuti di inattività
:: /sc ONEVENT             → su evento

:: Data di fine
schtasks /create /tn "TempTask" /tr "C:\Scripts\temp.bat" ^
    /sc daily /st 03:00 /ed 12/31/2026 /ru SYSTEM
```

### Gestione task

```batch
:: Visualizzare dettagli
schtasks /query /tn "BackupNightly" /v /fo list

:: Elencare tutti i task
schtasks /query /fo table

:: Esegui ora
schtasks /run /tn "BackupNightly"

:: Ferma esecuzione
schtasks /end /tn "BackupNightly"

:: Modifica
schtasks /change /tn "BackupNightly" /st 03:00
schtasks /change /tn "BackupNightly" /disable
schtasks /change /tn "BackupNightly" /enable

:: Elimina
schtasks /delete /tn "BackupNightly" /f

:: Esportare task (XML)
schtasks /query /tn "BackupNightly" /xml > backup_task.xml

:: Importare task da XML
schtasks /create /tn "BackupNightly" /xml backup_task.xml
```

### PowerShell equivalenti

```batch
:: PowerShell equivalente (più potente):
:: schtasks /query                  → Get-ScheduledTask
:: schtasks /create                 → Register-ScheduledTask
:: schtasks /change                 → Set-ScheduledTask
:: schtasks /run                    → Start-ScheduledTask
:: schtasks /end                    → Stop-ScheduledTask
:: schtasks /delete                 → Unregister-ScheduledTask
```

---

## Operazioni sul Registry

### REG QUERY — Lettura

```batch
:: Leggere una chiave specifica
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v ProductName

:: Leggere tutti i valori di una chiave
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion"

:: Ricorsivo
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /s

:: Con filtro su architettura (32/64 bit)
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall" /reg:64
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall" /reg:32

:: Cercare un valore in tutto il registry (lento!)
reg query HKLM /f "ServerName" /t REG_SZ /s

:: Abbreviazioni hive:
:: HKLM = HKEY_LOCAL_MACHINE
:: HKCU = HKEY_CURRENT_USER
:: HKCR = HKEY_CLASSES_ROOT
:: HKU  = HKEY_USERS
:: HKCC = HKEY_CURRENT_CONFIG
```

### REG ADD — Scrittura

```batch
:: Aggiungere/modificare un valore stringa
reg add "HKCU\Software\MyApp" /v SettingName /t REG_SZ /d "valore" /f

:: Tipi di dato:
:: REG_SZ        → Stringa
:: REG_EXPAND_SZ → Stringa con variabili d'ambiente espandibili
:: REG_DWORD     → Numero 32-bit
:: REG_QWORD     → Numero 64-bit
:: REG_MULTI_SZ  → Stringa multi-valore (separata da \0)
:: REG_BINARY    → Binario

:: Esempio: disabilitare autorun per USB
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\Explorer" ^
    /v NoDriveTypeAutoRun /t REG_DWORD /d 0xFF /f

:: Esempio: aggiungere programma all'avvio
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" ^
    /v "MyScript" /t REG_SZ /d "C:\Scripts\startup.bat" /f

:: Creare solo la chiave (senza valore)
reg add "HKCU\Software\MyApp\Settings" /f
```

### REG DELETE — Eliminazione

```batch
:: Eliminare un valore
reg delete "HKCU\Software\MyApp" /v SettingName /f

:: Eliminare un'intera chiave e sotto-chiavi
reg delete "HKCU\Software\MyApp" /f

:: /f = force (nessuna conferma)
```

### REG EXPORT / IMPORT — Backup e ripristino

```batch
:: Esportare chiave su file .reg
reg export "HKCU\Software\MyApp" C:\Backup\myapp_settings.reg /y

:: Importare da file .reg
reg import C:\Backup\myapp_settings.reg

:: Confrontare due chiavi
reg compare "HKLM\Software\Key1" "HKLM\Software\Key2"

:: Copiare chiave
reg copy "HKCU\Software\Source" "HKCU\Software\Dest" /s /f

:: Salvare hive binario (richiede privilegi)
reg save "HKLM\SOFTWARE" C:\Backup\software_hive.dat /y

:: Ripristinare hive binario
reg restore "HKLM\SOFTWARE" C:\Backup\software_hive.dat
```

### Pattern utili con il registry

```batch
:: Leggere versione Windows
for /f "tokens=3" %%a in ('reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion" /v CurrentBuild ^| findstr CurrentBuild') do (
    echo Build: %%a
)

:: Elencare software installato
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall" /s /v DisplayName 2>nul | findstr DisplayName

:: Verificare se una policy è attiva
reg query "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate" /v WUServer 2>nul
if %ERRORLEVEL% equ 0 (
    echo WSUS configurato
) else (
    echo WSUS non configurato
)
```

---

## Comandi di Rete

### PING — Connettività base

```batch
:: Ping base
ping -n 4 192.168.10.1

:: Ping continuo (Ctrl+C per fermare)
ping -t 192.168.10.1

:: Con dimensione pacchetto e no-fragment
ping -l 1472 -f 192.168.10.1    :: test MTU

:: Ping per verifica in script (silenzioso)
ping -n 1 -w 1000 192.168.10.1 >nul 2>&1
if %ERRORLEVEL% equ 0 (echo UP) else (echo DOWN)
```

### TRACERT — Tracciamento route

```batch
:: Traceroute
tracert 8.8.8.8

:: Senza risoluzione DNS (più veloce)
tracert -d 8.8.8.8

:: Con timeout e max hop
tracert -w 1000 -h 20 8.8.8.8
```

### NSLOOKUP — Query DNS

```batch
:: Query base
nslookup hostname.domain.com

:: Con server DNS specifico
nslookup hostname.domain.com 8.8.8.8

:: Record MX
nslookup -type=mx domain.com

:: Record TXT (SPF, DKIM)
nslookup -type=txt domain.com

:: Reverse lookup
nslookup 192.168.1.1

:: Tutti i record
nslookup -type=any domain.com
```

### NETSH — Configurazione rete

```batch
:: Mostrare configurazione IP
netsh interface ipv4 show config

:: Impostare IP statico
netsh interface ipv4 set address "Ethernet" static 192.168.1.100 255.255.255.0 192.168.1.1

:: Impostare DNS
netsh interface ipv4 set dns "Ethernet" static 8.8.8.8 primary
netsh interface ipv4 add dns "Ethernet" 8.8.4.4 index=2

:: Tornare a DHCP
netsh interface ipv4 set address "Ethernet" dhcp
netsh interface ipv4 set dns "Ethernet" dhcp

:: Firewall: regole
netsh advfirewall firewall show rule name=all
netsh advfirewall firewall add rule name="Allow SSH" dir=in action=allow protocol=TCP localport=22
netsh advfirewall firewall delete rule name="Allow SSH"

:: Esportare/importare configurazione firewall
netsh advfirewall export "C:\Backup\firewall.wfw"
netsh advfirewall import "C:\Backup\firewall.wfw"

:: WiFi: mostrare profili
netsh wlan show profiles
netsh wlan show profile name="NomeRete" key=clear

:: Reset stack TCP/IP
netsh int ip reset
netsh winsock reset

:: Mostrare porte in ascolto
netsh interface ipv4 show tcpconnections
```

### NET USE — Mappatura risorse di rete

```batch
:: Mappare drive di rete
net use Z: \\server\share /user:DOMAIN\user password

:: Mappare con credenziali persistenti
net use Z: \\server\share /user:DOMAIN\user password /persistent:yes

:: Disconnettere
net use Z: /delete

:: Disconnettere tutti
net use * /delete /y

:: Elencare connessioni
net use

:: Connessione senza mappare lettera (per script)
net use \\server\share /user:DOMAIN\user password
:: Poi accedere con UNC path: \\server\share\file.txt
```

### NET USER — Gestione utenti locali

```batch
:: Elencare utenti
net user

:: Dettagli utente
net user username

:: Creare utente
net user username password /add

:: Con opzioni
net user username password /add /fullname:"Nome Completo" ^
    /comment:"Account di servizio" /passwordchg:no /expires:never

:: Modificare password
net user username newpassword

:: Forzare cambio password al prossimo logon
net user username /logonpasswordchg:yes

:: Disabilitare account
net user username /active:no

:: Abilitare account
net user username /active:yes

:: Eliminare utente
net user username /delete

:: Gestione gruppi
net localgroup Administrators username /add
net localgroup "Remote Desktop Users" username /add
net localgroup Administrators
net localgroup Administrators username /delete
```

### NETSTAT — Connessioni di rete

```batch
:: Tutte le connessioni e porte in ascolto
netstat -an

:: Con PID del processo
netstat -ano

:: Con nome del processo
netstat -anb    :: richiede admin

:: Solo porte in ascolto
netstat -an | findstr "LISTENING"

:: Connessioni stabilite verso un IP
netstat -an | findstr "ESTABLISHED" | findstr "10.0.0.5"

:: Statistiche per protocollo
netstat -s
```

### ARP — Tabella ARP

```batch
:: Mostrare tabella ARP
arp -a

:: Aggiungere entry statica
arp -s 192.168.1.1 00-11-22-33-44-55

:: Cancellare entry
arp -d 192.168.1.1
```

---

## WMI da Batch (WMIC)

### Informazioni sistema

```batch
:: WMIC (Windows Management Instrumentation Command-line)
:: Deprecato ma ancora utile per script batch veloci

:: Informazioni sistema
wmic os get caption,version,buildnumber
wmic computersystem get name,domain,totalphysicalmemory
wmic cpu get name,numberofcores,numberoflogicalprocessors
wmic bios get serialnumber,manufacturer

:: Uptime
wmic os get lastbootuptime
```

### Processi e servizi

```batch
:: Processi
wmic process list brief
wmic process where name="notepad.exe" delete
wmic process where "name='chrome.exe'" get processid,commandline
wmic process where "workingsetsize>100000000" get name,workingsetsize

:: Servizi
wmic service where state="running" get name,displayname
wmic service where name="wuauserv" call startservice
wmic service where name="wuauserv" call stopservice
wmic service where startmode="auto" get name,state
```

### Hardware e software

```batch
:: Software installato
wmic product get name,version

:: Disco
wmic logicaldisk get name,size,freespace,filesystem
wmic logicaldisk where drivetype=3 get name,freespace,size

:: Memoria
wmic memorychip get capacity,speed,manufacturer

:: NIC
wmic nic where netenabled=true get name,macaddress
wmic nicconfig where ipenabled=true get ipaddress,macaddress,defaultipgateway

:: Monitor
wmic desktopmonitor get screenheight,screenwidth

:: Stampanti
wmic printer get name,portname,default
```

### Account e sicurezza

```batch
:: Utenti
wmic useraccount get name,sid,disabled
wmic useraccount where disabled=false get name,sid

:: Gruppi
wmic group get name,sid

:: Condivisioni
wmic share get name,path,type

:: Hotfix installati
wmic qfe get hotfixid,installedon,description
wmic qfe where "hotfixid='KB5001234'" get description
```

### Output formattato

```batch
:: CSV
wmic os get caption /format:csv

:: HTML
wmic process list brief /format:htable > processes.html

:: Lista
wmic logicaldisk get name,freespace /format:list

:: Separatore personalizzato
wmic os get caption,version /format:csv > system_info.csv
```

### WMIC — Deprecazione e alternative PowerShell

```batch
:: NOTA: WMIC è deprecato da Windows 11 (24H2 lo rimuove da alcune edizioni).
:: Preferire Get-CimInstance in PowerShell:

:: wmic os get caption
::   → Get-CimInstance Win32_OperatingSystem | Select Caption

:: wmic process list brief
::   → Get-CimInstance Win32_Process | Select Name,ProcessId,WorkingSetSize

:: wmic service where state="running" get name,displayname
::   → Get-CimInstance Win32_Service -Filter "State='Running'" | Select Name,DisplayName

:: wmic logicaldisk get name,size,freespace
::   → Get-CimInstance Win32_LogicalDisk | Select DeviceID,Size,FreeSpace

:: wmic product get name,version
::   → Get-CimInstance Win32_Product | Select Name,Version
::   (Nota: Win32_Product trigger MSI reconfiguration — usare:
::    Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*)

:: wmic useraccount get name,sid
::   → Get-CimInstance Win32_UserAccount | Select Name,SID
```

---

## Sicurezza negli Script Batch

### Validazione input

```batch
:: PROBLEMA: injection tramite set /p
:: Se l'utente digita: test & del /s /q C:\
:: il comando dopo & viene eseguito!

:: SOLUZIONE: sanitizzare con apici e verifiche
@echo off
setlocal enabledelayedexpansion

set /p "USERINPUT=Inserisci nome file: "

:: Verifica lunghezza
if "!USERINPUT!"=="" (
    echo ERRORE: input vuoto
    exit /b 1
)

:: Verifica caratteri pericolosi
echo !USERINPUT! | findstr /r "[&|<>^%%!]" >nul
if !ERRORLEVEL! equ 0 (
    echo ERRORE: caratteri non ammessi nel nome file
    exit /b 1
)

:: Verifica path traversal
echo !USERINPUT! | findstr /r "\.\." >nul
if !ERRORLEVEL! equ 0 (
    echo ERRORE: path traversal non ammesso
    exit /b 1
)

:: Usa la variabile sanitizzata
echo Elaboro file: !USERINPUT!
```

### Evitare injection in comandi

```batch
:: MAI costruire comandi con input utente non validato
:: SBAGLIATO:
set /p FILE=File da elaborare:
type %FILE%                     :: se FILE = "file.txt & del *.*" → disastro

:: CORRETTO: usare doppi apici e delayed expansion
set /p "FILE=File da elaborare: "
if not exist "!FILE!" (
    echo File non trovato
    exit /b 1
)
type "!FILE!"
```

### Esecuzione come amministratore

```batch
:: Verifica privilegi admin
@echo off
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Richiesti privilegi di amministratore.
    echo Riesegui come amministratore.
    pause
    exit /b 1
)
echo Esecuzione con privilegi elevati confermata.

:: Auto-elevazione (UAC prompt)
@echo off
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)
:: Da qui in poi siamo admin
echo Privilegi admin attivi
```

### Protezione file di script

```batch
:: Impedire modifica dello script
attrib +r +s "%~f0"

:: Verificare integrità (hash)
certutil -hashfile "%~f0" SHA256

:: Non esporre credenziali nello script
:: SBAGLIATO:
:: set PASSWORD=MiaPassword123
:: net use Z: \\server\share /user:admin %PASSWORD%

:: CORRETTO: leggere da file protetto o usare credential manager
:: Oppure usare lo scheduling con account di servizio
```

### Logging per audit

```batch
@echo off
setlocal enabledelayedexpansion

set LOGFILE=C:\Logs\audit_%COMPUTERNAME%_%date:~-4%%date:~3,2%%date:~0,2%.log

:: Log di inizio con contesto di sicurezza
echo [%date% %time%] Script: %~f0 >> "%LOGFILE%"
echo [%date% %time%] Utente: %USERNAME% >> "%LOGFILE%"
echo [%date% %time%] Dominio: %USERDOMAIN% >> "%LOGFILE%"
echo [%date% %time%] Computer: %COMPUTERNAME% >> "%LOGFILE%"
echo [%date% %time%] Privilegi: >> "%LOGFILE%"
whoami /priv >> "%LOGFILE%" 2>&1

:: Proteggere il file di log
icacls "%LOGFILE%" /inheritance:r /grant:r "SYSTEM:(F)" /grant:r "Administrators:(R)" >nul 2>&1
```

---

## Hardening Avanzato e Superficie di Attacco

La sicurezza batch va oltre il non hardcodare password. La superficie di attacco di CMD.exe include vettori spesso sottovalutati che possono compromettere l'intero sistema se sfruttati.

### PATH hijacking e ricerca comandi

Quando si invoca un comando senza percorso assoluto (es. `robocopy`), CMD.exe cerca prima nella directory corrente (CWD), poi nelle directory in `%PATH%`. Un attaccante che riesce a posizionare un eseguibile malevolo con lo stesso nome nella CWD dello script può dirottare l'esecuzione. Mitigazione:

```batch
:: SBAGLIATO: vulnerabile a PATH hijacking
robocopy %SRC% %DST% /MIR

:: CORRETTO: percorso assoluto per comandi critici
"%SystemRoot%\System32\Robocopy.exe" "%SRC%" "%DST%" /MIR

:: CORRETTO: verificare il percorso prima dell'esecuzione
for /f "delims=" %%p in ('where robocopy 2^>nul') do set "ROBOCOPY_PATH=%%p"
if not defined ROBOCOPY_PATH (echo ERRORE: robocopy non trovato & exit /b 1)
echo Usando: %ROBOCOPY_PATH%
```

Per comandi interni di CMD (`dir`, `copy`, `del`, `set`), il rischio non esiste perché vengono eseguiti direttamente dall'interprete senza ricerca su disco. Ma per qualsiasi eseguibile esterno in contesti di sicurezza elevata, usare il percorso completo.

### Vulnerabilità BatBadBut (CVE-2024-24576)

Nell'aprile 2024 è stata pubblicata la vulnerabilità BatBadBut con severità CVSS 10.0. Il problema riguarda linguaggi di programmazione (Rust, Python, Node.js, PHP, e altri) che invocano file `.bat`/`.cmd` tramite le loro API di processo. CMD.exe gestisce il parsing degli argomenti in modo diverso dalle shell Unix: le virgolette e i caratteri speciali (`&`, `|`, `^`) negli argomenti possono essere iniettati come comandi. Un argomento come `"file.txt" & del /q C:\*` viene interpretato da CMD.exe come due comandi separati.

Mitigazione in batch:

```batch
:: Sanitizzazione input: rimuovere caratteri pericolosi per CMD
set "SAFE_INPUT=%~1"
set "SAFE_INPUT=!SAFE_INPUT:&=!"
set "SAFE_INPUT=!SAFE_INPUT:|=!"
set "SAFE_INPUT=!SAFE_INPUT:>=!"
set "SAFE_INPUT=!SAFE_INPUT:<=!"
set "SAFE_INPUT=!SAFE_INPUT:^=!"
set "SAFE_INPUT=!SAFE_INPUT:%%=!"

:: Approccio whitelist (PREFERITO): accettare solo caratteri sicuri
echo "%~1" | findstr /r "^[a-zA-Z0-9_\.\-\\:]*$" >nul
if %ERRORLEVEL% neq 0 (
    echo ERRORE: input contiene caratteri non ammessi >&2
    exit /b 1
)
```

L'approccio whitelist è superiore al blocklist: invece di cercare di rimuovere tutti i caratteri pericolosi (che possono essere aggirati con encoding o combinazioni impreviste), si definisce esplicitamente l'insieme dei caratteri ammessi. Tutto ciò che non corrisponde viene rifiutato.

### Rischi UNC path e condivisioni di rete

Quando uno script batch viene eseguito da un percorso UNC (`\\server\share\script.bat`), CMD.exe cambia la directory corrente a `C:\Windows` e mostra un avviso. Ma se lo script usa percorsi relativi, le operazioni avverranno in una posizione inattesa. Mitigazione:

```batch
:: Forzare la directory dello script come CWD
pushd "%~dp0"

:: ... operazioni con percorsi relativi sicuri ...

popd
```

### Windows Terminal Enhanced Security

A partire dal 2024, Windows Terminal include l'opzione "Enhanced Security and Performance for Batch" che applica un sandboxing leggero all'esecuzione di script batch. Questa funzionalità limita l'accesso diretto al registry, riduce i privilegi di default, e migliora il logging delle operazioni. Per ambienti aziendali, abilitare questa opzione via GPO (Group Policy) su tutte le workstation.

### Verifica integrità script

Per proteggersi da modifiche non autorizzate agli script di produzione, usare hash di controllo:

```batch
:: Generare hash di riferimento (da fare una sola volta, conservare il valore)
certutil -hashfile "C:\Scripts\backup.bat" SHA256

:: Verificare integrità prima dell'esecuzione
for /f "skip=1 tokens=*" %%h in ('certutil -hashfile "%~f0" SHA256') do (
    if "%%h" neq "CertUtil" (
        if "%%h" neq "%EXPECTED_HASH%" (
            echo ALLARME: script modificato! Hash atteso: %EXPECTED_HASH% >&2
            echo ALLARME: hash attuale: %%h >&2
            exit /b 99
        )
    )
)
```

Questa verifica va integrata con un sistema di monitoraggio (SIEM) per generare alert in caso di manomissione. Lo script controlla il proprio hash all'avvio e rifiuta l'esecuzione se non corrisponde al valore atteso, prevenendo l'esecuzione di versioni alterate.

---

## Interoperabilità con PowerShell

### Chiamare PowerShell da batch

```batch
:: Comando inline
powershell -Command "Get-Process | Sort-Object CPU -Descending | Select -First 5"

:: Catturare output in variabile batch
for /f "delims=" %%a in ('powershell -Command "(Get-Date).ToString('yyyy-MM-dd')"') do set TODAY=%%a
echo Data: %TODAY%

:: Eseguire script .ps1
powershell -ExecutionPolicy Bypass -File "C:\Scripts\report.ps1"

:: Con parametri
powershell -ExecutionPolicy Bypass -File "C:\Scripts\report.ps1" -Param1 "valore" -Param2 42

:: PowerShell one-liner per operazioni complesse
powershell -Command "Get-ChildItem C:\Logs -Recurse -Filter *.log | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | Remove-Item -Force"

:: Output JSON da PowerShell, parsing in batch
powershell -Command "Get-ComputerInfo | Select-Object OsName,OsVersion,CsTotalPhysicalMemory | ConvertTo-Json" > sysinfo.json

:: Test connettività con PowerShell (più affidabile del ping)
powershell -Command "Test-NetConnection -ComputerName server01 -Port 443 -InformationLevel Quiet"
if %ERRORLEVEL% equ 0 echo Porta 443 aperta

:: Invio email da batch tramite PowerShell
powershell -Command "Send-MailMessage -From 'sender@domain.com' -To 'admin@domain.com' -Subject 'Backup Report' -Body 'Backup completato' -SmtpServer 'mail.domain.com'"
```

### Chiamare batch da PowerShell

```powershell
# Eseguire script batch da PowerShell
& "C:\Scripts\backup.bat" arg1 arg2

# Catturare output
$output = & "C:\Scripts\check.bat" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "Script fallito: $output"
}

# Usare cmd.exe direttamente
cmd.exe /c "dir /s /b C:\*.config"

# Start-Process per batch con admin
Start-Process -FilePath "C:\Scripts\admin-task.bat" -Verb RunAs -Wait
```

### Pattern ibrido batch+PowerShell

```batch
@echo off
:: Batch fa il bootstrap, PowerShell fa il lavoro pesante

:: Verificare che PowerShell sia disponibile
where powershell >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERRORE: PowerShell non disponibile
    echo Fallback a batch puro...
    goto :batch_fallback
)

:: Verifica versione PowerShell minima
for /f %%v in ('powershell -Command "$PSVersionTable.PSVersion.Major"') do set PSVER=%%v
if %PSVER% LSS 5 (
    echo AVVISO: PowerShell %PSVER% - alcune funzionalità limitate
)

:: Esegui la logica principale in PowerShell
powershell -ExecutionPolicy Bypass -Command ^
    "& {" ^
    "  $report = @{}" ^
    "  $report.Hostname = $env:COMPUTERNAME" ^
    "  $report.OS = (Get-CimInstance Win32_OperatingSystem).Caption" ^
    "  $report.Uptime = (Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime" ^
    "  $report | ConvertTo-Json | Out-File 'C:\Reports\system.json'" ^
    "}"
echo Report generato: C:\Reports\system.json
goto :eof

:batch_fallback
echo Esecuzione in modalità batch legacy...
systeminfo > C:\Reports\system.txt
```

---

## Script Ibridi Batch+PowerShell Avanzati

L'interoperabilità base vista nella sezione precedente copre i casi comuni. In ambienti reali servono pattern più sofisticati per creare script che sfruttano il meglio di entrambi i mondi.

### Script poliglotta batch/PowerShell

Il trucco `<# : #>` permette di creare un singolo file `.bat` che è contemporaneamente uno script batch valido e uno script PowerShell valido. CMD.exe ignora il blocco `<# : #>` (lo tratta come redirect fallito), mentre PowerShell lo interpreta come commento multi-riga:

```batch
<# : batch portion
@echo off & setlocal
powershell -noprofile -executionpolicy bypass -file "%~f0" %*
exit /b %ERRORLEVEL%
: end batch / begin PowerShell #>

# === Codice PowerShell ===
param([string]$Action = "status")

switch ($Action) {
    "status" {
        Get-Service | Where-Object Status -eq Running |
            Select-Object Name, DisplayName, StartType |
            Format-Table -AutoSize
    }
    "disk" {
        Get-CimInstance Win32_LogicalDisk |
            Where-Object DriveType -eq 3 |
            Select-Object DeviceID,
                @{N='Size_GB';E={[math]::Round($_.Size/1GB,1)}},
                @{N='Free_GB';E={[math]::Round($_.FreeSpace/1GB,1)}}
    }
}
```

Questo file si può eseguire come `script.bat status` da CMD oppure come `.\script.bat disk` da PowerShell — entrambi funzionano senza modifiche. Il vantaggio è un singolo file da distribuire e manutenere, eliminando la necessità di coppie `.bat`+`.ps1`.

### Scambio dati strutturati via JSON temporaneo

Per passare dati complessi tra batch e PowerShell, le variabili d'ambiente hanno limiti (lunghezza, caratteri speciali). Un pattern robusto usa file JSON temporanei:

```batch
@echo off
setlocal enabledelayedexpansion
set "TMPJSON=%TEMP%\exchange_%RANDOM%.json"

:: Batch raccoglie i dati
set "HOST=%COMPUTERNAME%"
set "USR=%USERNAME%"
set "TS=%date% %time%"

:: PowerShell elabora e genera output strutturato
powershell -noprofile -command ^
    "$data = @{ Host='%HOST%'; User='%USR%'; Timestamp='%TS%' };" ^
    "$data | ConvertTo-Json | Set-Content '%TMPJSON%';" ^
    "$json = Get-Content '%TMPJSON%' | ConvertFrom-Json;" ^
    "Write-Host ('Report per {0} generato alle {1}' -f $json.Host, $json.Timestamp)"

:: Cleanup
if exist "%TMPJSON%" del "%TMPJSON%"
```

### Selezione pwsh.exe vs powershell.exe

Con PowerShell 7+ installato come `pwsh.exe` accanto al legacy `powershell.exe` (v5.1), gli script ibridi devono selezionare la versione corretta. `pwsh.exe` offre prestazioni superiori, supporto cross-platform, e cmdlet aggiornati. La strategia consigliata:

```batch
:: Preferire pwsh.exe (PS 7+), fallback a powershell.exe (PS 5.1)
set "PSHELL=powershell.exe"
where pwsh.exe >nul 2>&1 && set "PSHELL=pwsh.exe"

:: Verificare versione minima
for /f "delims=" %%v in ('%PSHELL% -noprofile -command "$PSVersionTable.PSVersion.ToString()"') do (
    echo Usando %PSHELL% versione %%v
)

%PSHELL% -noprofile -executionpolicy bypass -file "C:\Scripts\logic.ps1" %*
```

La selezione automatica assicura che lo script sfrutti le feature più recenti quando disponibili, mantenendo compatibilità con sistemi che hanno solo PowerShell 5.1. Evitare `powershell.exe` con parametro `-Version` per forzare versioni precedenti: questo flag è deprecato e non garantisce il comportamento atteso su tutte le installazioni.

### Degradazione elegante con feature detection

Invece di testare solo la presenza di PowerShell, uno script robusto verifica la disponibilità delle funzionalità specifiche richieste:

```batch
@echo off
setlocal

:: Test 1: PowerShell disponibile?
where pwsh.exe >nul 2>&1 || where powershell.exe >nul 2>&1
if %ERRORLEVEL% neq 0 goto :pure_batch

:: Test 2: Modulo richiesto disponibile?
powershell -noprofile -command "if (Get-Module -ListAvailable ActiveDirectory) { exit 0 } else { exit 1 }"
if %ERRORLEVEL% neq 0 (
    echo AVVISO: modulo ActiveDirectory non disponibile, uso net.exe
    goto :legacy_ad
)

:: Percorso completo: PowerShell + modulo AD
powershell -noprofile -command "Get-ADUser -Filter * -Properties LastLogonDate | Export-Csv users.csv"
goto :eof

:legacy_ad
:: Fallback: strumenti nativi Windows
net user /domain > users.txt
goto :eof

:pure_batch
:: Fallback minimo: solo CMD
echo Funzionalita limitata senza PowerShell
systeminfo | findstr /i "utente dominio" > users.txt
goto :eof
```

Questo approccio a tre livelli garantisce che lo script produca risultati utili indipendentemente dall'ambiente, degradando progressivamente la funzionalità invece di fallire.

---

## Script Pratici

### 01 — Raccolta informazioni sistema

```batch
@echo off
setlocal enabledelayedexpansion
title System Info Collector

set REPORT=C:\Reports\sysinfo_%COMPUTERNAME%_%date:~-4%%date:~3,2%%date:~0,2%.txt
if not exist "C:\Reports" mkdir "C:\Reports"

echo ============================================= > "%REPORT%"
echo  REPORT SISTEMA - %COMPUTERNAME%              >> "%REPORT%"
echo  Data: %date% %time%                          >> "%REPORT%"
echo  Utente: %USERDOMAIN%\%USERNAME%              >> "%REPORT%"
echo ============================================= >> "%REPORT%"

echo. >> "%REPORT%"
echo --- INFORMAZIONI OS --- >> "%REPORT%"
systeminfo | findstr /i "nome host versione tipo build" >> "%REPORT%" 2>nul
systeminfo | findstr /i "OS Name Version Build Type" >> "%REPORT%" 2>nul

echo. >> "%REPORT%"
echo --- CPU --- >> "%REPORT%"
wmic cpu get name,numberofcores,numberoflogicalprocessors,maxclockspeed /format:list >> "%REPORT%" 2>nul

echo. >> "%REPORT%"
echo --- MEMORIA --- >> "%REPORT%"
wmic os get totalvisiblememorysize,freephysicalmemory /format:list >> "%REPORT%" 2>nul
wmic memorychip get capacity,speed,manufacturer /format:list >> "%REPORT%" 2>nul

echo. >> "%REPORT%"
echo --- DISCO --- >> "%REPORT%"
wmic logicaldisk where drivetype=3 get name,size,freespace,filesystem /format:list >> "%REPORT%" 2>nul

echo. >> "%REPORT%"
echo --- RETE --- >> "%REPORT%"
ipconfig /all >> "%REPORT%" 2>nul

echo. >> "%REPORT%"
echo --- SERVIZI IN ESECUZIONE --- >> "%REPORT%"
wmic service where state="running" get name,displayname /format:list >> "%REPORT%" 2>nul

echo. >> "%REPORT%"
echo --- SOFTWARE INSTALLATO --- >> "%REPORT%"
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall" /s /v DisplayName 2>nul | findstr DisplayName >> "%REPORT%"

echo. >> "%REPORT%"
echo --- HOTFIX --- >> "%REPORT%"
wmic qfe get hotfixid,installedon /format:list >> "%REPORT%" 2>nul

echo Report generato: %REPORT%
```

### 02 — Pulizia log con retention

```batch
@echo off
setlocal enabledelayedexpansion

:: Configurazione
set LOGDIR=C:\Logs
set RETENTION_DAYS=30
set ARCHIVE_DIR=C:\Archive\Logs
set SCRIPT_LOG=%LOGDIR%\cleanup_%date:~-4%%date:~3,2%%date:~0,2%.log

if not exist "%ARCHIVE_DIR%" mkdir "%ARCHIVE_DIR%"

echo [%date% %time%] Pulizia log iniziata >> "%SCRIPT_LOG%"
echo [%date% %time%] Retention: %RETENTION_DAYS% giorni >> "%SCRIPT_LOG%"

:: Conta file prima della pulizia
set BEFORE=0
for /f %%a in ('dir /b /s "%LOGDIR%\*.log" 2^>nul ^| find /c /v ""') do set BEFORE=%%a

:: Archivia file tra 30 e 90 giorni
echo [%date% %time%] Archiviazione file 30-90 giorni... >> "%SCRIPT_LOG%"
forfiles /p "%LOGDIR%" /s /m *.log /d -%RETENTION_DAYS% /c "cmd /c if @isdir==FALSE move @path \"%ARCHIVE_DIR%\@file\"" 2>>"%SCRIPT_LOG%"

:: Elimina file archiviati oltre 90 giorni
echo [%date% %time%] Eliminazione archivi oltre 90 giorni... >> "%SCRIPT_LOG%"
forfiles /p "%ARCHIVE_DIR%" /m *.log /d -90 /c "cmd /c del @path" 2>>"%SCRIPT_LOG%"

:: Elimina file temporanei
echo [%date% %time%] Pulizia file temporanei... >> "%SCRIPT_LOG%"
forfiles /p "%LOGDIR%" /s /m *.tmp /d -7 /c "cmd /c del @path" 2>>"%SCRIPT_LOG%"

:: Conta file dopo la pulizia
set AFTER=0
for /f %%a in ('dir /b /s "%LOGDIR%\*.log" 2^>nul ^| find /c /v ""') do set AFTER=%%a

set /a DELETED=%BEFORE%-%AFTER%
echo [%date% %time%] Pulizia completata. File rimossi/archiviati: %DELETED% >> "%SCRIPT_LOG%"

endlocal
```

### 03 — Audit account utente

```batch
@echo off
setlocal enabledelayedexpansion

set REPORT=C:\Reports\user_audit_%date:~-4%%date:~3,2%%date:~0,2%.txt

echo ============================================= > "%REPORT%"
echo  AUDIT ACCOUNT UTENTI - %COMPUTERNAME%        >> "%REPORT%"
echo  Data: %date% %time%                          >> "%REPORT%"
echo  Eseguito da: %USERNAME%                      >> "%REPORT%"
echo ============================================= >> "%REPORT%"

echo. >> "%REPORT%"
echo --- ACCOUNT LOCALI --- >> "%REPORT%"
net user >> "%REPORT%"

echo. >> "%REPORT%"
echo --- DETTAGLIO OGNI ACCOUNT --- >> "%REPORT%"
for /f "skip=4 tokens=1" %%u in ('net user') do (
    if not "%%u"=="The" if not "%%u"=="Il" (
        echo. >> "%REPORT%"
        echo [UTENTE: %%u] >> "%REPORT%"
        net user %%u 2>>"%REPORT%" | findstr /i "name active expires password last logon" >> "%REPORT%"
    )
)

echo. >> "%REPORT%"
echo --- MEMBRI GRUPPO ADMINISTRATORS --- >> "%REPORT%"
net localgroup Administrators >> "%REPORT%"

echo. >> "%REPORT%"
echo --- MEMBRI REMOTE DESKTOP USERS --- >> "%REPORT%"
net localgroup "Remote Desktop Users" >> "%REPORT%" 2>nul

echo. >> "%REPORT%"
echo --- ACCOUNT DISABILITATI --- >> "%REPORT%"
wmic useraccount where disabled=true get name,sid /format:list >> "%REPORT%" 2>nul

echo. >> "%REPORT%"
echo --- ACCOUNT CON PASSWORD CHE NON SCADE --- >> "%REPORT%"
wmic useraccount where passwordexpires=false get name /format:list >> "%REPORT%" 2>nul

echo Audit completato: %REPORT%
```

### 04 — Scanner di rete

```batch
@echo off
setlocal enabledelayedexpansion

set SUBNET=192.168.1
set START=1
set END=254
set REPORT=C:\Reports\network_scan_%date:~-4%%date:~3,2%%date:~0,2%.txt
set ONLINE=0
set OFFLINE=0

echo Scansione rete %SUBNET%.0/24 in corso...
echo. > "%REPORT%"
echo Scansione rete: %SUBNET%.0/24 >> "%REPORT%"
echo Data: %date% %time% >> "%REPORT%"
echo ===================================== >> "%REPORT%"

for /l %%i in (%START%,1,%END%) do (
    ping -n 1 -w 500 %SUBNET%.%%i >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        set /a ONLINE+=1
        echo [ONLINE]  %SUBNET%.%%i
        echo [ONLINE]  %SUBNET%.%%i >> "%REPORT%"

        :: Tentativo risoluzione hostname
        for /f "tokens=1" %%h in ('nslookup %SUBNET%.%%i 2^>nul ^| findstr "Name:"') do (
            echo           Hostname: %%h >> "%REPORT%"
        )

        :: MAC address dalla tabella ARP
        for /f "tokens=2" %%m in ('arp -a %SUBNET%.%%i 2^>nul ^| findstr %SUBNET%.%%i') do (
            echo           MAC: %%m >> "%REPORT%"
        )
    ) else (
        set /a OFFLINE+=1
    )
)

echo. >> "%REPORT%"
echo ===================================== >> "%REPORT%"
echo Host online: !ONLINE! / %END% >> "%REPORT%"
echo Host offline: !OFFLINE! >> "%REPORT%"

echo.
echo Scansione completata. Online: !ONLINE!, Offline: !OFFLINE!
echo Report: %REPORT%
endlocal
```

### 05 — Automazione backup con rotazione

```batch
@echo off
setlocal enabledelayedexpansion

:: Configurazione
set SOURCE=D:\Shares
set BACKUP_ROOT=E:\Backups
set MAX_BACKUPS=7
set LOGDIR=C:\Logs\Backup
set TIMESTAMP=%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%
set TIMESTAMP=%TIMESTAMP: =0%
set BACKUP_DIR=%BACKUP_ROOT%\%TIMESTAMP%
set LOGFILE=%LOGDIR%\backup_%TIMESTAMP%.log

if not exist "%LOGDIR%" mkdir "%LOGDIR%"
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

call :log "Backup iniziato"
call :log "Source: %SOURCE%"
call :log "Destinazione: %BACKUP_DIR%"

:: Esegui backup
robocopy "%SOURCE%" "%BACKUP_DIR%" /E /SEC /MT:8 /R:3 /W:10 /NP ^
    /XD "%SOURCE%\Temp" /XF *.tmp *.bak ^
    /LOG+:"%LOGFILE%"

set RC=!ERRORLEVEL!
if !RC! geq 8 (
    call :log "ERRORE: backup fallito [code=!RC!]"
    exit /b 1
)
call :log "Backup completato [code=!RC!]"

:: Rotazione: mantieni solo gli ultimi MAX_BACKUPS
call :log "Rotazione backup (max %MAX_BACKUPS%)..."
set COUNT=0
for /f "tokens=*" %%d in ('dir /b /ad /o:-d "%BACKUP_ROOT%" 2^>nul') do (
    set /a COUNT+=1
    if !COUNT! gtr %MAX_BACKUPS% (
        call :log "Rimozione backup vecchio: %%d"
        rd /s /q "%BACKUP_ROOT%\%%d"
    )
)

call :log "Rotazione completata. Backup attivi: %MAX_BACKUPS%"
call :log "Backup terminato"
exit /b 0

:log
echo [%date% %time:~0,8%] %~1
echo [%date% %time:~0,8%] %~1 >> "%LOGFILE%"
exit /b 0
```

### 06 — Monitor servizi

```batch
@echo off
setlocal enabledelayedexpansion

:: Configurazione
set SERVICES=wuauserv Spooler W3SVC MSSQLSERVER
set LOGFILE=C:\Logs\service_monitor.log
set CHECK_INTERVAL=300

:monitor_loop
echo [%date% %time:~0,8%] Controllo servizi... >> "%LOGFILE%"

for %%s in (%SERVICES%) do (
    sc query %%s 2>nul | findstr "RUNNING" >nul
    if !ERRORLEVEL! neq 0 (
        echo [%date% %time:~0,8%] AVVISO: %%s NON in esecuzione >> "%LOGFILE%"

        :: Tentativo di riavvio
        echo [%date% %time:~0,8%] Tentativo riavvio %%s... >> "%LOGFILE%"
        net start %%s >nul 2>&1
        if !ERRORLEVEL! equ 0 (
            echo [%date% %time:~0,8%] %%s riavviato con successo >> "%LOGFILE%"
        ) else (
            echo [%date% %time:~0,8%] CRITICO: impossibile riavviare %%s >> "%LOGFILE%"

            :: Notifica via evento Windows (visibile in Event Viewer)
            eventcreate /id 999 /l Application /t ERROR ^
                /so "ServiceMonitor" /d "Impossibile riavviare: %%s" >nul 2>&1
        )
    ) else (
        echo [%date% %time:~0,8%] OK: %%s in esecuzione >> "%LOGFILE%"
    )
)

:: Attendi prima del prossimo ciclo
timeout /t %CHECK_INTERVAL% /nobreak >nul
goto :monitor_loop
```

### 07 — Report spazio disco

```batch
@echo off
setlocal enabledelayedexpansion

set REPORT=C:\Reports\disk_report_%date:~-4%%date:~3,2%%date:~0,2%.txt
set THRESHOLD=20

echo ============================================= > "%REPORT%"
echo  REPORT SPAZIO DISCO - %COMPUTERNAME%         >> "%REPORT%"
echo  Data: %date% %time%                          >> "%REPORT%"
echo  Soglia allarme: %THRESHOLD%%%                >> "%REPORT%"
echo ============================================= >> "%REPORT%"

echo. >> "%REPORT%"
set ALARM=0

for /f "skip=1 tokens=1-3" %%a in ('wmic logicaldisk where drivetype^=3 get name^,size^,freespace /format:csv 2^>nul ^| findstr /r "[A-Z]:"') do (
    set DRIVE=%%a
    set FREE=%%b
    set TOTAL=%%c

    if defined TOTAL if defined FREE (
        :: Calcolo percentuale (approssimato con aritmetica intera)
        set /a "FREE_GB=!FREE:~0,-9!"
        set /a "TOTAL_GB=!TOTAL:~0,-9!"

        if !TOTAL_GB! gtr 0 (
            set /a "PCT_FREE=!FREE_GB!*100/!TOTAL_GB!"
            echo Drive !DRIVE!: !FREE_GB! GB liberi / !TOTAL_GB! GB totali [!PCT_FREE!%% libero] >> "%REPORT%"

            if !PCT_FREE! lss %THRESHOLD% (
                echo   *** ALLARME: sotto soglia %THRESHOLD%%% *** >> "%REPORT%"
                set ALARM=1
            )
        )
    )
)

echo. >> "%REPORT%"
echo --- DIRECTORY PIU GRANDI (C:\) --- >> "%REPORT%"
for /f "tokens=*" %%d in ('dir /ad /b C:\') do (
    for /f "tokens=3" %%s in ('dir /s "C:\%%d" 2^>nul ^| findstr "File(s)"') do (
        echo   C:\%%d: %%s bytes >> "%REPORT%"
    )
)

if %ALARM%==1 (
    echo.
    echo ATTENZIONE: uno o piu dischi sotto la soglia del %THRESHOLD%%%.
    echo Verificare il report: %REPORT%
)

echo Report generato: %REPORT%
endlocal
```

### 08 — Organizzatore file per tipo

```batch
@echo off
setlocal enabledelayedexpansion

:: Organizza file in una directory per estensione
set SOURCE=C:\Users\%USERNAME%\Downloads
set LOGFILE=C:\Logs\organizer_%date:~-4%%date:~3,2%%date:~0,2%.log

echo [%date% %time%] Organizzazione file in %SOURCE% >> "%LOGFILE%"

:: Definizione categorie
set "CAT_Documenti=doc docx pdf txt xlsx pptx odt"
set "CAT_Immagini=jpg jpeg png gif bmp svg webp ico tiff"
set "CAT_Video=mp4 avi mkv mov wmv flv webm"
set "CAT_Audio=mp3 wav flac aac ogg wma m4a"
set "CAT_Archivi=zip rar 7z tar gz bz2 xz"
set "CAT_Eseguibili=exe msi bat cmd ps1 vbs"

for %%f in ("%SOURCE%\*.*") do (
    set "EXT=%%~xf"
    set "EXT=!EXT:~1!"
    set "DEST="

    :: Cerca la categoria giusta
    for %%c in (Documenti Immagini Video Audio Archivi Eseguibili) do (
        for %%e in (!CAT_%%c!) do (
            if /i "!EXT!"=="%%e" set "DEST=%%c"
        )
    )

    :: Se nessuna categoria, usa "Altro"
    if not defined DEST set "DEST=Altro"

    :: Crea directory e sposta
    if not exist "%SOURCE%\!DEST!" mkdir "%SOURCE%\!DEST!"
    move "%%f" "%SOURCE%\!DEST!\" >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        echo [%date% %time%] %%~nxf → !DEST! >> "%LOGFILE%"
    )
    set "DEST="
)

echo [%date% %time%] Organizzazione completata >> "%LOGFILE%"
echo File organizzati. Log: %LOGFILE%
endlocal
```

### 09 — Verifica connettività multi-host

```batch
@echo off
setlocal enabledelayedexpansion

set HOSTS_FILE=C:\Scripts\hosts_monitor.txt
set LOGFILE=C:\Logs\connectivity_%date:~-4%%date:~3,2%%date:~0,2%.log

:: Se il file host non esiste, crealo con esempio
if not exist "%HOSTS_FILE%" (
    echo 8.8.8.8,Google DNS> "%HOSTS_FILE%"
    echo 1.1.1.1,Cloudflare DNS>> "%HOSTS_FILE%"
    echo gateway,Default Gateway>> "%HOSTS_FILE%"
    echo Creato file host di esempio: %HOSTS_FILE%
)

echo ===================================== >> "%LOGFILE%"
echo Controllo connettivita - %date% %time% >> "%LOGFILE%"
echo ===================================== >> "%LOGFILE%"

set TOTAL=0
set ONLINE=0
set OFFLINE=0

for /f "tokens=1,2 delims=," %%a in (%HOSTS_FILE%) do (
    set /a TOTAL+=1
    ping -n 2 -w 1000 %%a >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        set /a ONLINE+=1
        echo [OK]   %%b (%%a) >> "%LOGFILE%"
    ) else (
        set /a OFFLINE+=1
        echo [FAIL] %%b (%%a) >> "%LOGFILE%"
    )
)

echo. >> "%LOGFILE%"
echo Risultati: !ONLINE!/%TOTAL% online, !OFFLINE! offline >> "%LOGFILE%"

if !OFFLINE! gtr 0 (
    echo ATTENZIONE: !OFFLINE! host non raggiungibili
)
endlocal
```

### 10 — Esportazione configurazione sistema

```batch
@echo off
setlocal

set OUTDIR=C:\Reports\SysConfig_%COMPUTERNAME%_%date:~-4%%date:~3,2%%date:~0,2%
if not exist "%OUTDIR%" mkdir "%OUTDIR%"

echo Esportazione configurazione sistema in corso...

:: Informazioni sistema
systeminfo > "%OUTDIR%\systeminfo.txt" 2>&1

:: Configurazione IP
ipconfig /all > "%OUTDIR%\ipconfig.txt" 2>&1

:: Tabella routing
route print > "%OUTDIR%\routes.txt" 2>&1

:: Firewall
netsh advfirewall show allprofiles > "%OUTDIR%\firewall_profiles.txt" 2>&1
netsh advfirewall firewall show rule name=all > "%OUTDIR%\firewall_rules.txt" 2>&1

:: Servizi
sc query type= service state= all > "%OUTDIR%\services.txt" 2>&1

:: Task schedulati
schtasks /query /fo list /v > "%OUTDIR%\scheduled_tasks.txt" 2>&1

:: Registry chiavi chiave
reg export "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" "%OUTDIR%\reg_run_machine.reg" /y >nul 2>&1
reg export "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" "%OUTDIR%\reg_run_user.reg" /y >nul 2>&1

:: Utenti e gruppi
net user > "%OUTDIR%\users.txt" 2>&1
net localgroup > "%OUTDIR%\groups.txt" 2>&1

:: Connessioni di rete
netstat -ano > "%OUTDIR%\netstat.txt" 2>&1

echo.
echo Configurazione esportata in: %OUTDIR%
echo Contenuto:
dir /b "%OUTDIR%"

endlocal
```

### 11 — Monitor risorse con soglie

```batch
@echo off
setlocal enabledelayedexpansion

set LOGFILE=C:\Logs\resource_monitor.log
set CPU_THRESHOLD=90
set MEM_THRESHOLD=90

echo [%date% %time%] Controllo risorse >> "%LOGFILE%"

:: CPU usage (via WMIC, approssimato)
for /f "skip=1" %%c in ('wmic cpu get loadpercentage /format:list 2^>nul ^| findstr "="') do (
    for /f "tokens=2 delims==" %%v in ("%%c") do (
        set CPU=%%v
        echo CPU: !CPU!%% >> "%LOGFILE%"
        if !CPU! gtr %CPU_THRESHOLD% (
            echo ALLARME CPU: !CPU!%% supera soglia %CPU_THRESHOLD%%% >> "%LOGFILE%"
        )
    )
)

:: Memoria (via WMIC)
for /f "skip=1" %%t in ('wmic os get totalvisiblememorysize /value 2^>nul ^| findstr "="') do (
    for /f "tokens=2 delims==" %%v in ("%%t") do set TOTAL_MEM=%%v
)
for /f "skip=1" %%f in ('wmic os get freephysicalmemory /value 2^>nul ^| findstr "="') do (
    for /f "tokens=2 delims==" %%v in ("%%f") do set FREE_MEM=%%v
)

if defined TOTAL_MEM if defined FREE_MEM (
    set /a USED_MEM=TOTAL_MEM-FREE_MEM
    set /a MEM_PCT=USED_MEM*100/TOTAL_MEM
    echo Memoria: !MEM_PCT!%% in uso >> "%LOGFILE%"
    if !MEM_PCT! gtr %MEM_THRESHOLD% (
        echo ALLARME MEMORIA: !MEM_PCT!%% supera soglia %MEM_THRESHOLD%%% >> "%LOGFILE%"
    )
)

endlocal
```

### 12 — Backup incrementale con hash di verifica

```batch
@echo off
setlocal enabledelayedexpansion

set SOURCE=D:\ImportantData
set DEST=E:\VerifiedBackup
set LOGFILE=C:\Logs\verified_backup_%date:~-4%%date:~3,2%%date:~0,2%.log
set ERRORS=0

call :log "Backup con verifica iniziato"

:: Copia con robocopy
robocopy "%SOURCE%" "%DEST%" /E /R:3 /W:5 /NP /LOG+:"%LOGFILE%"
if !ERRORLEVEL! geq 8 (
    call :log "ERRORE: robocopy fallito"
    exit /b 1
)

:: Verifica hash su campione di file
call :log "Verifica integrita su campione..."
set CHECKED=0
set FAILED=0

for /f "delims=" %%f in ('dir /b /s /a:-d "%SOURCE%"') do (
    set /a CHECKED+=1
    :: Verifica solo ogni 10 file per velocizzare
    set /a "MOD=!CHECKED! %% 10"
    if !MOD! equ 0 (
        set "RELPATH=%%f"
        set "RELPATH=!RELPATH:%SOURCE%=!"
        set "DESTFILE=%DEST%!RELPATH!"

        if exist "!DESTFILE!" (
            for /f "tokens=*" %%h in ('certutil -hashfile "%%f" MD5 2^>nul ^| findstr /v ":" ^| findstr /v "CertUtil"') do set HASH_SRC=%%h
            for /f "tokens=*" %%h in ('certutil -hashfile "!DESTFILE!" MD5 2^>nul ^| findstr /v ":" ^| findstr /v "CertUtil"') do set HASH_DST=%%h

            if "!HASH_SRC!" neq "!HASH_DST!" (
                call :log "MISMATCH: %%f"
                set /a FAILED+=1
            )
        )
    )
)

call :log "Verifica completata: !CHECKED! file, !FAILED! mismatch"
if !FAILED! gtr 0 (
    call :log "ATTENZIONE: rilevati file con hash diverso"
    exit /b 1
)
exit /b 0

:log
echo [%date% %time:~0,8%] %~1
echo [%date% %time:~0,8%] %~1 >> "%LOGFILE%"
exit /b 0
```

### 13 — Inventory software installato

```batch
@echo off
setlocal enabledelayedexpansion

set REPORT=C:\Reports\software_inventory_%COMPUTERNAME%_%date:~-4%%date:~3,2%%date:~0,2%.csv
echo "Computer","Software","Versione","Editore" > "%REPORT%"

:: Registro 64-bit
for /f "tokens=*" %%k in ('reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall" /s 2^>nul ^| findstr "HKEY_"') do (
    set "DN="
    set "DV="
    set "DP="
    for /f "tokens=2*" %%a in ('reg query "%%k" /v DisplayName 2^>nul ^| findstr DisplayName') do set "DN=%%b"
    for /f "tokens=2*" %%a in ('reg query "%%k" /v DisplayVersion 2^>nul ^| findstr DisplayVersion') do set "DV=%%b"
    for /f "tokens=2*" %%a in ('reg query "%%k" /v Publisher 2^>nul ^| findstr Publisher') do set "DP=%%b"
    if defined DN echo "%COMPUTERNAME%","!DN!","!DV!","!DP!" >> "%REPORT%"
)

:: Registro 32-bit su OS 64-bit
for /f "tokens=*" %%k in ('reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall" /s 2^>nul ^| findstr "HKEY_"') do (
    set "DN="
    set "DV="
    set "DP="
    for /f "tokens=2*" %%a in ('reg query "%%k" /v DisplayName 2^>nul ^| findstr DisplayName') do set "DN=%%b"
    for /f "tokens=2*" %%a in ('reg query "%%k" /v DisplayVersion 2^>nul ^| findstr DisplayVersion') do set "DV=%%b"
    for /f "tokens=2*" %%a in ('reg query "%%k" /v Publisher 2^>nul ^| findstr Publisher') do set "DP=%%b"
    if defined DN echo "%COMPUTERNAME%","!DN!","!DV!","!DP!" >> "%REPORT%"
)

:: Conta
for /f %%c in ('find /c /v "" ^< "%REPORT%"') do set /a TOTAL=%%c-1
echo Inventario completato: %TOTAL% software trovati
echo Report: %REPORT%
endlocal
```

### 14 — Hardening check base

```batch
@echo off
setlocal enabledelayedexpansion

set REPORT=C:\Reports\hardening_%COMPUTERNAME%_%date:~-4%%date:~3,2%%date:~0,2%.txt
set PASS=0
set FAIL=0

echo ============================================= > "%REPORT%"
echo  HARDENING CHECK - %COMPUTERNAME%             >> "%REPORT%"
echo  Data: %date% %time%                          >> "%REPORT%"
echo ============================================= >> "%REPORT%"

:: 1. Firewall attivo
netsh advfirewall show allprofiles state 2>nul | findstr "ON" >nul
if !ERRORLEVEL! equ 0 (set /a PASS+=1 & echo [PASS] Firewall attivo >> "%REPORT%") else (set /a FAIL+=1 & echo [FAIL] Firewall NON attivo >> "%REPORT%")

:: 2. Guest account disabilitato
net user Guest 2>nul | findstr /i "active.*No" >nul
if !ERRORLEVEL! equ 0 (set /a PASS+=1 & echo [PASS] Account Guest disabilitato >> "%REPORT%") else (set /a FAIL+=1 & echo [FAIL] Account Guest ATTIVO >> "%REPORT%")

:: 3. Windows Update configurato
reg query "HKLM\SOFTWARE\Policies\Microsoft\Windows\WindowsUpdate\AU" /v NoAutoUpdate 2>nul | findstr "0x0" >nul
if !ERRORLEVEL! equ 0 (set /a PASS+=1 & echo [PASS] Windows Update abilitato >> "%REPORT%") else (set /a FAIL+=1 & echo [FAIL] Windows Update potenzialmente disabilitato >> "%REPORT%")

:: 4. Nessuna condivisione amministrativa esposta
net share 2>nul | findstr "C\$" >nul
if !ERRORLEVEL! equ 0 (echo [INFO] Admin share C$ presente >> "%REPORT%") else (echo [INFO] Admin share C$ non presente >> "%REPORT%")

:: 5. Remote Desktop
reg query "HKLM\SYSTEM\CurrentControlSet\Control\Terminal Server" /v fDenyTSConnections 2>nul | findstr "0x1" >nul
if !ERRORLEVEL! equ 0 (set /a PASS+=1 & echo [PASS] RDP disabilitato >> "%REPORT%") else (echo [INFO] RDP abilitato - verificare se necessario >> "%REPORT%")

:: 6. SMBv1 disabilitato
reg query "HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" /v SMB1 2>nul | findstr "0x0" >nul
if !ERRORLEVEL! equ 0 (set /a PASS+=1 & echo [PASS] SMBv1 disabilitato >> "%REPORT%") else (set /a FAIL+=1 & echo [FAIL] SMBv1 potenzialmente attivo >> "%REPORT%")

:: 7. Password complexity
net accounts 2>nul | findstr /i "password" >> "%REPORT%"

echo. >> "%REPORT%"
echo ===================================== >> "%REPORT%"
echo Risultato: !PASS! pass, !FAIL! fail >> "%REPORT%"

echo Check completato: !PASS! pass, !FAIL! fail
echo Report: %REPORT%
endlocal
```

### 15 — Deploy applicazione con rollback

```batch
@echo off
setlocal enabledelayedexpansion

:: Parametri
set APP_NAME=%1
set DEPLOY_DIR=C:\Apps\%APP_NAME%
set BACKUP_DIR=C:\Apps\Backup\%APP_NAME%_%date:~-4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%
set BACKUP_DIR=!BACKUP_DIR: =0!
set SOURCE_PKG=%2
set LOGFILE=C:\Logs\deploy_%APP_NAME%_%date:~-4%%date:~3,2%%date:~0,2%.log

if "%APP_NAME%"=="" (echo Uso: %~nx0 ^<app_name^> ^<source_package^> & exit /b 1)
if "%SOURCE_PKG%"=="" (echo Uso: %~nx0 ^<app_name^> ^<source_package^> & exit /b 1)
if not exist "%SOURCE_PKG%" (echo ERRORE: pacchetto non trovato: %SOURCE_PKG% & exit /b 1)

call :log "Deploy %APP_NAME% iniziato"

:: Step 1: Backup versione corrente
if exist "%DEPLOY_DIR%" (
    call :log "Backup versione corrente..."
    mkdir "%BACKUP_DIR%" 2>nul
    robocopy "%DEPLOY_DIR%" "%BACKUP_DIR%" /MIR /R:1 /W:1 /NP >nul
    if !ERRORLEVEL! geq 8 (
        call :log "ERRORE: backup fallito, annullo deploy"
        exit /b 1
    )
    call :log "Backup completato: %BACKUP_DIR%"
)

:: Step 2: Ferma servizio (se applicabile)
sc query %APP_NAME% >nul 2>&1
if !ERRORLEVEL! equ 0 (
    call :log "Fermo servizio %APP_NAME%..."
    net stop %APP_NAME% >nul 2>&1
    timeout /t 5 /nobreak >nul
)

:: Step 3: Deploy nuova versione
call :log "Deploy nuova versione da %SOURCE_PKG%..."
robocopy "%SOURCE_PKG%" "%DEPLOY_DIR%" /MIR /R:3 /W:5 /NP >nul
if !ERRORLEVEL! geq 8 (
    call :log "ERRORE: deploy fallito, avvio rollback..."
    goto :rollback
)

:: Step 4: Avvia servizio
sc query %APP_NAME% >nul 2>&1
if !ERRORLEVEL! equ 0 (
    call :log "Avvio servizio %APP_NAME%..."
    net start %APP_NAME% >nul 2>&1
    timeout /t 5 /nobreak >nul
    sc query %APP_NAME% | findstr "RUNNING" >nul
    if !ERRORLEVEL! neq 0 (
        call :log "ERRORE: servizio non avviato, avvio rollback..."
        goto :rollback
    )
)

call :log "Deploy completato con successo"
exit /b 0

:rollback
call :log "ROLLBACK in corso..."
if exist "%BACKUP_DIR%" (
    robocopy "%BACKUP_DIR%" "%DEPLOY_DIR%" /MIR /R:1 /W:1 /NP >nul
    sc query %APP_NAME% >nul 2>&1
    if !ERRORLEVEL! equ 0 net start %APP_NAME% >nul 2>&1
    call :log "Rollback completato"
) else (
    call :log "CRITICO: nessun backup disponibile per rollback"
)
exit /b 1

:log
echo [%date% %time:~0,8%] %~1
echo [%date% %time:~0,8%] %~1 >> "%LOGFILE%"
exit /b 0
```

---

## Troubleshooting

### 01 — Variabile vuota dentro un blocco IF o FOR

**Problema**: `%VAR%` mostra il valore vecchio o vuoto all'interno di parentesi.

**Causa**: l'espansione `%VAR%` avviene prima dell'esecuzione del blocco.

**Soluzione**: usare `setlocal enabledelayedexpansion` e `!VAR!` al posto di `%VAR%`.

### 02 — Spazio prima o dopo `=` in SET

**Problema**: `set VAR = valore` crea una variabile `"VAR "` con valore `" valore"`.

**Soluzione**: nessuno spazio attorno al `=`. Usare `set "VAR=valore"` (con apici esterni) per proteggere da spazi finali.

### 03 — Script fallisce su path con spazi

**Problema**: `cd C:\Program Files` interpreta `Files` come secondo argomento.

**Soluzione**: racchiudere sempre i path tra doppi apici: `cd "C:\Program Files"`. Usare `cd /d` per cambiare drive.

### 04 — FOR non processa file con spazi nel nome

**Problema**: `for %%f in (C:\dir\*.txt)` funziona, ma se i nomi contengono spazi il parsing si rompe.

**Soluzione**: con `for /f`, usare `"usebackq delims="` e racchiudere il path tra apici.

### 05 — ERRORLEVEL non si resetta

**Problema**: dopo un errore, ERRORLEVEL rimane non-zero anche per comandi successivi che non lo impostano.

**Soluzione**: usare `cmd /c "exit /b 0"` per resettare esplicitamente, oppure controllare subito dopo il comando critico.

### 06 — Robocopy segnala errore ma i file sono copiati

**Problema**: lo script tratta exit code 1-7 come errori.

**Soluzione**: robocopy usa exit code non standard. Solo `>= 8` sono errori reali. Usare `if %ERRORLEVEL% GEQ 8`.

### 07 — Caratteri speciali rompono l'output

**Problema**: `echo` con `&`, `|`, `>`, `<` causa errori o redirect indesiderati.

**Soluzione**: escape con `^`: `echo Prezzo ^> 100`. In alternativa, usare `echo.` per riga vuota.

### 08 — Script non trova comandi che funzionano al prompt

**Problema**: comandi come `python` o `npm` non trovati quando lo script gira come task schedulato.

**Causa**: il task schedulato usa un `PATH` diverso da quello della sessione utente.

**Soluzione**: usare path assoluti nel task (`C:\Python310\python.exe`) oppure impostare `PATH` esplicitamente nello script.

### 09 — `IF ERRORLEVEL 1` è vero per ERRORLEVEL 2, 3, ...

**Problema**: la sintassi legacy `if errorlevel N` significa `>= N`, non `== N`.

**Soluzione**: usare `if %ERRORLEVEL% equ N` per confronto esatto.

### 10 — Parentesi nelle variabili rompono i blocchi IF/FOR

**Problema**: se una variabile contiene `)`, il parser di CMD confonde la fine del blocco.

**Soluzione**: usare delayed expansion `!VAR!` che viene espansa dopo il parsing dei blocchi. Oppure escape: `^)`.

### 11 — `SET /P` legge solo la prima riga da un file

**Problema**: `set /p VAR=<file.txt` legge solo la prima riga.

**Soluzione**: per leggere tutte le righe, usare `for /f "delims=" %%a in (file.txt) do ...`.

### 12 — Lo script non gira se invocato da un altro drive

**Problema**: i path relativi si rompono quando lo script è invocato da una directory diversa.

**Soluzione**: usare `%~dp0` per riferirsi alla directory dello script: `set SCRIPTDIR=%~dp0`.

### 13 — Task schedulato non produce output o log

**Problema**: il task gira ma non scrive file o log.

**Causa**: la working directory del task potrebbe essere `C:\Windows\System32`.

**Soluzione**: usare path assoluti per tutti i file. Impostare "Start in" nelle proprietà del task.

### 14 — Codifica caratteri — output illeggibile

**Problema**: caratteri accentati o Unicode corrotti nell'output o nei file di log.

**Soluzione**: aggiungere `chcp 65001 >nul` all'inizio dello script per UTF-8. Per file di log, specificare la codifica.

### 15 — Script batch consumano 100% CPU in loop

**Problema**: un `goto :loop` senza pausa consuma tutta la CPU.

**Soluzione**: inserire `timeout /t N /nobreak >nul` o `ping -n N 127.0.0.1 >nul` come delay nel loop.

### 16 — `CALL` vs esecuzione diretta di un altro .bat

**Problema**: `script2.bat` senza `CALL` non torna mai al primo script.

**Causa**: CMD sostituisce lo script corrente con il nuovo, come `exec` in Unix.

**Soluzione**: usare `CALL script2.bat` per eseguire e tornare.

---

## FAQ

### Q1: Qual è la differenza tra `.bat` e `.cmd`?

`.bat` è il formato originale MS-DOS, `.cmd` è il formato Windows NT+. La differenza pratica principale è che `.cmd` imposta `ERRORLEVEL` dopo ogni comando, rendendo il controllo errori più affidabile. Per script nuovi, usare `.cmd`.

### Q2: Posso usare variabili d'ambiente impostate in un altro script?

Solo se lo script viene eseguito con `CALL` e senza `setlocal`. Con `setlocal`, le variabili sono confinate al blocco. Per passare valori tra script, usare file temporanei, variabili d'ambiente persistenti (`setx`), o parametri di ritorno.

### Q3: Come faccio a eseguire uno script batch come amministratore?

Tasto destro → "Esegui come amministratore", oppure auto-elevazione via PowerShell: `powershell -Command "Start-Process '%~f0' -Verb RunAs"`. Per task schedulati, impostare "Run with highest privileges".

### Q4: Come gestisco i path con spazi?

Racchiuderli sempre tra doppi apici: `"C:\Program Files\App"`. Per i parametri dello script, usare `%~f1` per ottenere il path completo già gestito.

### Q5: Perche il mio `FOR /F` non processa tutte le righe?

Verificare: (1) `eol` di default è `;` — righe che iniziano con `;` vengono ignorate. Usare `eol=` per disabilitarlo. (2) `skip=N` salta N righe. (3) Righe vuote vengono sempre ignorate da `FOR /F`.

### Q6: Come faccio debugging di uno script batch?

Rimuovere temporaneamente `@echo off` per vedere ogni comando prima dell'esecuzione. Aggiungere `echo DEBUG: VAR=%VAR%` nei punti critici. Usare `pause` per fermare l'esecuzione. Redirigere output su file per analisi post-mortem.

### Q7: Come lancio un comando in background?

Usare `start "" /b comando` per avviare senza finestra. `start "" comando` apre una nuova finestra CMD. Per attività lunghe, preferire task schedulati.

### Q8: Come catturo l'output di un comando in una variabile?

Usare `for /f "delims=" %%a in ('comando') do set VAR=%%a`. Per output multi-riga, iterare con il loop.

### Q9: Posso fare aritmetica con decimali?

No. `SET /A` supporta solo interi a 32 bit. Per calcoli con decimali, invocare PowerShell: `for /f %%a in ('powershell -c "10/3"') do set RESULT=%%a`.

### Q10: Come gestisco file con nomi che contengono `!` con delayed expansion attiva?

Il carattere `!` viene interpretato come delimitatore di variabile. Disabilitare temporaneamente delayed expansion con `setlocal disabledelayedexpansion` prima di elaborare quei file, poi riabilitare.

### Q11: Quale codifica devo usare per i file `.bat`?

Batch files sono tradizionalmente in codifica ANSI/OEM. Per supporto UTF-8, aggiungere `chcp 65001 >nul` e salvare il file come UTF-8 con BOM. Nota: non tutte le operazioni batch gestiscono UTF-8 correttamente.

### Q12: Come testo uno script batch senza eseguirlo in produzione?

Usare `echo` davanti ai comandi distruttivi durante lo sviluppo: `echo del /s /q "%DIR%"` mostra cosa verrebbe eliminato senza farlo. Robocopy ha `/L` per dry-run.

### Q13: Come passo più di 9 parametri a uno script?

Usare `SHIFT` in un loop per scorrere i parametri: ogni `SHIFT` sposta `%2` in `%1`, `%3` in `%2`, ecc. `%*` contiene sempre tutti i parametri.

### Q14: Come rendo portatile uno script batch tra sistemi con locale diverso?

Evitare `%DATE%` e `%TIME%` che dipendono dal locale. Usare PowerShell per date consistenti: `for /f %%d in ('powershell -c "Get-Date -Format yyyy-MM-dd"') do set TODAY=%%d`. Per path, usare variabili d'ambiente come `%USERPROFILE%`, `%TEMP%`, `%SystemRoot%`.

### Q15: Batch scripting ha un futuro?

Batch non riceve nuove funzionalita da Windows NT, ma rimane supportato per retrocompatibilita. Microsoft raccomanda PowerShell per tutto lo sviluppo nuovo. Batch resta utile per bootstrap, WinPE, login script GPO e ambienti dove PowerShell non e disponibile. Investire tempo nell'imparare PowerShell per lavoro nuovo.

---

## Guida Migrazione Batch → PowerShell

Tabella di corrispondenza per i comandi piu comuni.

### Comandi di base

| Batch | PowerShell | Note |
|-------|-----------|------|
| `echo testo` | `Write-Output "testo"` | oppure `Write-Host` per console |
| `@echo off` | `$ErrorActionPreference = 'Stop'` | PS non ha echo dei comandi |
| `set VAR=valore` | `$VAR = "valore"` | PS usa `$` per variabili |
| `set /a X=5+3` | `$X = 5 + 3` | PS supporta float nativo |
| `set /p INPUT=Prompt:` | `$INPUT = Read-Host "Prompt"` | |
| `%VAR%` / `!VAR!` | `$VAR` | nessuna distinzione delayed |
| `%ERRORLEVEL%` | `$LASTEXITCODE` / `$?` | `$?` per cmdlet, `$LASTEXITCODE` per exe |
| `pause` | `Read-Host "Premi Invio"` | oppure `pause` (alias) |
| `cls` | `Clear-Host` | |
| `exit /b N` | `exit N` | |
| `rem` / `::` | `# commento` | |

### File e directory

| Batch | PowerShell |
|-------|-----------|
| `dir /s /b` | `Get-ChildItem -Recurse -Name` |
| `dir /ad` | `Get-ChildItem -Directory` |
| `copy src dst` | `Copy-Item src dst` |
| `xcopy /e /i src dst` | `Copy-Item src dst -Recurse` |
| `robocopy src dst /MIR` | `robocopy` (ancora il migliore) |
| `move src dst` | `Move-Item src dst` |
| `del /f /q file` | `Remove-Item file -Force` |
| `ren old new` | `Rename-Item old new` |
| `mkdir path` | `New-Item path -ItemType Directory` |
| `rmdir /s /q path` | `Remove-Item path -Recurse -Force` |
| `attrib +r file` | `Set-ItemProperty file -Name IsReadOnly -Value $true` |
| `type file` | `Get-Content file` |
| `find "str" file` | `Select-String "str" file` |
| `findstr /r "regex" file` | `Select-String -Pattern "regex" file` |
| `sort file` | `Get-Content file \| Sort-Object` |

### Control flow

| Batch | PowerShell |
|-------|-----------|
| `if "%VAR%"=="val"` | `if ($VAR -eq "val")` |
| `if exist file` | `if (Test-Path file)` |
| `if defined VAR` | `if ($VAR)` o `if ($null -ne $VAR)` |
| `if errorlevel 1` | `if ($LASTEXITCODE -ge 1)` |
| `for %%f in (*.txt)` | `foreach ($f in Get-ChildItem *.txt)` |
| `for /l %%i in (1,1,10)` | `1..10 \| ForEach-Object {...}` o `for ($i=1; $i -le 10; $i++)` |
| `for /f "tokens=..." %%a in (file)` | `Get-Content file \| ForEach-Object { $_.Split(...) }` |
| `for /r ... %%f in (...)` | `Get-ChildItem -Recurse -Filter ...` |
| `goto :label` | Non necessario (struttura procedurale) |
| `call :func` | Definire funzione PS nativa |
| `call script.bat` | `& ".\script.ps1"` o `. .\script.ps1` (dot-source) |

### Rete

| Batch | PowerShell |
|-------|-----------|
| `ping -n 4 host` | `Test-Connection host -Count 4` |
| `nslookup host` | `Resolve-DnsName host` |
| `tracert host` | `Test-NetConnection host -TraceRoute` |
| `ipconfig /all` | `Get-NetIPConfiguration` |
| `netstat -an` | `Get-NetTCPConnection` |
| `net use Z: \\srv\share` | `New-PSDrive Z FileSystem \\srv\share` |
| `net user` | `Get-LocalUser` |
| `net localgroup` | `Get-LocalGroup` |

### Sistema e registry

| Batch | PowerShell |
|-------|-----------|
| `systeminfo` | `Get-ComputerInfo` |
| `tasklist` | `Get-Process` |
| `taskkill /im app.exe /f` | `Stop-Process -Name app -Force` |
| `sc query service` | `Get-Service service` |
| `sc start service` | `Start-Service service` |
| `reg query key /v name` | `Get-ItemProperty "Registry::key" -Name name` |
| `reg add key /v name /d val` | `Set-ItemProperty "Registry::key" -Name name -Value val` |
| `reg delete key /v name /f` | `Remove-ItemProperty "Registry::key" -Name name` |
| `wmic os get caption` | `Get-CimInstance Win32_OperatingSystem \| Select Caption` |
| `schtasks /create ...` | `Register-ScheduledTask ...` |

### Esempio comparativo completo

**Batch — backup con logging:**

```batch
@echo off
setlocal
set LOGFILE=C:\Logs\backup_%date:~-4%%date:~3,2%%date:~0,2%.log
robocopy "D:\Data" "E:\Backup" /MIR /R:3 /W:5 /NP /LOG:"%LOGFILE%"
if %ERRORLEVEL% GEQ 8 (
    echo ERRORE >> "%LOGFILE%"
    exit /b 1
)
echo OK >> "%LOGFILE%"
exit /b 0
```

**PowerShell equivalente:**

```powershell
$LogFile = "C:\Logs\backup_$(Get-Date -Format yyyyMMdd).log"
$result = robocopy "D:\Data" "E:\Backup" /MIR /R:3 /W:5 /NP /LOG:$LogFile
if ($LASTEXITCODE -ge 8) {
    Add-Content $LogFile "ERRORE"
    exit 1
}
Add-Content $LogFile "OK"
exit 0
```

---

## Ottimizzazione delle Prestazioni

Batch scripting non è noto per la velocità, ma la differenza tra uno script ottimizzato e uno scritto ingenuamente può essere di ordini di grandezza su operazioni massive (migliaia di file, log voluminosi, elaborazioni ripetitive).

### Comandi interni vs esterni: il costo del processo

La distinzione fondamentale in batch è tra comandi interni (eseguiti direttamente da CMD.exe: `set`, `if`, `for`, `echo`, `goto`, `call`, `copy`, `del`, `dir`, `type`, `ren`, `mkdir`, `rmdir`) e comandi esterni (eseguibili separati: `findstr.exe`, `robocopy.exe`, `xcopy.exe`, `wmic.exe`, `forfiles.exe`). Ogni comando esterno crea un nuovo processo con il relativo overhead di kernel: allocazione memoria, caricamento immagine, inizializzazione, distruzione. In un ciclo su migliaia di file, questa differenza è drammatica:

```batch
:: LENTO: findstr è un processo esterno lanciato per ogni file
for %%f in (C:\Logs\*.log) do (
    findstr /i "errore" "%%f" >nul && echo Trovato in: %%f
)

:: PIU' VELOCE: un singolo findstr su tutti i file
findstr /s /i /m "errore" "C:\Logs\*.log"
```

Il secondo approccio lancia `findstr.exe` una sola volta. La regola generale: minimizzare il numero di processi esterni, preferendo invocarli una volta con wildcard o lista di file piuttosto che in un ciclo.

### Caching output di FOR /F

Quando `FOR /F` cattura l'output di un comando esterno, il comando viene eseguito completamente prima che il ciclo inizi. Questo è un vantaggio prestazionale: l'output viene bufferizzato. Ma se lo stesso comando viene invocato più volte nello script, il costo si moltiplica inutilmente:

```batch
:: SBAGLIATO: wmic chiamato 3 volte (3 processi, ~1.5s ciascuno)
for /f "tokens=2 delims==" %%a in ('wmic os get localdatetime /value') do set "TS1=%%a"
:: ... 100 righe dopo ...
for /f "tokens=2 delims==" %%a in ('wmic os get localdatetime /value') do set "TS2=%%a"

:: CORRETTO: catturare una volta, riusare
for /f "tokens=2 delims==" %%a in ('wmic os get localdatetime /value') do set "DT=%%a"
set "TS_DATE=%DT:~0,4%-%DT:~4,2%-%DT:~6,2%"
set "TS_TIME=%DT:~8,2%:%DT:~10,2%:%DT:~12,2%"
:: Usare %TS_DATE% e %TS_TIME% ovunque servano
```

### Robocopy /MT: parallelismo nativo

`robocopy` supporta il flag `/MT:n` per copiare file in parallelo con n thread (default 8, massimo 128). Su operazioni di copia massive, questo riduce drasticamente i tempi:

```batch
:: Copia single-thread (default senza /MT)
robocopy "%SRC%" "%DST%" /MIR /R:2 /W:3

:: Copia multi-thread: 16 thread paralleli
robocopy "%SRC%" "%DST%" /MIR /R:2 /W:3 /MT:16

:: Nota: /MT non è compatibile con /IPG (inter-packet gap)
:: e disabilita il logging a console per thread secondari
:: Usare /LOG per catturare output completo
robocopy "%SRC%" "%DST%" /MIR /MT:16 /LOG:"%LOGDIR%\robocopy.log" /NP
```

Il numero ottimale di thread dipende dall'I/O: per SSD locali 16-32, per rete 8-16, per HDD meccanici 4-8. Valori troppo alti degradano le prestazioni per contesa I/O.

### Evitare CALL in cicli stretti

`CALL` ha overhead significativo: CMD.exe deve salvare lo stato corrente, risolvere l'etichetta, e ripristinare al ritorno. In cicli su migliaia di iterazioni, inlineare la logica:

```batch
:: LENTO: CALL per ogni file (~100ms overhead per CALL)
for %%f in (*.txt) do call :process_file "%%f"

:: PIU' VELOCE: logica inline nel FOR
for %%f in (*.txt) do (
    set "FNAME=%%~nf"
    if "!FNAME:~0,4!"=="temp" del "%%f"
)
```

Per logica complessa impossibile da inlineare, considerare un approccio a due passate: prima generare la lista di file in un file temporaneo, poi elaborarla con meno overhead:

```batch
:: Passata 1: generare lista (veloce, un solo dir)
dir /b /s "C:\Data\*.csv" > "%TEMP%\filelist.tmp"

:: Passata 2: elaborare la lista
for /f "delims=" %%f in ('type "%TEMP%\filelist.tmp"') do (
    call :process_csv "%%f"
)
del "%TEMP%\filelist.tmp"
```

### Pipe chaining efficiente

Concatenare troppi comandi in pipe (`|`) crea un processo per ogni segmento. Ridurre gli stadi:

```batch
:: INEFFICIENTE: 4 processi in pipe
type file.log | findstr "ERROR" | sort | findstr /v "DEBUG"

:: MEGLIO: combinare findstr con regex
findstr /r /c:"ERROR" /v /c:"DEBUG" file.log | sort
```

Ogni `|` crea un processo aggiuntivo con pipe I/O kernel. Combinare le operazioni in un singolo comando con le opzioni native (flag `/v` per esclusione, `/r` per regex) è sempre più veloce.

---

## Best Practices

1. **Preferire PowerShell**: per nuovi script, usare PowerShell. Batch solo per compatibilita, WinPE, o script semplicissimi
2. **`@echo off` sempre**: prima riga di ogni script batch
3. **Usare `setlocal`**: isola le variabili e previene side effects
4. **Delayed expansion**: usare `!var!` anziche `%var%` nei loop con `setlocal enabledelayedexpansion`
5. **Gestire errori**: controllare `%ERRORLEVEL%` dopo ogni comando critico
6. **Logging**: redirigere output su file log con timestamp
7. **Quotare i path**: sempre `"doppi apici"` per path con spazi
8. **Robocopy exit codes**: ricordare che 1-7 sono successi, >= 8 sono errori
9. **Path assoluti**: preferire path assoluti in script destinati a task schedulati o esecuzione remota
10. **Validare input**: mai fidarsi dell'input utente, verificare e sanitizzare
11. **`set "VAR=valore"`**: usare apici esterni per evitare spazi trailing invisibili
12. **Commenti**: documentare il perche, non il cosa — il codice batch e gia di per se criptico
13. **Backup prima di modifiche**: sempre backup prima di operazioni distruttive su file o registry
14. **Test con `/L` o `echo`**: usare dry-run prima di comandi distruttivi (robocopy /L, prefisso echo)
15. **`exit /b` non `exit`**: usare `exit /b N` per uscire dallo script senza chiudere il prompt CMD
16. **Encoding**: usare `chcp 65001` se lo script deve gestire caratteri non-ASCII
17. **Subroutine**: strutturare script lunghi con `CALL :label` per leggibilita e riuso
18. **Migrazione graduale**: per script batch complessi, migrare a PowerShell incrementalmente invocando PS per le parti che batch non gestisce bene

---

## Esercizi

1. Spiega la differenza tra `%var%` e `!var!` in un ciclo `FOR`: in quali situazioni la delayed expansion e indispensabile?
2. **Lab:** Scrivi uno script batch che esegua un backup incrementale con Robocopy, registri data/ora e risultato in un file di log, e restituisca un exit code diverso in caso di successo (0), warning (1) ed errore (2).
3. Un amministratore eredita 50 script batch non documentati su un server di produzione. Descrivi un piano per inventariarli, valutarne la criticita e decidere quali migrare a PowerShell.
4. Confronta la gestione degli errori in batch (`%ERRORLEVEL%`, `IF ERRORLEVEL`, `||`) con quella di PowerShell (`try/catch`, `$LASTEXITCODE`). Quale approccio offre maggiore robustezza e perche?

## Auto-valutazione

<details><summary>1. Perche la prima riga di ogni script batch dovrebbe essere @echo off?</summary>
`@echo off` disabilita l'eco dei comandi sulla console. Il prefisso `@` nasconde anche il comando `echo off` stesso. Senza di esso, ogni riga dello script viene stampata prima dell'esecuzione, rendendo l'output illeggibile — vedi sezione Fondamenti CMD.
</details>

<details><summary>2. Cosa fa setlocal enabledelayedexpansion?</summary>
`setlocal` isola le variabili dello script (non inquina l'ambiente del chiamante). `enabledelayedexpansion` permette di espandere le variabili con `!var!` al momento dell'esecuzione di ogni riga, anziche al momento del parsing del blocco. Essenziale nei loop FOR e nei blocchi IF con piu comandi — vedi sezione Variabili e Operatori.
</details>

<details><summary>3. Quali exit code di Robocopy indicano successo e quali errore?</summary>
Exit code 0: nessuna copia necessaria. 1-7: successo con variazioni (file copiati, extra, mismatch). 8 e superiori: errore (file non copiati, errori fatali). Lo script deve controllare `IF %ERRORLEVEL% GEQ 8` per rilevare errori — vedi sezione Robocopy.
</details>

<details><summary>4. Perche usare exit /b anziche exit in uno script batch?</summary>
`exit` chiude l'intero processo CMD, incluso il prompt interattivo se lo script e stato lanciato da li. `exit /b N` esce solo dallo script (o dalla subroutine corrente) restituendo il codice N, senza chiudere la finestra — vedi Best Practices.
</details>

<details><summary>5. Come si definisce e invoca una subroutine in batch?</summary>
Si definisce con un label (`:NomeSubroutine`) e si invoca con `CALL :NomeSubroutine [argomenti]`. Gli argomenti sono accessibili come `%~1`, `%~2` ecc. La subroutine termina con `exit /b` o `goto :eof` — vedi sezione Gestione Errori e Pattern di Logging.
</details>

<details><summary>6. Come si gestiscono path con spazi in batch?</summary>
Racchiudere sempre i path tra doppi apici: `"C:\Program Files\App\file.txt"`. Nelle variabili, usare `"%USERPROFILE%\Documents"`. Nei cicli FOR, usare `%%~fI` per ottenere il path completo gia quotato — vedi Best Practices.
</details>

<details><summary>7. Qual e la sintassi corretta per evitare spazi trailing nelle variabili?</summary>
Usare `set "VAR=valore"` con gli apici che racchiudono l'intera assegnazione. Senza apici, eventuali spazi dopo il valore vengono inclusi nella variabile, causando errori difficili da diagnosticare — vedi Best Practices.
</details>

## Letture primarie consigliate

- Microsoft Learn — Windows commands reference: <https://learn.microsoft.com/windows-server/administration/windows-commands/windows-commands> (consultato: 2026-05-23)
- Microsoft Learn — Robocopy: <https://learn.microsoft.com/windows-server/administration/windows-commands/robocopy> (consultato: 2026-05-23)
- SS64 — CMD syntax and command reference: <https://ss64.com/nt/> (consultato: 2026-05-23)
- Microsoft Learn — Schtasks command: <https://learn.microsoft.com/windows-server/administration/windows-commands/schtasks> (consultato: 2026-05-23)

## Collegamenti incrociati

- [PowerShell](02-powershell.md) — linguaggio moderno che sostituisce batch per nuovi script
- [PowerShell Scripting Avanzato](22-powershell-scripting-avanzato.md) — tecniche avanzate per la migrazione da batch
- [Registry](04-registry.md) — operazioni sul registro con REG ADD/QUERY/DELETE
- [Backup e Ripristino](15-backup-ripristino.md) — automazione backup con Robocopy e script schedulati
- [Troubleshooting](19-troubleshooting.md) — diagnostica da linea di comando

## Glossario locale

| Termine | Definizione |
|---------|-------------|
| Delayed expansion | Modalita che espande le variabili (`!var!`) al momento dell'esecuzione anziche al parsing del blocco |
| ERRORLEVEL | Variabile pseudo-ambiente che contiene l'exit code dell'ultimo comando eseguito |
| Robocopy | Robust File Copy: comando avanzato per copia e sincronizzazione file con retry, logging e filtri |
| setlocal | Comando che isola le modifiche alle variabili d'ambiente impedendo che influenzino il chiamante |
| CALL | Comando per invocare un altro script batch o una subroutine interna senza chiudere lo script corrente |
| pipe (|) | Operatore che redirige l'output di un comando come input del successivo |
| exit /b | Uscita dallo script o subroutine corrente senza chiudere il processo CMD |
| WMIC | Windows Management Instrumentation Command-line: interfaccia CLI legacy per query WMI |
| schtasks | Comando per creare, modificare e gestire task schedulati da linea di comando |
| FOR /F | Variante del ciclo FOR che elabora l'output di comandi, file di testo o stringhe token per token |
