import base64
import hashlib
import os
import secrets
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from dotenv import load_dotenv, set_key
import ssl

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', '.env')
load_dotenv(dotenv_path)

CLIENT_ID = os.getenv('ZOOM_CLIENT_ID')

# The requested redirect URI
REDIRECT_URI = 'http://127.0.0.1:8081/zoom/callback'

if not CLIENT_ID:
    print("Error: ZOOM_CLIENT_ID not found in .env file.")
    exit(1)

# Generate PKCE verifier and challenge
def generate_pkce_pair():
    # Generate a high-entropy cryptographically secure string (code_verifier)
    verifier = secrets.token_urlsafe(64)
    
    # Hash the verifier using SHA-256
    digest = hashlib.sha256(verifier.encode('ascii')).digest()
    
    # Base64URL encode the hash without padding (code_challenge)
    challenge = base64.urlsafe_b64encode(digest).decode('ascii').rstrip('=')
    
    return verifier, challenge

CODE_VERIFIER, CODE_CHALLENGE = generate_pkce_pair()
STATE = secrets.token_urlsafe(16)

class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        if parsed_url.path != '/zoom/callback':
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")
            return
            
        query_components = urllib.parse.parse_qs(parsed_url.query)
        
        # Verify state
        returned_state = query_components.get('state', [None])[0]
        if returned_state != STATE:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authorization Failed</h1><p>State mismatch. CSRF protection triggered.</p></body></html>")
            threading.Thread(target=self.server.shutdown).start()
            return

        if 'code' in query_components:
            code = query_components['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Exchange code for token
            token_url = "https://zoom.us/oauth/token"
            data = {
                'grant_type': 'authorization_code',
                'client_id': CLIENT_ID,
                'redirect_uri': REDIRECT_URI,
                'code': code,
                'code_verifier': CODE_VERIFIER
            }
            
            try:
                response = requests.post(token_url, data=data)
                response.raise_for_status()
                token_data = response.json()
                
                access_token = token_data.get('access_token')
                refresh_token = token_data.get('refresh_token')
                
                if refresh_token:
                    set_key(dotenv_path, 'ZOOM_REFRESH_TOKEN', refresh_token)
                    print("Successfully retrieved and saved ZOOM_REFRESH_TOKEN to .env")
                    self.wfile.write(b"<html><body><h1>Authorization Successful!</h1><p>You can close this window now.</p><script>window.close();</script></body></html>")
                else:
                    if access_token:
                        print("Got access token but no refresh token. Make sure your Zoom App settings support refresh tokens.")
                    print("Failed to get refresh token from response.")
                    print(token_data)
                    self.wfile.write(b"<html><body><h1>Authorization Completed without Refresh Token</h1><p>See terminal for details.</p></body></html>")
            except requests.exceptions.RequestException as e:
                print(f"Error fetching token: {e}")
                if hasattr(e, 'response') and e.response is not None:
                     print(e.response.text)
                self.wfile.write(b"<html><body><h1>Authorization Failed</h1><p>Check terminal for details.</p></body></html>")
                
            threading.Thread(target=self.server.shutdown).start()
            
        else:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Authorization Failed</h1><p>No code provided.</p></body></html>")
            threading.Thread(target=self.server.shutdown).start()

    def log_message(self, format, *args):
        pass # suppress default logging

def main():
    # Bind to localhost port 8081
    server_address = ('127.0.0.1', 8081)
    httpd = HTTPServer(server_address, AuthHandler)
    
    # Construct auth URL
    auth_params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'code_challenge': CODE_CHALLENGE,
        'code_challenge_method': 'S256',
        'state': STATE
    }
    auth_url = f"https://zoom.us/oauth/authorize?{urllib.parse.urlencode(auth_params)}"
    
    print(f"Starting local server to handle callback on {REDIRECT_URI}...")
    print(f"Authorization URL:\n{auth_url}\n")
    print("Opening browser for authorization...")
    webbrowser.open(auth_url)
    
    # Run the server to wait for callback
    httpd.serve_forever()
    print("Server shut down.")

if __name__ == '__main__':
    main()
