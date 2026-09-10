# Teams Local Backup

Teams Local Backup creates a local archive of the Microsoft Teams chats that are accessible to the user running the program. It connects directly to Microsoft 365 with delegated permissions: there is no central backend, the program contains no client secret, and it never stores tokens on disk.

The MVP covers:

- one-on-one chats (`oneOnOne`);
- group chats (`group`);
- meeting chats (`meeting`);
- an offline HTML archive with search and filters;
- the original Graph JSON, page by page;
- automatic retry on throttling;
- a single-executable build for Windows and macOS.

Teams channels and attachment downloads are out of scope for the MVP.

## 1. Entra ID setup

An App Registration is required. It is created once by an administrator, or by anyone holding the permission to register applications.

1. Open **Microsoft Entra admin center → Identity → Applications → App registrations → New registration**.
2. Give it a name, for example `Teams Local Backup`.
3. If the tool targets a single tenant, choose **Accounts in this organizational directory only**. For multiple corporate tenants, choose **Accounts in any organizational directory**.
4. After creation, copy the **Application (client) ID**. For a single-tenant registration, also copy the **Directory (tenant) ID**.
5. Open **Authentication → Advanced settings** and set **Allow public client flows** to **Yes**.
6. Open **API permissions → Add a permission → Microsoft Graph → Delegated permissions** and add:
   - `User.Read`
   - `Chat.Read`
7. Do not create a client secret. A public desktop app cannot keep one safely.

`Chat.Read` is the minimum permission documented by Microsoft for reading the messages of a chat under a delegated identity. A tenant may still block user consent or require administrative approval through its own policies.

