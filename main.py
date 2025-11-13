from utils import *

def main():
    display_loading_screen()
    setup_readline()
    
    while True:
        try:
            process_commands()
        except KeyboardInterrupt:
            print("\nUse 'quit' command to exit")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()