# DNS Lookup Tools

A simple DNS lookup tool collection with both web interface and command-line versions for checking DNS records of any domain.

## Features

- **Web Interface**: Beautiful, responsive web application for DNS lookups
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **CLI Tool**: Command-line interface for terminal users and automation
- **Multiple Record Types**: Support for A, AAAA, MX, NS, CNAME, TXT, SOA records
- **Reverse DNS**: IP to domain name resolution
- **Multiple Output Formats**: Text and JSON output options
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Quick Start

### Docker Deployment (Recommended)

Deploy the web interface on port 7001:

```bash
# Build and run with Docker Compose
docker-compose up -d

# Or build and run manually
docker build -t dns-lookup .
docker run -d -p 7001:7001 --name dns-lookup-tool dns-lookup
```

Access the web interface at: `http://localhost:7001`

### Web Interface (Local)

1. Open `index.html` in your web browser
2. Enter a domain name (e.g., `google.com`)
3. Select record type or choose "All Records"
4. Click "Lookup" to see results

### Command Line Interface

Make the script executable:

```bash
chmod +x dns_lookup.py
```

Basic usage:

```bash
# Lookup all records for a domain
python3 dns_lookup.py google.com

# Lookup specific record type
python3 dns_lookup.py google.com -t A
python3 dns_lookup.py google.com -t MX

# Reverse DNS lookup
python3 dns_lookup.py 8.8.8.8 -r

# JSON output
python3 dns_lookup.py google.com --json
```

## 📋 Supported DNS Record Types

| Record Type | Description                   |
| ----------- | ----------------------------- |
| **A**       | IPv4 address records          |
| **AAAA**    | IPv6 address records          |
| **MX**      | Mail exchange records         |
| **NS**      | Name server records           |
| **CNAME**   | Canonical name records        |
| **TXT**     | Text records                  |
| **SOA**     | Start of authority records    |
| **PTR**     | Reverse DNS (pointer) records |

## CLI Usage Examples

```bash
# Check all DNS records for a domain
./dns_lookup.py example.com

# Check only A records
./dns_lookup.py example.com -t A

# Check MX (mail) records
./dns_lookup.py example.com -t MX

# Reverse DNS lookup for an IP
./dns_lookup.py 1.1.1.1 -r

# Get results in JSON format
./dns_lookup.py example.com --json

# Check specific record type with JSON output
./dns_lookup.py example.com -t NS --json
```

## Web Interface Features

- **Neobrutalist Design**: Bold, high-contrast design with thick black borders and vibrant colors
- **Dark/Light Theme**: Seamless theme switching with system preference detection
- **Theme Persistence**: Remembers your preferred theme across sessions
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Interactive Elements**: Hover effects and smooth animations
- **Real-time Validation**: Domain name validation before lookup
- **Loading Indicators**: Visual feedback during DNS queries
- **Error Handling**: Clear error messages for failed lookups
- **Clean Results**: Organized display of DNS records by type
- **Copy-friendly**: Results formatted for easy copying

## Technical Details

### Dependencies

**Python CLI Tool:**

- Python 3.6+
- Built-in libraries only (no external dependencies)
- Optional: `dig` or `nslookup` commands for enhanced functionality

**Web Interface:**

- Modern web browser with JavaScript support
- Internet connection for DNS queries via Google's DNS-over-HTTPS API
- **Docker** (for containerized deployment)

**Docker Deployment:**

- Docker 20.0+ and Docker Compose 2.0+
- Port 7001 available for web service

### How It Works

**Python CLI:**

1. Uses multiple lookup methods for reliability:
   - `dig` command (preferred)
   - `nslookup` command (fallback)
   - Python `socket` library (basic A records)
2. Validates domain names and IP addresses
3. Supports multiple output formats

**Web Interface:**

1. Uses Google's DNS-over-HTTPS API for secure DNS queries
2. Client-side JavaScript for real-time results
3. No server required - runs entirely in the browser

## Error Handling

Both tools include comprehensive error handling:

- **Invalid domain names**: Proper validation and user-friendly error messages
- **Network timeouts**: Graceful handling of slow or failed DNS queries
- **Missing tools**: Fallback methods when `dig` or `nslookup` aren't available
- **API failures**: Error handling for web API unavailability

## Privacy & Security

- **No data storage**: Neither tool stores or logs DNS queries
- **HTTPS**: Web version uses encrypted DNS-over-HTTPS
- **Local execution**: CLI tool runs entirely on your machine
- **No external dependencies**: Python tool uses only built-in libraries

## Contributing

Feel free to contribute by:

- Adding support for more DNS record types
- Improving the user interface
- Adding more output formats
- Enhancing error handling
- Adding tests

## License

This project is open source and available under the MIT License.

