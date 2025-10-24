# 📊 ReportB24 — detailed Excel reports for Bitrix24

<div align="center">

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-261%20passed-green.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Release](https://img.shields.io/badge/release-v2.1.1-orange.svg)](https://github.com/bivlked/ReportB24/releases)
[![Security](https://img.shields.io/badge/security-checked-green.svg)](SECURITY.md)
[![Русский](https://img.shields.io/badge/язык-русский-blue.svg)](README.md)
[![English](https://img.shields.io/badge/language-english-red.svg)](README_EN.md)

**Professional reporting system for Bitrix24 Smart Invoices with secure Excel output**
**v2.1.1 highlights: `run_detailed_report.py` builds a dual-sheet report with automatic preflight checks**

[📌 Positioning](#-positioning-at-a-glance) • [🧰 What's inside](#-whats-inside) • [🚀 Quick Start (Windows)](#-quick-start-windows) • [🛠️ Preflight checks](#️-preflight-checks-and-typical-issues) • [⚡ Advanced scenarios](#-advanced-scenarios) • [📚 Docs](#-documentation) • [💬 Support](#-support) • [🏛️ Legacy](#-legacycompatibility)

---

</div>

## 📋 Table of Contents

- [📌 Positioning at a Glance](#-positioning-at-a-glance)
- [🧰 What's inside](#-whats-inside)
- [🚀 Quick Start (Windows)](#-quick-start-windows)
- [🛠️ Preflight checks and typical issues](#️-preflight-checks-and-typical-issues)
- [⚡ Advanced scenarios](#-advanced-scenarios)
- [📚 Documentation](#-documentation)
- [💬 Support](#-support)
- [🏛️ Legacy/compatibility](#-legacycompatibility)

---

<a id="-positioning-at-a-glance"></a>
## 📌 Positioning at a Glance

ReportB24 automates Smart Invoices exports from Bitrix24 and produces secure Excel deliverables for finance teams. The flagship `run_detailed_report.py` script runs configuration validation, connectivity diagnostics, and finally composes a dual-sheet workbook that combines a Brief sheet summary with a Detailed sheet product catalogue.

---

<a id="-whats-inside"></a>
## 🧰 What's inside

### 🔗 Integration & security
- Hardened Bitrix24 REST client with masked webhook URLs and rate limiting.
- Hybrid configuration system (`.env` + `config.ini`) with validation and automatic secret migration.
- 261 automated tests covering security, data processing, and Excel generation.

### 📊 Data processing
- INN validation, Russian date formatting, and VAT calculations tailored for local regulations.
- ProductRows API support to fetch invoice items with zebra striping for grouped display.
- Automatic VAT-based aggregates and consolidated statistics.

### 📈 Excel generation
- Dual-sheet layout: **Brief sheet** for invoice overview and **Detailed sheet** for an 8-column product ledger.
- Pixel-perfect templates with frozen headers, auto-width columns, and consistent zebra striping.
- Verbose logging (`logs/app.log`) and report storage under `reports/`.

---

<a id="-quick-start-windows"></a>
## 🚀 Quick Start (Windows)

> **Goal:** prepare a Windows environment and launch `py run_detailed_report.py` to generate the dual-sheet Excel report.

### 1. Verify tooling
```cmd
py --version
where git
```
Install [Python 3.8+](https://www.python.org/downloads/windows/) and [Git for Windows](https://git-scm.com/download/win) if either command fails.

### 2. Fetch the project
```cmd
mkdir C:\Projects\ReportB24
cd C:\Projects\ReportB24
git clone https://github.com/bivlked/ReportB24.git .
```

### 3. Create a virtual environment
```cmd
py -3 -m venv .venv
.\.venv\Scripts\activate
```
The command prompt will show the `(.venv)` prefix once the environment is active.

### 4. Install dependencies
```cmd
py -m pip install -r requirements.txt
```

### 5. Configure secrets and settings
```cmd
copy .env.example .env
copy config.ini.example config.ini
notepad .env
```
Set `BITRIX_WEBHOOK_URL=https://your-portal.bitrix24.ru/rest/USER_ID/WEBHOOK_CODE/`. Adjust the reporting period and output path in `config.ini` if needed.

### 6. Run the detailed report
```cmd
py run_detailed_report.py
```
You will see the primary checkpoints emitted by `run_detailed_report.py`:
- version banner describing the Brief/Detailed sheet structure;
- configuration discovery, highlighting `.env`/`config.ini` status;
- `✅ Configuration valid` once validation passes ([troubleshooting guide](docs/TROUBLESHOOTING.md#ошибки-в-конфигурации));
- `✅ Bitrix24 connection established` after the API probe ([connection checklist](docs/TROUBLESHOOTING.md#не-удаётся-подключиться-к-bitrix24));
- progress counters such as `✅ Invoices retrieved: N` and `✅ Product rows processed: M`;
- final message `🎉 Detailed report created successfully!` with the output path and log file hint.

### 7. Verify the output
```cmd
rem list generated reports
dir reports

rem confirm logging is enabled
dir logs
type logs\app.log | more
```
By default, the workbook name comes from `config.ini` (for example, `reports/bitrix24_report.xlsx`). Use `deactivate` when you finish working in the virtual environment.

---

<a id="️-preflight-checks-and-typical-issues"></a>
## 🛠️ Preflight checks and typical issues

| Situation | Quick diagnostic | Detailed guide |
| --- | --- | --- |
| Python missing or inaccessible | `py --version` | [Python on Windows](docs/TROUBLESHOOTING.md#python-не-установлен-или-не-доступен) |
| Bitrix24 webhook not reachable | `py -c "from src.core.app import AppFactory;\nwith AppFactory.create_app('config.ini') as app: print(app.test_api_connection())"` | [Bitrix24 connection issues](docs/TROUBLESHOOTING.md#не-удаётся-подключиться-к-bitrix24) |
| `reports` folder absent | `dir reports` | [File path & permissions](docs/TROUBLESHOOTING.md#папка-reports-не-создаётся-или-недоступна) |
| Configuration error | `py -c "from src.config.config_reader import SecureConfigReader; SecureConfigReader('config.ini').validate()"` | [.env and config.ini setup](docs/TROUBLESHOOTING.md#ошибки-в-конфигурации) |
| Virtual environment inactive | Look for the `(.venv)` prefix | [Virtual environment tips](docs/TROUBLESHOOTING.md#виртуальное-окружение-не-активируется) |

---

<a id="-advanced-scenarios"></a>
## ⚡ Advanced scenarios

- **Flexible filters and periods:** call `AppFactory.create_app()` and use `set_report_period` / `set_contractor_filter` for ad-hoc selections. Examples live in the [User Guide](docs/USER_GUIDE.md#работа-с-фильтрами-и-периодами).
- **Excel formatting tweaks:** leverage `ExcelSettings` to adjust header colors, zebra striping, and page orientation. See the [Technical Guide](docs/TECHNICAL_GUIDE.md#excel-генератор).
- **Automation & CI:** schedule `run_detailed_report.py` via Windows Task Scheduler, GitHub Actions, or Docker. Recommendations are in [docs/USER_GUIDE.md#автоматизация-и-планировщики](docs/USER_GUIDE.md#автоматизация-и-планировщики).
- **Extending Bitrix24 integration:** add endpoints and use `Bitrix24Client` with retry and throttling helpers. Refer to [docs/TECHNICAL_GUIDE.md#интеграция-с-bitrix24](docs/TECHNICAL_GUIDE.md#интеграция-с-bitrix24).

---

<a id="-documentation"></a>
## 📚 Documentation

- [📘 User Guide](docs/USER_GUIDE.md) — walkthroughs, usage scenarios, and FAQ-style answers.
- [📗 Technical Guide](docs/TECHNICAL_GUIDE.md) — architecture overview, core modules, and extension points.
- [🔐 Security setup](docs/SECURITY_SETUP.md) — secret management and production hardening tips.
- [🗃️ Archive](docs/archive/enhancements/2025-07/remaining-fixes-and-docs-2025-07-03.md) — historical notes and refinements.

---

<a id="-support"></a>
## 💬 Support

- Open an issue on [GitHub](https://github.com/bivlked/ReportB24/issues) with logs and reproduction steps.
- Consult [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) first — most common questions are documented there.
- For security-sensitive matters, follow the process in [SECURITY.md](SECURITY.md).

---

<a id="-legacycompatibility"></a>
## 🏛️ Legacy/compatibility

The historical `run_report.py` entry point remains for single-sheet exports without product details. For new deployments we recommend `run_detailed_report.py`: it validates configuration, checks the Bitrix24 API, and produces the dual-sheet workbook combining the **Brief sheet** and the **Detailed sheet** with zebra striping.

