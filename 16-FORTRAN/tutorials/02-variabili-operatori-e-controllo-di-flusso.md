# Tutorial 02 — Variabili, operatori e controllo di flusso

## Obiettivo
Comprendere come dichiarare variabili, usare operatori e costruire programmi con controllo di flusso.

## Esempio
```fortran
program flow
  implicit none
  integer :: x
  x = 10

  if (x > 5) then
    print *, 'x is greater than 5'
  else
    print *, 'x is not greater than 5'
  end if
end program flow
```

## Esercizio
Estendere il programma con un ciclo `do` e stampare i valori da 1 a 10.
