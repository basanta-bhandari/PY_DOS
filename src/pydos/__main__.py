import sys
from .display import display_loading_screen, display_home
from .fs.persistence import setup_readline
from .shell.pipeline import process_commands
from .shell.builtins import seed_apps

def main():
    try:
        setup_readline()
        display_loading_screen()
        seed_apps()
        display_home()
        while True:
            try:
                process_commands()
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit.")
            except Exception as e:
                print(f"Error: {e}")
    except (KeyboardInterrupt, EOFError):
        print("\nExiting PY DOS...")
        sys.exit(0)

if __name__ == "__main__":
    main()
