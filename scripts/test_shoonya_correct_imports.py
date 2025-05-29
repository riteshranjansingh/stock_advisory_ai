#!/usr/bin/env python3
"""
Test Shoonya API with correct NorenRestApiPy package
"""

def test_norenrestapipy_structure():
    """Test the actual installed package structure"""
    print("🔍 Testing NorenRestApiPy Structure")
    print("=" * 50)
    
    # Test 1: Basic import
    try:
        import NorenRestApiPy
        print("✅ SUCCESS: import NorenRestApiPy")
        print(f"   Package path: {NorenRestApiPy.__file__}")
        print(f"   Package contents: {dir(NorenRestApiPy)}")
    except Exception as e:
        print(f"❌ FAILED: import NorenRestApiPy - {e}")
        return
    
    print()
    
    # Test 2: Look for NorenApi inside the package
    try:
        from NorenRestApiPy import NorenApi
        print("✅ SUCCESS: from NorenRestApiPy import NorenApi")
        print(f"   NorenApi: {NorenApi}")
        print(f"   NorenApi methods: {[m for m in dir(NorenApi) if not m.startswith('_')][:15]}...")
    except ImportError as e:
        print(f"❌ FAILED: from NorenRestApiPy import NorenApi - {e}")
        
        # Try to explore what's inside NorenRestApiPy
        try:
            import os
            package_path = os.path.dirname(NorenRestApiPy.__file__)
            files = os.listdir(package_path)
            print(f"   Files in package: {files}")
            
            # Try importing each .py file
            for file in files:
                if file.endswith('.py') and file != '__init__.py':
                    module_name = file[:-3]  # Remove .py
                    try:
                        module = getattr(NorenRestApiPy, module_name, None)
                        if module:
                            print(f"   ✅ Found module: {module_name}")
                        else:
                            # Try dynamic import
                            exec(f"from NorenRestApiPy import {module_name}")
                            print(f"   ✅ Dynamic import successful: {module_name}")
                    except:
                        print(f"   ❌ Could not import: {module_name}")
        except Exception as explore_error:
            print(f"   Exploration failed: {explore_error}")
    
    print()
    
    # Test 3: Try alternative import patterns
    import_patterns = [
        "NorenRestApiPy.NorenApi",
        "NorenRestApiPy.noren_api", 
        "NorenRestApiPy.api",
        "NorenRestApiPy.client",
        "NorenRestApiPy.shoonya"
    ]
    
    print("🔗 Testing Alternative Import Patterns")
    print("-" * 30)
    
    for pattern in import_patterns:
        try:
            # Dynamic import
            module_parts = pattern.split('.')
            if len(module_parts) == 2:
                main_module = __import__(module_parts[0])
                sub_module = getattr(main_module, module_parts[1])
                print(f"✅ SUCCESS: {pattern}")
                print(f"   Module: {sub_module}")
                
                # Check if it has login method
                if hasattr(sub_module, 'login') or (hasattr(sub_module, '__call__') and 'login' in str(sub_module)):
                    print(f"   🚀 HAS LOGIN METHOD!")
                
        except Exception as e:
            print(f"❌ FAILED: {pattern} - {e}")
    
    print()
    
    # Test 4: Try to instantiate based on GitHub examples
    try:
        # Pattern from GitHub: from NorenRestApiPy.NorenApi import ...
        import NorenRestApiPy
        
        # Check if there's a submodule
        import importlib
        
        # Try loading NorenApi as submodule
        noren_api_spec = importlib.util.find_spec("NorenRestApiPy.NorenApi")
        if noren_api_spec:
            print("✅ Found NorenApi submodule spec")
            noren_api_module = importlib.util.module_from_spec(noren_api_spec)
            noren_api_spec.loader.exec_module(noren_api_module)
            print(f"   Module loaded: {noren_api_module}")
            print(f"   Contents: {dir(noren_api_module)}")
        else:
            print("❌ NorenApi submodule not found via importlib")
            
    except Exception as e:
        print(f"❌ FAILED: Submodule test - {e}")

def explore_package_files():
    """Explore the actual files in the package"""
    print("📁 Exploring Package Files")
    print("=" * 50)
    
    try:
        import NorenRestApiPy
        import os
        
        package_path = os.path.dirname(NorenRestApiPy.__file__)
        print(f"Package location: {package_path}")
        
        # List all files
        for root, dirs, files in os.walk(package_path):
            level = root.replace(package_path, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
                
                # If it's a Python file, try to peek inside
                if file.endswith('.py') and file != '__init__.py':
                    try:
                        with open(os.path.join(root, file), 'r') as f:
                            first_lines = [f.readline().strip() for _ in range(10)]
                            first_lines = [line for line in first_lines if line]
                            if first_lines:
                                print(f"{subindent}  → First few lines:")
                                for line in first_lines[:3]:
                                    print(f"{subindent}     {line}")
                    except:
                        pass
        
    except Exception as e:
        print(f"❌ FAILED: Package exploration - {e}")

if __name__ == "__main__":
    print("🚀 Testing NorenRestApiPy Package Structure")
    print()
    
    test_norenrestapipy_structure()
    print("\n" + "="*50 + "\n")
    explore_package_files()
    
    print("\n✨ Analysis Complete!")