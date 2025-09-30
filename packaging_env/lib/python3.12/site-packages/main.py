#!/usr/bin/env python3
"""
PyDOS Main Entry Point
Handles various installation scenarios and import issues
"""

import sys
import os

def bootstrap_imports():
    """Handle different import scenarios"""
    try:
        # Standard import
        import utils
        return utils
    except ImportError:
        # Try adding current directory to path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        try:
            import utils
            return utils
        except ImportError:
            # Last resort: try relative import
            try:
                from . import utils
                return utils
            except ImportError:
                raise ImportError("Could not import utils module")

def main():
    """Main entry point for PyDOS"""
    try:
        # Bootstrap the imports
        utils = bootstrap_imports()
        
        # Start PyDOS
        utils.clear_terminal()
        print(utils.PY_DOS)
        print("PY DOS [Version Beta]")
        print("ENTER 'help' TO GET STARTED.")
        
        # Initialize system
        utils.setup_readline()
        utils.load_filesystem()
        
        # Main loop
        while True:
            try:
                print()
                utils.process_commands()
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit safely.")
                continue
            except Exception as e:
                print(f"An error occurred: {e}")
                continue
                
    except ImportError as e:
        print(f"Error: Could not import required modules: {e}")
        print("Please ensure PyDOS is properly installed.")
        print("\nTry reinstalling with:")
        print("  pip uninstall Py-DOS-B1")
        print("  pip install Py-DOS-B1")
        sys.exit(1)
        
    except Exception as e:
        print(f"Fatal error starting PyDOS: {e}")
        sys.exit(1)

def console_entry_point():
    """Alternative entry point for console scripts"""
    main()

if __name__ == "__main__":
    main()