from utils import *

def main():
    clear_terminal()
    print(PY_DOS)
    print("PY DOS [Version Beta]")
    print("ENTER 'help' TO GET STARTED.")
    setup_readline()
    load_filesystem()
    while True:
        try:
            print("\n")
            process_commands()
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()