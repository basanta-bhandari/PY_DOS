from utils import *

if __name__ == "__main__":
    clear_terminal()
    print(PY_DOS)
    print("PY DOS [Version Beta]")
    print("ENTER 'help' TO GET STARTED.")
    setup_readline()  # Add this line
    load_filesystem()
    while True:
        try:
            print("\n")
            process_commands()
        except KeyboardInterrupt:
            break