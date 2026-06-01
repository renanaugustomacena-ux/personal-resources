# Case Study — AWS S3 us-east-1 Outage 2017 (the typo)

> **Tipo:** cloud provider incident postmortem
> **Aggiornamento:** 2026-04-27

## Cronologia

**2017-02-28** — AWS S3 team esegue maintenance: rimozione subset di server.

**Comando:** typo in command line. Invece di rimuovere un subset, rimuove un set piu grande del previsto.

**Cascade:** rimuovere quel set rimuove gli S3 indexing/placement subsystem. Senza index, S3 non puo servire request.

**Durata outage:** 4 ore.

**Impact:** S3 us-east-1 down → S3 dashboard giù → AWS Status Dashboard down (perche hosted on S3) → migliaia di service Internet downstream giù.

**Postmortem AWS:** pubblicato giorni dopo, blameless e dettagliato. Action items:
- Refactor subsystem a essere piu modular (un set non puo prendere tutto down).
- Tooling cap su comando: validate before execute.
- Audit log con auto-cap.

## Lezioni

1. **Single command che dipende su typing perfetto = single point of failure umano.** Wrap in tool con confirm + dry-run.
2. **Status dashboard deve hostare *fuori* dal sistema che monitora.** Meta-irony AWS dashboard giù.
3. **Modular subsystem reduces blast radius.** Una pulizia non puo rimuovere prod.
4. **Postmortem pubblico builds trust.** AWS guadagno credibility nonostante outage.

## Riferimenti

- AWS Postmortem. https://aws.amazon.com/message/41926/
- The Register coverage. https://www.theregister.com/2017/03/02/aws_s3_outage_human_error/

## Cross-links

- Modulo 21 — postmortem culture.
- Modulo 23 — change automation con validation.
