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
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
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
            
            # Perform DNS lookup using pure Python implementation
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

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="DNS Lookup Web Server")
    parser.add_argument("-p", "--port", type=int, default=7001, help="Port to run server on (default: 7001)")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    
    args = parser.parse_args()
    
    try:
        with socketserver.TCPServer(("0.0.0.0", args.port), DNSWebServer) as httpd:
            url = f"http://localhost:{args.port}"
            
            print(f"🌐 DNS Lookup Web Server starting at {url}")
            print(f"🔍 Using pure Python DNS resolution")
            print(f"💡 Press Ctrl+C to stop the server")
            
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
            print(f"❌ Error: Port {args.port} is already in use. Try a different port with -p")
        else:
            print(f"❌ Error starting web server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down web server...")

if __name__ == "__main__":
    main()