Microsoft references: [list chats](https://learn.microsoft.com/en-us/graph/api/chat-list?view=graph-rest-1.0), [list chat messages](https://learn.microsoft.com/en-us/graph/api/chat-list-messages?view=graph-rest-1.0), [device code flow](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-device-code).

## 2. Tool configuration

Copy `config.example.json` to `config.json`, next to the executable:

```json
{
  "client_id": "APPLICATION-CLIENT-ID",
  "tenant": "DIRECTORY-TENANT-ID"
}
```

For a multi-tenant app you can use `"tenant": "organizations"`. Both values can also be passed with `--client-id` and `--tenant`, or through `TEAMS_BACKUP_CLIENT_ID` and `TEAMS_BACKUP_TENANT`.

The client ID is not a secret. Do not put passwords or client secrets in this file.

## 3. Running the tool

Windows PowerShell:

```powershell
.\teams-backup.exe --output "$HOME\Documents"
```

macOS:

```bash
bash ./start-mac.command --output "$HOME/Documents"
```

The macOS launcher automatically removes the quarantine attribute from the binary and makes it executable. This step has to happen on the Mac after downloading, because it is macOS itself that adds quarantine to the downloaded file.

The program displays a code, opens the Microsoft sign-in page, and waits for login, MFA, and consent where required. When it finishes, it opens `index.html` from the backup it has just created. Use `--no-browser` to skip opening the sign-in page automatically, and `--no-open` to skip opening the archive.

### First run on macOS

1. Download the `teams-backup-macos-arm64` artifact from the GitHub Actions pipeline.
2. Extract the ZIP into a folder, for example `Downloads/teams-backup-macos-arm64`.
3. Rename `config.example.json` to `config.json` and fill in the `client_id` and `tenant` of the Entra App Registration.
4. Open Terminal and move into the extracted folder:

   ```bash
   cd "$HOME/Downloads/teams-backup-macos-arm64"
   ```

5. Start the test run:

   ```bash
   bash ./start-mac.command --output "$HOME/Documents" --no-open
   ```

6. Complete the Microsoft sign-in on the page opened by the browser.
7. Check that a `TeamsBackup-YYYY-MM-DD_HH-MM-SS` folder has appeared in `Documents`, containing `index.html`, `export-info.json`, and the `json` folder.
8. Open `index.html`: the chats, the search box, and the One-on-one, Groups, and Meetings filters should all be there.

If the run ends with `Backup complete`, then sign-in, Microsoft Graph, and local writing all work. Any chats that could not be exported are reported as warnings in `export-info.json`.

The resulting folder has this shape:

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

`original-data` keeps the raw Graph responses, pagination information included. `archive.json` merges the data into a form that is easier to consume. The HTML uses a sanitised copy of the message bodies, so that dangerous markup is never executed.

## 4. Development and tests

Requires Python 3.10 or later:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
python3 -m pytest
teams-backup --config config.json --no-open
```

On Windows, activate the environment with `.venv\Scripts\Activate.ps1` and use `py` instead of `python3`.

## 5. Building for Windows and macOS

PyInstaller does not cross-compile: each binary has to be built on the target operating system and architecture.

macOS:

```bash
chmod +x packaging/build-macos.sh
./packaging/build-macos.sh
```

Windows PowerShell:

```powershell
.\packaging\build-windows.ps1
```

On Windows the build produces the application folder `dist/teams-backup/` and the distributable package `release/teams-backup-windows-x64.zip`. The ZIP contains:

```text
teams-backup-windows-x64.zip
├── teams-backup.exe
├── _internal/            <- interpreter and dependencies
├── config.example.json
└── README.md
```

The recipient has to extract the ZIP, rename `config.example.json` to `config.json`, fill in the Entra client ID, and run `teams-backup.exe` from PowerShell. The `_internal` folder has to stay next to the executable, and `config.json` has to sit in the same folder as `teams-backup.exe`.

On macOS the result is `dist/teams-backup`, and the build also adds `dist/start-mac.command`. The `.github/workflows/build.yml` workflow automatically produces complete artifacts for macOS Apple Silicon and Windows x64, either when triggered manually or when a `v*` tag is published. Artifacts downloaded from GitHub Actions also include the example configuration and the README.

Unsigned binaries may trigger Gatekeeper, SmartScreen, or antivirus warnings. See section 6.

## 6. Code signing and antivirus

Windows antivirus engines flag unsigned PyInstaller builds through generic heuristics; Trend Micro, for instance, reports them as `Troj.WIN32.TRX.*`. Two properties of the build drive this, and both are addressed here:

- **No self-extraction.** The Windows build is onedir, so the interpreter and the dependencies sit next to the executable. A onefile build unpacks itself into `%TEMP%` and executes code from there, which is indistinguishable from dropper behaviour and is scored as such.
- **No packing, and a real version resource.** UPX compression is off, and `packaging/windows-version-info.txt` gives the executable proper publisher metadata. An anonymous, packed PE starts from the worst possible heuristic score.

### Signing the build

`packaging/build-windows.ps1` calls `packaging/sign-windows.ps1`, which signs the executable together with every bundled DLL and PYD. Signing the dependencies matters as much as signing the entry point: an on-access scanner inspects each module as it is loaded, so an unsigned dependency undoes most of the benefit.

The script is a no-op when nothing is configured, so unsigned local builds keep working. Set one of these three groups of environment variables to enable it:

| Provider | Variables |
|---|---|
| Certificate in the Windows store, by thumbprint | `TEAMS_BACKUP_SIGN_SHA1` |
| Certificate in the Windows store, by subject name | `TEAMS_BACKUP_SIGN_SUBJECT` |
| Azure Artifact Signing (formerly Trusted Signing) | `TEAMS_BACKUP_SIGN_DLIB`, `TEAMS_BACKUP_SIGN_DMDF` |

`TEAMS_BACKUP_SIGN_TIMESTAMP_URL` overrides the RFC3161 timestamp server. A timestamp is not optional in practice: without one, every signature stops validating the day the certificate expires.

In GitHub Actions the values come from the `SIGN_SHA1` and `SIGN_SUBJECT` repository secrets. A certificate whose private key lives on a hardware token cannot be used from a hosted runner; signing then has to happen on a self-hosted runner or through a cloud signing service.

### Obtaining a certificate

| Option | Cost | Notes |
|---|---|---|
| [SignPath Foundation](https://signpath.org/) | free | Requires an OSI-approved licence and a verifiable project reputation. The publisher shown to users is SignPath Foundation, not the project. |
| [OSSign](https://ossign.org/) | free | Younger initiative, and the operating legal entity is not publicly disclosed. Worth asking who controls the key and what appears in the certificate subject. |
| [Certum Open Source](https://shop.certum.eu/code-signing.html) | ~25-50 EUR/year | Issued to an individual, subject reads `Open Source Developer`, and the software must be non-commercial. No popularity requirement. |
| [Azure Artifact Signing](https://azure.microsoft.com/en-gb/pricing/details/trusted-signing/) | ~10 USD/month | Publisher is the organisation. Individual sign-up is limited to the USA and Canada; organisations are covered in the EU and UK. |

### When a signature is not enough

A valid signature substantially lowers the heuristic score but does not guarantee a clean verdict, and reputation-based systems such as SmartScreen accumulate trust per publisher over successive releases. Two things help in the meantime:

- Report the false positive to the vendor. Note that any rebuild changes the file hash and may need resubmitting.
- Inside an organisation, ask IT to allow the application by hash or by certificate on the antivirus console. For an internally distributed tool this is usually both faster and more reliable than buying a certificate.

## Privacy and security

- The OAuth token stays in memory only, for the duration of the run.
- Data is requested from `graph.microsoft.com` and written to the chosen folder.
- The tool contains no telemetry and sends backups to no third-party service.
- The "Open in Teams" links in the archive contact Microsoft only when they are clicked.
- The output folder holds personal data: protect it with disk encryption and appropriate permissions.

## MVP limitations

- It does not export messages from standard, private, or shared channels.
- It does not download attachments: it keeps the references present in the messages and in the JSON, but many of those links still require authorisation and can expire.
- It is not a compliance tool and does not replace Purview/eDiscovery or an organisation's retention policies.
- It exports only what Graph makes accessible to the user at backup time; messages that were deleted, expired under retention, or are no longer accessible cannot be recovered.
- A very large export can take a while and is subject to Graph throttling. The tool follows `@odata.nextLink` and honours `Retry-After`.
- Federated chats may depend on the tenant hosting them and on that tenant's policies.
- If one chat fails, the backup continues and records the warning in `export-info.json`.
