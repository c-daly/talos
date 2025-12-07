"""Pytest configuration and shared fixtures.

This file imports all Talos fixtures to make them available to all tests
without requiring explicit imports in each test file.

NOTE: Talos is currently a stub/simulation layer. The integration tests here
are minimal because talos doesn't have much functionality yet. As talos grows
to handle real sensor/actuator interfaces and Sophia integration, comprehensive
tests MUST be added. Talos should:
  - Receive plan execution instructions from Sophia
  - Execute actions via sensor/actuator interfaces
  - Report execution results back to Sophia
  - NOT connect directly to Neo4j/Milvus (Sophia owns the world model)

When real functionality is added, ensure integration tests cover the Sophia
communication protocol and all sensor/actuator abstractions.
"""

# Import all fixtures from talos.fixtures to make them available
pytest_plugins = ["talos.fixtures"]
