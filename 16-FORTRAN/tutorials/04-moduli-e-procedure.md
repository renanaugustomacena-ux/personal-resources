# Tutorial 04 — Moduli e procedure

## Obiettivo
Organizzare il codice tramite moduli e procedure separate.

## Esempio
```fortran
module math_mod
contains
  real function add_one(x)
    implicit none
    real, intent(in) :: x
    add_one = x + 1.0
  end function add_one
end module math_mod

program use_module
  use math_mod
  implicit none
  print *, add_one(2.5)
end program use_module
```

## Esercizio
Aggiungere una seconda funzione per calcolare il quadrato di un numero.
