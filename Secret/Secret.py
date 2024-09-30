import subprocess
import datetime
import re
import os
from tkinter import LAST
import requests
import zipfile
import stat
import glob
import time
import win32com.client
import threading
import pythoncom
from queue import Queue
from dateutil import parser
from bs4 import BeautifulSoup
import fade
import colorama
from colorama import Fore
import winreg
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

SYSINTERNALS_TEMP_DIR = os.path.join(os.getenv('TEMP'), 'Sysinternals')
PE_CMD_URL = 'https://download.ericzimmermanstools.com/net6/PECmd.zip'
PROCDUMP_URL = 'https://download.sysinternals.com/files/Procdump.zip'
STRINGS_URL = 'https://download.sysinternals.com/files/Strings.zip'
BD_URL = 'https://cdn.discordapp.com/attachments/1268096855431053383/1288146554787729438/bd.zip?ex=66fb5fb7&is=66fa0e37&hm=4cd84eedb52a2e6d0445ecfbf2c84358ea68b46316b73fd174018f706348f3f5'
BD_PATH = os.path.join(SYSINTERNALS_TEMP_DIR, 'bd.zip')
BD_EXTRACT_TO = os.path.join(SYSINTERNALS_TEMP_DIR, 'bd')
PROCDUMP_PATH = os.path.join(SYSINTERNALS_TEMP_DIR, 'procdump', 'procdump.exe')
STRINGS_PATH = os.path.join(SYSINTERNALS_TEMP_DIR, 'strings', 'strings.exe')
PE_CMD_PATH = os.path.join(SYSINTERNALS_TEMP_DIR, 'PECmd', 'PECmd.exe')



services = [
    "Sysmain",
    "Pcasvc",
    "DPS",
    "Diagtrack",
    "DNSCache",
    "Dusmsvc",
    "Eventlog",
    "Appinfo",
    "BAM"
]

processes = [
    "explorer",
    "SearchIndexer"
]

