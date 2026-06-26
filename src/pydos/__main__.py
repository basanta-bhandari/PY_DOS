import sys
from pydos.core import display_loading_screen, display_home, process_commands

def main():
    try:
        display_loading_screen()
        display_home()
        while True:
            process_commands()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting PY DOS...")
        sys.exit(0)

if __name__ == "__main__":
    main()