#!python
"""
PyDOS Boot Script - Fallback executable
This serves as a backup method if entry_points don't work
"""

import sys
import os

def main():
    """Bootstrap the PyDOS main function"""
    try:
        # Try to import and run the main function
        import main as pydos_main
        pydos_main.main()
    except ImportError:
        # If direct import fails, try adding current directory to path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        sys.path.insert(0, parent_dir)
        
        try:
            import main as pydos_main
            pydos_main.main()
        except ImportError as e:
            print(f"Error: Could not import PyDOS modules: {e}")
            print("Please ensure PyDOS is properly installed.")
            sys.exit(1)
    except Exception as e:
        print(f"Error starting PyDOS: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()