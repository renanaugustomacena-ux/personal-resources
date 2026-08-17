# Setup, compilatori e ambienti

## Scope
Questo capitolo copre tutto ciò che serve per passare dall'idea di "voler programmare in Fortran" alla realtà di avere un ambiente di sviluppo funzionante, configurato e pronto per l'uso quotidiano. Non si tratta solo di installare un compilatore: si tratta di comprendere il panorama delle toolchain Fortran, le differenze tra i compilatori disponibili, i flag di compilazione più importanti, gli editor e gli IDE più adatti, e gli strumenti moderni di build come `make` e `fpm`. L'obiettivo è che lo studente, alla fine di questo capitolo, sia in grado di compilare, eseguire e gestire programmi Fortran in modo autonomo su qualsiasi sistema operativo.

## Audience
Questo documento è pensato per chi si avvicina a Fortran per la prima volta e ha bisogno di configurare il proprio ambiente, ma anche per chi già programma in altri linguaggi e vuole capire come funziona la toolchain Fortran. È particolarmente utile per studenti universitari, ricercatori, ingegneri e sviluppatori scientifici che devono lavorare su Linux, Windows o macOS.

## Obiettivo didattico
Alla fine di questo capitolo lo studente dovrebbe essere in grado di:
- conoscere i principali compilatori Fortran e le loro caratteristiche
- installare gfortran su Linux, Windows e macOS
- compilare ed eseguire un programma Fortran dalla riga di comando
- comprendere le fasi del processo di compilazione
- usare i flag di compilazione più importanti per debugging, ottimizzazione e controllo
- configurare un editor o IDE per lo sviluppo Fortran
- creare un progetto semplice con `make` o `fpm`
- risolvere i problemi di compilazione più comuni

## Prerequisiti
Prima di affrontare questo capitolo è utile avere almeno:
- una conoscenza di base del terminale o della riga di comando
- la capacità di navigare il filesystem da shell
- familiarità con il concetto di compilazione (codice sorgente → eseguibile)
- un sistema operativo funzionante (Linux, Windows o macOS)

Non è necessario aver mai usato Fortran, ma è utile aver completato o almeno letto il capitolo sui fondamenti del linguaggio.

## Fonti autorevoli da tenere come riferimento
- Fortran-lang: https://fortran-lang.org
- GCC/gfortran documentation: https://gcc.gnu.org/fortran/
- fpm (Fortran Package Manager): https://fpm.fortran-lang.org
- Intel oneAPI Fortran Compiler: https://www.intel.com/content/www/us/en/developer/tools/oneapi/fortran-compiler.html
- LFortran: https://lfortran.org
- LLVM flang: https://flang.llvm.org

## 1. Il panorama dei compilatori Fortran
Il mondo Fortran è servito da diversi compilatori, ognuno con le proprie caratteristiche, punti di forza e contesti d'uso. A differenza di linguaggi come Python, dove esiste un singolo interprete dominante, Fortran ha una tradizione di compilatori multipli, sia open-source sia commerciali. Questa diversità è un vantaggio, perché permette di scegliere lo strumento più adatto al proprio contesto, ma richiede anche di comprendere le differenze.

### gfortran (GNU Fortran)
`gfortran` è il compilatore Fortran della GNU Compiler Collection (GCC). È open-source, gratuito, multipiattaforma e supporta gli standard Fortran fino al 2018 in modo molto ampio. È il compilatore più usato in ambito accademico e open-source, ed è la scelta predefinita per chi inizia a imparare Fortran.

I suoi punti di forza sono:
- disponibilità su praticamente tutte le piattaforme
- ottimo supporto degli standard moderni
- integrazione con l'ecosistema GNU (make, gdb, etc.)
- ampia documentazione e comunità attiva
- buone capacità di diagnostica e messaggi di errore

### Intel Fortran (ifort / ifx)
Intel offre un compilatore Fortran di alta qualità, oggi disponibile gratuitamente come parte della suite Intel oneAPI. Storicamente chiamato `ifort`, il nuovo compilatore basato su LLVM si chiama `ifx`. Il compilatore Intel è noto per generare codice molto ottimizzato per processori Intel, ed è molto usato in ambito HPC (High Performance Computing) e nelle simulazioni di grandi dimensioni.

I punti di forza sono:
- ottimizzazioni avanzate per architetture Intel
- eccellente supporto degli standard Fortran
- diagnostica dettagliata
- strumenti di profiling integrati (VTune, Advisor)
- disponibilità gratuita tramite oneAPI

### flang (LLVM)
`flang` è il compilatore Fortran del progetto LLVM. È in fase di sviluppo attivo e non è ancora maturo come gfortran o Intel, ma è promettente perché si integra con l'infrastruttura LLVM, che è la stessa usata da Clang per C/C++. La sua rilevanza crescerà negli anni.

