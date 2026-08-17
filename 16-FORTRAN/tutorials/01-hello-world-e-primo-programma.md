# Tutorial 01 — Hello world e primo programma

## Obiettivo
Scrivere, compilare ed eseguire un programma Fortran minimo.

## Esempio
```fortran
program hello
  implicit none
  print *, 'Hello, Fortran!'
end program hello
```

## Passi
1. salvare il file con estensione `.f90`
2. compilare con `gfortran nome.f90 -o hello`
3. eseguire `./hello`

## Esercizio
Modificare il programma in modo che stampi il tuo nome e un messaggio personalizzato.
