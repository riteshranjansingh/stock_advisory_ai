"""
Fyers Authentication Implementation
Handles Fyers-specific authentication flow with automatic token management
"""
import webbrowser
import re
import threading
import time
from datetime import datetime, timedelta
from typing import Optional
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socket

try:
    from fyers_apiv3 import fyersModel
except ImportError:
    fyersModel = None
    
from .base_auth import BaseAuthenticator

logger = logging.getLogger(__name__)

class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for catching OAuth callback"""
    
    def __init__(self, auth_code_container, *args, **kwargs):
        self.auth_code_container = auth_code_container
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET request from OAuth callback"""
        try:
            # Ignore favicon requests
            if self.path == '/favicon.ico':
                self.send_response(404)
                self.end_headers()
                return
            
            print(f"🔍 Callback received: {self.path}")
            logger.info(f"Callback received: {self.path}")
            
            # Parse the URL to get query parameters
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            print(f"🔍 Query parameters: {query_params}")
            logger.info(f"Query parameters: {query_params}")
            
            # Extract auth code
            auth_code = None
            if 'auth_code' in query_params:
                auth_code = query_params['auth_code'][0]
                print(f"✅ Found auth_code parameter")
            elif 'code' in query_params:
                auth_code = query_params['code'][0]
                print(f"✅ Found code parameter")
            else:
                print(f"❌ No auth_code or code parameter found")
                print(f"Available parameters: {list(query_params.keys())}")
            
            if auth_code:
                # Store the auth code
                self.auth_code_container['auth_code'] = auth_code
                self.auth_code_container['success'] = True
                
                print(f"✅ Successfully captured auth code!")
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                success_html = """
                <html>
                <head><title>Fyers Authentication</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: green;">✅ Authentication Successful!</h1>
                    <p>You can close this window and return to your application.</p>
                    <p>Your trading system is now connected to Fyers!</p>
                    <script>
                        setTimeout(function() {
                            window.close();
                        }, 3000);
                    </script>
                </body>
                </html>
                """
                self.wfile.write(success_html.encode())
                
            else:
                # Only set error if this isn't a favicon request and no auth code is found
                if not self.auth_code_container.get('success'):  # Don't override existing success
                    self.auth_code_container['success'] = False
                    self.auth_code_container['error'] = f'No authorization code in callback. Available params: {list(query_params.keys())}'
                
                print(f"❌ No auth code found in callback")
                
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                error_html = f"""
                <html>
                <head><title>Fyers Authentication Error</title></head>
                <body style="font-family: Arial; text-align: center; padding: 50px;">
                    <h1 style="color: red;">❌ Authentication Failed</h1>
                    <p>No authorization code received.</p>
                    <p>Received URL: {self.path}</p>
                    <p>Available parameters: {list(query_params.keys())}</p>
                    <p>Please try again or check your app settings.</p>
                </body>
                </html>
                """
                self.wfile.write(error_html.encode())
                
        except Exception as e:
            error_msg = f"Callback handler error: {e}"
            print(f"❌ {error_msg}")
            logger.error(error_msg)
            if not self.auth_code_container.get('success'):  # Don't override existing success
                self.auth_code_container['success'] = False
                self.auth_code_container['error'] = error_msg
    
    def log_message(self, format, *args):
        """Custom logging to see server requests"""
        print(f"🌐 Server: {format % args}")

