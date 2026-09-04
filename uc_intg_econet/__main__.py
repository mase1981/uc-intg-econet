"""Module entry point for the Rheem EcoNet integration."""

import asyncio

from uc_intg_econet import main

if __name__ == "__main__":
    asyncio.run(main())
