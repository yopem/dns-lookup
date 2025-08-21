#!/usr/bin/env python3

import argparse
import json
import socket
import subprocess
import sys
from typing import Dict, List, Optional


class DNSLookup:
    def __init__(self):
        pass

    def _run_dig(self, domain: str, record_type: str) -> List[str]:
        try:
            # Try dig first
            cmd = ["dig", "+short", domain, record_type]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return [
                    line.strip()
                    for line in result.stdout.strip().split("\n")
                    if line.strip()
                ]
        except FileNotFoundError:
            # If dig is not available, try adig
            try:
                cmd = ["adig", domain, record_type]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return self._parse_adig_output(result.stdout, record_type)
            except FileNotFoundError:
                pass
        except subprocess.TimeoutExpired:
            pass
        return []

    def _parse_adig_output(self, output: str, record_type: str) -> List[str]:
        """Parse adig output to extract DNS records"""
        lines = output.split('\n')
        records = []
        in_answer_section = False
        
        for line in lines:
            line = line.strip()
            if line.startswith(';; ANSWER SECTION:'):
                in_answer_section = True
                continue
            elif line.startswith(';;') and in_answer_section:
                break
            elif in_answer_section and line and not line.startswith(';'):
                parts = line.split()
                if len(parts) >= 5 and parts[3] == record_type:
                    if record_type == "MX" and len(parts) >= 6:
                        records.append(f"{parts[4]} {parts[5]}")
                    elif record_type in ["A", "AAAA", "NS", "CNAME"]:
                        records.append(parts[4])
                    elif record_type == "TXT":
                        # TXT records might have quoted text
                        txt_data = " ".join(parts[4:])
                        records.append(txt_data.strip('"'))
                    elif record_type == "SOA" and len(parts) >= 10:
                        records.append(f"{parts[4]} {parts[5]} {parts[6]} {parts[7]} {parts[8]} {parts[9]} {parts[10]}")
        
        return records

    def _run_nslookup(self, domain: str, record_type: str) -> List[str]:
        try:
            if record_type == "A":
                cmd = ["nslookup", domain]
            else:
                cmd = ["nslookup", "-type=" + record_type, domain]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.split("\n")
                records = []
                for line in lines:
                    line = line.strip()
                    if (
                        record_type == "A"
                        and "Address:" in line
                        and not line.startswith("Server:")
                    ):
                        records.append(line.split("Address:")[1].strip())
                    elif record_type == "MX" and "mail exchanger" in line:
                        records.append(line.split("=")[1].strip())
                    elif record_type == "NS" and "nameserver" in line:
                        records.append(line.split("=")[1].strip())
                    elif record_type == "CNAME" and "canonical name" in line:
                        records.append(line.split("=")[1].strip())
                return records
            return []
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []

    def _socket_lookup(self, domain: str) -> List[str]:
        try:
            result = socket.gethostbyname_ex(domain)
            return result[2]
        except socket.gaierror:
            return []

    def lookup_a(self, domain: str) -> List[str]:
        records = self._run_dig(domain, "A")
        if not records:
            records = self._run_nslookup(domain, "A")
        if not records:
            records = self._socket_lookup(domain)
        return records or ["No A records found"]

    def lookup_aaaa(self, domain: str) -> List[str]:
        records = self._run_dig(domain, "AAAA")
        if not records:
            records = self._run_nslookup(domain, "AAAA")
        return records or ["No AAAA records found"]

    def lookup_mx(self, domain: str) -> List[str]:
        records = self._run_dig(domain, "MX")
        if not records:
            records = self._run_nslookup(domain, "MX")
        return records or ["No MX records found"]

    def lookup_ns(self, domain: str) -> List[str]:
        records = self._run_dig(domain, "NS")
        if not records:
            records = self._run_nslookup(domain, "NS")
        return records or ["No NS records found"]

    def lookup_cname(self, domain: str) -> List[str]:
        records = self._run_dig(domain, "CNAME")
        if not records:
            records = self._run_nslookup(domain, "CNAME")
        return records or ["No CNAME records found"]

    def lookup_txt(self, domain: str) -> List[str]:
        records = self._run_dig(domain, "TXT")
        if not records:
            records = self._run_nslookup(domain, "TXT")
        return records or ["No TXT records found"]

    def lookup_soa(self, domain: str) -> List[str]:
        records = self._run_dig(domain, "SOA")
        if not records:
            records = self._run_nslookup(domain, "SOA")
        return records or ["No SOA records found"]

    def reverse_lookup(self, ip: str) -> List[str]:
        try:
            result = socket.gethostbyaddr(ip)
            return [result[0]]
        except socket.herror:
            records = self._run_dig(ip, "PTR")
            return records or ["No PTR records found"]

    def lookup_all(self, domain: str) -> Dict[str, List[str]]:
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
        """,
    )

    parser.add_argument("domain", help="Domain name or IP address to lookup")
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

    args = parser.parse_args()

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