### LFortran
LFortran è un compilatore Fortran moderno con un approccio interattivo e innovativo. Supporta la compilazione interattiva, simile a un REPL, e ha l'obiettivo di rendere Fortran più accessibile. È ancora in sviluppo, ma è un progetto molto interessante da seguire.

### NAG Fortran
Il compilatore NAG è commerciale e noto per la sua severità nei controlli di conformità allo standard. È molto usato per verificare che il codice sia portabile e conforme. Non è il compilatore più veloce in termini di generazione di codice, ma è eccellente per lo sviluppo e il testing.

## 2. Installazione di gfortran su Linux
Su Linux, l'installazione di gfortran è generalmente molto semplice perché è disponibile nei repository ufficiali di tutte le distribuzioni principali.

### Debian, Ubuntu e derivate

```bash
sudo apt update
sudo apt install gfortran
```

Questo installa l'ultima versione di gfortran disponibile nei repository della distribuzione. Per verificare che l'installazione sia andata a buon fine:

```bash
gfortran --version
```

L'output dovrebbe mostrare la versione del compilatore, ad esempio `GNU Fortran (Ubuntu 13.2.0-23ubuntu4) 13.2.0`.

### Fedora, Red Hat, CentOS

```bash
sudo dnf install gcc-gfortran
```

### Arch Linux e derivate

```bash
sudo pacman -S gcc-fortran
```

### Nota sulle versioni
Le distribuzioni Linux includono spesso versioni di gfortran che non sono le più recenti. In generale, la versione nei repository è adeguata per l'apprendimento e per la maggior parte degli usi. Se si ha bisogno di una versione specifica, è possibile installare versioni multiple o compilare GCC da sorgente, ma questo è raramente necessario per chi inizia.

## 3. Installazione di gfortran su Windows
Windows non include compilatori Fortran di default, ma ci sono diverse opzioni per installare gfortran.

### Opzione 1: MSYS2 (consigliata)
MSYS2 è un ambiente che fornisce una shell Unix-like e un gestore di pacchetti (pacman) su Windows. È il modo più pulito per avere un ambiente di sviluppo Fortran completo.

1. Scaricare e installare MSYS2 da https://www.msys2.org
2. Aprire il terminale MSYS2 UCRT64
3. Aggiornare il sistema:

```bash
pacman -Syu
```

4. Installare gfortran:

```bash
pacman -S mingw-w64-ucrt-x86_64-gcc-fortran
```

5. Verificare l'installazione:

```bash
gfortran --version
```

È importante usare il terminale MSYS2 UCRT64 (non MSYS2 MSYS) per avere accesso ai compilatori MinGW. Per usare gfortran anche dal prompt di Windows, è necessario aggiungere la directory di installazione al PATH di sistema.

### Opzione 2: WSL (Windows Subsystem for Linux)
Se si usa Windows 10 o 11, WSL è un'ottima alternativa. Con WSL si ottiene un ambiente Linux completo all'interno di Windows, e l'installazione di gfortran segue le stesse istruzioni di Linux.

```bash
wsl --install
```

Una volta dentro WSL (ad esempio Ubuntu):

```bash
sudo apt update
sudo apt install gfortran
```

Questa opzione è particolarmente comoda per chi vuole usare strumenti Linux nativi senza dualboot.

### Opzione 3: MinGW standalone
È possibile scaricare MinGW con gfortran precompilato da vari siti. Tuttavia, MSYS2 è generalmente preferibile perché mantiene i pacchetti aggiornati tramite il suo gestore.

## 4. Installazione di gfortran su macOS
Su macOS, il modo più semplice per installare gfortran è tramite Homebrew.

### Con Homebrew

```bash
brew install gcc
```

Questo installa l'intera suite GCC, che include gfortran. Dopo l'installazione, il compilatore è disponibile come `gfortran` nel terminale.

```bash
gfortran --version
```

### Con MacPorts
Chi usa MacPorts può installare gfortran con:

```bash
sudo port install gcc13
```

Il nome del comando potrebbe essere `gfortran-mp-13` o simile, a seconda della versione.

### Nota su Xcode
Xcode include Clang per C/C++ ma non include un compilatore Fortran. È necessario installare gfortran separatamente tramite Homebrew o MacPorts.

## 5. Installazione di Intel oneAPI Fortran
Il compilatore Intel Fortran è disponibile gratuitamente come parte della suite Intel oneAPI Base and HPC Toolkit. L'installazione varia per sistema operativo.

### Su Linux
Il metodo più semplice è usare i repository APT o YUM forniti da Intel:

