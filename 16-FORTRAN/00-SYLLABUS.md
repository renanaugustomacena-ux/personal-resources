# Syllabus — Fortran

## 1. Introduzione al linguaggio
- storia e contesto di Fortran
- perché Fortran è ancora rilevante
- confronto con Python, C, C++, Rust per contesti scientifici
- standard moderni: Fortran 90/95/2008/2018

## 2. Setup e ambienti di sviluppo
- installazione di gfortran, flang, ifort/lfortran dove appropriato
- editor e IDE supportati
- compilazione da linea di comando
- gestione di versioni e toolchain

## 3. Fondamenti di sintassi
- program, implicit none, variabili, costanti
- operatori aritmetici, relazionali, logici
- strutture di controllo: if, select case, do, cycle, exit
- funzioni e subroutines

## 4. Tipi numerici e precisione
- integer, real, complex, logical
- kind, selected_real_kind, precisione numerica
- overflow, underflow, round-off, epsilon
- best practice per calcolo scientifico

## 5. Array e stringhe
- array monodimensionali e multidimensionali
- array sections, reshape, spread, pack
- allocatable arrays, assumed-shape arrays
- stringhe, caratteri, manipolazione testuale

## 6. Moduli e organizzazione del codice
- module, use, private, public
- separazione tra interfacce e implementazione
- organizzazione di progetti medi e grandi
- include files e convenzioni di stile

## 7. Procedure e programmazione strutturata
- function e subroutine
- intent, interface, optional, keyword arguments
- recursion, internal procedures
- program units e modularità

## 8. Derived types e programmazione orientata agli oggetti
- derived types
- type-bound procedures
- object-based programming
- limiti e vantaggi del modello OOP in Fortran

## 9. Input/Output e gestione file
- read/write, open/close, rewind
- formati, unformatted I/O, binary I/O
- gestione di file di testo e dati scientifici
- error handling in I/O

## 10. Memoria, allocazione e puntatori
- allocatable, pointer, target
- memory leaks, dangling pointers
- gestione di array dinamici
- performance e sicurezza della memoria

## 11. Interoperabilità con C/C++ e Python
- binding C
- interoperable types
- wrapping di routine Fortran per C
- integrazione con Python scientifico e librerie esterne

## 12. Parallel computing e performance
- OpenMP
- coarrays
- MPI-oriented design patterns
- profiling e benchmark

## 13. Build systems e packaging
- make
- CMake e Fortran
- fpm (Fortran Package Manager)
- packaging e distribuzione di librerie

## 14. Testing, debugging e qualità del software
- unit testing
- assert, logging, tracing
- debugging con gdb e strumenti moderni
- gestione di bug numerici e regressioni

## 15. Scientific computing e librerie
- BLAS, LAPACK
- FFTW, HDF5, netCDF
- linear algebra, optimization, PDE
- integrazione con ambienti scientifici

## 16. Progetto capstone
- simulazione numerica, modello matematico o pipeline scientifica
- packaging, documentazione, test, benchmark
- presentazione dei risultati
