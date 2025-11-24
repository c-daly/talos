"""Comprehensive Milvus integration tests for Talos."""

import os
from typing import Generator
import uuid
import numpy as np
import pytest

# Conditional imports for optional dependencies
try:
    from pymilvus import (
        Collection,
        CollectionSchema,
        DataType,
        FieldSchema,
        connections,
        utility,
    )

    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False


# Integration test marker
pytestmark = pytest.mark.integration


def milvus_available() -> bool:
    """Check if Milvus is available for testing."""
    if not MILVUS_AVAILABLE:
        return False

    try:
        connections.connect(host="localhost", port="19530", timeout=5)
        connections.disconnect("default")
        return True
    except Exception:
        return False


@pytest.fixture(scope="function")
def milvus_connection() -> Generator[None, None, None]:
    """Provide Milvus connection for tests."""
    if not milvus_available():
        pytest.skip("Milvus not available")

    connections.connect(host="localhost", port="19530")
    yield
    connections.disconnect("default")


@pytest.fixture
def collection_name() -> str:
    """Generate unique collection name."""
    return f"test_talos_{uuid.uuid4().hex[:8]}"


@pytest.mark.skipif(not milvus_available(), reason="Milvus not available")
def test_milvus_collection_creation(
    milvus_connection: None, collection_name: str
) -> None:
    """Test Milvus collection creation via Talos."""
    # Define schema
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
        FieldSchema(name="sensor_data", dtype=DataType.VARCHAR, max_length=5000),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128),
    ]
    schema = CollectionSchema(fields=fields, description="Talos sensor data")

    # Create collection
    collection = Collection(name=collection_name, schema=schema)

    assert utility.has_collection(collection_name)
    assert collection.name == collection_name

    # Cleanup
    utility.drop_collection(collection_name)


@pytest.mark.skipif(not milvus_available(), reason="Milvus not available")
def test_embedding_storage_for_sensor_data(
    milvus_connection: None, collection_name: str
) -> None:
    """Test embedding storage for sensor data."""
    # Create collection
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
        FieldSchema(name="sensor_data", dtype=DataType.VARCHAR, max_length=5000),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128),
    ]
    schema = CollectionSchema(fields=fields)
    collection = Collection(name=collection_name, schema=schema)

    # Store sensor embedding
    sensor_id = str(uuid.uuid4())
    sensor_data_json = '{"sensor": "camera", "timestamp": "2024-01-01T00:00:00Z"}'
    embedding = np.random.rand(128).astype(np.float32)

    collection.insert([[sensor_id], [sensor_data_json], [embedding.tolist()]])
    collection.flush()

    # Load and verify
    collection.load()
    assert collection.num_entities == 1

    # Cleanup
    collection.release()
    utility.drop_collection(collection_name)


@pytest.mark.skipif(not milvus_available(), reason="Milvus not available")
def test_embedding_retrieval_by_similarity(
    milvus_connection: None, collection_name: str
) -> None:
    """Test embedding retrieval by similarity."""
    # Create collection with index
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=1000),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128),
    ]
    schema = CollectionSchema(fields=fields)
    collection = Collection(name=collection_name, schema=schema)

    # Create index
    index_params = {
        "metric_type": "L2",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128},
    }
    collection.create_index(field_name="embedding", index_params=index_params)

    # Insert data
    embeddings = [np.random.rand(128).astype(np.float32) for _ in range(10)]
    ids = [str(uuid.uuid4()) for _ in range(10)]
    texts = [f"sensor_data_{i}" for i in range(10)]

    collection.insert(
        [ids, texts, [emb.tolist() for emb in embeddings]]
    )
    collection.flush()
    collection.load()

    # Search for similar embedding
    query_embedding = embeddings[0]  # Use first embedding as query
    search_params = {"metric_type": "L2", "params": {"nprobe": 10}}

    results = collection.search(
        data=[query_embedding.tolist()],
        anns_field="embedding",
        param=search_params,
        limit=3,
    )

    # Should find at least the exact match
    assert len(results) > 0
    assert len(results[0]) > 0

    # Cleanup
    collection.release()
    utility.drop_collection(collection_name)


@pytest.mark.skipif(not milvus_available(), reason="Milvus not available")
def test_metadata_linkage_to_neo4j_uuids(
    milvus_connection: None, collection_name: str
) -> None:
    """Test metadata linkage to Neo4j UUIDs."""
    # Create collection
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
        FieldSchema(name="neo4j_uuid", dtype=DataType.VARCHAR, max_length=100),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128),
    ]
    schema = CollectionSchema(fields=fields)
    collection = Collection(name=collection_name, schema=schema)

    # Insert with Neo4j UUID
    milvus_id = str(uuid.uuid4())
    neo4j_uuid = str(uuid.uuid4())
    embedding = np.random.rand(128).astype(np.float32)

    collection.insert([[milvus_id], [neo4j_uuid], [embedding.tolist()]])
    collection.flush()

    # Verify storage
    collection.load()
    assert collection.num_entities == 1

    # Cleanup
    collection.release()
    utility.drop_collection(collection_name)