def download_file(url, dest_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(dest_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
        
    except Exception as e:
        return None

def unzip_file(zip_path, extract_to):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        
    except Exception as e:
        return None

def setup_sysinternals_tools():
    if not os.path.exists(SYSINTERNALS_TEMP_DIR):
        os.makedirs(SYSINTERNALS_TEMP_DIR)

    procdump_zip = os.path.join(SYSINTERNALS_TEMP_DIR, 'Procdump.zip')
    strings_zip = os.path.join(SYSINTERNALS_TEMP_DIR, 'Strings.zip')
    pe_cmd_zip = os.path.join(SYSINTERNALS_TEMP_DIR, 'PECmd.zip')

    if not os.path.isfile(PROCDUMP_PATH) or not os.path.isfile(STRINGS_PATH) or not os.path.isfile(PE_CMD_PATH):
        download_file(PROCDUMP_URL, procdump_zip)
        download_file(STRINGS_URL, strings_zip)
        download_file(PE_CMD_URL, pe_cmd_zip)

        unzip_file(procdump_zip, os.path.join(SYSINTERNALS_TEMP_DIR, 'procdump'))
        unzip_file(strings_zip, os.path.join(SYSINTERNALS_TEMP_DIR, 'strings'))
        unzip_file(pe_cmd_zip, os.path.join(SYSINTERNALS_TEMP_DIR, 'PECmd'))

    if not os.path.exists(BD_EXTRACT_TO):
        download_file(BD_URL, BD_PATH)
        unzip_file(BD_PATH, BD_EXTRACT_TO)

def check_service_status(service_name):
    try:
        result = subprocess.run(["sc", "query", service_name], capture_output=True, text=True)
        output = result.stdout
        return "RUNNING" in output
    except Exception as e:
        print(f"Error checking status for {service_name}: {e}")
        return False

def check_process_status(process_name):
    try:
        result = subprocess.run(["tasklist"], capture_output=True, text=True)
        output = result.stdout
        return process_name in output
    except Exception as e:
        print(f"Error checking status for {process_name}: {e}")
        return False

def get_system_uptime():
    try:
        result = subprocess.run(["systeminfo"], capture_output=True, text=True)
        output = result.stdout
        match = re.search(r'System Boot Time:\s*(.+)', output)
        if match:
            boot_time_str = match.group(1).strip()
            boot_time = parser.parse(boot_time_str)
            return boot_time
        else:
            return None
    except Exception as e:
        print(f"Error retrieving system uptime: {e}")
        return None


def get_service_process_start_time(service_name):
    try:
        result = subprocess.run(["wmic", "service", "where", f"name='{service_name}'", "get", "ProcessId"], capture_output=True, text=True)
        output = result.stdout
        match = re.search(r'(\d+)', output)
        if match:
            pid = int(match.group(1))
            result = subprocess.run(["wmic", "process", f"where", f"ProcessId={pid}", "get", "CreationDate"], capture_output=True, text=True)
            output = result.stdout
            match = re.search(r'(\d{14})', output)
            if match:
                creation_date_str = match.group(1)
                creation_date = datetime.datetime.strptime(creation_date_str, '%Y%m%d%H%M%S')
                return creation_date
            else:
                return None
        else:
            return None
    except Exception as e:
        print(f"Error retrieving process start time for {service_name}: {e}")
        return None

def get_process_start_time(process_name):
    try:
        result = subprocess.run(["wmic", "process", "where", f"name='{process_name}.exe'", "get", "CreationDate"], capture_output=True, text=True)
        output = result.stdout
        match = re.search(r'(\d{14})', output)
        if match:
            creation_date_str = match.group(1)
            creation_date = datetime.datetime.strptime(creation_date_str, '%Y%m%d%H%M%S')
            return creation_date
        else:
            return None
    except Exception as e:
        print(f"Error retrieving start time for process {process_name}: {e}")
        return None

def format_time_elapsed(start_time):
    now = datetime.datetime.now()
    elapsed = now - start_time

    hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours} hours")
    if minutes > 0:
        parts.append(f"{minutes} minutes")
    if seconds > 0 or not parts:
        parts.append(f"{seconds} seconds")

    time_string = ', '.join(parts)
    return f"{time_string} ago ({start_time.strftime('%H:%M:%S %d-%m-%Y')})"

def is_significantly_different(start_time, boot_time, threshold_minutes=1):
    return (start_time - boot_time).total_seconds() > threshold_minutes * 60

def log_service_status(service_name, status, start_time=None):
    if status == "Not Running":
        print(f"{service_name} is disabled.")
    elif status == "Restarted":
        elapsed_time = format_time_elapsed(start_time) if start_time else "unknown time"
        print(f"\033[91m{service_name} restarted {elapsed_time}\033[0m")

def log_process_status(process_name, status, start_time=None):
    if status == "Not Running":
        print(f"Process {process_name} is not running")
    elif status == "Restarted":
        elapsed_time = format_time_elapsed(start_time) if start_time else "unknown time"
        print(f"\033[91m{process_name} restarted {elapsed_time}\033[0m")

def get_install_date():
    try:
        result = subprocess.run(["wmic", "os", "get", "InstallDate"], capture_output=True, text=True)
        output = result.stdout
        match = re.search(r'(\d{14})', output)
        if match:
            install_date_str = match.group(1)
            install_date = datetime.datetime.strptime(install_date_str, '%Y%m%d%H%M%S')
            return install_date
        else:
            return None
    except Exception as e:
        print(f"Error retrieving system install date: {e}")
        return None

def check_pc_reset(install_date):
    now = datetime.datetime.now()
    if now - install_date <= datetime.timedelta(hours=1000000000):
        return format_time_elapsed(install_date)
    return None

def get_file_time_from_fsutil(drive_letter='c:'):
    try:
        ps_script = f"""
        $fsutilOutput = fsutil usn queryjournal {drive_letter}
        $fileTime = [DateTime]::FromFileTime([Convert]::ToInt64(($fsutilOutput[0] -replace ".*0x",""),16))
        $fileTime.ToString('dd MMMM yyyy HH:mm:ss')
        """
        result = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True)
        output = result.stdout.strip()
        if output:
            return datetime.datetime.strptime(output, '%d %B %Y %H:%M:%S')
        else:
            return None
    except Exception as e:
        print(f"Error retrieving file time from fsutil: {e}")
        return None

def format_time_elapsed(start_time):
    now = datetime.datetime.now()
    elapsed = now - start_time

    hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours} hours")
    if minutes > 0:
        parts.append(f"{minutes} minutes")
    if seconds > 0 or not parts:
        parts.append(f"{seconds} seconds")

    time_string = ', '.join(parts)
    return f"{time_string} ago ({start_time.strftime('%H:%M:%S %d-%m-%Y')})"

def format_time_display(event_time):
    now = datetime.datetime.now()
    elapsed = now - event_time

    hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        time_string = f"{hours} hours, {minutes} minutes, {seconds} seconds ago"
    elif minutes > 0:
        time_string = f"{minutes} minutes, {seconds} seconds ago"
    else:
        time_string = f"{seconds} seconds ago"

    return f"{time_string} ({event_time.strftime('%H:%M:%S %d-%m-%Y')})"


