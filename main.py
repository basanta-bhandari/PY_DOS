from utils import *

def main():
    """Main entry point for PyDOS"""
    clear_terminal()
    print(PY_DOS)
    print("PY DOS [Version 1.2] ")
    print("Enter help for instruction menu. ")
    print("Please use quit for a better experience ")
    load_filesystem()
    while True:
        try:
            print("\n")
            process_commands()
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()