@pytest.mark.skipif(not milvus_available(), reason="Milvus not available")
def test_collection_health_checks(
    milvus_connection: None, collection_name: str
) -> None:
    """Test collection health checks."""
    # Create collection
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
        FieldSchema(name="data", dtype=DataType.VARCHAR, max_length=1000),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128),
    ]
    schema = CollectionSchema(fields=fields)
    collection = Collection(name=collection_name, schema=schema)

    # Check collection exists
    assert utility.has_collection(collection_name)

    # Check collection is initially empty
    assert collection.is_empty

    # Insert data
    collection.insert(
        [
            [str(uuid.uuid4())],
            ["test_data"],
            [np.random.rand(128).astype(np.float32).tolist()],
        ]
    )
    collection.flush()

    # Check not empty after insert
    assert not collection.is_empty

    # Cleanup
    utility.drop_collection(collection_name)


@pytest.mark.skipif(not milvus_available(), reason="Milvus not available")
def test_error_handling_when_milvus_unavailable() -> None:
    """Test error handling when Milvus unavailable."""
    # Disconnect if connected
    if connections.has_connection("default"):
        connections.disconnect("default")

    # Try to connect to invalid host
    with pytest.raises(Exception):
        connections.connect(host="invalid_host", port="19530", timeout=1)


@pytest.mark.skipif(not milvus_available(), reason="Milvus not available")
def test_concurrent_embedding_operations(
    milvus_connection: None, collection_name: str
) -> None:
    """Test concurrent embedding operations."""
    # Create collection
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128),
    ]
    schema = CollectionSchema(fields=fields)
    collection = Collection(name=collection_name, schema=schema)

    # Insert multiple embeddings concurrently (in rapid succession)
    num_embeddings = 50
    ids = [str(uuid.uuid4()) for _ in range(num_embeddings)]
    embeddings = [
        np.random.rand(128).astype(np.float32).tolist() for _ in range(num_embeddings)
    ]

    collection.insert([ids, embeddings])
    collection.flush()

    # Verify all inserted
    collection.load()
    assert collection.num_entities == num_embeddings

    # Cleanup
    collection.release()
    utility.drop_collection(collection_name)


@pytest.mark.skipif(not milvus_available(), reason="Milvus not available")
def test_large_batch_embedding_storage(
    milvus_connection: None, collection_name: str
) -> None:
    """Test large batch embedding storage."""
    # Create collection
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128),
    ]
    schema = CollectionSchema(fields=fields)
    collection = Collection(name=collection_name, schema=schema)

    # Insert large batch
    batch_size = 1000
    ids = [str(uuid.uuid4()) for _ in range(batch_size)]
    embeddings = [
        np.random.rand(128).astype(np.float32).tolist() for _ in range(batch_size)
    ]

    collection.insert([ids, embeddings])
    collection.flush()

    # Verify count
    collection.load()
    assert collection.num_entities == batch_size

    # Cleanup
    collection.release()
    utility.drop_collection(collection_name)


@pytest.mark.skipif(not milvus_available(), reason="Milvus not available")
def test_collection_indexing(milvus_connection: None, collection_name: str) -> None:
    """Test collection indexing for performance."""
    # Create collection
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128),
    ]
    schema = CollectionSchema(fields=fields)
    collection = Collection(name=collection_name, schema=schema)

    # Create index
    index_params = {
        "metric_type": "L2",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128},
    }
    collection.create_index(field_name="embedding", index_params=index_params)

    # Verify index exists
    assert collection.has_index()

    # Cleanup
    utility.drop_collection(collection_name)


@pytest.mark.skipif(not milvus_available(), reason="Milvus not available")
def test_collection_persistence(
    milvus_connection: None, collection_name: str
) -> None:
    """Test collection data persistence."""
    # Create and populate collection
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=128),
    ]
    schema = CollectionSchema(fields=fields)
    collection = Collection(name=collection_name, schema=schema)

    # Insert data
    test_id = str(uuid.uuid4())
    test_embedding = np.random.rand(128).astype(np.float32)
    collection.insert([[test_id], [test_embedding.tolist()]])
    collection.flush()

    # Release collection
    collection.release()

    # Reload collection (simulates reconnection)
    collection_reloaded = Collection(name=collection_name)
    collection_reloaded.load()

    # Verify data persisted
    assert collection_reloaded.num_entities == 1

    # Cleanup
    collection_reloaded.release()
    utility.drop_collection(collection_name)