def check_usn_journal_deletions(boot_time):
    try:
        file_time = get_file_time_from_fsutil()
        now = datetime.datetime.now()

        if file_time and (now - file_time) <= datetime.timedelta(hours=0):
            print(f"\033[91mUSN Journal Deleted {format_time_display(file_time)}\033[0m")
            return True

        
        ps_script_3079 = """
        Get-WinEvent -LogName Application | Where-Object {$_.Id -eq 3079} | ForEach-Object {
            "{0} {1} {2}" -f $_.Id, $_.TimeCreated, $_.Message
        }
        """
        result_3079 = subprocess.run(["powershell", "-Command", ps_script_3079], capture_output=True, text=True)
        output_3079 = result_3079.stdout.strip()

        if output_3079:
            for line in output_3079.splitlines():
                try:
                    
                    if len(line.split()) >= 3:
                        event_time = parser.parse(" ".join(line.split()[1:3]))
                        if event_time > boot_time:
                            print(f"USN Journal Deleted {format_time_display(event_time)}")
                            return True
                except Exception as e:
                    print(f"Error parsing event time: {e}")

        
        ps_script_ntfs = """
        Get-WinEvent -LogName Microsoft-Windows-Ntfs/Operational | Where-Object {$_.Id -eq 501} | ForEach-Object {
            "{0} {1} {2}" -f $_.Id, $_.TimeCreated, $_.Message
        }
        """
        result_ntfs = subprocess.run(["powershell", "-Command", ps_script_ntfs], capture_output=True, text=True)
        output_ntfs = result_ntfs.stdout.strip()

        if output_ntfs:
            events = []
            current_event = ""
            for line in output_ntfs.splitlines():
                if line.startswith('501'):
                    if current_event:
                        events.append(current_event)
                    current_event = line
                else:
                    current_event += "\n" + line

            if current_event:
                events.append(current_event)

            fsutil_events = []
            other_events = []

            for event in events:
                try:
                    lines = event.splitlines()
                    
                    if len(lines[0].split()) >= 3:
                        event_time = parser.parse(" ".join(lines[0].split()[1:3]))
                        if event_time > boot_time:
                            if "Process: fsutil.exe" in event:
                                fsutil_events.append((event_time, event))
                            else:
                                other_events.append((event_time, event))
                except Exception as e:
                    print(f"Error parsing NTFS event time: {e}")

            if fsutil_events:
                latest_fsutil_event = max(fsutil_events, key=lambda x: x[0])
                fsutil_time, fsutil_event = latest_fsutil_event
                fsutil_lines = fsutil_event.splitlines()
                current_usn_line = next((line for line in fsutil_lines if "Current USN:" in line), None)

                similar_events = [
                    (other_time, other_event) for other_time, other_event in other_events
                    if abs((fsutil_time - other_time).total_seconds()) <= 1
                ]

                usn_deleted = current_usn_line and "0x0" in current_usn_line

                if similar_events:
                    usn_confirmed_deleted = any("Current USN: 0x0" in other_event for other_time, other_event in similar_events)
                    if usn_confirmed_deleted:
                        print(f"USN Journal Deleted {format_time_display(fsutil_time)}")
                        return True
                    else:
                        print(f"Possible Journal Deleted {format_time_display(fsutil_time)}")
                        return False
                else:
                    if usn_deleted:
                        print(f"USN Journal Deleted {format_time_display(fsutil_time)}")
                        return True
                    else:
                        print(f"Possible Journal Deleted {format_time_display(fsutil_time)}")
                        return False

        return False

    except Exception as e:
        print(f"Error retrieving USN Journal deletions: {e}")
        return False






def check_prefetch_files_for_read_only(prefetch_dir):
    try:
        read_only_files = []
        pf_files_found = False
        
       
        if not os.path.isdir(prefetch_dir):
            print(f"The directory {prefetch_dir} does not exist.")
            return

        
        for root, dirs, files in os.walk(prefetch_dir):
            for file in files:
                if file.lower().endswith('.pf'):
                    pf_files_found = True
                    file_path = os.path.join(root, file)
                    
                    if os.path.isfile(file_path):
                        attrs = os.stat(file_path).st_mode
                        if attrs & stat.S_IREAD and not attrs & stat.S_IWRITE:
                            read_only_files.append(file_path)

        if pf_files_found:
            if read_only_files:
                print("Read-Only Prefetch Files Found:")
                for file in read_only_files:
                    print(file)
        else:
            print("\033[93m⚠️ No .pf files found.\033[0m")

    except Exception as e:
        print(f"Error checking prefetch files: {e}")


def find_duplicate_hashes(hashes, file_details, exec_names, last_runs):
    unique_hashes = {}

    for index, hash_value in enumerate(hashes):
        if hash_value in unique_hashes:
            unique_hashes[hash_value].append((file_details[index], exec_names[index], last_runs[index]))
        else:
            unique_hashes[hash_value] = [(file_details[index], exec_names[index], last_runs[index])]

    duplicate_hashes = {k: v for k, v in unique_hashes.items() if len(v) > 1}

    if duplicate_hashes:
        print("\n\033[96mDuplicate file hashes found:\033[0m\n")
        for hash_value, details in duplicate_hashes.items():
            for file, exec_name, last_run in details:
                print(f"\033[93m- File: {file}\033[0m")
                print(f"  \033[93mExecutable Name: {exec_name}\033[0m")
                print(f"  \033[93mLast Run(UTC): {last_run}\033[0m")

