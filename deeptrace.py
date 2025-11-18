#!/usr/bin/env python3
"""
DeepTrace - Interactive Navigation System
Choose your investigation mode easily!
"""

import os
import sys
from pathlib import Path

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')

def print_banner():
    """Display main banner"""
    banner = """
    ╔════════════════════════════════════════════════════════════╗
    ║                                                            ║
    ║             🔍 DEEPTRACE - OSINT Platform                  ║
    ║          Professional Intelligence Gathering              ║
    ║                                                            ║
    ╚════════════════════════════════════════════════════════════╝
    """
    print(banner)

def print_modes():
    """Display available modes"""
    print("\n📋 INVESTIGATION MODES:\n")
    print("─" * 70)

    print("\n🚀 100% FREE MODES (NO API KEY REQUIRED):\n")

    print("1. 🤖 ADVANCED v3 [RECOMMENDED - WITH LOCAL AI!]")
    print("   • Pre-investigation questionnaire (precision targeting!)")
    print("   • Local AI reasoning (Hugging Face - FREE!)")
    print("   • Interactive account verification")
    print("   • 11 enterprise features + AI intelligence")
    print("   • 100% accuracy (AI + user verification)")
    print("   • Cost: $0.00\n")

    print("2. ⚡ ADVANCED v2 [Manual Filtering]")
    print("   • Interactive account verification (filters false positives!)")
    print("   • 100% accuracy (user confirms each account)")
    print("   • 11 enterprise features + smart filtering")
    print("   • Filters out people with same name")
    print("   • Cost: $0.00\n")

    print("3. ⚡ ADVANCED (classic)")
    print("   • 20-30 accounts found")
    print("   • 90% accuracy")
    print("   • 11 enterprise features (Database, NLP, ML, Graphs, etc.)")
    print("   • 100% FREE forever")
    print("   • Cost: $0.00\n")

    print("─" * 70)
    print("\n🛠️  UTILITIES:\n")

    print("4. 📊 View Database / Past Investigations")
    print("5. 🔔 Setup Monitoring / Alerts")
    print("6. ⚙️  System Configuration")
    print("7. 📚 Documentation / Help")
    print("8. 🧪 Test Installation")

    print("\n0. ❌ Exit")
    print("\n" + "─" * 70)

def run_mode(choice):
    """Execute selected mode"""
    modes = {
        '1': ('main_advanced_v3.py', 'Advanced Mode v3 (AI + Profiling)'),
        '2': ('main_advanced_v2.py', 'Advanced Mode v2 (With Verification)'),
        '3': ('main_advanced.py', 'Advanced Mode (Classic)'),
    }

    if choice in modes:
        script, name = modes[choice]
        print(f"\n🚀 Starting {name}...\n")
        os.system(f"python3 {script}")
        return True

    elif choice == '4':
        print("\n📊 Database Viewer")
        os.system("python3 utils/view_database.py")
        return True

    elif choice == '5':
        print("\n🔔 Monitoring Setup")
        os.system("python3 utils/setup_monitoring.py")
        return True

    elif choice == '6':
        print("\n⚙️  Configuration Wizard")
        os.system("python3 utils/configure.py")
        return True

    elif choice == '7':
        show_documentation()
        return True

    elif choice == '8':
        print("\n🧪 Testing Installation...\n")
        os.system("python3 test_advanced.py")
        input("\nPress Enter to continue...")
        return True

    elif choice == '0':
        print("\n👋 Goodbye!\n")
        return False

    else:
        print("\n❌ Invalid choice. Please try again.")
        input("\nPress Enter to continue...")
        return True

def show_documentation():
    """Display documentation menu"""
    clear_screen()
    print("\n📚 DOCUMENTATION\n")
    print("─" * 70)
    print("\n1. README.md - Main overview & quick start")
    print("2. AI_MODEL_GUIDE.md - AI model selection & training (NEW!)")
    print("3. AI_FEATURES.md - Local AI features guide")
    print("4. README_ADVANCED.md - Advanced mode guide")
    print("5. QUICKSTART_ADVANCED.md - 5-minute tutorial")
    print("6. ADVANCED_FEATURES_V2.md - Complete feature documentation")
    print("7. COST_COMPARISON.md - Cost analysis")
    print("8. IMPROVEMENTS.md - Future enhancements")
    print("9. NAVIGATION.md - Project navigation")
    print("\n0. Back to main menu")
    print("\n" + "─" * 70)

    choice = input("\nOpen which document? (0-9): ").strip()

    docs = {
        '1': 'README.md',
        '2': 'AI_MODEL_GUIDE.md',
        '3': 'AI_FEATURES.md',
        '4': 'README_ADVANCED.md',
        '5': 'QUICKSTART_ADVANCED.md',
        '6': 'ADVANCED_FEATURES_V2.md',
        '7': 'COST_COMPARISON.md',
        '8': 'IMPROVEMENTS.md',
        '9': 'NAVIGATION.md',
    }

    if choice in docs:
        doc = docs[choice]
        if Path(doc).exists():
            os.system(f"less {doc}" if os.name != 'nt' else f"more {doc}")
        else:
            print(f"\n❌ Document {doc} not found.")
            input("\nPress Enter to continue...")

def main():
    """Main interactive menu"""
    while True:
        clear_screen()
        print_banner()
        print_modes()

        choice = input("\n🎯 Choose option (0-8): ").strip()

        if not run_mode(choice):
            break

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user\n")
        sys.exit(0)