class FyersAuthenticator(BaseAuthenticator):
    """
    Fyers-specific authentication implementation
    Handles the OAuth flow with automatic browser opening and token extraction
    """
    
    def __init__(self):
        super().__init__("fyers")
        self.app_session = None
        
    def _is_port_available(self, port: int) -> bool:
        """Check if a port is available for use"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return True
        except OSError:
            return False
        
    def get_required_credential_keys(self) -> list:
        """Return required credentials for Fyers"""
        return [
            "CLIENT_ID",
            "SECRET_KEY", 
            "REDIRECT_URI",
            "GRANT_TYPE",
            "RESPONSE_TYPE",
            "STATE"
        ]
    
    def authenticate(self) -> Optional[str]:
        """
        Main Fyers authentication flow
        Returns access token or None if failed
        """
        if not self.validate_credentials():
            logger.error("Invalid Fyers credentials")
            return None
            
        if not fyersModel:
            logger.error("fyers_apiv3 library not installed. Run: pip install fyers-apiv3")
            return None
        
        try:
            # Step 1: Create session
            self._create_session()
            
            # Step 2: Get authorization code
            auth_code = self._get_authorization_code()
            if not auth_code:
                return None
            
            # Step 3: Exchange for access token
            access_token = self._exchange_for_access_token(auth_code)
            if access_token:
                # Set expiry (Fyers tokens typically last 24 hours)
                self.token_expiry = datetime.now() + timedelta(hours=24)
                
            return access_token
            
        except Exception as e:
            logger.error(f"Fyers authentication failed: {e}")
            return None
    
    def _create_session(self):
        """Create Fyers session model"""
        self.app_session = fyersModel.SessionModel(
            client_id=self.credentials["CLIENT_ID"],
            redirect_uri=self.credentials["REDIRECT_URI"],
            response_type=self.credentials["RESPONSE_TYPE"],
            state=self.credentials["STATE"],
            secret_key=self.credentials["SECRET_KEY"],
            grant_type=self.credentials["GRANT_TYPE"]
        )
        logger.debug("Created Fyers session model")
    
    def _get_authorization_code(self) -> Optional[str]:
        """
        Get authorization code through automated callback server
        Returns authorization code or None
        """
        try:
            # Check if redirect URI is localhost (automated) or external (manual)
            redirect_uri = self.credentials["REDIRECT_URI"]
            is_localhost = (redirect_uri.startswith("http://localhost:") or 
                          redirect_uri.startswith("http://127.0.0.1:"))
            
            if is_localhost:
                return self._get_auth_code_automated()
            else:
                return self._get_auth_code_manual()
                
        except Exception as e:
            logger.error(f"Failed to get authorization code: {e}")
            print(f"❌ Error getting authorization code: {e}")
            return None
    
    def _get_auth_code_automated(self) -> Optional[str]:
        """
        Automated auth code retrieval using localhost callback server
        """
        try:
            # Extract port from redirect URI
            redirect_uri = self.credentials["REDIRECT_URI"]
            port = int(redirect_uri.split(":")[2].split("/")[0])
            
            # Check if port is available
            if not self._is_port_available(port):
                print(f"⚠️  Port {port} is already in use. Falling back to manual authentication...")
                return self._get_auth_code_manual()
            
            print(f"\n{'='*60}")
            print("🚀 AUTOMATED FYERS AUTHENTICATION")
            print(f"{'='*60}")
            print("1. Starting local callback server...")
            print("2. Opening browser for Fyers login...")
            print("3. After login, authentication should complete automatically!")
            print("4. If browser blocks localhost redirect, we'll detect and help!")
            print(f"{'='*60}\n")
            
            # Container to store auth code
            auth_code_container = {'auth_code': None, 'success': False, 'error': None}
            
            # Create server
            def handler(*args, **kwargs):
                return CallbackHandler(auth_code_container, *args, **kwargs)
            
            httpd = HTTPServer(('127.0.0.1', port), handler)
            
            # Start server in background thread
            server_thread = threading.Thread(target=httpd.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            print(f"✅ Callback server started on 127.0.0.1:{port}")
            print(f"🔗 Callback URL: {redirect_uri}")
            
            # Generate login URL and open browser
            login_url = self.app_session.generate_authcode()
            print("🌐 Opening browser for authentication...")
            webbrowser.open(login_url, new=1)
            
            # Wait for callback (with timeout)
            timeout = 60  # Reduced to 1 minute for faster fallback
            start_time = time.time()
            
            print("⏳ Waiting for authentication completion...")
            print("   (Please complete login in the browser window)")
            print(f"   If redirect doesn't work automatically, we'll help you!")
            
            while time.time() - start_time < timeout:
                if auth_code_container['success']:
                    httpd.shutdown()
                    print("✅ Authentication completed automatically!")
                    return auth_code_container['auth_code']
                elif auth_code_container.get('error'):
                    httpd.shutdown()
                    print(f"❌ Authentication error: {auth_code_container['error']}")
                    return None
                
                time.sleep(1)
            
            # Timeout - likely browser security blocking redirect
            httpd.shutdown()
            print("\n⚠️  Automated callback timeout (browser likely blocked localhost redirect)")
            print("💡 This is normal browser security behavior")
            print("🔄 Switching to guided manual mode...")
            
            # Show the user what URL to look for
            print(f"\n📋 GUIDED MANUAL RECOVERY:")
            print(f"1. Check your browser for a page that failed to load")
            print(f"2. Look for a URL starting with: {redirect_uri}")
            print(f"3. If you see it, copy and paste it below")
            print(f"4. If not, we'll restart the login process")
            
            manual_url = input("\nDid you see a redirect URL? Paste it here (or press Enter to restart): ").strip()
            
            if manual_url and redirect_uri in manual_url:
                # Extract auth code from manually provided URL
                auth_code = self._extract_auth_code(manual_url)
                if auth_code:
                    print("✅ Successfully extracted auth code from manual URL!")
                    return auth_code
            
            # Fallback to full manual mode
            print("🔄 Falling back to manual authentication mode...")
            return self._get_auth_code_manual()
            
        except Exception as e:
            logger.error(f"Automated auth code retrieval failed: {e}")
            print(f"❌ Automated authentication failed: {e}")
            print("💡 Falling back to manual authentication...")
            return self._get_auth_code_manual()
    
    def _get_auth_code_manual(self) -> Optional[str]:
        """
        Manual auth code retrieval (original method)
        """
        try:
            # Generate login URL
            login_url = self.app_session.generate_authcode()
            
            print(f"\n{'='*60}")
            print("🔐 MANUAL FYERS AUTHENTICATION")
            print(f"{'='*60}")
            print("1. A browser window will open automatically")
            print("2. Login with your Fyers credentials")
            print("3. After login, you'll be redirected")
            print("4. Copy the ENTIRE URL from your browser")
            print("5. Paste it below when prompted")
            print(f"{'='*60}\n")
            
            # Open browser automatically
            print("Opening browser for Fyers login...")
            webbrowser.open(login_url, new=1)
            
            # Wait for user to complete login and provide redirect URL
            print("\nAfter completing login, copy the complete redirect URL:")
            redirect_url = input("Enter redirect URL: ").strip()
            
            # Extract authorization code from URL
            auth_code = self._extract_auth_code(redirect_url)
            if auth_code:
                print(f"✅ Successfully extracted authorization code!")
                return auth_code
            else:
                print("❌ Could not extract authorization code from URL")
                return None
                
        except Exception as e:
            logger.error(f"Manual auth code retrieval failed: {e}")
            print(f"❌ Manual authentication error: {e}")
            return None
    
    def _extract_auth_code(self, redirect_url: str) -> Optional[str]:
        """
        Extract authorization code from redirect URL
        
        Args:
            redirect_url: The full redirect URL from browser
            
        Returns:
            Authorization code or None
        """
        try:
            # Fyers uses 'auth_code' parameter, not 'code'
            auth_code_match = re.search(r'auth_code=([^&]+)', redirect_url)
            if auth_code_match:
                return auth_code_match.group(1)
            
            # Fallback: also check for 'code' parameter (in case format changes)
            code_match = re.search(r'code=([^&]+)', redirect_url)
            if code_match:
                return code_match.group(1)
                
            logger.error("No 'auth_code' or 'code' parameter found in redirect URL")
            return None
        except Exception as e:
            logger.error(f"Error extracting auth code: {e}")
            return None
    
    def _exchange_for_access_token(self, auth_code: str) -> Optional[str]:
        """
        Exchange authorization code for access token
        
        Args:
            auth_code: Authorization code from OAuth flow
            
        Returns:
            Access token or None
        """
        try:
            # Set the authorization code
            self.app_session.set_token(auth_code)
            
            # Generate access token
            print("🔄 Exchanging authorization code for access token...")
            response = self.app_session.generate_token()
            
            if "access_token" in response:
                access_token = response["access_token"]
                print("✅ Successfully obtained access token!")
                logger.info("Successfully obtained Fyers access token")
                return access_token
            else:
                print(f"❌ Failed to get access token: {response}")
                logger.error(f"Token exchange failed: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            print(f"❌ Token exchange error: {e}")
            return None
    
    def is_token_valid(self) -> bool:
        """
        Check if current access token is still valid
        
        Returns:
            bool: True if token is valid
        """
        if not self.access_token:
            return False
            
        if not self.token_expiry:
            # If no expiry set, assume it's expired
            return False
            
        # Check if token has expired
        return datetime.now() < self.token_expiry
    
    def test_token(self) -> bool:
        """
        Test if the access token works by making a simple API call
        
        Returns:
            bool: True if token works
        """
        if not self.access_token:
            return False
            
        try:
            # Create Fyers model with token
            fyers = fyersModel.FyersModel(
                token=self.access_token,
                is_async=False,
                client_id=self.credentials["CLIENT_ID"],
                log_path=""
            )
            
            # Test with profile API call
            response = fyers.get_profile()
            
            if response and response.get("s") == "ok":
                logger.info("Fyers token test successful")
                return True
            else:
                logger.warning(f"Fyers token test failed: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Fyers token test error: {e}")
            return False
    
    def get_authenticated_client(self):
        """
        Get authenticated Fyers client for API calls
        
        Returns:
            FyersModel instance or None
        """
        if not self.access_token:
            logger.error("No access token available")
            return None
            
        if not fyersModel:
            logger.error("fyers_apiv3 library not installed")
            return None
            
        try:
            return fyersModel.FyersModel(
                token=self.access_token,
                is_async=False,
                client_id=self.credentials["CLIENT_ID"],
                log_path=""
            )
        except Exception as e:
            logger.error(f"Failed to create Fyers client: {e}")
            return None