```bash
# Aggiungere il repository Intel
wget -O- https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS.PUB \
  | gpg --dearmor | sudo tee /usr/share/keyrings/oneapi-archive-keyring.gpg > /dev/null
echo "deb [signed-by=/usr/share/keyrings/oneapi-archive-keyring.gpg] \
  https://apt.repos.intel.com/oneapi all main" \
  | sudo tee /etc/apt/sources.list.d/oneAPI.list
sudo apt update
sudo apt install intel-oneapi-compiler-fortran
```

Dopo l'installazione, è necessario attivare l'ambiente:

```bash
source /opt/intel/oneapi/setvars.sh
ifx --version
```

### Su Windows
Intel fornisce un installer grafico scaricabile dal sito Intel oneAPI. L'installazione è guidata e al termine il compilatore `ifx` è disponibile dal prompt di sviluppo Intel oneAPI.

### Quando usare Intel vs gfortran
Per l'apprendimento, gfortran è più che sufficiente ed è la scelta consigliata. Il compilatore Intel diventa interessante quando si lavora su progetti dove la performance è critica, si usano processori Intel e si ha bisogno di ottimizzazioni avanzate. In ambito HPC, molti centri di calcolo hanno il compilatore Intel preinstallato.

## 6. Il primo programma: compilare e eseguire

La verifica più importante dopo l'installazione è compilare ed eseguire un programma semplice. Questo passaggio conferma che il compilatore funziona correttamente e che l'ambiente è configurato in modo adeguato.

### Creare il file sorgente
Creare un file chiamato `hello.f90` con il seguente contenuto:

```fortran
program hello
  implicit none
  print *, 'Hello, Fortran!'
end program hello
```

L'estensione `.f90` indica al compilatore che si tratta di codice Fortran in formato libero (free-form), che è lo standard moderno. Le estensioni `.f` e `.for` indicano invece il formato fisso (fixed-form), usato nel Fortran legacy e oggi sconsigliato per nuovi programmi.

### Compilare

```bash
gfortran hello.f90 -o hello
```

Questo comando prende il file sorgente `hello.f90`, lo compila e produce un eseguibile chiamato `hello` (su Windows, `hello.exe`).

### Eseguire

```bash
./hello
```

Su Windows:

```bash
hello.exe
```

L'output atteso è:

```
 Hello, Fortran!
```

Lo spazio iniziale è una caratteristica del formato di output predefinito di Fortran con `print *`. Non è un errore.

### Se qualcosa non funziona
Se il compilatore non viene trovato, verificare che sia nel PATH. Se ci sono errori di compilazione, leggere attentamente il messaggio: gfortran produce messaggi di errore generalmente chiari che indicano la riga e il tipo di problema.

## 7. Il processo di compilazione in dettaglio
Quando si esegue `gfortran hello.f90 -o hello`, in realtà avvengono diverse fasi distinte. Comprendere queste fasi è utile per diagnosticare problemi e per gestire progetti più complessi.

### Fase 1: Preprocessing
Il preprocessore gestisce eventuali direttive di preprocessamento (come `#include`, `#ifdef`, etc.). In Fortran il preprocessing non è comune come in C, ma è disponibile. Se il file ha estensione `.F90` (con F maiuscola) o se si usa il flag `-cpp`, il preprocessore viene attivato.

### Fase 2: Compilazione
Il compilatore traduce il codice sorgente Fortran in codice oggetto. Il codice oggetto è una rappresentazione intermedia in linguaggio macchina, ma non è ancora un programma eseguibile perché mancano i collegamenti con le librerie.

Per produrre solo il file oggetto senza linkare:

```bash
gfortran -c hello.f90
```

Questo produce un file `hello.o` (su Windows, `hello.obj`).

### Fase 3: Linking
Il linker combina i file oggetto con le librerie necessarie (libreria standard Fortran, libreria matematica, etc.) per produrre l'eseguibile finale.

```bash
gfortran hello.o -o hello
```

In pratica, quando si usa `gfortran hello.f90 -o hello`, tutte e tre le fasi vengono eseguite in sequenza. La separazione diventa importante quando si lavora con progetti multi-file, dove si compilano separatamente i singoli moduli e poi si linkano insieme.

### Compilazione di più file
Quando un progetto ha più file sorgente, si possono compilare tutti insieme:

```bash
gfortran modulo.f90 main.f90 -o programma
```

Oppure separatamente:

```bash
gfortran -c modulo.f90
gfortran -c main.f90
gfortran modulo.o main.o -o programma
```

L'ordine è importante: i file che contengono moduli usati da altri file devono essere compilati prima. Questo è un aspetto specifico di Fortran che lo distingue da C/C++, dove l'ordine di compilazione dei file oggetto non ha importanza.

## 8. Flag di compilazione essenziali
I flag di compilazione controllano il comportamento del compilatore e sono fondamentali per lo sviluppo efficace. Conoscere i flag giusti può fare la differenza tra un programma che funziona e uno che ha bug nascosti.

