# WinTriage

> **Windows live forensic triage tool for rapid incident response and tamper detection.**

WinTriage collects and cross-references forensic artifacts from a live Windows system to surface signs of anti-forensics, suspicious execution, and post-compromise activity — in seconds, with no manual digging.

---

## What it does

WinTriage runs a coordinated sweep of Windows forensic artifacts and flags anomalies automatically:

| Artifact | What it checks |
|---|---|
| **BAM registry** | Unsigned or deleted executables run after boot |
| **Prefetch** | Duplicate hashes, read-only `.pf` files, no files present |
| **USN Journal** | Deletion events via `fsutil`, NTFS event ID 501, and file time |
| **MFT (`$MFT`)** | Unsigned EXEs/DLLs, Python/batch/JAR execution, deleted file traces |
| **Event logs** | Security log cleared (event 1102) |
| **PCA (Program Compatibility Assistant)** | Unsigned or deleted executables from `PcaAppLaunchDic.txt` / `PcaGeneralDb` |
| **DPS memory dump** | Unsigned executable paths extracted via strings |
| **Services & processes** | Restarts since boot (BAM, DPS, EventLog, DiagTrack, etc.) |
| **Recycle Bin** | Modification within last 24 hours |
| **Recent files** | Unsigned LNK targets, recently accessed Python scripts |
| **Unicode artifacts** | Unicode filenames in Prefetch, unicode value names in execution registry keys |
| **USB devices** | VID/PID lookup via devicehunt.com |
| **PC reset** | OS install date within 48 hours |

---

## Requirements

- Windows 10 / 11 (64-bit)
- Python 3.10+
- **Administrator privileges** (required for BAM, MFT, memory dumps, and event log access)

### Python dependencies

```
pip install requests beautifulsoup4 colorama pywin32 pandas psutil
```

### Auto-downloaded tools (on first run)

WinTriage downloads the following to `%TEMP%\Sysinternals` automatically:

- [PECmd](https://ericzimmerman.github.io/) — Prefetch parser
- [MFTECmd](https://ericzimmerman.github.io/) — MFT parser
- [ProcDump](https://learn.microsoft.com/en-us/sysinternals/downloads/procdump) — Memory dumper
- [Strings](https://learn.microsoft.com/en-us/sysinternals/downloads/strings) — String extractor
- `bd.exe` — BAM deletion checker

---

## Usage

Run from an elevated (Administrator) command prompt:

```cmd
python wintriage.py
```

Output is printed directly to the console. Red text indicates a high-confidence anomaly. Yellow indicates a warning worth investigating. No output for a given check means nothing suspicious was found.

---

## Output examples

```
Sysmain restarted 14 minutes ago (10:32:11 14-03-2025)
USN Journal Deleted 2 hours, 4 minutes ago (08:43:02 14-03-2025)
⚠️ No .pf files found.

Executed Unsigned (After Boot Time):
Last Execution Time   Path
2025-03-14 10:41:02   C:\Users\User\AppData\Local\Temp\loader.exe

Deleted BAM Entries:
C:\Users\User\Downloads\tool.exe

Unsigned Executables (MFT):
C:\ProgramData\Microsoft\temp\svc.exe

Recycle Bin Modified 3 hours, 12 minutes ago (07:34:55 14-03-2025)
```

---

## Architecture

```
wintriage.py
├── setup_sysinternals_tools()    # Download/extract tools on first run
├── System baseline
│   ├── get_system_uptime()
│   ├── get_install_date()
│   └── get_file_time_from_fsutil()
├── Anti-forensics detection
│   ├── check_usn_journal_deletions()
│   └── event_logs_cleared()
├── Execution artifacts
│   ├── bam_detection()           # BAM registry (PowerShell)
│   ├── deleted_bam_check()       # bd.exe cross-reference
│   ├── parse_prefetch_files()    # PECmd + duplicate hash detection
│   ├── parse_pca()               # PCA AppLaunch + GeneralDb
│   └── mft()                     # MFTECmd async signature sweep
├── Memory analysis
│   └── dump_services_and_processes_and_extract_strings()
├── Filesystem & UI artifacts
│   ├── check_prefetch_files_for_read_only()
│   ├── unicode_search()
│   ├── check_recent_files()
│   └── get_latest_modification_time() → Recycle Bin
├── Service/process health
│   ├── check_service_status()
│   └── check_process_status()
└── External
    ├── get_usb_devices()         # devicehunt.com VID/PID lookup
    └── regex_dps()              # Unsigned paths from DPS dump
```

---

## Limitations

- **Live systems only** — WinTriage does not support offline image analysis
- **Windows only** — no macOS or Linux support
- MFT parsing requires a non-locked `C:\$MFT`; results may vary on heavily active systems
- USB lookups require internet access
- Memory dumps may be blocked by endpoint security products

---

## Disclaimer

WinTriage is intended for use by incident responders, forensic analysts, and system administrators on systems they are authorized to examine. Do not use this tool on systems without explicit permission. The authors accept no liability for misuse.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
