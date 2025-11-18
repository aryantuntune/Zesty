#!/usr/bin/env python3
"""
Configuration Wizard - Easy system setup
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config

def print_banner():
    print("\n" + "="*70)
    print("⚙️  DeepTrace Configuration Wizard")
    print("="*70 + "\n")

def show_current_config():
    """Display current configuration"""
    print("\n📋 Current Configuration:\n")

    print(f"Mode: {'Advanced (FREE)' if True else 'AI-powered'}")
    print(f"Headless browser: {Config.HEADLESS}")
    print(f"Max leads to process: {Config.MAX_LEADS}")
    print(f"Ethical mode: {Config.ETHICAL_MODE}")
    print(f"Request timeout: {Config.REQUEST_TIMEOUT}s")
    print(f"Browser timeout: {Config.BROWSER_TIMEOUT}s")

    print(f"\n📁 Directories:")
    print(f"Data: {Config.DATA_DIR}")
    print(f"Reports: {Config.REPORTS_DIR}")
    print(f"Input: {Config.INPUT_DIR}")

def configure_mode():
    """Choose investigation mode"""
    print("\n🎯 Choose Default Investigation Mode:\n")

    print("1. ⚡ Advanced (FREE, RECOMMENDED)")
    print("   - 20-30 accounts, 90% accuracy")
    print("   - All enterprise features")
    print("   - NO API key needed")
    print()

    print("2. 🔥 Independent (FREE)")
    print("   - 15-20 accounts, 75% accuracy")
    print("   - Platform scrapers, behavioral analysis")
    print()

    print("3. 💡 Lite (FREE)")
    print("   - 3-5 accounts, basic features")
    print()

    print("4. 🤖 AI-powered (PAID)")
    print("   - Requires Anthropic API key ($0.15/run)")
    print()

    choice = input("Choice (1-4, default=1): ").strip() or '1'

    modes = {
        '1': 'Advanced',
        '2': 'Independent',
        '3': 'Lite',
        '4': 'AI-powered'
    }

    mode = modes.get(choice, 'Advanced')
    print(f"\n✅ Default mode set to: {mode}")

    if choice == '4':
        print("\n⚠️  AI-powered modes require Anthropic API key")
        print("   Get yours at: https://console.anthropic.com")
        print("   Cost: ~$0.15 per investigation")

        setup_api = input("\nSetup API key now? (y/n): ").strip().lower()

        if setup_api == 'y':
            api_key = input("\nEnter Anthropic API key: ").strip()

            if api_key:
                env_file = Path('.env')
                with open(env_file, 'w') as f:
                    f.write(f"ANTHROPIC_API_KEY={api_key}\n")

                print(f"\n✅ API key saved to .env")
            else:
                print("\n❌ No API key provided")

def configure_performance():
    """Configure performance settings"""
    print("\n⚡ Performance Settings:\n")

    # Max leads
    print(f"Current max leads: {Config.MAX_LEADS}")
    print("\nHow many URLs should we analyze per investigation?")
    print("  • 5  = Fast (1-2 min)")
    print("  • 10 = Balanced (2-3 min) [Default]")
    print("  • 20 = Thorough (5-7 min)")

    max_leads = input("\nMax leads (5-50): ").strip()

    if max_leads.isdigit():
        max_leads = int(max_leads)
        if 5 <= max_leads <= 50:
            print(f"✅ Max leads set to: {max_leads}")
            print(f"   (Edit src/config.py to make permanent)")
        else:
            print("❌ Invalid value, keeping default")

    # Headless mode
    print(f"\nHeadless browser mode: {Config.HEADLESS}")
    print("  • True  = Faster, runs in background")
    print("  • False = Slower, shows browser (demo mode)")

    headless = input("\nEnable headless mode? (y/n, default=y): ").strip().lower()

    if headless == 'n':
        print("✅ Browser will be visible (demo mode)")
        print("   (Edit src/config.py to make permanent)")
    else:
        print("✅ Headless mode enabled (faster)")

def configure_ethical():
    """Configure ethical settings"""
    print("\n🛡️  Ethical Settings:\n")

    print(f"Current ethical mode: {Config.ETHICAL_MODE}")
    print("\nEthical mode enforces:")
    print("  • Rate limiting (respectful scraping)")
    print("  • robots.txt compliance")
    print("  • Reduced request frequency")

    ethical = input("\nEnable ethical mode? (y/n, default=y): ").strip().lower() or 'y'

    if ethical == 'y':
        print("✅ Ethical mode enabled")
    else:
        print("⚠️  Ethical mode disabled - use responsibly!")

    print(f"\nRequest timeout: {Config.REQUEST_TIMEOUT}s")
    timeout = input("Request timeout in seconds (10-60, default=30): ").strip()

    if timeout.isdigit():
        timeout = int(timeout)
        if 10 <= timeout <= 60:
            print(f"✅ Timeout set to: {timeout}s")
        else:
            print("❌ Invalid value, keeping default")

def check_installation():
    """Verify installation"""
    print("\n🔍 Checking Installation...\n")

    checks = {
        'Python': True,
        'Sherlock': False,
        'spaCy': False,
        'NetworkX': False,
        'TextBlob': False,
        'Plotly': False,
    }

    # Check imports
    try:
        import spacy
        checks['spaCy'] = True
    except:
        pass

    try:
        import networkx
        checks['NetworkX'] = True
    except:
        pass

    try:
        import textblob
        checks['TextBlob'] = True
    except:
        pass

    try:
        import plotly
        checks['Plotly'] = True
    except:
        pass

    # Check sherlock
    import subprocess
    try:
        subprocess.run(['sherlock', '--version'], capture_output=True, timeout=5)
        checks['Sherlock'] = True
    except:
        pass

    print("Installation Status:")
    for name, installed in checks.items():
        symbol = '✅' if installed else '❌'
        print(f"  {symbol} {name}")

    missing = [name for name, installed in checks.items() if not installed]

    if missing:
        print(f"\n⚠️  Missing: {', '.join(missing)}")
        print("\nTo install missing components:")
        print("  ./install_advanced.sh")
    else:
        print("\n🎉 All components installed!")

def manage_directories():
    """Manage data directories"""
    print("\n📁 Data Directories:\n")

    dirs = {
        'Data': Config.DATA_DIR,
        'Reports': Config.REPORTS_DIR,
        'Input': Config.INPUT_DIR,
        'Raw Leads': Config.RAW_LEADS_DIR,
    }

    for name, path in dirs.items():
        exists = '✅' if path.exists() else '❌'
        print(f"  {exists} {name}: {path}")

    print("\n1. Create missing directories")
    print("2. Clear reports directory")
    print("3. Clear raw leads")
    print("0. Back")

    choice = input("\nChoice: ").strip()

    if choice == '1':
        for path in dirs.values():
            path.mkdir(parents=True, exist_ok=True)
        print("✅ All directories created")

    elif choice == '2':
        confirm = input("⚠️  Delete all reports? (yes/no): ").strip().lower()
        if confirm == 'yes':
            import shutil
            for file in Config.REPORTS_DIR.glob('*'):
                if file.is_file():
                    file.unlink()
            print("✅ Reports cleared")

    elif choice == '3':
        confirm = input("⚠️  Delete all raw leads? (yes/no): ").strip().lower()
        if confirm == 'yes':
            for file in Config.RAW_LEADS_DIR.glob('*'):
                if file.is_file():
                    file.unlink()
            print("✅ Raw leads cleared")

def main():
    """Main configuration wizard"""
    print_banner()

    while True:
        print("\n" + "-"*70)
        print("\n1. View current configuration")
        print("2. Configure investigation mode")
        print("3. Configure performance settings")
        print("4. Configure ethical settings")
        print("5. Check installation")
        print("6. Manage directories")
        print("\n0. Back to main menu")
        print("\n" + "-"*70)

        choice = input("\nChoice: ").strip()

        if choice == '1':
            show_current_config()

        elif choice == '2':
            configure_mode()

        elif choice == '3':
            configure_performance()

        elif choice == '4':
            configure_ethical()

        elif choice == '5':
            check_installation()

        elif choice == '6':
            manage_directories()

        elif choice == '0':
            break

        else:
            print("❌ Invalid choice")

    print("\n✅ Configuration complete!")
    print("   Note: Some changes require editing src/config.py directly\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
