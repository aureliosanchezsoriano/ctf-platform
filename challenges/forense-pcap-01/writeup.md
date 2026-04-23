# Traffic Analysis — Find the credentials

## Vulnerability
Credentials transmitted over unencrypted protocols (HTTP, FTP, Telnet) are
visible to anyone on the network who can capture traffic.
This is OWASP A02:2021 — Cryptographic Failures.

## Solution with Wireshark
1. Open `captura.pcap` in Wireshark
2. Apply filter: `ftp`
3. Find the packet with `PASS` command
4. The password is the flag: wrap it in `CTF{}`

## Solution with tshark (command line)
```bash
tshark -r captura.pcap -Y ftp -T fields -e ftp.request.arg
```

## Fix
Never transmit credentials over unencrypted protocols.
Use FTPS, SFTP, or HTTPS instead of FTP and HTTP.

## OWASP Reference
A02:2021 — Cryptographic Failures
