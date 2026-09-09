---
date: 2026-09-08
topic: teams-local-backup
---

# Backup locale delle chat Teams

## Cosa costruiamo

Un'applicazione a riga di comando distribuibile come singolo eseguibile. Ogni utente accede direttamente a Microsoft 365 tramite device-code flow e salva sul proprio computer le chat 1:1, di gruppo e delle riunioni.

## Perché questo approccio

Un client pubblico Python con MSAL è portabile, non richiede segreti né un backend, e consente pacchetti nativi tramite PyInstaller. Un archivio HTML statico funziona anche quando il tool non è più installato.

## Decisioni chiave

- Permessi delegated `User.Read` e `Chat.Read`.
- Dati Graph grezzi conservati separatamente dalla vista HTML sanificata.
- Paginazione completa, retry su throttling ed esportazione parziale con avvisi.
- Nessun token persistente e nessun invio di dati a servizi diversi da Microsoft Graph.
- Canali e download degli allegati rinviati dopo l'MVP.

## Questioni aperte

- Firma e notarizzazione dei binari dipendono dai certificati del distributore.
- Alcuni tenant richiedono approvazione amministrativa nonostante i permessi delegated.