### Flag di base

| Flag | Significato |
|------|-------------|
| `-o nome` | Specifica il nome dell'eseguibile di output |
| `-c` | Compila senza linkare (produce file .o) |
| `-Wall` | Abilita la maggior parte dei warning |
| `-Wextra` | Abilita warning aggiuntivi |
| `-Werror` | Tratta i warning come errori |

### Flag di debugging

| Flag | Significato |
|------|-------------|
| `-g` | Include informazioni di debug per gdb |
| `-fcheck=all` | Abilita tutti i controlli runtime (bounds checking, overflow, etc.) |
| `-fbacktrace` | Genera un backtrace in caso di errore runtime |
| `-ffpe-trap=invalid,zero,overflow` | Trappa le eccezioni floating-point |

Il flag `-fcheck=all` è particolarmente importante durante lo sviluppo. Abilita il controllo dei limiti degli array (bounds checking), che in Fortran non è attivo di default per ragioni di performance. Senza questo flag, un accesso fuori dai limiti di un array non genera un errore ma produce un comportamento indefinito, che può portare a risultati errati o crash imprevedibili.

```bash
gfortran -g -fcheck=all -fbacktrace -Wall hello.f90 -o hello
```

Questa combinazione è la raccomandazione standard per lo sviluppo. Genera un eseguibile con informazioni di debug, controlli runtime completi e warning attivi. È più lento dell'eseguibile ottimizzato, ma cattura errori che altrimenti rimarrebbero nascosti.

### Flag di ottimizzazione

| Flag | Significato |
|------|-------------|
| `-O0` | Nessuna ottimizzazione (default) |
| `-O1` | Ottimizzazioni di base |
| `-O2` | Ottimizzazioni standard (buon bilanciamento) |
| `-O3` | Ottimizzazioni aggressive |
| `-Ofast` | Come -O3 più ottimizzazioni che possono violare lo standard |
| `-march=native` | Ottimizza per l'architettura del processore corrente |

Per lo sviluppo si usa `-O0` (o nessun flag di ottimizzazione) insieme ai flag di debug. Per la produzione si usa `-O2` o `-O3`. La differenza di performance può essere molto significativa, soprattutto in codice numerico con molti loop.

```bash
# Per lo sviluppo
gfortran -g -fcheck=all -fbacktrace -Wall -O0 programma.f90 -o programma_debug

# Per la produzione
gfortran -O2 -march=native programma.f90 -o programma_ottimizzato
```

È importante non usare `-fcheck=all` insieme a `-O2` o superiore in produzione, perché i controlli runtime hanno un costo significativo in termini di performance.

### Flag specifici per lo standard

| Flag | Significato |
|------|-------------|
| `-std=f2018` | Richiede conformità allo standard Fortran 2018 |
| `-std=f2008` | Richiede conformità allo standard Fortran 2008 |
| `-pedantic` | Segnala qualsiasi deviazione dallo standard scelto |

Usare `-std=f2018 -pedantic` è utile quando si vuole scrivere codice portabile che funzioni con qualsiasi compilatore conforme allo standard.

## 9. Estensioni dei file e formato del codice
In Fortran, l'estensione del file sorgente ha un significato specifico per il compilatore:

| Estensione | Formato | Preprocessing |
|------------|---------|---------------|
| `.f90`, `.f95`, `.f03`, `.f08` | Libero (free-form) | No |
| `.F90`, `.F95`, `.F03`, `.F08` | Libero (free-form) | Sì |
| `.f`, `.for`, `.ftn` | Fisso (fixed-form) | No |
| `.F`, `.FOR`, `.FTN` | Fisso (fixed-form) | Sì |

Il formato libero è lo standard moderno e dovrebbe essere usato per tutti i nuovi programmi. Il formato fisso risale al Fortran 77 e ha regole rigide sulla posizione dei caratteri (colonne 1-5 per etichette, colonna 6 per continuazione, colonne 7-72 per il codice). Queste limitazioni derivano dall'epoca delle schede perforate.

Per nuovi progetti, usare sempre `.f90` come estensione. Nonostante il nome suggerisca "Fortran 90", questa estensione è convenzione per tutto il Fortran moderno, inclusi i programmi scritti secondo gli standard 2008 e 2018.

## 10. Editor e IDE per lo sviluppo Fortran
La scelta dell'editor è personale, ma alcuni strumenti offrono un supporto particolarmente buono per Fortran.

### Visual Studio Code
VS Code è probabilmente l'editor più popolare per Fortran moderno, grazie all'estensione "Modern Fortran" che fornisce:
- syntax highlighting
- completamento automatico
- navigazione del codice (go to definition, find references)
- integrazione con il Language Server Protocol tramite fortls
- integrazione con il terminale per compilazione diretta
- supporto per debugging con gdb

