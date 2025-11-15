#!/usr/bin/env python3
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from gateway_server import main

if __name__ == "__main__":
    main()