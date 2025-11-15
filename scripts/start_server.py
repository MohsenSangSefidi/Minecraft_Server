#!/usr/bin/env python3
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from main import ForgeServerApp

if __name__ == "__main__":
    app = ForgeServerApp()
    app.run()