Per configurarlo:
1. Installare VS Code
2. Installare l'estensione "Modern Fortran" dal marketplace
3. Installare `fortls` (Fortran Language Server):

```bash
pip install fortls
```

4. Configurare le impostazioni di VS Code per puntare al compilatore

VS Code con Modern Fortran è la combinazione consigliata per chi inizia, perché offre un buon bilanciamento tra facilità d'uso e funzionalità avanzate.

### Vim e Neovim
Vim offre syntax highlighting nativo per Fortran. Per un'esperienza più ricca, si può configurare Neovim con:
- plugin LSP per integrare fortls
- plugin di completamento (nvim-cmp o simili)
- plugin per la compilazione rapida

Vim è particolarmente popolare tra chi lavora su sistemi remoti via SSH, dove un editor grafico non è disponibile.

### Emacs
Emacs ha il modo `f90-mode` integrato per Fortran in formato libero. Supporta indentazione automatica, syntax highlighting e può essere configurato con LSP per funzionalità avanzate.

### Altri editor
- **Sublime Text**: supporta Fortran tramite pacchetti della comunità
- **Kate/KDevelop**: buon supporto su KDE/Linux
- **Eclipse con Photran**: IDE completo per Fortran, ma meno mantenuto negli ultimi anni
- **Code::Blocks**: IDE leggero con supporto Fortran

### La scelta pratica
Per chi inizia, VS Code con Modern Fortran è la scelta più semplice e completa. Per chi lavora in ambito HPC su server remoti, Vim o Emacs sono spesso preferiti. La cosa importante è avere almeno syntax highlighting e la capacità di compilare ed eseguire dal terminale integrato.

## 11. Introduzione a make
`make` è uno strumento di build automation che esiste da decenni ed è ancora ampiamente usato in ambito scientifico. Il suo scopo è automatizzare il processo di compilazione, ricompilando solo i file che sono stati modificati.

