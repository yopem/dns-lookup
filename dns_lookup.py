#!/usr/bin/env python3

import argparse
import json
import socket
import struct
import sys
from typing import Dict, List, Optional, Tuple


class PurePythonDNS:
    """Pure Python DNS resolver using socket and struct modules"""
    
    def __init__(self):
        self.dns_servers = [
            "8.8.8.8",      # Google DNS
            "1.1.1.1",      # Cloudflare DNS
            "8.8.4.4",      # Google DNS Secondary
        ]
        self.record_types = {
            "A": 1,
            "AAAA": 28,
            "MX": 15,
            "NS": 2,
            "CNAME": 5,
            "TXT": 16,
            "SOA": 6,
            "PTR": 12,
        }

    def _build_dns_query(self, domain: str, record_type: int) -> bytes:
        """Build a DNS query packet"""
        # DNS Header (12 bytes)
        query_id = 0x1234
        flags = 0x0100  # Standard query with recursion desired
        qdcount = 1
        ancount = 0
        nscount = 0
        arcount = 0
        
        header = struct.pack('!HHHHHH', query_id, flags, qdcount, ancount, nscount, arcount)
        
        # DNS Question
        question = b''
        for part in domain.split('.'):
            question += struct.pack('B', len(part)) + part.encode()
        question += b'\x00'  # Null terminator
        question += struct.pack('!HH', record_type, 1)  # Type and Class (IN)
        
        return header + question

    def _parse_dns_response(self, response: bytes, record_type: int) -> List[str]:
        """Parse DNS response packet"""
        try:
            if len(response) < 12:
                return []
            
            # Parse header
            header = struct.unpack('!HHHHHH', response[:12])
            ancount = header[3]  # Answer count
            
            if ancount == 0:
                return []
            
            # Skip question section
            offset = 12
            while offset < len(response) and response[offset] != 0:
                length = response[offset]
                if length & 0xC0 == 0xC0:  # Compression pointer
                    offset += 2
                    break
                offset += length + 1
            
            if offset < len(response) and response[offset] == 0:
                offset += 1
            offset += 4  # Skip QTYPE and QCLASS
            
            # Parse answer section
            answers = []
            for _ in range(ancount):
                if offset >= len(response):
                    break
                
                # Skip name (with compression handling)
                if response[offset] & 0xC0 == 0xC0:
                    offset += 2
                else:
                    while offset < len(response) and response[offset] != 0:
                        offset += response[offset] + 1
                    offset += 1
                
                if offset + 10 > len(response):
                    break
                
                # Parse answer RR
                rr_type, rr_class, ttl, rdlength = struct.unpack('!HHIH', response[offset:offset+10])
                offset += 10
                
                if rr_type == record_type and offset + rdlength <= len(response):
                    rdata = response[offset:offset+rdlength]
                    answer = self._parse_rdata(rdata, record_type, response)
                    if answer:
                        answers.append(answer)
                
                offset += rdlength
            
            return answers
        except Exception:
            return []

    def _parse_rdata(self, rdata: bytes, record_type: int, full_response: bytes) -> Optional[str]:
        """Parse DNS record data"""
        try:
            if record_type == 1:  # A record
                if len(rdata) == 4:
                    return '.'.join(str(b) for b in rdata)
            elif record_type == 28:  # AAAA record
                if len(rdata) == 16:
                    return ':'.join(f'{rdata[i]:02x}{rdata[i+1]:02x}' for i in range(0, 16, 2))
            elif record_type == 15:  # MX record
                if len(rdata) >= 3:
                    priority = struct.unpack('!H', rdata[:2])[0]
                    domain = self._parse_domain_name(rdata[2:], full_response)
                    return f"Priority: {priority}, Server: {domain}"
            elif record_type in [2, 5]:  # NS, CNAME
                return self._parse_domain_name(rdata, full_response)
            elif record_type == 16:  # TXT record
                txt_data = ""
                offset = 0
                while offset < len(rdata):
                    length = rdata[offset]
                    if offset + length + 1 > len(rdata):
                        break
                    txt_data += rdata[offset+1:offset+1+length].decode('utf-8', errors='ignore')
                    offset += length + 1
                return txt_data
            elif record_type == 6:  # SOA record
                # Simplified SOA parsing
                return "SOA record (parsing simplified)"
        except Exception:
            pass
        return None

    def _parse_domain_name(self, data: bytes, full_response: bytes) -> str:
        """Parse domain name with compression support"""
        domain_parts = []
        offset = 0
        
        while offset < len(data):
            length = data[offset]
            if length == 0:
                break
            elif length & 0xC0 == 0xC0:  # Compression pointer
                if offset + 1 < len(data):
                    pointer = ((length & 0x3F) << 8) | data[offset + 1]
                    if pointer < len(full_response):
                        compressed_part = self._parse_domain_name_at_offset(full_response, pointer)
                        if compressed_part:
                            domain_parts.append(compressed_part)
                break
            else:
                if offset + length + 1 > len(data):
                    break
                part = data[offset+1:offset+1+length].decode('utf-8', errors='ignore')
                domain_parts.append(part)
                offset += length + 1
        
        return '.'.join(domain_parts)

    def _parse_domain_name_at_offset(self, data: bytes, offset: int) -> str:
        """Parse domain name starting at specific offset"""
        domain_parts = []
        
        while offset < len(data):
            length = data[offset]
            if length == 0:
                break
            elif length & 0xC0 == 0xC0:  # Avoid infinite recursion
                break
            else:
                if offset + length + 1 > len(data):
                    break
                part = data[offset+1:offset+1+length].decode('utf-8', errors='ignore')
                domain_parts.append(part)
                offset += length + 1
        
        return '.'.join(domain_parts)

    def query_dns(self, domain: str, record_type_name: str) -> List[str]:
        """Query DNS using pure Python implementation"""
        record_type = self.record_types.get(record_type_name.upper())
        if not record_type:
            return []
        
        query = self._build_dns_query(domain, record_type)
        
        # Try multiple DNS servers
        for dns_server in self.dns_servers:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(5)
                sock.sendto(query, (dns_server, 53))
                response, _ = sock.recvfrom(4096)
                sock.close()
                
                results = self._parse_dns_response(response, record_type)
                if results:
                    return results
            except Exception:
                continue
        
        return []


