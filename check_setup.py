#!/usr/bin/env python3
"""
Simple setup verification script for the Invoice Reimbursement System.
"""

import sys
from pathlib import Path


def check_project_structure():
    """Check if project structure is correct."""
    print("🏗️  Checking project structure...")

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
    venv_path = Path(__file__).parent / "venv"

    if not env_example.exists():
        print("❌ .env.example file not found")
        return False
    else:
        print("✅ .env.example file found")

    if not venv_path.exists():
        print("❌ Virtual environment not found")
        return False
    else:
        print("✅ Virtual environment found")

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
    structure_ok = check_project_structure()
    env_ok = check_environment()

    print("\n" + "=" * 55)
    print("📋 VERIFICATION SUMMARY")
    print("=" * 55)

    if structure_ok and env_ok:
        print("🎉 Basic setup checks passed!")
        print("\n🏃 Next steps:")
        print("1. Configure your .env file with API keys")
        print("2. Start Qdrant: docker run -p 6333:6333 qdrant/qdrant")
        print("3. Run the server: python -m uvicorn app.main:app --reload")
        print("4. Visit: http://localhost:8000/docs")
        print("\n📚 Read the README.md for detailed instructions")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