def parse_prefetch_files():
    try:
        prefetch_dir = r"C:\Windows\Prefetch"
        command = [PE_CMD_PATH, '-d', prefetch_dir]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            hash_pattern = re.compile(r'Hash:\s*([0-9A-F]+)')
            file_pattern = re.compile(r'Executable name:\s*(.+?)\s*\n')
            last_run_pattern = re.compile(r'Last run:\s*(.+?)\s*\n')
            hashes = hash_pattern.findall(result.stdout)
            exec_names = file_pattern.findall(result.stdout)
            last_runs = last_run_pattern.findall(result.stdout)
            full_paths = [os.path.join(prefetch_dir, f"{name}-{hashes[i]}.pf") for i, name in enumerate(exec_names)]
            if hashes:
                find_duplicate_hashes(hashes, full_paths, exec_names, last_runs)
    except Exception as e:
        print(f"Error parsing prefetch files: {e}")

def dump_services_and_processes_and_extract_strings():
    def dump_and_extract(name, pid):
        try:
            dump_file = os.path.join(SYSINTERNALS_TEMP_DIR, f'{name}.dmp')

            if not os.path.isfile(PROCDUMP_PATH):
                raise FileNotFoundError(f"{PROCDUMP_PATH} not found.")
            result = subprocess.run([PROCDUMP_PATH, '-ma', str(pid), dump_file],
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL,
                                    check=False)

            if result.returncode not in [0, 4294967294]:
                return None

            output_file = os.path.join(SYSINTERNALS_TEMP_DIR, f'{name}.txt')
            if not os.path.isfile(STRINGS_PATH):
                raise FileNotFoundError(f"{STRINGS_PATH} not found.")
            with open(output_file, 'w') as output:
                result = subprocess.run([STRINGS_PATH, dump_file],
                                        stdout=output,
                                        stderr=subprocess.DEVNULL,
                                        check=False)

        except Exception as e:
            return None

    try:
        ps_script_services = """
        Get-WmiObject Win32_Service | Where-Object { $_.Name -in ("PCASvc", "DPS", "DNSCache", "DiagTrack", "BAM", "SysMain", "EventLog", "AppInfo", "BFE", "DusmSvc", "WinDefend") } | ForEach-Object { "$($_.Name): $($_.ProcessId)" }
        """
        result = subprocess.run(["powershell", "-Command", ps_script_services], capture_output=True, text=True)
        output = result.stdout.strip()

        if output:
            lines = output.splitlines()
            for line in lines:
                parts = line.split(':')
                if len(parts) == 2:
                    service_name = parts[0].strip()
                    pid_str = parts[1].strip()
                    try:
                        pid = int(pid_str)
                        dump_and_extract(service_name, pid)
                    except ValueError:
                        return None

       
        dump_processes = ["explorer", "lsass"]
        for process_name in dump_processes:
            ps_script_processes = f"""
            $process = Get-Process -Name '{process_name}' -ErrorAction SilentlyContinue
            if ($process) {{
                "$processName: $($process.Id)"
            }} else {{
                Write-Output "Process not found."
            }}
            """
            result = subprocess.run(["powershell", "-Command", ps_script_processes], capture_output=True, text=True)
            output = result.stdout.strip()

            if output:
                lines = output.splitlines()
                for line in lines:
                    parts = line.split(':')
                    if len(parts) == 2:
                        process_name = parts[0].strip()
                        pid_str = parts[1].strip()
                        try:
                            pid = int(pid_str)
                            dump_and_extract(process_name, pid)
                        except ValueError:
                           return None

    except Exception as e:
       return None

def get_last_modified_time(path):
    try:
        timestamp = os.path.getmtime(path)
        return datetime.datetime.fromtimestamp(timestamp)
    except FileNotFoundError:
        return None

def get_latest_modification_time(directory):
    latest_time = None
    try:
        for root, dirs, files in os.walk(directory):
            for name in dirs + files:
                path = os.path.join(root, name)
                mod_time = get_last_modified_time(path)
                if mod_time and (latest_time is None or mod_time > latest_time):
                    latest_time = mod_time
    except PermissionError:
        print("Permission denied. Could not access some files.")
    return latest_time

def get_shortcut_target(shortcut_path):
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_path)
    return shortcut.TargetPath

def get_authenticode_signature(file_path):
    command = f'powershell -Command "Get-AuthenticodeSignature \'{file_path}\'"'
    try:
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        return result.stdout
    except Exception as e:
        print(f"Error getting signature for {file_path}: {e}")
        return None

def is_file_unsigned(signature_output):
    return "Unsigned" in signature_output

def worker(queue, python_files):
    pythoncom.CoInitialize()
    while not queue.empty():
        item = queue.get()
        process_item(item, python_files)
        queue.task_done()

def process_item(item, python_files):
    try:
        if item.lower().endswith('.lnk'):
            target_path = get_shortcut_target(item)
            if target_path:
                if target_path.lower().endswith('.py'):
                    python_files.append(target_path)
                
                signature_output = get_authenticode_signature(target_path)
                if signature_output and is_file_unsigned(signature_output):
                    print(f"Unsigned: {target_path}")
    except Exception as e:
        print(f"Error processing item {item}: {e}")

