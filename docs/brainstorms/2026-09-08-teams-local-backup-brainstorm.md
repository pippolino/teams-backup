---
date: 2026-09-08
topic: teams-local-backup
---

# Local backup of Teams chats

## What we are building

A command-line application distributed as a single executable. Each user signs in to Microsoft 365 directly through the device code flow and saves their one-on-one, group, and meeting chats onto their own computer.

## Why this approach

A Python public client with MSAL is portable, needs no secrets and no backend, and allows native packages through PyInstaller. A static HTML archive keeps working even once the tool is no longer installed.

## Key decisions

- Delegated `User.Read` and `Chat.Read` permissions.
- Raw Graph data kept separate from the sanitised HTML view.
- Full pagination, retry on throttling, and partial export with warnings.
- No persistent tokens and no data sent to any service other than Microsoft Graph.
- Channels and attachment downloads deferred until after the MVP.

## Open questions

- Signing and notarising the binaries depends on the distributor's certificates.
- Some tenants require administrative approval despite the delegated permissions.
