#!/usr/bin/env python3
"""
Debug script to test Fyers API calls directly
This helps understand the exact response structure
"""
import sys
import os
import json
import time
from datetime import date, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.auth.fyers_auth import FyersAuthenticator

def debug_authentication():
    """Debug authentication"""
    print("🔐 Debug: Testing Authentication")
    print("="*50)
    
    try:
        auth = FyersAuthenticator()
        access_token = auth.get_access_token()
        
        if access_token:
            print("✅ Authentication successful")
            print(f"Token (first 20 chars): {access_token[:20]}...")
            
            # Get the authenticated client
            fyers_client = auth.get_authenticated_client()
            if fyers_client:
                print("✅ Fyers client created successfully")
                return fyers_client
            else:
                print("❌ Failed to create Fyers client")
                return None
        else:
            print("❌ Authentication failed")
            return None
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def debug_quotes_api(fyers_client):
    """Debug quotes API call"""
    print("\n📊 Debug: Testing Quotes API")
    print("="*50)
    
    try:
        # Test single symbol first
        single_symbol = "NSE:RELIANCE-EQ"
        print(f"Testing single symbol: {single_symbol}")
        
        data = {"symbols": single_symbol}
        print(f"Request data: {data}")
        
        response = fyers_client.quotes(data=data)
        print(f"Raw response: {json.dumps(response, indent=2)}")
        
        if response and response.get('s') == 'ok':
            quotes = response.get('d', [])
            if quotes:
                quote = quotes[0]
                print(f"\nFirst quote structure:")
                for key, value in quote.items():
                    print(f"  {key}: {value} (type: {type(value)})")
                
                # Check if there's nested 'v' structure
                if 'v' in quote:
                    print(f"\nNested 'v' structure:")
                    for key, value in quote['v'].items():
                        print(f"  v.{key}: {value} (type: {type(value)})")
        
        # Test multiple symbols
        print(f"\n" + "-"*30)
        print("Testing multiple symbols:")
        
        multiple_symbols = "NSE:RELIANCE-EQ,NSE:TCS-EQ"
        data = {"symbols": multiple_symbols}
        print(f"Request data: {data}")
        
        response = fyers_client.quotes(data=data)
        print(f"Multiple symbols response: {json.dumps(response, indent=2)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Quotes API error: {e}")
        return False

def debug_history_api(fyers_client):
    """Debug historical data API call"""
    print("\n📅 Debug: Testing Historical Data API")
    print("="*50)
    
    try:
        symbol = "NSE:RELIANCE-EQ"
        print(f"Testing historical data for: {symbol}")
        
        # Get last 7 days
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        # Convert to Unix timestamps
        start_timestamp = int(time.mktime(start_date.timetuple()))
        end_timestamp = int(time.mktime(end_date.timetuple()))
        
        print(f"Date range: {start_date} to {end_date}")
        print(f"Timestamps: {start_timestamp} to {end_timestamp}")
        
        # Test with different date formats
        for date_format in ['0', '1']:
            print(f"\n--- Testing with date_format: {date_format} ---")
            
            if date_format == '0':
                # Unix timestamps
                data = {
                    "symbol": symbol,
                    "resolution": "D",
                    "date_format": date_format,
                    "range_from": str(start_timestamp),
                    "range_to": str(end_timestamp),
                    "cont_flag": "1"
                }
            else:
                # Date strings
                data = {
                    "symbol": symbol,
                    "resolution": "D", 
                    "date_format": date_format,
                    "range_from": start_date.strftime('%Y-%m-%d'),
                    "range_to": end_date.strftime('%Y-%m-%d'),
                    "cont_flag": "1"
                }
            
            print(f"Request data: {data}")
            
            response = fyers_client.history(data=data)
            print(f"Response: {json.dumps(response, indent=2)}")
            
            if response and response.get('s') == 'ok':
                candles = response.get('candles', [])
                print(f"Number of candles: {len(candles)}")
                if candles:
                    print(f"First candle: {candles[0]}")
                    print(f"Last candle: {candles[-1]}")
                    break  # Found working format
        
        return True
        
    except Exception as e:
        print(f"❌ History API error: {e}")
        return False

def debug_profile_api(fyers_client):
    """Debug profile API call"""
    print("\n👤 Debug: Testing Profile API")
    print("="*50)
    
    try:
        response = fyers_client.get_profile()
        print(f"Profile response: {json.dumps(response, indent=2)}")
        
        if response and response.get('s') == 'ok':
            profile_data = response.get('data', {})
            print(f"\nProfile data:")
            for key, value in profile_data.items():
                print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Profile API error: {e}")
        return False

def main():
    """Main debug function"""
    print("🐛 Fyers API Debug Session")
    print("="*60)
    print("This will help us understand the exact API response structure")
    print("="*60)
    
    # Test authentication
    fyers_client = debug_authentication()
    if not fyers_client:
        return False
    
    # Test profile API
    debug_profile_api(fyers_client)
    
    # Test quotes API
    debug_quotes_api(fyers_client)
    
    # Test historical data API
    debug_history_api(fyers_client)
    
    print("\n" + "="*60)
    print("🏁 Debug session complete!")
    print("Check the output above to understand API response structure")
    print("="*60)
    
    return True

if __name__ == "__main__":
    main()