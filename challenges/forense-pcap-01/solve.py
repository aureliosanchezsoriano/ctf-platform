"""
Official solution for forense-pcap-01.
Using tshark to extract FTP credentials from the pcap.
"""
import subprocess, re

result = subprocess.run(
    ["tshark", "-r", "files/captura.pcap", "-Y", "ftp", "-T", "fields", "-e", "ftp.request.arg"],
    capture_output=True, text=True
)
print("FTP arguments found:")
print(result.stdout)
print("Flag: CTF{" + result.stdout.strip().split('\n')[-1] + "}")
