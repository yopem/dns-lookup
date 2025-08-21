# 🔍 DNS Lookup Tool

A simple DNS lookup tool with both CLI and web interfaces, powered by pure
Python DNS resolution.

## Features

- **Pure Python DNS Resolution** - No external dependencies or system tools
  required
- **Multiple Interfaces** - CLI, Web UI, and API
- **Complete Record Support** - A, AAAA, MX, NS, CNAME, TXT, SOA, PTR records
- **Cross-Platform** - Works on any system with Python 3
- **Multiple DNS Servers** - Fallback to Google DNS, Cloudflare DNS
- **Dark/Light Theme** - Responsive web interface with theme toggle

## Usage

### 1. Command Line Interface

```bash
# Basic usage
python3 dns_lookup.py google.com                    # All records
python3 dns_lookup.py google.com -t A               # A records only
python3 dns_lookup.py google.com -t MX              # MX records only
python3 dns_lookup.py google.com --json             # JSON output

# Reverse DNS lookup
python3 dns_lookup.py 8.8.8.8 -r                   # Reverse lookup

# Launch web interface from CLI
python3 dns_lookup.py --web                         # Start web server
python3 dns_lookup.py --web google.com              # Pre-fill domain
python3 dns_lookup.py --web -p 7001                 # Custom port
```

### 2. Standalone Web Server

```bash
# Start web server with Python DNS backend
python3 server.py                                   # Default port 7001
python3 server.py -p 8000                          # Custom port
python3 server.py --no-browser                     # Don't auto-open browser
```

### 3. Web Interface

To use the web interface, you need to run the Python server first:

1. **Start the server**: `python3 server.py`
2. **Open browser**: Navigate to `http://localhost:7001`
3. **Or use CLI web mode**: `python3 dns_lookup.py --web`

The web interface uses the same pure Python DNS resolution as the CLI.

## 📋 Record Types Supported

| Type  | Description        | Example                                                   |
| ----- | ------------------ | --------------------------------------------------------- |
| A     | IPv4 Address       | `142.251.10.100`                                          |
| AAAA  | IPv6 Address       | `2404:6800:4003:c20::71`                                  |
| MX    | Mail Exchange      | `Priority: 10, Server: smtp.google.com`                   |
| NS    | Name Server        | `ns1.google.com`                                          |
| CNAME | Canonical Name     | `www.example.com`                                         |
| TXT   | Text Record        | `v=spf1 include:_spf.google.com ~all`                     |
| SOA   | Start of Authority | `Primary NS: ns1.google.com, Email: dns-admin.google.com` |
| PTR   | Reverse DNS        | `google-public-dns-a.google.com`                          |

## 🔧 Technical Details

- **Pure Python Implementation** - Uses `socket` and `struct` modules for DNS
  packet construction/parsing
- **DNS Servers Used**: 8.8.8.8 (Google), 1.1.1.1 (Cloudflare), 8.8.4.4 (Google
  Secondary)
- **Protocol**: UDP port 53 for DNS queries
- **Fallbacks**: Python `socket` module for A/AAAA records when custom resolver
  fails

## Files

- `dns_lookup.py` - Main CLI tool with integrated web server
- `server.py` - Standalone web server
- `index.html` - Web interface
- `assets/style.css` - Web interface styles
- `assets/script.js` - Web interface JavaScript
- `assets/logo/` - Logo files for web interface

## 🌐 API Endpoint

When running the web server, you can access the API directly:

```bash
# API endpoint format
GET /api/dns?name=DOMAIN&type=TYPE_CODE

# Examples
curl "http://localhost:7001/api/dns?name=google.com&type=1"    # A records
curl "http://localhost:7001/api/dns?name=google.com&type=15"   # MX records
```

Type codes: A=1, NS=2, CNAME=5, SOA=6, MX=15, TXT=16, AAAA=28

## Why Pure Python?

- **No Dependencies** - Works out of the box with Python 3
- **Cross-Platform** - No reliance on system DNS tools (dig, nslookup)
- **Reliable** - Direct control over DNS queries and responses
- **Consistent** - Same resolution logic for both CLI and web interfaces

## Docker Deployment

You can also use Docker for easy deployment:

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build and run manually
docker build -t dns-lookup .
docker run -d -p 7001:7001 --name dns-lookup-tool dns-lookup
```

## Examples

### CLI Examples

```bash
# Check all records for google.com
python3 dns_lookup.py google.com

# Check only MX records with JSON output
python3 dns_lookup.py google.com -t MX --json

# Reverse lookup for 8.8.8.8
python3 dns_lookup.py 8.8.8.8 -r

# Start web interface on port 9000
python3 dns_lookup.py --web -p 9000
```

### Web Server Examples

```bash
# Start server on default port 7001
python3 server.py

# Start server on port 3000 without opening browser
python3 server.py -p 3000 --no-browser
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.