### Il concetto di Makefile
Un `Makefile` è un file di testo che descrive le regole di compilazione. Ogni regola ha un target (l'obiettivo), delle dipendenze e dei comandi.

```makefile
# Makefile per un progetto Fortran semplice
FC = gfortran
FFLAGS = -Wall -g -fcheck=all

# Target principale
programma: main.o modulo.o
	$(FC) $(FFLAGS) main.o modulo.o -o programma

# Regole di compilazione
main.o: main.f90 modulo.o
	$(FC) $(FFLAGS) -c main.f90

modulo.o: modulo.f90
	$(FC) $(FFLAGS) -c modulo.f90

# Pulizia
clean:
	rm -f *.o *.mod programma
```

In questo esempio:
- `FC` è la variabile per il compilatore
- `FFLAGS` contiene i flag di compilazione
- `programma` dipende da `main.o` e `modulo.o`
- `main.o` dipende da `main.f90` e da `modulo.o` (perché main usa il modulo)
- `clean` è un target convenzionale per rimuovere i file generati

Per compilare, basta eseguire:

```bash
make
```

Per pulire:

```bash
make clean
```

### Vantaggi di make
Il vantaggio principale di make è che ricompila solo ciò che è necessario. Se si modifica solo `main.f90`, make ricompila solo `main.o` e ri-linka, senza ricompilare `modulo.o`. Questo risparmio è trascurabile per progetti piccoli, ma diventa molto significativo per progetti con centinaia di file sorgente.

### Limiti di make
Il limite principale di make per Fortran è che la gestione delle dipendenze dei moduli deve essere fatta manualmente. Quando un file `use` un modulo definito in un altro file, il file `.mod` deve esistere al momento della compilazione, e questa dipendenza deve essere espressa nel Makefile. Per progetti grandi, questo diventa complesso e soggetto a errori.

## 12. Introduzione a fpm (Fortran Package Manager)
`fpm` è uno strumento moderno per la gestione di progetti Fortran. È progettato specificamente per Fortran e risolve molti dei problemi di make, in particolare la gestione automatica delle dipendenze tra moduli.

### Installazione di fpm
Fpm può essere installato in diversi modi:

```bash
# Su Linux con i binari precompilati
curl -LO https://github.com/fortran-lang/fpm/releases/latest/download/fpm-linux-x86_64
chmod +x fpm-linux-x86_64
sudo mv fpm-linux-x86_64 /usr/local/bin/fpm

# Su macOS con Homebrew
brew install fpm

# Su Windows con MSYS2
pacman -S mingw-w64-ucrt-x86_64-fpm
```

### Creare un nuovo progetto con fpm

```bash
fpm new il_mio_progetto
cd il_mio_progetto
```

Questo crea una struttura di progetto standard:

```
il_mio_progetto/
├── fpm.toml
├── src/
│   └── il_mio_progetto.f90
├── app/
│   └── main.f90
└── test/
    └── check.f90
```

Il file `fpm.toml` è il file di configurazione del progetto:

```toml
name = "il_mio_progetto"
version = "0.1.0"
license = "MIT"
author = "Nome Cognome"

[build]
auto-executables = true
auto-tests = true
```

### Compilare e eseguire con fpm

```bash
# Compilare
fpm build

# Eseguire il programma principale
fpm run

# Eseguire i test
fpm test
```

Fpm gestisce automaticamente le dipendenze tra moduli, l'ordine di compilazione e la struttura del progetto. Non è necessario scrivere un Makefile o preoccuparsi dell'ordine dei file.

### Vantaggi di fpm rispetto a make
- Gestione automatica delle dipendenze tra moduli
- Struttura di progetto standardizzata
- Gestione delle dipendenze esterne (pacchetti)
- Compilazione, esecuzione e testing con un singolo comando
- Configurazione minima tramite `fpm.toml`

### Quando usare make vs fpm
Per nuovi progetti, fpm è quasi sempre la scelta migliore. È più semplice, più moderno e progettato specificamente per Fortran. Make rimane utile quando si lavora con codice legacy, quando si ha bisogno di regole di build molto personalizzate, o quando si lavora in ambienti dove fpm non è disponibile.

## 13. Introduzione a CMake
CMake è un sistema di build multipiattaforma molto usato in ambito scientifico e ingegneristico. Non è specifico per Fortran, ma lo supporta bene ed è la scelta preferita per progetti che combinano Fortran con C, C++ o altre lingue.

### Un CMakeLists.txt minimale per Fortran

```cmake
cmake_minimum_required(VERSION 3.12)
project(il_mio_progetto Fortran)

# Impostare lo standard Fortran
set(CMAKE_Fortran_FLAGS "${CMAKE_Fortran_FLAGS} -Wall")
set(CMAKE_Fortran_FLAGS_DEBUG "-g -fcheck=all -fbacktrace")
set(CMAKE_Fortran_FLAGS_RELEASE "-O2 -march=native")

# Aggiungere l'eseguibile
add_executable(programma
  src/modulo.f90
  src/main.f90
)
```

### Compilare con CMake

```bash
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Debug
make
```

CMake genera automaticamente i Makefile (o i file per altri sistemi di build come Ninja) e gestisce le dipendenze in modo più sofisticato di make. È particolarmente utile per progetti che devono essere compilati su diverse piattaforme o che dipendono da librerie esterne come BLAS, LAPACK o MPI.

## 14. Gestione di progetti multi-file
Man mano che un programma cresce, diventa necessario organizzare il codice in più file. In Fortran, la pratica standard è avere un file per ogni modulo e un file principale per il programma.

### Struttura tipica di un progetto

```
progetto/
├── src/
│   ├── costanti.f90      ! modulo con costanti
│   ├── matematica.f90    ! modulo con funzioni matematiche
│   ├── io_utils.f90      ! modulo per input/output
│   └── main.f90          ! programma principale
├── test/
│   └── test_matematica.f90
├── Makefile (o fpm.toml)
└── README.md
```

### Esempio pratico
File `src/costanti.f90`:

```fortran
module costanti
  implicit none
  integer, parameter :: dp = selected_real_kind(15, 307)
  real(dp), parameter :: pi = 3.141592653589793238_dp
  real(dp), parameter :: e_euler = 2.718281828459045235_dp
end module costanti
```

File `src/matematica.f90`:

```fortran
module matematica
  use costanti, only: dp, pi
  implicit none
contains
  function area_cerchio(raggio) result(area)
    real(dp), intent(in) :: raggio
    real(dp) :: area
    area = pi * raggio**2
  end function area_cerchio

  function volume_sfera(raggio) result(volume)
    real(dp), intent(in) :: raggio
    real(dp) :: volume
    volume = (4.0_dp / 3.0_dp) * pi * raggio**3
  end function volume_sfera
end module matematica
```

File `src/main.f90`:

```fortran
program geometria
  use costanti, only: dp
  use matematica, only: area_cerchio, volume_sfera
  implicit none

  real(dp) :: r

  r = 5.0_dp
  print *, 'Raggio:', r
  print *, 'Area del cerchio:', area_cerchio(r)
  print *, 'Volume della sfera:', volume_sfera(r)
end program geometria
```

Compilazione manuale:

```bash
gfortran -c src/costanti.f90
gfortran -c src/matematica.f90
gfortran -c src/main.f90
gfortran costanti.o matematica.o main.o -o geometria
```

Oppure con fpm, basta mettere i file nella struttura corretta e il build è automatico.

## 15. File .mod e la compilazione di moduli
Quando si compila un file che contiene un `module`, il compilatore genera un file `.mod` oltre al file `.o`. Il file `.mod` contiene le informazioni sull'interfaccia del modulo (nomi, tipi, procedure) e viene letto dal compilatore quando un altro file fa `use` di quel modulo.

Questo meccanismo ha implicazioni importanti:
- L'ordine di compilazione conta: il modulo deve essere compilato prima di chi lo usa
- I file `.mod` sono specifici del compilatore: non sono portabili tra gfortran e Intel
- I file `.mod` devono essere nella directory corrente o in una directory specificata con `-I`

```bash
# Compilare il modulo
gfortran -c -J mod/ src/costanti.f90

# Compilare chi usa il modulo, indicando dove trovare i .mod
gfortran -c -I mod/ src/main.f90
```

Il flag `-J` specifica la directory dove scrivere i file `.mod`, e `-I` specifica dove cercarli. Questa gestione è automatica con fpm e CMake, ma va fatta manualmente con make.

## 16. Debugging con gdb
Quando un programma Fortran non funziona come previsto, il debugger `gdb` (GNU Debugger) è lo strumento standard per investigare. Per usare gdb, il programma deve essere compilato con il flag `-g`.

### Sessione di debug tipica

```bash
# Compilare con informazioni di debug
gfortran -g -fcheck=all -fbacktrace programma.f90 -o programma

# Avviare gdb
gdb ./programma
```

All'interno di gdb, i comandi più utili sono:

```
(gdb) break main          # Impostare un breakpoint all'inizio
(gdb) run                 # Eseguire il programma
(gdb) next                # Eseguire la riga successiva
(gdb) step                # Entrare dentro una subroutine
(gdb) print variabile     # Stampare il valore di una variabile
(gdb) print array(1:5)    # Stampare una sezione di array
(gdb) continue            # Continuare l'esecuzione
(gdb) backtrace           # Mostrare lo stack delle chiamate
(gdb) quit                # Uscire
```

Per chi usa VS Code, il debugging è integrato nell'editor e può essere configurato per usare gdb con un'interfaccia grafica, rendendo il processo molto più intuitivo.

## 17. Troubleshooting degli errori comuni
Quando si inizia a lavorare con Fortran, ci sono alcuni errori che si incontrano frequentemente. Conoscerli in anticipo aiuta a risolverli più rapidamente.

### "Command not found" per gfortran
Significa che il compilatore non è installato o non è nel PATH. Su Linux, installare il pacchetto appropriato. Su Windows con MSYS2, assicurarsi di usare il terminale corretto (UCRT64).

### "Error: Unexpected end of file"
Spesso indica un blocco non chiuso. Ogni `program` deve avere il suo `end program`, ogni `do` il suo `end do`, ogni `if` il suo `end if`.

### "Error: Symbol 'x' has no IMPLICIT type"
Si sta usando una variabile non dichiarata (con `implicit none` attivo). Dichiarare la variabile con il tipo appropriato.

### "Error: Cannot open module file 'modulo.mod'"
Il modulo non è stato compilato prima del file che lo usa, oppure il file `.mod` non è nella directory corretta. Compilare il modulo prima e usare `-I` per indicare dove cercarlo.

### "Error: Type mismatch in argument"
Si sta passando un argomento di tipo errato a una subroutine o funzione. Verificare che i tipi corrispondano all'interfaccia.

### Runtime error: "Index out of bounds"
Si sta accedendo a un array con un indice fuori dai limiti. Questo errore appare solo se il programma è compilato con `-fcheck=all`. Verificare che gli indici siano nell'intervallo corretto.

## 18. Ambienti online per provare Fortran
Per chi vuole provare Fortran senza installare nulla, esistono ambienti di compilazione online:

- **Compiler Explorer (godbolt.org)**: permette di compilare codice Fortran e vedere l'assembly generato. Molto utile per capire le ottimizzazioni del compilatore.
- **play.fortran-lang.org**: playground ufficiale della comunità Fortran. Permette di scrivere, compilare ed eseguire codice Fortran direttamente nel browser.
- **Replit**: supporta Fortran e permette di creare piccoli progetti online.

Questi strumenti sono utili per test rapidi e per l'apprendimento iniziale, ma per progetti reali è necessario avere un ambiente locale configurato.

## 19. Best practices per la configurazione dell'ambiente
Dopo aver installato e configurato tutto, è utile stabilire alcune abitudini:

- **Usare sempre `implicit none`** in ogni program unit. Questo può essere forzato anche con il flag del compilatore `-fimplicit-none`.
- **Compilare sempre con warning attivi** durante lo sviluppo (`-Wall -Wextra`).
- **Usare `-fcheck=all` durante lo sviluppo** per catturare errori di bounds e overflow.
- **Separare i flag di debug da quelli di produzione**: usare `-O0 -g -fcheck=all` per sviluppo e `-O2` per produzione.
- **Organizzare il progetto fin dall'inizio** con una struttura di cartelle chiara.
- **Usare fpm per nuovi progetti** quando possibile.
- **Mantenere il codice sotto version control** con git fin dall'inizio.

## 20. Esempio completo: dal file sorgente all'eseguibile ottimizzato
Per consolidare tutti i concetti di questo capitolo, vediamo un workflow completo.

### Passo 1: Creare la struttura del progetto

```bash
mkdir -p progetto_test/src
cd progetto_test
```

### Passo 2: Scrivere il codice

File `src/calcolo.f90`:

```fortran
module calcolo
  implicit none
  integer, parameter :: dp = selected_real_kind(15, 307)
contains
  function somma_quadrati(n) result(s)
    integer, intent(in) :: n
    real(dp) :: s
    integer :: i
    s = 0.0_dp
    do i = 1, n
      s = s + real(i, dp)**2
    end do
  end function somma_quadrati

  function formula_chiusa(n) result(s)
    integer, intent(in) :: n
    real(dp) :: s
    s = real(n, dp) * real(n + 1, dp) * real(2*n + 1, dp) / 6.0_dp
  end function formula_chiusa
end module calcolo
```

File `src/main.f90`:

```fortran
program test_calcolo
  use calcolo, only: dp, somma_quadrati, formula_chiusa
  implicit none

  integer :: n
  real(dp) :: risultato_loop, risultato_formula

  n = 1000000
  risultato_loop = somma_quadrati(n)
  risultato_formula = formula_chiusa(n)

  print '(A, I0)', 'N = ', n
  print '(A, ES20.13)', 'Somma con loop:    ', risultato_loop
  print '(A, ES20.13)', 'Formula chiusa:    ', risultato_formula
  print '(A, ES10.3)',  'Differenza:        ', abs(risultato_loop - risultato_formula)
end program test_calcolo
```

### Passo 3: Compilare in modalità debug

```bash
gfortran -g -fcheck=all -fbacktrace -Wall -O0 src/calcolo.f90 src/main.f90 -o test_debug
./test_debug
```

### Passo 4: Verificare che tutto funzioni e compilare in modalità ottimizzata

```bash
gfortran -O2 -march=native src/calcolo.f90 src/main.f90 -o test_ottimizzato
./test_ottimizzato
```

### Passo 5: Con fpm (alternativa)

```bash
fpm new progetto_test
# Copiare i file nella struttura fpm
fpm build
fpm run
```

Questo workflow — scrivere, compilare con debug, verificare, ottimizzare — è il ciclo fondamentale dello sviluppo Fortran e va interiorizzato fin dall'inizio.

## 21. Errori frequenti nella configurazione dell'ambiente
È comune, soprattutto all'inizio, incontrare problemi di configurazione che frustrano lo studente. Ecco i più frequenti:

- **Non aggiungere il compilatore al PATH**: il sistema non trova `gfortran` perché la directory non è nel PATH di sistema. Verificare con `which gfortran` (Linux/macOS) o `where gfortran` (Windows).
- **Usare il terminale sbagliato su Windows**: con MSYS2, è fondamentale usare il terminale UCRT64, non il terminale MSYS2 generico.
- **Confondere formato libero e fisso**: usare `.f90` per codice moderno, mai `.f` a meno che non si lavori con codice legacy.
- **Dimenticare `-fcheck=all` durante lo sviluppo**: senza questo flag, molti errori rimangono invisibili.
- **Compilare nell'ordine sbagliato**: i moduli devono essere compilati prima dei file che li usano.
- **Non pulire i file `.mod` dopo cambiamenti**: a volte file `.mod` vecchi causano errori. `make clean` o eliminare manualmente i `.mod` risolve il problema.

## 22. Una prospettiva finale sull'ambiente di sviluppo
L'ambiente di sviluppo non è solo un prerequisito tecnico: è il contesto nel quale si lavora ogni giorno. Un ambiente ben configurato riduce l'attrito, accelera il ciclo di sviluppo e permette di concentrarsi sul problema scientifico anziché sugli strumenti. Per questo motivo, investire tempo nella configurazione iniziale non è tempo perso, ma tempo risparmiato in futuro.

Il consiglio finale è: partire con gfortran e un editor con syntax highlighting (VS Code è un'ottima scelta), usare fpm per i progetti, compilare sempre con flag di debug durante lo sviluppo e ottimizzare solo quando il programma è corretto. Questa base è sufficiente per affrontare tutti i capitoli successivi con sicurezza.
