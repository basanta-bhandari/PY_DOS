from utils import *

if __name__ == "__main__":
    clear_terminal()
    print(PY_DOS)
    print("PY DOS [Version 1.0]")
    while True:
        try:
            process_commands()
        except KeyboardInterrupt:
            break