class DNSLookup:
    def __init__(self):
        self.dns_resolver = PurePythonDNS()

    def lookup_single(self, domain: str, record_type: str) -> List[str]:
        """Lookup a single DNS record type"""
        results = self.dns_resolver.query_dns(domain, record_type)
        return results if results else [f"No {record_type} records found"]

    def lookup_a(self, domain: str) -> List[str]:
        # Fallback to socket for A records
        results = self.dns_resolver.query_dns(domain, "A")
        if not results or "No A records found" in results:
            try:
                ip_list = socket.gethostbyname_ex(domain)[2]
                return list(ip_list) if ip_list else ["No A records found"]
            except socket.gaierror:
                pass
        return results

    def lookup_aaaa(self, domain: str) -> List[str]:
        # Try socket getaddrinfo for AAAA records
        results = self.dns_resolver.query_dns(domain, "AAAA")
        if not results or "No AAAA records found" in results:
            try:
                addr_info = socket.getaddrinfo(domain, None, socket.AF_INET6)
                ipv6_addrs = [str(info[4][0]) for info in addr_info]
                ipv6_addrs = list(set(ipv6_addrs))  # Remove duplicates
                return ipv6_addrs if ipv6_addrs else ["No AAAA records found"]
            except socket.gaierror:
                pass
        return results

    def lookup_mx(self, domain: str) -> List[str]:
        return self.lookup_single(domain, "MX")

    def lookup_ns(self, domain: str) -> List[str]:
        return self.lookup_single(domain, "NS")

    def lookup_cname(self, domain: str) -> List[str]:
        return self.lookup_single(domain, "CNAME")

    def lookup_txt(self, domain: str) -> List[str]:
        return self.lookup_single(domain, "TXT")

    def lookup_soa(self, domain: str) -> List[str]:
        return self.lookup_single(domain, "SOA")

    def reverse_lookup(self, ip: str) -> List[str]:
        """Perform reverse DNS lookup"""
        try:
            # Use socket for reverse lookup
            hostname = socket.gethostbyaddr(ip)[0]
            return [hostname]
        except socket.herror:
            # Try PTR query
            if self._is_ipv4(ip):
                octets = ip.split(".")
                reverse_domain = ".".join(reversed(octets)) + ".in-addr.arpa"
                results = self.dns_resolver.query_dns(reverse_domain, "PTR")
                return results if results else ["No PTR records found"]
            return ["Reverse lookup failed"]

    def _is_ipv4(self, ip: str) -> bool:
        """Check if string is valid IPv4 address"""
        parts = ip.split(".")
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False

    def lookup_all(self, domain: str) -> Dict[str, List[str]]:
        """Lookup all DNS record types"""
        results = {}
        record_types = ["A", "AAAA", "MX", "NS", "CNAME", "TXT", "SOA"]

        for record_type in record_types:
            method_name = f"lookup_{record_type.lower()}"
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                results[record_type] = method(domain)

        return results

    def format_output(
        self, domain: str, results: Dict[str, List[str]], output_format: str = "text"
    ) -> str:
        """Format output for display"""
        if output_format == "json":
            return json.dumps({domain: results}, indent=2)

        output = [f"\n🔍 DNS Lookup Results for: {domain}"]
        output.append("=" * 60)

        for record_type, records in results.items():
            if records:
                # Check if all records are "No ... found" messages
                all_no_records = all(
                    "No" in record and "found" in record for record in records
                )
                
                if not all_no_records:
                    output.append(f"\n📋 {record_type} Records:")
                    for record in records:
                        output.append(f"   • {record}")
                else:
                    # Show that no records were found for this type
                    output.append(f"\n📋 {record_type} Records:")
                    output.append(f"   • No {record_type} records found")

        return "\n".join(output)


