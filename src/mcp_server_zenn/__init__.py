import asyncio

from . import server


def main():
    asyncio.run(server.serve())


__all__ = ["main", "server"]
