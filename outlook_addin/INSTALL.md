# Outlook Plugin Installation Guide

## Requirements

- MS Outlook (any version that supports Ribbon)
- Python 3.8+ installed and available from the command line
- pywin32 installed (`pip install pywin32`)

## Installation

### Step 1: Prepare the Files

1. Copy all files from the `outlook_addin/` folder into the Outlook macros folder:
   - Typically: `%APPDATA%\Microsoft\Outlook\`
   - Or: `C:\Users\<YourName>\AppData\Roaming\Microsoft\Outlook\`

2. Files to copy:
   - `customUI.xml`
   - `RibbonHandler.bas`
   - `ThisAddIn.cls`

### Step 2: Configure Paths

1. Open `RibbonHandler.bas` in a text editor
2. Find the line:
   ```vba
   Private Const PYTHON_SCRIPT_PATH As String = "C:\path\to\gold-outreach\outlook_launcher.py"
   ```
3. Replace the path with the actual path to `outlook_launcher.py` in your project
4. If Python is not in PATH, also update:
   ```vba
   pythonPath = "python"
   ```
   to the full path, for example:
   ```vba
   pythonPath = "C:\Python312\python.exe"
   ```

### Step 3: Import Macros into Outlook

1. Open Outlook
2. Press `Alt + F11` to open the VBA editor
3. From the menu, select: `File → Import File...`
4. Import the files:
   - `ThisAddIn.cls`
   - `RibbonHandler.bas`
5. Save the project (Ctrl+S)

### Step 4: Configure Security Settings

1. In Outlook: `File → Options → Trust Center → Trust Center Settings`
2. Go to the "Macro Settings" tab
3. Select "Notify me about all macros" or "Enable all macros" (not recommended for security)

### Step 5: Configure the Ribbon

1. In the VBA editor, create a new module if needed
2. Ensure that `customUI.xml` is in the correct folder
3. Restart Outlook

### Step 6: Verify

1. Restart Outlook
2. A new "Gold Outreach" tab should appear in the Ribbon panel
3. Click the buttons to verify that everything works

## Troubleshooting

### The tab does not appear

- Ensure that `customUI.xml` is in the correct folder
- Verify that macros are enabled
- Check the Outlook logs for errors

### The Python script does not launch

- Check the path to Python in `RibbonHandler.bas`
- Ensure that Python is accessible from the command line
- Check the path to `outlook_launcher.py`

### Errors during execution

- Ensure all dependencies are installed (`pip install -r requirements.txt`)
- Verify that Outlook is running and accessible
- Check the logs in the application's "Logs" dialog window

## Alternative Method (without VBA)

If you prefer not to use VBA, you can launch the application directly:

```bash
python outlook_launcher.py create_campaign
python outlook_launcher.py manage_campaigns
```

This lets you use the application as a standalone program rather than as an Outlook plugin.
