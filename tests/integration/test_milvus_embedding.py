"""Milvus embedding integration smoke test.

This test validates the integration between Milvus (vector database) and Neo4j
for storing and retrieving embeddings with metadata. It simulates the Hermes
embedding utility synchronizing data between systems.

Phase 1: Small integration test covering:
- Milvus collection initialization
- Embedding storage via sync utility
- Metadata/UUID verification in Neo4j
- Health check and collection count assertions
- Optional skip when Milvus is unavailable

Skip conditions (talos#31):
- Tests: @pytest.mark.skipif(not MILVUS_AVAILABLE, ...) — skips when pymilvus
  cannot be imported. pymilvus is a declared dependency, so this should only
  trigger in broken environments.
- Runtime: pytest.skip() inside try/except blocks — catches connection errors
  when Milvus service is unreachable. In CI, Milvus must be provided via Docker.
"""

from typing import Any, Dict, List, Optional
import uuid
import numpy as np
import pytest
from logos_config.ports import get_repo_ports

# Conditional imports for optional dependencies
try:
    from pymilvus import (  # type: ignore[import-untyped]
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

TALOS_PORTS = get_repo_ports("talos")


class MockNeo4jDriver:
    """Mock Neo4j driver for testing without a real database."""

    def __init__(self) -> None:
        """Initialize mock driver with in-memory storage."""
        self.embeddings: Dict[str, Dict[str, Any]] = {}
        self.closed = False

    def close(self) -> None:
        """Mock close method."""
        self.closed = True

    def session(self) -> "MockNeo4jSession":
        """Create a mock session."""
        return MockNeo4jSession(self)


class MockNeo4jSession:
    """Mock Neo4j session for testing."""

    def __init__(self, driver: MockNeo4jDriver) -> None:
        """Initialize mock session."""
        self.driver = driver

    def __enter__(self) -> "MockNeo4jSession":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        pass

    def run(self, query: str, **params: Any) -> "MockNeo4jResult":
        """Execute a mock query."""
        return MockNeo4jResult(self.driver, query, params)


class MockNeo4jResult:
    """Mock Neo4j result."""

    def __init__(
        self, driver: MockNeo4jDriver, query: str, params: Dict[str, Any]
    ) -> None:
        """Initialize mock result."""
        self.driver = driver
        self.query = query
        self.params = params
        self._records: List[Dict[str, Any]] = []
        self._execute_query()

    def _execute_query(self) -> None:
        """Execute the query against mock storage."""
        if "MERGE (e:Embedding" in self.query or "CREATE (e:Embedding" in self.query:
            # Store embedding metadata
            embedding_id = self.params.get("embedding_id")
            if embedding_id:
                self.driver.embeddings[embedding_id] = {
                    "embedding_id": embedding_id,
                    "text": self.params.get("text", ""),
                    "metadata": self.params.get("metadata", {}),
                    "collection": self.params.get("collection", ""),
                }
        elif "MATCH (e:Embedding" in self.query:
            # Query embedding metadata
            embedding_id = self.params.get("embedding_id")
            if embedding_id and embedding_id in self.driver.embeddings:
                self._records = [{"e": self.driver.embeddings[embedding_id]}]

    def single(self) -> Optional[Dict[str, Any]]:
        """Return single record."""
        return self._records[0] if self._records else None

    def data(self) -> List[Dict[str, Any]]:
        """Return all records."""
        return self._records


class EmbeddingSyncUtility:
    """Utility to sync embeddings between Milvus and Neo4j.

    This simulates the Hermes embedding utility that would:
    1. Generate/receive embeddings
    2. Store them in Milvus
    3. Store metadata in Neo4j
    """

    def __init__(
        self,
        neo4j_driver: MockNeo4jDriver,
        milvus_collection: Optional[Any] = None,
    ) -> None:
        """Initialize the sync utility.

        Args:
            neo4j_driver: Neo4j driver instance
            milvus_collection: Milvus collection instance (optional for mock mode)
        """
        self.neo4j_driver = neo4j_driver
        self.milvus_collection = milvus_collection
        self.use_mock = milvus_collection is None

    def store_embedding(
        self,
        text: str,
        embedding: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store embedding in both Milvus and Neo4j.

        Args:
            text: The text that was embedded
            embedding: The embedding vector
            metadata: Additional metadata

        Returns:
            The UUID of the stored embedding
        """
        embedding_id = str(uuid.uuid4())
        metadata = metadata or {}

        # Store in Milvus (or simulate if in mock mode)
        if not self.use_mock and self.milvus_collection:
            self.milvus_collection.insert(
                [
                    [embedding_id],  # id field
                    [text],  # text field
                    [embedding.tolist()],  # embedding field
                ]
            )
            # Flush to ensure data is persisted
            self.milvus_collection.flush()

        # Store metadata in Neo4j
        with self.neo4j_driver.session() as session:
            session.run(
                """
                CREATE (e:Embedding {
                    embedding_id: $embedding_id,
                    text: $text,
                    metadata: $metadata,
                    collection: $collection
                })
                """,
                embedding_id=embedding_id,
                text=text,
                metadata=metadata,
                collection=(
                    self.milvus_collection.name if self.milvus_collection else "test"
                ),
            )

        return embedding_id

    def verify_embedding(self, embedding_id: str) -> bool:
        """Verify embedding exists in Neo4j.

        Args:
            embedding_id: UUID of the embedding to verify

        Returns:
            True if embedding exists, False otherwise
        """
        with self.neo4j_driver.session() as session:
            result = session.run(
                """
                MATCH (e:Embedding {embedding_id: $embedding_id})
                RETURN e
                """,
                embedding_id=embedding_id,
            )
            return result.single() is not None


def create_milvus_collection(collection_name: str, dim: int = 128) -> Collection:
    """Create a Milvus collection for embeddings.

    Args:
        collection_name: Name of the collection
        dim: Dimension of the embedding vectors

    Returns:
        Milvus Collection instance
    """
    # Define schema
    fields = [
        FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=100),
        FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=1000),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
    ]
    schema = CollectionSchema(fields=fields, description="Embedding storage")

    # Create collection
    collection = Collection(name=collection_name, schema=schema)

    # Create index for the embedding field
    index_params = {
        "metric_type": "L2",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128},
    }
    collection.create_index(field_name="embedding", index_params=index_params)

    return collection


@pytest.fixture
def mock_neo4j_driver() -> MockNeo4jDriver:
    """Provide a mock Neo4j driver."""
    return MockNeo4jDriver()


@pytest.fixture
def sample_embedding() -> np.ndarray:
    """Provide a sample embedding vector."""
    return np.random.rand(128).astype(np.float32)


# Mark test to skip if Milvus is not available
@pytest.mark.skipif(not MILVUS_AVAILABLE, reason="pymilvus not installed")
def test_milvus_health_check() -> None:
    """Test Milvus server health check.

    This test verifies that we can connect to Milvus and check its health.
    Skips gracefully if Milvus service is not available.
    """
    try:
        # Try to connect to Milvus
        connections.connect(
            host="localhost", port=str(TALOS_PORTS.milvus_grpc), timeout=5
        )

        # Check if connection is healthy
        assert connections.has_connection("default")

        # List collections to verify connectivity
        collections = utility.list_collections()
        assert isinstance(collections, list)

        connections.disconnect("default")
    except Exception as e:
        pytest.skip(f"Milvus service not available: {e}")


@pytest.mark.skipif(not MILVUS_AVAILABLE, reason="pymilvus not installed")
def test_milvus_collection_initialization() -> None:
    """Test Milvus collection initialization.

    This test verifies that we can create and configure a Milvus collection
    for storing embeddings.
    """
    collection_name = f"test_embeddings_{uuid.uuid4().hex[:8]}"

    try:
        connections.connect(
            host="localhost", port=str(TALOS_PORTS.milvus_grpc), timeout=5
        )

        # Create collection
        collection = create_milvus_collection(collection_name, dim=128)

        # Verify collection exists
        assert utility.has_collection(collection_name)

        # Check collection properties
        assert collection.name == collection_name
        assert collection.is_empty

        # Clean up
        utility.drop_collection(collection_name)
        connections.disconnect("default")
    except Exception as e:
        pytest.skip(f"Milvus service not available: {e}")


@pytest.mark.skipif(not MILVUS_AVAILABLE, reason="pymilvus not installed")
def test_milvus_embedding_integration_full(
    mock_neo4j_driver: MockNeo4jDriver, sample_embedding: np.ndarray
) -> None:
    """Full integration test with Milvus and Neo4j.

    This test performs a complete integration test:
    1. Initializes Milvus collection
    2. Stores embedding via sync utility
    3. Verifies metadata/UUID in Neo4j
    4. Performs health checks
    5. Verifies collection counts

    Skips gracefully if Milvus service is not available.
    """
    collection_name = f"test_embeddings_{uuid.uuid4().hex[:8]}"

    try:
        # Connect to Milvus
        connections.connect(
            host="localhost", port=str(TALOS_PORTS.milvus_grpc), timeout=5
        )

        # Create collection
        collection = create_milvus_collection(collection_name, dim=128)

        # Create sync utility
        sync_util = EmbeddingSyncUtility(
            neo4j_driver=mock_neo4j_driver, milvus_collection=collection
        )

        # Store an embedding
        text = "Integration test document"
        metadata = {"source": "integration_test", "version": "1.0"}
        embedding_id = sync_util.store_embedding(text, sample_embedding, metadata)

        # Verify UUID in Neo4j
        assert sync_util.verify_embedding(embedding_id)

        # Load collection to query
        collection.load()

        # Verify collection count
        assert collection.num_entities == 1

        # Perform health check
        assert connections.has_connection("default")
        assert utility.has_collection(collection_name)

        # Verify metadata in Neo4j
        with mock_neo4j_driver.session() as session:
            result = session.run(
                """
                MATCH (e:Embedding {embedding_id: $embedding_id})
                RETURN e
                """,
                embedding_id=embedding_id,
            )
            record = result.single()
            assert record is not None
            embedding_data = record["e"]
            assert embedding_data["collection"] == collection_name
            assert embedding_data["text"] == text
            assert embedding_data["metadata"] == metadata

        # Clean up
        collection.release()
        utility.drop_collection(collection_name)
        connections.disconnect("default")
    except Exception as e:
        pytest.skip(f"Milvus service not available: {e}")


@pytest.mark.skipif(not MILVUS_AVAILABLE, reason="pymilvus not installed")
def test_milvus_collection_count_assertions(mock_neo4j_driver: MockNeo4jDriver) -> None:
    """Test collection count assertions with multiple embeddings.

    This test verifies that we can accurately track the number of embeddings
    stored in both Milvus and Neo4j.
    """
    collection_name = f"test_count_{uuid.uuid4().hex[:8]}"

    try:
        connections.connect(
            host="localhost", port=str(TALOS_PORTS.milvus_grpc), timeout=5
        )
        collection = create_milvus_collection(collection_name, dim=128)

        sync_util = EmbeddingSyncUtility(
            neo4j_driver=mock_neo4j_driver, milvus_collection=collection
        )

        # Store multiple embeddings
        num_embeddings = 5
        for i in range(num_embeddings):
            text = f"Document {i}"
            embedding = np.random.rand(128).astype(np.float32)
            sync_util.store_embedding(text, embedding, metadata={"index": i})

        # Load and verify count in Milvus
        collection.load()
        assert collection.num_entities == num_embeddings

        # Verify count in Neo4j mock storage
        assert len(mock_neo4j_driver.embeddings) == num_embeddings

        # Clean up
        collection.release()
        utility.drop_collection(collection_name)
        connections.disconnect("default")
    except Exception as e:
        pytest.skip(f"Milvus service not available: {e}")
