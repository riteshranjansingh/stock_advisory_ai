#!/usr/bin/env python3
"""
Check what methods are available in TechnicalAnalysisAgent
"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.agents.data_agents.technical_agent import TechnicalAnalysisAgent

def main():
    print("🔍 Checking TechnicalAnalysisAgent Methods")
    print("="*50)
    
    try:
        # Create agent
        agent = TechnicalAnalysisAgent()
        
        # Get all methods
        methods = [method for method in dir(agent) if not method.startswith('_')]
        
        print("Available methods:")
        for method in methods:
            method_obj = getattr(agent, method)
            if callable(method_obj):
                print(f"  ✅ {method}()")
            else:
                print(f"  📊 {method} (attribute)")
        
        # Check for common method names
        common_names = ['analyze_stock', 'analyze', 'calculate_indicators', 'get_recommendation']
        
        print(f"\nChecking for common method names:")
        for name in common_names:
            if hasattr(agent, name):
                print(f"  ✅ Found: {name}()")
            else:
                print(f"  ❌ Missing: {name}()")
                
        # Try to see the class structure
        print(f"\nClass info:")
        print(f"  Class: {agent.__class__.__name__}")
        print(f"  Module: {agent.__class__.__module__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking agent: {e}")
        return False

if __name__ == "__main__":
    main()