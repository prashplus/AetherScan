"""
Test script to verify Fast3R installation and functionality
Run this inside the backend container to diagnose issues
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("=" * 60)
    print("FAST3R INSTALLATION TEST")
    print("=" * 60)
    
    tests = []
    
    # Test 1: Basic Python packages
    print("\n1. Testing basic dependencies...")
    try:
        import torch
        print(f"   ✅ PyTorch {torch.__version__}")
        print(f"   ✅ CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   ✅ GPU: {torch.cuda.get_device_name(0)}")
        tests.append(("PyTorch", True))
    except Exception as e:
        print(f"   ❌ PyTorch: {e}")
        tests.append(("PyTorch", False))
    
    try:
        import numpy as np
        print(f"   ✅ NumPy {np.__version__}")
        tests.append(("NumPy", True))
    except Exception as e:
        print(f"   ❌ NumPy: {e}")
        tests.append(("NumPy", False))
    
    try:
        import PIL
        print(f"   ✅ Pillow {PIL.__version__}")
        tests.append(("Pillow", True))
    except Exception as e:
        print(f"   ❌ Pillow: {e}")
        tests.append(("Pillow", False))
    
    try:
        import cv2
        print(f"   ✅ OpenCV {cv2.__version__}")
        tests.append(("OpenCV", True))
    except Exception as e:
        print(f"   ❌ OpenCV: {e}")
        tests.append(("OpenCV", False))
    
    # Test 2: Fast3R package
    print("\n2. Testing Fast3R package...")
    try:
        import fast3r
        print(f"   ✅ fast3r package found")
        print(f"   📁 Location: {fast3r.__file__}")
        
        # List what's in the package
        import pkgutil
        modules = [name for _, name, _ in pkgutil.iter_modules(fast3r.__path__)]
        print(f"   📦 Available modules: {modules}")
        tests.append(("fast3r package", True))
    except Exception as e:
        print(f"   ❌ fast3r package: {e}")
        tests.append(("fast3r package", False))
        return tests
    
    # Test 3: Fast3R submodules
    print("\n3. Testing Fast3R submodules...")
    
    submodules = [
        "fast3r.models",
        "fast3r.models.fast3r",
        "fast3r.dust3r",
        "fast3r.dust3r.utils",
        "fast3r.dust3r.utils.image",
        "fast3r.dust3r.inference_multiview",
        "fast3r.models.multiview_dust3r_module",
    ]
    
    for module_name in submodules:
        try:
            module = __import__(module_name, fromlist=[''])
            print(f"   ✅ {module_name}")
            tests.append((module_name, True))
        except Exception as e:
            print(f"   ❌ {module_name}: {e}")
            tests.append((module_name, False))
    
    # Test 4: Try to import the main Fast3R class
    print("\n4. Testing Fast3R model class...")
    try:
        from fast3r.models.fast3r import Fast3R
        print(f"   ✅ Fast3R class imported successfully")
        tests.append(("Fast3R class", True))
    except Exception as e:
        print(f"   ❌ Fast3R class: {e}")
        tests.append(("Fast3R class", False))
    
    # Test 5: Check if model can be instantiated (without downloading)
    print("\n5. Testing model instantiation...")
    try:
        from fast3r.models.fast3r import Fast3R
        print("   ℹ️  Attempting to load model from Hugging Face...")
        print("   ℹ️  This will download ~2GB on first run")
        # Note: We won't actually load it here to avoid long download
        print("   ⏭️  Skipping actual model load (would download 2GB)")
        tests.append(("Model instantiation", "skipped"))
    except Exception as e:
        print(f"   ❌ Model instantiation test: {e}")
        tests.append(("Model instantiation", False))
    
    return tests


def test_package_structure():
    """Check the installed package structure"""
    print("\n" + "=" * 60)
    print("PACKAGE STRUCTURE CHECK")
    print("=" * 60)
    
    try:
        import fast3r
        import os
        
        package_dir = os.path.dirname(fast3r.__file__)
        print(f"\nPackage directory: {package_dir}")
        
        print("\nDirectory contents:")
        for root, dirs, files in os.walk(package_dir):
            level = root.replace(package_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files[:10]:  # Limit to first 10 files per dir
                print(f'{subindent}{file}')
            if len(files) > 10:
                print(f'{subindent}... and {len(files) - 10} more files')
            if level > 2:  # Limit depth
                break
    except Exception as e:
        print(f"❌ Error checking package structure: {e}")


def test_reconstruction_service():
    """Test the reconstruction service"""
    print("\n" + "=" * 60)
    print("RECONSTRUCTION SERVICE TEST")
    print("=" * 60)
    
    try:
        sys.path.insert(0, '/app')
        from services.reconstruction import ReconstructionService, get_reconstruction_service
        
        print("\n1. Testing service import...")
        print("   ✅ Service imported successfully")
        
        print("\n2. Testing service instantiation...")
        service = ReconstructionService()
        print(f"   ✅ Service created on device: {service.device}")
        
        print("\n3. Testing model loading...")
        print("   ℹ️  Attempting to load Fast3R model...")
        service._load_model()
        
        if service.model_loaded:
            print("   ✅ Model loaded successfully!")
            print(f"   ✅ Model: {type(service.model)}")
        else:
            print("   ❌ Model failed to load")
            print("   ℹ️  Check logs above for specific error")
        
        return service.model_loaded
        
    except Exception as e:
        print(f"   ❌ Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(tests):
    """Print test summary"""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in tests if result is True)
    failed = sum(1 for _, result in tests if result is False)
    skipped = sum(1 for _, result in tests if result == "skipped")
    
    print(f"\n✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"📊 Total: {len(tests)}")
    
    if failed > 0:
        print("\n❌ Failed tests:")
        for name, result in tests:
            if result is False:
                print(f"   - {name}")
    
    print("\n" + "=" * 60)
    if failed == 0:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED - Check output above")
    print("=" * 60)


if __name__ == "__main__":
    print("\nStarting Fast3R diagnostic tests...\n")
    
    # Run import tests
    test_results = test_imports()
    
    # Check package structure
    test_package_structure()
    
    # Test reconstruction service
    service_ok = test_reconstruction_service()
    test_results.append(("Reconstruction Service", service_ok))
    
    # Print summary
    print_summary(test_results)
    
    # Exit with appropriate code
    failed = sum(1 for _, result in test_results if result is False)
    sys.exit(0 if failed == 0 else 1)
