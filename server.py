#!/usr/bin/env python3

import http.server
import socketserver
import json
import urllib.parse
import os
import sys
from dns_lookup import DNSLookup


class DNSWebServer(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Set web directory as the document root
        web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
        super().__init__(*args, directory=web_dir, **kwargs)

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)

        # Handle DNS lookup base path
        if parsed_path.path.startswith("/dns-lookup"):
            # Strip /dns-lookup prefix for internal routing
            internal_path = parsed_path.path[len("/dns-lookup") :]
            if not internal_path:
                internal_path = "/"

            # Handle API endpoint
            if internal_path == "/api/dns":
                self.handle_dns_api(parsed_path.query)
            else:
                # Serve static files with modified path
                original_path = self.path
                self.path = internal_path
                super().do_GET()
                self.path = original_path
        else:
            # For backward compatibility, also serve on root
            if parsed_path.path == "/api/dns":
                self.handle_dns_api(parsed_path.query)
            else:
                super().do_GET()

    def guess_type(self, path):
        """Override to ensure proper MIME types for CSS and JS files"""
        path_str = str(path)
        if path_str.endswith(".css"):
            return "text/css"
        elif path_str.endswith(".js"):
            return "application/javascript"
        else:
            return super().guess_type(path)

    def end_headers(self):
        """Add security and caching headers"""
        # Add CORS headers for all requests
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

        # Add cache control for static files
        if self.path.endswith((".css", ".js", ".png", ".jpg", ".ico")):
            self.send_header("Cache-Control", "public, max-age=3600")

        super().end_headers()

    def handle_dns_api(self, query_string):
        try:
            params = urllib.parse.parse_qs(query_string)
            domain = params.get("name", [""])[0]
            record_type = params.get("type", ["1"])[0]

            if not domain:
                self.send_error(400, "Missing domain parameter")
                return

            # Map type codes to names
            type_map = {
                "1": "A",
                "28": "AAAA",
                "15": "MX",
                "2": "NS",
                "5": "CNAME",
                "16": "TXT",
                "6": "SOA",
            }
            type_name = type_map.get(record_type, "A")

            # Perform DNS lookup using pure Python implementation
            dns_lookup = DNSLookup()
            method_name = f"lookup_{type_name.lower()}"

            if hasattr(dns_lookup, method_name):
                method = getattr(dns_lookup, method_name)
                results = method(domain)

                # Format response like Google DNS API
                answer_records = []
                if results:
                    # Filter out "No ... found" messages
                    valid_results = [
                        result
                        for result in results
                        if not ("No" in result and "found" in result)
                    ]
                    for result in valid_results:
                        answer_records.append({"data": result})

                response_data = {
                    "Status": 0 if answer_records else 2,
                    "Answer": answer_records,
                }
            else:
                response_data = {"Status": 2, "Answer": []}

            # Send JSON response
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())

        except Exception as e:
            self.send_error(500, f"DNS lookup failed: {str(e)}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="DNS Lookup Web Server")
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=7001,
        help="Port to run server on (default: 7001)",
    )
    parser.add_argument(
        "--no-browser", action="store_true", help="Don't open browser automatically"
    )

    args = parser.parse_args()

    try:
        with socketserver.TCPServer(("0.0.0.0", args.port), DNSWebServer) as httpd:
            url = f"http://localhost:{args.port}"

            print(f"🌐 DNS Lookup Web Server starting at {url}")
            print("🔍 Using pure Python DNS resolution")
            print("💡 Press Ctrl+C to stop the server")

            if not args.no_browser:
                import webbrowser
                import time
                import threading

                def open_browser():
                    time.sleep(1)
                    webbrowser.open(url)

                threading.Thread(target=open_browser, daemon=True).start()

            httpd.serve_forever()

    except OSError as e:
        if "Address already in use" in str(e):
            print(
                f"❌ Error: Port {args.port} is already in use. Try a different port with -p"
            )
        else:
            print(f"❌ Error starting web server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down web server...")


if __name__ == "__main__":
    main()
