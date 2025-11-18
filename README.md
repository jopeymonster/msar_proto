# Microsoft Ads Reporter (MSAR)

MSAR is a command-line reporting utility for **Microsoft Ads** (Bing Ads) built in Python.
It authenticates via OAuth, lists accessible advertising accounts, runs reporting jobs,
merges multi-account output, and saves a cleaned CSV directly to the user’s home directory.

This tool is designed to streamline daily/weekly reporting workflows and reduce reliance on the Microsoft Ads UI.

---

## ⚡ Features (v0.1)

### Core
- OAuth authentication (Desktop/Mobile flow)
- Detects all Microsoft Ads accounts available to the authenticated user
- Runs **Campaign Performance** reports with custom date range selection
- Supports **single-account** or **multi-account (all)** extraction
- Merges all account results into a single CSV file
- Cleans footer/blank rows from Microsoft’s RAW export

### Output
- Saves cleaned CSV → `~/msar_campaign_performance_<timestamp>.csv`
- RAW files stored temporarily in `./output` and deleted after processing
- User can choose:
  - Save CSV
  - Display table
  - Both
  - Auto view (`--auto`)

### Dimensions & Toggles

- **MAC Extraction (`--mac`)**  
  Automatically derive Marketing Attribution Codes from `CampaignName`  
  (takes the substring after the final colon).

- **Campaign Type Toggle (`--ctype`)**  
  Choose whether to include the `CampaignType` column.

Both options are interactive by default unless overridden via CLI.

---

## 🧭 Usage

### OAuth Configuration
Your config (`auth_info.json`) should look like:

```json
{
    "developer_token": "YOUR_TOKEN",
    "environment": "production",
    "client_id": "xxxx-xxxx-xxxx",
    "client_state": "SOME_STATE",
    "redirect_uri": "https://login.microsoftonline.com/common/oauth2/nativeclient",
    "refresh_token": ""
}
````

---

## 🚀 Running a Report

### Basic example:


```bash
python main.py --config auth_info.json
```

### Run for a specific account:

```bash
python main.py --config auth_info.json --account 2809172
```

### Run for ALL accounts:

```bash
python main.py --config auth_info.json --account all
```

### Include/exclude MAC or CampaignType:

```bash
python main.py --config auth_info.json --mac exclude --ctype include
```

---

## 📁 Output Files

### RAW merged export (temporary)

```
./output/msar_campaign_performance_<timestamp>_RAW.csv
```

### Clean final export (saved to user’s HOME)

```
~/msar_campaign_performance_<timestamp>.csv
```

---

## 🧩 Requirements

See `requirements.txt` below.

---

## License

MIT License — see [LICENSE](LICENSE).

## Contributors

* **Joe Thompson** (@jopeymonster)

---

## Legal

The developers of this application are not responsible for any actions
performed using this tool. Your privacy is respected—see our
[Privacy Policy](https://jopeymonster.github.io/privacy/).