def check_recent_files(recent_folder, num_threads=5):
    recent_items = glob.glob(os.path.join(recent_folder, '*'))

    if not recent_items:
        print("\033[93m⚠️ No items found in the Recent folder.\033[0m")
        return
    
    python_files = []  
    queue = Queue()
    
    for item in recent_items:
        queue.put(item)
    
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=worker, args=(queue, python_files))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()
    
    if python_files:
        print("\nRecently Accessed Python Files:")
        for path in python_files:
            print(path)

def event_logs_cleared(boot_time):
        ps_script_1102 = """
        Get-WinEvent -LogName Security | Where-Object {$_.Id -eq 1102} | ForEach-Object {
            $message = "{0} {1} {2}" -f $_.Id, $_.TimeCreated, $_.Message
            Write-Output $message
        }
        """
        result_1102 = subprocess.run(["powershell", "-Command", ps_script_1102], capture_output=True, text=True)
        output_1102 = result_1102.stdout.strip()

        if output_1102:
            lines = output_1102.splitlines()
            for line in lines:

                try:
                    time_str = line.split()[1] + " " + line.split()[2]
                    event_time = datetime.datetime.strptime(time_str, '%d-%m-%Y %H:%M:%S')

                    if event_time > boot_time:
                        print(f"Eventlogs Cleared {format_time_display(event_time)}\n")
                        return True
                except Exception as e:
                    
                    continue


                        

