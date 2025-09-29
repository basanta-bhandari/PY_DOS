from utils import *

def main():
    try:
        clear_terminal()
        print(PY_DOS)
        print("PY DOS [Version Beta]")
        print("ENTER 'help' TO GET STARTED.")
        setup_readline()
        load_filesystem()
        while True:
            try:
                print()
                process_commands()
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit safely.")
            except Exception as e:
                print(f"An error occurred: {e}")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()