def validate_domain(domain: str) -> bool:
    import re

    pattern = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$"
    return bool(re.match(pattern, domain))


def validate_ip(ip: str) -> bool:
    import re

    ipv4_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    ipv6_pattern = r"^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$"
    return bool(re.match(ipv4_pattern, ip)) or bool(re.match(ipv6_pattern, ip))


def main():
    parser = argparse.ArgumentParser(
        description="🔍 DNS Lookup Tool - Check DNS records for any domain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s google.com                    # Lookup all records
  %(prog)s google.com -t A               # Lookup only A records
  %(prog)s google.com -t MX              # Lookup only MX records
  %(prog)s 8.8.8.8 -r                    # Reverse DNS lookup
  %(prog)s google.com --json             # Output in JSON format
  %(prog)s --web                         # Launch web interface
  %(prog)s --web google.com              # Launch web interface with domain pre-filled
        """,
    )

    parser.add_argument("domain", nargs='?', help="Domain name or IP address to lookup")
    parser.add_argument(
        "-t",
        "--type",
        choices=["A", "AAAA", "MX", "NS", "CNAME", "TXT", "SOA", "ALL"],
        default="ALL",
        help="DNS record type to lookup (default: ALL)",
    )
    parser.add_argument(
        "-r",
        "--reverse",
        action="store_true",
        help="Perform reverse DNS lookup (use with IP address)",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output results in JSON format"
    )
    parser.add_argument(
        "--web", action="store_true", help="Launch web interface in browser"
    )
    parser.add_argument(
        "-p", "--port", type=int, default=8080, help="Port for web server (default: 8080)"
    )

    args = parser.parse_args()

    # If --web flag is used, start web server
    if args.web:
        import http.server
        import os
        import socketserver
        import threading
        import time
        import urllib.parse
        import webbrowser

        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Change to script directory to serve files
        os.chdir(script_dir)
        
        class DNSApiHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=script_dir, **kwargs)
            
            def do_GET(self):
                parsed_path = urllib.parse.urlparse(self.path)
                
                # Handle API endpoint
                if parsed_path.path == '/api/dns':
                    self.handle_dns_api(parsed_path.query)
                else:
                    # Serve static files
                    super().do_GET()
            
            def handle_dns_api(self, query_string):
                try:
                    params = urllib.parse.parse_qs(query_string)
                    domain = params.get('name', [''])[0]
                    record_type = params.get('type', ['1'])[0]
                    
                    if not domain:
                        self.send_error(400, "Missing domain parameter")
                        return
                    
                    # Map type codes to names
                    type_map = {"1": "A", "28": "AAAA", "15": "MX", "2": "NS", "5": "CNAME", "16": "TXT", "6": "SOA"}
                    type_name = type_map.get(record_type, "A")
                    
                    # Perform DNS lookup
                    dns_lookup = DNSLookup()
                    method_name = f"lookup_{type_name.lower()}"
                    
                    if hasattr(dns_lookup, method_name):
                        method = getattr(dns_lookup, method_name)
                        results = method(domain)
                        
                        # Format response like Google DNS API
                        answer_records = []
                        if results and not any("No" in result and "found" in result for result in results):
                            for result in results:
                                answer_records.append({"data": result})
                        
                        response_data = {
                            "Status": 0 if answer_records else 2,
                            "Answer": answer_records
                        }
                    else:
                        response_data = {"Status": 2, "Answer": []}
                    
                    # Send JSON response
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(response_data).encode())
                    
                except Exception as e:
                    self.send_error(500, f"DNS lookup failed: {str(e)}")
        
        try:
            with socketserver.TCPServer(("0.0.0.0", args.port), DNSApiHandler) as httpd:
                url = f"http://localhost:{args.port}"
                
                # If domain is provided, add it as URL parameter
                if args.domain:
                    url += f"?domain={args.domain}"
                    if args.type != "ALL":
                        url += f"&type={args.type}"
                
                print(f"🌐 Starting web server at {url}")
                print("🔗 Opening browser...")
                print("💡 Press Ctrl+C to stop the server")
                
                # Start server in background thread
                server_thread = threading.Thread(target=httpd.serve_forever)
                server_thread.daemon = True
                server_thread.start()
                
                # Wait a moment for server to start, then open browser
                time.sleep(1)
                webbrowser.open(url)
                
                try:
                    # Keep main thread alive
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 Shutting down web server...")
                    httpd.shutdown()
                    
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"❌ Error: Port {args.port} is already in use. Try a different port with -p")
            else:
                print(f"❌ Error starting web server: {e}")
            sys.exit(1)
        
        return

    # Existing CLI functionality
    if not args.domain:
        print("❌ Error: Domain name is required when not using --web mode")
        parser.print_help()
        sys.exit(1)

    if args.reverse and not validate_ip(args.domain):
        print("❌ Error: Invalid IP address for reverse lookup")
        sys.exit(1)

    if not args.reverse and not validate_domain(args.domain):
        print("❌ Error: Invalid domain name")
        sys.exit(1)

    dns_lookup = DNSLookup()
    output_format = "json" if args.json else "text"

    print("🔄 Performing DNS lookup...")

    if args.reverse:
        results = dns_lookup.reverse_lookup(args.domain)
        if output_format == "json":
            print(json.dumps({f"PTR_{args.domain}": results}, indent=2))
        else:
            print(f"\n🔄 Reverse DNS Lookup for: {args.domain}")
            print("=" * 50)
            for result in results:
                print(f"   • {result}")
    elif args.type == "ALL":
        results = dns_lookup.lookup_all(args.domain)
        print(dns_lookup.format_output(args.domain, results, output_format))
    else:
        method_name = f"lookup_{args.type.lower()}"
        if hasattr(dns_lookup, method_name):
            method = getattr(dns_lookup, method_name)
            results = method(args.domain)

            if output_format == "json":
                print(json.dumps({f"{args.type}_{args.domain}": results}, indent=2))
            else:
                print(f"\n📋 {args.type} Records for: {args.domain}")
                print("=" * 50)
                for result in results:
                    print(f"   • {result}")
        else:
            print(f"❌ Error: Unsupported record type: {args.type}")
            sys.exit(1)


if __name__ == "__main__":
    main()
