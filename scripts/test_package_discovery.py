#!/usr/bin/env python3
"""
Discover what's actually installed in our Python environment
"""

import sys
import pkg_resources
import importlib.util

def discover_noren_packages():
    """Discover all Noren-related packages"""
    print("🔍 Discovering Installed Packages")
    print("=" * 50)
    
    # Check all installed packages
    installed_packages = [d.project_name for d in pkg_resources.working_set]
    noren_packages = [pkg for pkg in installed_packages if 'noren' in pkg.lower()]
    
    print("📦 Noren-related packages found:")
    for pkg in noren_packages:
        print(f"   ✅ {pkg}")
        
        # Try to get package details
        try:
            dist = pkg_resources.get_distribution(pkg)
            print(f"      Version: {dist.version}")
            print(f"      Location: {dist.location}")
        except:
            pass
    
    print()
    
    # Try different import patterns
    import_patterns = [
        "NorenRestApi",
        "NorenRestApiPy", 
        "NorenApi",
        "noren",
        "norenrestapi",
        "norenrestapipy"
    ]
    
    print("🔗 Testing Import Patterns")
    print("=" * 50)
    
    for pattern in import_patterns:
        try:
            spec = importlib.util.find_spec(pattern)
            if spec:
                print(f"✅ Found module: {pattern}")
                print(f"   Location: {spec.origin}")
                
                # Try to import it
                try:
                    module = importlib.import_module(pattern)
                    print(f"   Import successful: {module}")
                    print(f"   Contents: {dir(module)[:10]}...")
                except Exception as e:
                    print(f"   Import failed: {e}")
            else:
                print(f"❌ Module not found: {pattern}")
        except Exception as e:
            print(f"❌ Error checking {pattern}: {e}")
        
        print()

def check_site_packages():
    """Check site-packages directory directly"""
    print("📁 Checking site-packages directory")
    print("=" * 50)
    
    import site
    site_packages = site.getsitepackages()
    
    for sp in site_packages:
        print(f"Site-packages: {sp}")
        
        try:
            import os
            items = os.listdir(sp)
            noren_items = [item for item in items if 'noren' in item.lower()]
            
            if noren_items:
                print("   Noren-related items:")
                for item in noren_items:
                    print(f"      📂 {item}")
        except Exception as e:
            print(f"   Error reading directory: {e}")

if __name__ == "__main__":
    print("🚀 Package Discovery Tool")
    print()
    
    discover_noren_packages()
    check_site_packages()
    
    print("\n✨ Discovery Complete!")