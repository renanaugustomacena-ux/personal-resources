# Tutorial 03 — Array e stringhe

## Obiettivo
Usare array e stringhe in modo pratico all’interno di un programma Fortran.

## Esempio
```fortran
program arrays_strings
  implicit none
  integer :: i
  integer, dimension(5) :: values
  character(len=20) :: name

  values = (/ 1, 2, 3, 4, 5 /)
  name = 'Fortran'

  do i = 1, 5
    print *, values(i)
  end do

  print *, 'Name: ', trim(name)
end program arrays_strings
```

## Esercizio
Creare un array di 10 elementi e calcolare la somma dei valori.
