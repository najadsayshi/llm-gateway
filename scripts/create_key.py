
import sys
import asyncio

from app.security import generate_api_key, hash_api_key
from app.db import AsyncSessionLocal
from app.models import APIKey
from app.db import engine




async def main():
    # Read the API key name from the command line or prompt the user
    if len(sys.argv) > 1:
        name = sys.argv[1]
    else:
        name = input("Enter a name for the API key: ")

    # Generate the API key
    api_key = generate_api_key()

    # Hash the API key
    hashed_key = hash_api_key(api_key)

    # Create a database record
    row = APIKey(
        key_hash=hashed_key,
        key_prefix=api_key[:16],
        name=name
    )

    # Save the record to the database
    async with AsyncSessionLocal() as session:
        session.add(row)
        await session.commit()
    await engine.dispose()
    # Display the full key once
    print(f"API key name: {name}")
    print(f"API key: {api_key}")
    print("Save this key now. It cannot be shown again.")


if __name__ == "__main__":
    asyncio.run(main())

#broski 