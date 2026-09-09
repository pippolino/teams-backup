# Teams Local Backup

Teams Local Backup crea un archivio locale delle chat Microsoft Teams accessibili all'utente che esegue il programma. L'accesso avviene direttamente su Microsoft 365 con permessi delegated: non esiste un backend centrale, il programma non contiene un client secret e non conserva token su disco.

L'MVP include:

- chat individuali (`oneOnOne`);
- chat di gruppo (`group`);
- chat delle riunioni (`meeting`);
- archivio HTML offline con ricerca e filtri;
- JSON Graph originale, pagina per pagina;
- retry automatico in caso di throttling;
- build in un singolo eseguibile per Windows e macOS.

I canali Teams e il download dei file allegati non fanno parte dell'MVP.

## 1. Configurazione Entra ID

Serve una App Registration, creata una volta dall'amministratore o da chi ha il permesso di registrare applicazioni.

1. Apri **Microsoft Entra admin center → Identity → Applications → App registrations → New registration**.
2. Assegna un nome, per esempio `Teams Local Backup`.
3. Se il tool è per un solo tenant, scegli **Accounts in this organizational directory only**. Per più tenant aziendali scegli **Accounts in any organizational directory**.
4. Dopo la creazione, copia **Application (client) ID**. Per una registrazione single-tenant copia anche **Directory (tenant) ID**.
5. Apri **Authentication → Advanced settings** e imposta **Allow public client flows** su **Yes**.
6. Apri **API permissions → Add a permission → Microsoft Graph → Delegated permissions** e aggiungi:
   - `User.Read`
   - `Chat.Read`
7. Non creare alcun client secret. Un'app desktop pubblica non può custodirlo in modo sicuro.

`Chat.Read` è il permesso minimo documentato da Microsoft per leggere i messaggi di una chat con identità delegated. Il tenant può comunque bloccare il consenso degli utenti o richiedere approvazione amministrativa tramite le proprie policy.

Riferimenti Microsoft: [elenco delle chat](https://learn.microsoft.com/en-us/graph/api/chat-list?view=graph-rest-1.0), [messaggi di una chat](https://learn.microsoft.com/en-us/graph/api/chat-list-messages?view=graph-rest-1.0), [device-code flow](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-device-code).

## 2. Configurazione del tool

Copia `config.example.json` come `config.json`, accanto all'eseguibile:

```json
{
  "client_id": "APPLICATION-CLIENT-ID",
  "tenant": "DIRECTORY-TENANT-ID"
}
```

Per un'app multi-tenant puoi usare `"tenant": "organizations"`. I valori possono essere passati anche con `--client-id` e `--tenant`, oppure tramite `TEAMS_BACKUP_CLIENT_ID` e `TEAMS_BACKUP_TENANT`.

Il client ID non è un segreto. Non inserire password o client secret nel file.

## 3. Esecuzione

Windows PowerShell:

```powershell
.\teams-backup.exe --output "$HOME\Documents"
```

macOS:

```bash
./teams-backup --output "$HOME/Documents"
```

Il programma mostra un codice, apre la pagina Microsoft di accesso e attende login, MFA ed eventuale consenso. Al termine apre `index.html` dal backup appena creato. Usa `--no-browser` per non aprire automaticamente la pagina di login e `--no-open` per non aprire l'archivio.

La cartella risultante ha questa forma:

```text
TeamsBackup-2026-09-08_14-30-00/
├── index.html
├── archive.css
├── archive.js
├── archive-data.js
├── export-info.json
└── json/
    ├── archive.json
    └── original-data/
        ├── me.json
        ├── chats-pages.json
        └── chat-0001/
            ├── chat.json
            ├── members-pages.json
            └── messages-pages.json
```

`original-data` conserva le risposte Graph grezze, comprese le informazioni di paginazione. `archive.json` riunisce i dati per un uso più semplice. L'HTML usa una copia sanificata dei corpi dei messaggi per evitare l'esecuzione di markup pericoloso.

## 4. Sviluppo e test

Richiede Python 3.10 o successivo:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
python3 -m pytest
teams-backup --config config.json --no-open
```

Su Windows, attiva l'ambiente con `.venv\Scripts\Activate.ps1` e usa `py` al posto di `python3`.

## 5. Build Windows e macOS

PyInstaller non esegue cross-compilation: ogni binario va creato sul sistema operativo e sull'architettura di destinazione.

macOS:

```bash
chmod +x packaging/build-macos.sh
./packaging/build-macos.sh
```

Windows PowerShell:

```powershell
.\packaging\build-windows.ps1
```

Su Windows vengono creati sia `dist/teams-backup.exe` sia il pacchetto distribuibile `release/teams-backup-windows-x64.zip`. Lo ZIP contiene:

```text
teams-backup-windows-x64.zip
├── teams-backup.exe
├── config.example.json
└── README.md
```

Il destinatario deve estrarre lo ZIP, rinominare `config.example.json` in `config.json`, inserire il client ID Entra e avviare `teams-backup.exe` da PowerShell.

Su macOS il risultato è in `dist/teams-backup`. Il workflow `.github/workflows/build.yml` produce automaticamente artefatti completi per macOS Apple Silicon, macOS Intel e Windows x64 quando viene avviato manualmente o viene pubblicato un tag `v*`. Gli artefatti scaricati da GitHub Actions includono anche configurazione di esempio e README.

I binari non firmati possono mostrare avvisi di Gatekeeper o SmartScreen. Per una distribuzione aziendale è opportuno firmare il binario Windows e firmare/notarizzare quello macOS con i certificati dell'organizzazione.

## Privacy e sicurezza

- Il token OAuth resta soltanto in memoria per la durata dell'esecuzione.
- I dati vengono richiesti a `graph.microsoft.com` e scritti nella cartella scelta.
- Il tool non contiene telemetria e non invia backup a servizi terzi.
- I link “Apri in Teams” nell'archivio contattano Microsoft solo quando vengono selezionati.
- La cartella contiene dati personali: proteggila con cifratura del disco e permessi adeguati.

## Limiti dell'MVP

- Non esporta messaggi dei canali standard, privati o condivisi.
- Non scarica allegati: conserva i riferimenti presenti nei messaggi e nei JSON, ma molti link richiedono ancora autorizzazione e possono scadere.
- Non è uno strumento di compliance e non sostituisce Purview/eDiscovery o le policy di conservazione aziendali.
- Esporta solo ciò che Graph rende accessibile all'utente al momento del backup; messaggi eliminati, scaduti per retention o non più accessibili non possono essere recuperati.
- Un export molto grande può richiedere tempo ed essere soggetto al throttling di Graph. Il tool segue `@odata.nextLink` e rispetta `Retry-After`.
- Le chat federate possono dipendere dal tenant che le ospita e dalle sue policy.
- Se una chat fallisce, il backup prosegue e registra l'avviso in `export-info.json`.
