# PyWinLogView

PyWinLogView is a lightweight Python-based command-line tool for reading, filtering, and exporting Windows Event Viewer logs.

---

## 🚀 Features

* 📄 Read Windows Event Logs (System, Application, Security)
* 🔍 Filter logs by level, source, or keyword
* 📤 Export logs to structured formats
* ⚡ Simple and modular CLI interface
* 🧪 Demo mode support on non-Windows systems

---

## 🛠️ Installation (Optional)

> Not required to run locally, but useful for CLI usage

```bash
pip install -e .
```

---

## ▶️ Usage

Run directly:

```bash
python main.py
```

Or (recommended):

```bash
python -m winlogview
```

Example:

```bash
python main.py --log System --limit 50
```

---

## 📂 Project Structure

```
PyWinLogView/
│
├── winlogview/
│   ├── __init__.py
│   ├── cli.py
│   ├── reader.py
│   ├── filter.py
│   ├── exporter.py
│   └── models.py
│
├── main.py
├── basic_usage.py
├── test_winlogview.py
├── pyproject.toml
├── setup.py
└── requirements.txt
```

---

## ⚙️ Requirements

* Python 3.8+
* (Optional for Windows) `pywin32`

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🖥️ Platform Support

| Platform    | Support                  |
| ----------- | ------------------------ |
| Windows     | ✅ Full (real Event Logs) |
| Linux/macOS | ⚠️ Demo mode only        |

---

## 📚 Example Output

```
Reading logs from System...
Retrieved 50 records.

[INFO] Service started successfully
[ERROR] Failed to load driver
```

---

## 🎯 Use Cases

* System log monitoring
* Debugging Windows issues
* Learning Python CLI development
* Basic security / event analysis

---

## ⚠️ Notes

* Real Windows Event Logs require running on Windows
* Linux/macOS will use mock/demo data
* CLI options can be extended easily

---

## 🤝 Contributing

Contributions are welcome! Feel free to fork and improve.

---

## 📄 License

This project is open-source and available under the MIT License.

---

## 👨‍💻 Author

**Md. Munkasir Haque**  
Aspiring Cybersecurity Enthusiast | Python Developer
