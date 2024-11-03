import contextlib
import traceback
from typing import Any
import docker
from docker.models import containers
import pytest

_port: int = 8800


def _wait_until_uvicorn_run(container: containers.Container):
    logs = container.logs(stream=True)
    for log in logs:
        if b"Uvicorn running on" in log:
            break
    logs.close()


class RegistryContainer(contextlib.AbstractContextManager["RegistryContainer"]):
    url: str

    def __init__(self, docker_client: docker.DockerClient) -> None:
        global _port
        self.port = _port
        _port += 1
        self.client = docker_client
        self.network = self.client.networks.create(name="gcn")
        self.image = self.client.images.build(path=".", tag="gc")[0]
        self._container = self.client.containers.run(
            image=self.image,
            hostname="registry",
            command=f"uvicorn 'registry.main:app' --host '0.0.0.0' --port {self.port}",
            ports={f"{self.port}/tcp": self.port},
            network=self.network.name,
            detach=True,
        )
        _wait_until_uvicorn_run(self._container)
        self.url = f"http://0.0.0.0:{self.port}"

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any | None,
    ) -> bool | None:
        self._container.stop()
        self._container.remove()
        self.network.remove()


class CollectorContainer(contextlib.AbstractContextManager["CollectorContainer"]):
    def __init__(self, registry: RegistryContainer) -> None:
        global _port
        port = _port
        _port += 1
        self.registry = registry
        self._container = self.registry.client.containers.run(
            image=self.registry.image,
            command=f"uvicorn 'collector.main:app' --host '0.0.0.0' --port {port}",
            environment={
                "COLLECTOR_DB_URI": "sqlite:///sqlite.db",
                "COLLECTOR_SELF_URL": f"http://0.0.0.0:{port}",
                "COLLECTOR_REGISTRY_URL": f"http://registry:{self.registry.port}",
                "COLLECTOR_POSITION_X": f"{port - 8800}",
                "COLLECTOR_POSITION_Y": f"{port - 8800}",
            },
            ports={f"{port}/tcp": port},
            network=self.registry.network.name,
            detach=True,
        )
        _wait_until_uvicorn_run(self._container)
        self.url = f"http://0.0.0.0:{port}"

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: Any | None,
    ) -> bool | None:
        self._container.stop()
        self._container.remove()


@pytest.fixture(scope="module")
def docker_client():
    client = docker.from_env()
    try:
        yield client
    finally:
        client.close()  # type: ignore


@pytest.fixture(scope="module")
def registry(docker_client: docker.DockerClient):
    registry = RegistryContainer(docker_client)
    try:
        yield registry.__enter__()
    except Exception:
        traceback.print_exc()
    finally:
        registry.__exit__(None, None, None)


@pytest.fixture(scope="module")
def collector(registry: RegistryContainer):
    collector = CollectorContainer(registry)
    try:
        yield collector.__enter__()
    except Exception:
        traceback.print_exc()
    finally:
        collector.__exit__(None, None, None)

@pytest.fixture(scope='module')
def anyio_backend():
    return 'asyncio'
