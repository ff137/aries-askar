import os

from pytest import fixture, mark

from aries_askar import (
    KeyAlg,
    Key,
    Store,
)


TEST_STORE_URI = os.getenv("TEST_STORE_URI", "sqlite://:memory:")
TEST_ENTRY = {
    "category": "test category",
    "name": "test name",
    "value": b"test_value",
    "tags": {"~plaintag": "a", "enctag": {"b", "c"}},
}


@fixture
async def store() -> Store:
    key = Store.generate_raw_key(b"00000000000000000000000000000My1")
    store = await Store.provision(TEST_STORE_URI, "raw", key, recreate=True)
    yield store
    await store.close(remove=True)


@mark.asyncio
async def test_insert_update(store: Store):

    async with store as session:
        # Insert a new entry
        await session.insert(
            TEST_ENTRY["category"],
            TEST_ENTRY["name"],
            TEST_ENTRY["value"],
            TEST_ENTRY["tags"],
        )

        # Count rows by category and (optional) tag filter
        assert (
            await session.count(
                TEST_ENTRY["category"], {"~plaintag": "a", "enctag": "b"}
            )
        ) == 1

        # Fetch an entry by category and name
        found = await session.fetch(TEST_ENTRY["category"], TEST_ENTRY["name"])
        assert dict(found) == TEST_ENTRY

        # Fetch entries by category and tag filter
        found = await session.fetch_all(
            TEST_ENTRY["category"], {"~plaintag": "a", "enctag": "b"}
        )
        assert len(found) == 1 and dict(found[0]) == TEST_ENTRY

        # Remove entry
        await session.remove(TEST_ENTRY["category"], TEST_ENTRY["name"])
        found = await session.fetch(TEST_ENTRY["category"], TEST_ENTRY["name"])
        assert found is None


@mark.asyncio
async def test_remove_all(store: Store):

    async with store as session:
        # Insert a new entry
        await session.insert(
            TEST_ENTRY["category"],
            TEST_ENTRY["name"],
            TEST_ENTRY["value"],
            TEST_ENTRY["tags"],
        )

        # Remove using remove_all
        await session.remove_all(
            TEST_ENTRY["category"],
            # note: this query syntax is optional
            {"~plaintag": "a", "$and": [{"enctag": "b"}, {"enctag": "c"}]},
        ),

        # Check removed
        found = await session.fetch(TEST_ENTRY["category"], TEST_ENTRY["name"])
        assert found is None


@mark.asyncio
async def test_scan(store: Store):

    async with store as session:
        await session.insert(
            TEST_ENTRY["category"],
            TEST_ENTRY["name"],
            TEST_ENTRY["value"],
            TEST_ENTRY["tags"],
        )

    # Scan entries by category and (optional) tag filter)
    rows = await store.scan(
        TEST_ENTRY["category"], {"~plaintag": "a", "enctag": "b"}
    ).fetch_all()
    assert len(rows) == 1 and dict(rows[0]) == TEST_ENTRY


@mark.asyncio
async def test_transaction(store: Store):
    async with store.transaction() as txn:

        # Insert a new entry
        await txn.insert(
            TEST_ENTRY["category"],
            TEST_ENTRY["name"],
            TEST_ENTRY["value"],
            TEST_ENTRY["tags"],
        )

        # Count rows by category and (optional) tag filter
        assert (
            await txn.count(TEST_ENTRY["category"], {"~plaintag": "a", "enctag": "b"})
        ) == 1

        # Fetch an entry by category and name
        found = await txn.fetch(TEST_ENTRY["category"], TEST_ENTRY["name"])
        assert dict(found) == TEST_ENTRY

        # Fetch entries by category and tag filter
        found = await txn.fetch_all(
            TEST_ENTRY["category"], {"~plaintag": "a", "enctag": "b"}
        )
        assert len(found) == 1 and dict(found[0]) == TEST_ENTRY

        await txn.commit()

    # Check the transaction was committed
    async with store.session() as session:
        found = await session.fetch(TEST_ENTRY["category"], TEST_ENTRY["name"])
        assert dict(found) == TEST_ENTRY


@mark.asyncio
async def test_key_store(store: Store):
    # test key operations in a new session
    async with store as session:
        # Create a new keypair
        keypair = Key.generate(KeyAlg.ED25519)

        # Store keypair
        key_name = "testkey"
        await session.insert_key(
            key_name, keypair, metadata="metadata", tags={"a": "b"}
        )

        # Fetch keypair
        fetch_key = await session.fetch_key(key_name)
        assert fetch_key and fetch_key.name == key_name and fetch_key.tags == {"a": "b"}

        # Update keypair
        await session.update_key(key_name, metadata="updated metadata", tags={"a": "c"})

        # Fetch keypair
        fetch_key = await session.fetch_key(key_name)
        assert fetch_key and fetch_key.name == key_name and fetch_key.tags == {"a": "c"}

        # Check key equality
        thumbprint = keypair.get_jwk_thumbprint()
        assert fetch_key.key.get_jwk_thumbprint() == thumbprint

        # Fetch with filters
        keys = await session.fetch_all_keys(
            alg=KeyAlg.ED25519, thumbprint=thumbprint, tag_filter={"a": "c"}, limit=1
        )
        assert len(keys) == 1 and keys[0].name == key_name

        # Remove
        await session.remove_key(key_name)
        assert await session.fetch_key(key_name) is None


@mark.asyncio
async def test_profile(store: Store):
    profile = await store.create_profile()
    await store.remove_profile(profile)