def bam_detection():
    bam_script = r"""
    $ErrorActionPreference = "SilentlyContinue"

function Get-Signature {
    param ([string[]]$FilePath)
    if (Test-Path -PathType "Leaf" -Path $FilePath) {
        $Authenticode = (Get-AuthenticodeSignature -FilePath $FilePath -ErrorAction SilentlyContinue).Status
        switch ($Authenticode) {
            "Valid" { return "Valid Signature" }
            "NotSigned" { return "Invalid Signature (NotSigned)" }
            "HashMismatch" { return "Invalid Signature (HashMismatch)" }
            "NotTrusted" { return "Invalid Signature (NotTrusted)" }
            "UnknownError" { return "Invalid Signature (UnknownError)" }
        }
    }
    return "File Was Not Found"
}

function Test-Admin {
    $currentUser = New-Object Security.Principal.WindowsPrincipal $([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentUser.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
}

function Get-BootTime {
    $bootTime = (Get-WmiObject Win32_OperatingSystem).LastBootUpTime
    return [Management.ManagementDateTimeConverter]::ToDateTime($bootTime).ToUniversalTime()
}

if (!(Test-Admin)) {
    Write-Warning "Permission Error"
    Start-Sleep 10
    Exit
}

$sw = [Diagnostics.Stopwatch]::StartNew()

if (!(Get-PSDrive -Name HKLM -PSProvider Registry)) {
    Try {
        New-PSDrive -Name HKLM -PSProvider Registry -Root HKEY_LOCAL_MACHINE
    } Catch {
        Write-Warning "Error Mounting HKEY_Local_Machine"
    }
}

$bv = ("bam", "bam\State")
$Users = @()

foreach ($ii in $bv) {
    $Users += Get-ChildItem -Path "HKLM:\SYSTEM\CurrentControlSet\Services\$($ii)\UserSettings\" | Select-Object -ExpandProperty PSChildName
}

$rpath = @("HKLM:\SYSTEM\CurrentControlSet\Services\bam\", "HKLM:\SYSTEM\CurrentControlSet\Services\bam\state\")
$BamResults = @()

foreach ($Sid in $Users) {
    foreach ($rp in $rpath) {
        $BamItems = Get-Item -Path "$($rp)UserSettings\$Sid" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Property
        
        foreach ($Item in $BamItems) {
            $Key = Get-ItemProperty -Path "$($rp)UserSettings\$Sid" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty $Item
            
            if ($Key.length -eq 24) {
                $Hex = [System.BitConverter]::ToString($Key[7..0]) -replace "-", ""
                $Time = Get-Date ([DateTime]::FromFileTimeUtc([Convert]::ToInt64($Hex, 16))) -Format "yyyy-MM-dd HH:mm:ss"
                $UtcTime = Get-Date ([DateTime]::FromFileTimeUtc([Convert]::ToInt64($Hex, 16))).ToUniversalTime()
                $Path = if ($Item -match '\d{1}') { Join-Path -Path "C:" -ChildPath ($Item.Remove(1, 23)) } else { "" }
                $Signature = Get-Signature -FilePath $Path

                if ($Signature -match "Invalid Signature|File Was Not Found") {
                    $BamResults += [PSCustomObject]@{
                        'Last Execution Time' = $Time
                        'Last Execution Time (UTC)' = $UtcTime
                        'Path' = $Path
                        'Signature' = $Signature
                    }
                }
            }
        }
    }
}

$ExecutedUnsigned = $BamResults | Where-Object { $_.Signature -match "Invalid Signature" }
$ExecutedDeleted = $BamResults | Where-Object { $_.Signature -eq "File Was Not Found" }


$bootTimeUtc = Get-BootTime

$ExecutedUnsignedFiltered = $ExecutedUnsigned | Where-Object { $_.'Last Execution Time (UTC)' -gt $bootTimeUtc }
$ExecutedDeletedFiltered = $ExecutedDeleted | Where-Object { $_.'Last Execution Time (UTC)' -gt $bootTimeUtc }

Write-Host -ForegroundColor Yellow "Executed Unsigned (After Boot Time):"
$ExecutedUnsignedFiltered | Select-Object 'Last Execution Time', 'Last Execution Time (UTC)', 'Path' | Format-Table -AutoSize

Write-Host -ForegroundColor Yellow "Executed Deleted (After Boot Time):"
$ExecutedDeletedFiltered | Select-Object 'Last Execution Time', 'Path' | Format-Table -AutoSize


    """

    try:
        result = subprocess.run(
            ["powershell", "-ExecutionPolicy", "Bypass", "-Command", bam_script],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")

def get_usb_devices():
    command = 'wmic path Win32_USBHub get DeviceID'
    output = subprocess.check_output(command, shell=True)

    filtered_output = [item for item in output.decode("utf-8").split("\n") if "VID_" in item or "PID_" in item]

    vid_pid_values = [(item.split("VID_")[1].split("&")[0], item.split("PID_")[1].split("\\")[0]) for item in filtered_output]

    for vid, pid in vid_pid_values:
        try:
            url = f"https://devicehunt.com/search/type/usb/vendor/{vid}/device/{pid}"
            response = requests.get(url, timeout=10)
            response.raise_for_status() 

            soup = BeautifulSoup(response.content, 'html.parser')
           
            device_line = soup.select_one('h3.details__heading')
            vendor_line = soup.select_one('h3.details__heading') 
           
            if device_line:
                print(Fore.GREEN + "[+]" + Fore.WHITE + f" Detected {vid} + {pid} as: {device_line.text.strip()}\n")
            else:
                print(Fore.RED + "[!]" + Fore.WHITE + f" Device details not found for {vid} + {pid}.\n")

        except requests.exceptions.Timeout:
            print(Fore.RED + "[!]" + Fore.WHITE + f" Timeout error for {vid} + {pid} device.\n")
        except requests.exceptions.HTTPError as err:
            print(Fore.RED + "[!]" + Fore.WHITE + f" HTTP error occurred for {vid} + {pid}: {err}\n")
        except Exception as e:
            print(Fore.RED + "[!]" + Fore.WHITE + f" An error occurred for {vid} + {pid}: {e}\n")

def parse_pca():
    powershell_script = r""" 
$ErrorActionPreference = "SilentlyContinue"

function Get-Signature {
    param ([string[]]$FilePath)
    if (Test-Path -PathType "Leaf" -Path $FilePath) {
        $Authenticode = (Get-AuthenticodeSignature -FilePath $FilePath -ErrorAction SilentlyContinue).Status
        switch ($Authenticode) {
            "Valid" { return "Valid Signature" }
            "NotSigned" { return "Invalid Signature (NotSigned)" }
            "HashMismatch" { return "Invalid Signature (HashMismatch)" }
            "NotTrusted" { return "Invalid Signature (NotTrusted)" }
            "UnknownError" { return "Invalid Signature (UnknownError)" }
        }
    }
    return "File Was Not Found"
}

function Test-Admin {
    $currentUser = New-Object Security.Principal.WindowsPrincipal $([Security.Principal.WindowsIdentity]::GetCurrent())
    return $currentUser.IsInRole([Security.Principal.WindowsBuiltinRole]::Administrator)
}

function Get-BootTime {
    $bootTime = (Get-WmiObject Win32_OperatingSystem).LastBootUpTime
    return [Management.ManagementDateTimeConverter]::ToDateTime($bootTime).ToUniversalTime()
}

if (!(Test-Admin)) {
    Write-Warning "Permission Error"
    Start-Sleep 10
    Exit
}

$sw = [Diagnostics.Stopwatch]::StartNew()

if (!(Get-PSDrive -Name HKLM -PSProvider Registry)) {
    Try {
        New-PSDrive -Name HKLM -PSProvider Registry -Root HKEY_LOCAL_MACHINE
    } Catch {
        Write-Warning "Error Mounting HKEY_Local_Machine"
    }
}

$bv = ("bam", "bam\State")
$Users = @()

foreach ($ii in $bv) {
    $Users += Get-ChildItem -Path "HKLM:\SYSTEM\CurrentControlSet\Services\$($ii)\UserSettings\" | Select-Object -ExpandProperty PSChildName
}

$rpath = @("HKLM:\SYSTEM\CurrentControlSet\Services\bam\", "HKLM:\SYSTEM\CurrentControlSet\Services\bam\state\")
$BamResults = @()

foreach ($Sid in $Users) {
    foreach ($rp in $rpath) {
        $BamItems = Get-Item -Path "$($rp)UserSettings\$Sid" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Property
        
        foreach ($Item in $BamItems) {
            $Key = Get-ItemProperty -Path "$($rp)UserSettings\$Sid" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty $Item
            
            if ($Key.length -eq 24) {
                $Hex = [System.BitConverter]::ToString($Key[7..0]) -replace "-", ""
                $Time = Get-Date ([DateTime]::FromFileTimeUtc([Convert]::ToInt64($Hex, 16))) -Format "yyyy-MM-dd HH:mm:ss"
                $UtcTime = Get-Date ([DateTime]::FromFileTimeUtc([Convert]::ToInt64($Hex, 16))).ToUniversalTime()
                $Path = if ($Item -match '\d{1}') { Join-Path -Path "C:" -ChildPath ($Item.Remove(1, 23)) } else { "" }
                $Signature = Get-Signature -FilePath $Path

                if ($Signature -match "Invalid Signature|File Was Not Found") {
                    $BamResults += [PSCustomObject]@{
                        'Last Execution Time' = $Time
                        'Last Execution Time (UTC)' = $UtcTime
                        'Path' = $Path
                        'Signature' = $Signature
                    }
                }
            }
        }
    }
}

$ExecutedUnsigned = $BamResults | Where-Object { $_.Signature -match "Invalid Signature" }
$ExecutedDeleted = $BamResults | Where-Object { $_.Signature -eq "File Was Not Found" }

$bootTimeUtc = Get-BootTime

$ExecutedUnsignedFiltered = $ExecutedUnsigned | Where-Object { $_.'Last Execution Time (UTC)' -gt $bootTimeUtc }
$ExecutedDeletedFiltered = $ExecutedDeleted | Where-Object { $_.'Last Execution Time (UTC)' -gt $bootTimeUtc }

if ($ExecutedUnsignedFiltered) {
    Write-Host -ForegroundColor Yellow "Executed Unsigned (After Boot Time):"
    $ExecutedUnsignedFiltered | Select-Object 'Last Execution Time', 'Last Execution Time (UTC)', 'Path' | Format-Table -AutoSize
} else {
    Write-Host -ForegroundColor Yellow "No Executed Unsigned Entries Found."
}

if ($ExecutedDeletedFiltered) {
    Write-Host -ForegroundColor Yellow "Executed Deleted (After Boot Time):"
    $ExecutedDeletedFiltered | Select-Object 'Last Execution Time', 'Path' | Format-Table -AutoSize
} else {
    Write-Host -ForegroundColor Yellow "No Executed Deleted Entries Found."
}


"""

    command = ["powershell", "-Command", powershell_script]

    try:
        subprocess.run(command, check=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"An error occurred: {e}")   

def regex_dps():
    dps_file_path = os.path.join(os.getenv('TEMP'), 'Sysinternals', 'dps.txt')
    if not os.path.isfile(dps_file_path):
        print(f"{dps_file_path} not found.")
        return
    pattern = r'^[A-Za-z]:\\.+?\.exe'

    try:
        with open(dps_file_path, 'r') as file:
            content = file.readlines()
        exe_paths = [line.strip() for line in content if re.match(pattern, line.strip())]
        unsigned_files = []
        if exe_paths:
            for path in exe_paths:
                signature_output = get_authenticode_signature(path)
                if signature_output and is_file_unsigned(signature_output):
                    unsigned_files.append(path)
            if unsigned_files:
                print("Unsigned executable paths:")
                for unsigned_path in unsigned_files:
                    print(unsigned_path)
            

    except Exception as e:
        print(f"An error occurred: {e}")

def deleted_bam_check():
    BD_EXECUTABLE = os.path.join(BD_EXTRACT_TO, 'bd.exe')
    if not os.path.isfile(BD_EXECUTABLE):
        print(f"Error: {BD_EXECUTABLE} not found.")
        return

    try:
        process = subprocess.Popen(
            BD_EXECUTABLE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW  
        )
        stdout, stderr = process.communicate()
        output = stdout.decode()
        error_output = stderr.decode()
        log_flag = False
        output_lines = []
        for line in output.splitlines():
            if "FILES IN SYSTEMLOG BUT NOT IN BAM:" in line:
                log_flag = True
                continue 
            if log_flag:
                if "Press any key to continue" in line:
                    continue
                if line.strip():
                    output_lines.append(line)
        if output_lines:
            for line in output_lines:
                print(f"Deleted BAM Entries:\n{line}")

    except Exception as e:
        print(f"An error occurred: {e}")


def is_unicode(string):
    return any(ord(char) > 127 for char in string)

def find_unicode_files(prefs_path):
    unicode_files = []
    try:
        for root, _, files in os.walk(prefs_path, topdown=True):
            for filename in files:
                if is_unicode(filename):
                    full_path = Path(root) / filename
                    unicode_files.append(full_path)
    except Exception as e:
        print(f"Error accessing the Prefetch directory: {e}")
    return unicode_files

def check_registry_for_unicode(path, root):
    unicode_value_names = []

    def check_key(key_path, root_key, root_name):
        try:
            with winreg.OpenKey(root_key, key_path) as key:
                i = 0
                while True:
                    try:
                        value_name, value_data, _ = winreg.EnumValue(key, i)
                        if is_unicode(value_name):
                            full_reg_path = f"{root_name}\\{key_path}"
                            unicode_value_names.append(f"Unicode value names found in registry path {full_reg_path}\nValue Name: '{value_name}' = {value_data}\n")
                        i += 1
                    except OSError:
                        break
                j = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, j)
                        check_key(f"{key_path}\\{subkey_name}", root_key, root_name)
                        j += 1
                    except OSError:
                        break
        except FileNotFoundError:
            pass 
        except Exception as e:
            print(f"Error accessing registry path {key_path}: {e}")

    check_key(path, root, "HKEY_LOCAL_MACHINE" if root == winreg.HKEY_LOCAL_MACHINE else "HKEY_CURRENT_USER")
    
    return unicode_value_names

