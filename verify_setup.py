#!/usr/bin/env python3
"""
Quick setup verification script for the Invoice Reimbursement System.

This script verifies that all dependencies are properly installed and the
system can be started without issues.
"""

import importlib
import sys
from pathlib import Path


def check_imports():
    """Check if all required packages can be imported."""
    required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "pydantic_settings",
        "dotenv",
        "PyPDF2",
        "aiofiles",
        "langchain",
        "langchain_google_genai",
        "qdrant_client",
        "sentence_transformers",
        "google.genai",
    ]

    print("🔍 Checking package imports...")
    failed_imports = []

    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError as e:
            print(f"❌ {package} - {e}")
            failed_imports.append(package)

    if failed_imports:
        print(f"\n❌ Failed to import {len(failed_imports)} packages")
        return False
    else:
        print(f"\n✅ All {len(required_packages)} packages imported successfully!")
        return True


def check_project_structure():
    """Check if project structure is correct."""
    print("\n🏗️  Checking project structure...")

    required_files = [
        "app/__init__.py",
        "app/main.py",
        "app/core/config.py",
        "app/core/logging_config.py",
        "app/models/schemas.py",
        "app/services/__init__.py",
        "app/api/routes/invoice_analysis.py",
        "app/api/routes/chatbot.py",
        "requirements.txt",
        ".env.example",
        "README.md",
    ]

    missing_files = []
    project_root = Path(__file__).parent

    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files")
        return False
    else:
        print(f"\n✅ All {len(required_files)} files found!")
        return True


def check_environment():
    """Check environment configuration."""
    print("\n⚙️  Checking environment configuration...")

    env_file = Path(__file__).parent / ".env"
    env_example = Path(__file__).parent / ".env.example"

    if not env_example.exists():
        print("❌ .env.example file not found")
        return False
    else:
        print("✅ .env.example file found")

    if not env_file.exists():
        print("⚠️  .env file not found - please copy .env.example to .env and configure")
        print("   You can do this by running: cp .env.example .env")
        return False
    else:
        print("✅ .env file found")

    return True


def main():
    """Main verification function."""
    print("🚀 Invoice Reimbursement System - Setup Verification")
    print("=" * 55)

    # Run checks
    imports_ok = check_imports()
    structure_ok = check_project_structure()
    env_ok = check_environment()

    print("\n" + "=" * 55)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 55)

    if imports_ok and structure_ok and env_ok:
        print("🎉 All checks passed! Your setup is ready.")
        print("\n🏃 Next steps:")
        print("1. Configure your .env file with API keys")
        print("2. Start Qdrant: docker run -p 6333:6333 qdrant/qdrant")
        print("3. Run the server: python -m uvicorn app.main:app --reload")
        print("4. Visit: http://localhost:8000/docs")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