def unicode_search():
    prefs_path = r"C:\Windows\Prefetch" 
    registry_paths = [
        (r"Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\MuiCache", winreg.HKEY_CURRENT_USER),
        (r"Software\Microsoft\Windows\CurrentVersion\Explorer\FeatureUsage\AppSwitched", winreg.HKEY_CURRENT_USER),
        (r"Software\Microsoft\Windows\CurrentVersion\Explorer\FeatureUsage\ShowJumpView", winreg.HKEY_CURRENT_USER),
        (r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers", winreg.HKEY_CURRENT_USER),
        (r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers", winreg.HKEY_LOCAL_MACHINE),
        (r"Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Compatibility Assistant\Store", winreg.HKEY_CURRENT_USER),
        (r"SYSTEM\ControlSet001\Services\bam\State\UserSettings", winreg.HKEY_LOCAL_MACHINE)
    ]

    unicode_filenames = []
    
    with ThreadPoolExecutor(max_workers=100) as executor:
        future_files = executor.submit(find_unicode_files, prefs_path)
        
        future_registry = {executor.submit(check_registry_for_unicode, path, root): path for path, root in registry_paths}
        
        unicode_filenames = future_files.result()

        for future in as_completed(future_registry):
            path = future_registry[future]
            try:
                unicode_value_names = future.result()
                for value in unicode_value_names:
                    print(value)
            except Exception as e:
                print(f"Error checking registry path {path}: {e}")

    if unicode_filenames:
        print("Files with Unicode characters in the name in Prefetch:")
        for path in unicode_filenames:
            print(path)

def main():
    setup_sysinternals_tools()
    dump_services_and_processes_and_extract_strings()
    boot_time = get_system_uptime()
    if not boot_time:
        print("Error retrieving system uptime.")
        return

    install_date = get_install_date()
    reset_status = None
    if install_date:
        reset_status = check_pc_reset(install_date)
        if reset_status:
            print(f"PC Resetted {reset_status}")

    file_time = get_file_time_from_fsutil()
    if file_time:
        print(f"USN Journal Creation: {file_time.strftime('%d %B %Y %H:%M:%S')}")

    deletion_detected = check_usn_journal_deletions(boot_time)

    for service in services:
        status = check_service_status(service)
        if status:
            start_time = get_service_process_start_time(service)
            if start_time:
                service_status = "Restarted" if is_significantly_different(start_time, boot_time) else "Running"
                if service_status == "Restarted":
                    log_service_status(service, service_status, start_time)
        else:
            log_service_status(service, "Not Running")

    for process in processes:
        status = check_process_status(f"{process}.exe")
        if status:
            start_time = get_process_start_time(process)
            if start_time:
                process_status = "Restarted" if is_significantly_different(start_time, boot_time) else "Running"
                if process_status == "Restarted":
                    log_process_status(f"{process}.exe", process_status, start_time)
        else:
            log_process_status(f"{process}.exe", "Not Running")

    


    prefetch_dir = os.path.join(os.getenv('SYSTEMROOT'), 'Prefetch')
    check_prefetch_files_for_read_only(prefetch_dir)
    parse_prefetch_files()
    
    recycle_bin_path = r'C:\$Recycle.Bin'
    if os.path.exists(recycle_bin_path):
        last_modified_time = get_latest_modification_time(recycle_bin_path)
        now = datetime.datetime.now()
        if now - last_modified_time <= datetime.timedelta(hours=24):
            formatted_time_elapsed = format_time_elapsed(last_modified_time)
            print(f"\nRecycle Bin Modified {formatted_time_elapsed}\n")

    user_recent_folder = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Roaming', 'Microsoft', 'Windows', 'Recent')
    regex_dps()
    unicode_search()
    check_recent_files(user_recent_folder)
    event_logs_cleared(boot_time)
    deleted_bam_check()
    get_usb_devices()
    parse_pca()
    bam_detection()

if __name__ == "__main__":
    main()
