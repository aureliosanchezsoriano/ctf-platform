import logging
import docker
import docker.errors
from app.core.config import get_settings
from app.core.security import generate_flag

logger = logging.getLogger(__name__)
settings = get_settings()

# Module-level Docker client — one connection reused across requests
_docker_client: docker.DockerClient | None = None


def get_docker_client() -> docker.DockerClient:
    global _docker_client
    if _docker_client is None:
        _docker_client = docker.from_env()
    return _docker_client


def _container_name(user_id: str, challenge_slug: str) -> str:
    """Deterministic container name per user per challenge."""
    safe_user = user_id.replace("-", "")[:12]
    return f"ctf_{safe_user}_{challenge_slug}"


def _network_name(user_id: str) -> str:
    """One isolated network per user."""
    safe_user = user_id.replace("-", "")[:12]
    return f"ctf_net_{safe_user}"


def start_challenge(
    user_id: str,
    challenge_slug: str,
    docker_config: dict,
) -> dict:
    """
    Launch a challenge container for a user.
    Returns {"url": "http://...", "container_id": "..."} or raises.
    """
    client = get_docker_client()
    container_name = _container_name(user_id, challenge_slug)
    network_name = _network_name(user_id)

    # If container already running, return its info
    try:
        existing = client.containers.get(container_name)
        if existing.status == "running":
            port = docker_config["port"]
            host_port = existing.ports.get(f"{port}/tcp", [{}])[0].get("HostPort")
            logger.info(f"Container already running: {container_name}")
            return {
                "url": f"http://localhost:{host_port}",
                "container_id": existing.short_id,
                "status": "already_running",
            }
        else:
            # Stale container — remove it
            existing.remove(force=True)
    except docker.errors.NotFound:
        pass

    # Ensure isolated network exists for this user
    try:
        client.networks.get(network_name)
    except docker.errors.NotFound:
        client.networks.create(
            network_name,
            driver="bridge",
            internal=False,  # needs internet access for some challenges
            labels={"ctf.user": user_id},
        )

    # Generate the flag for this user/challenge
    flag = generate_flag(user_id, challenge_slug)

    # Launch the container
    container = client.containers.run(
        image=docker_config["image"],
        name=container_name,
        detach=True,
        environment={"CTF_FLAG": flag},
        network=network_name,
        ports={f"{docker_config['port']}/tcp": None},  # random host port
        mem_limit=docker_config.get("memory", "128m"),
        cpu_quota=int(float(docker_config.get("cpu", "0.5")) * 100_000),
        labels={
            "ctf.user": user_id,
            "ctf.challenge": challenge_slug,
            "ctf.managed": "true",
        },
        restart_policy={"Name": "no"},
    )

    container.reload()
    port = docker_config["port"]
    host_port = container.ports[f"{port}/tcp"][0]["HostPort"]

    logger.info(f"Started container: {container_name} on port {host_port}")
    return {
        "url": f"http://localhost:{host_port}",
        "container_id": container.short_id,
        "status": "started",
    }


def stop_challenge(user_id: str, challenge_slug: str) -> bool:
    """Stop and remove a challenge container."""
    client = get_docker_client()
    container_name = _container_name(user_id, challenge_slug)
    try:
        container = client.containers.get(container_name)
        container.remove(force=True)
        logger.info(f"Removed container: {container_name}")
        return True
    except docker.errors.NotFound:
        return False


def stop_all_for_user(user_id: str) -> int:
    """Stop all challenge containers for a user. Returns count removed."""
    client = get_docker_client()
    containers = client.containers.list(
        filters={"label": f"ctf.user={user_id}"}
    )
    count = 0
    for c in containers:
        c.remove(force=True)
        count += 1
    # Clean up the user network
    network_name = _network_name(user_id)
    try:
        network = client.networks.get(network_name)
        network.remove()
    except docker.errors.NotFound:
        pass
    logger.info(f"Removed {count} containers for user {user_id}")
    return count


def get_container_status(user_id: str, challenge_slug: str) -> dict:
    """Return running status and URL of a challenge container."""
    client = get_docker_client()
    container_name = _container_name(user_id, challenge_slug)
    try:
        container = client.containers.get(container_name)
        container.reload()
        if container.status == "running":
            docker_port = list(container.ports.keys())[0]
            host_port = container.ports[docker_port][0]["HostPort"]
            return {
                "running": True,
                "url": f"http://localhost:{host_port}",
                "container_id": container.short_id,
                "status": container.status,
            }
        return {"running": False, "status": container.status}
    except docker.errors.NotFound:
        return {"running": False, "status": "not_found"}


def list_all_containers() -> list[dict]:
    """List all CTF-managed containers. Used by admin panel."""
    client = get_docker_client()
    containers = client.containers.list(
        all=True,
        filters={"label": "ctf.managed=true"}
    )
    result = []
    for c in containers:
        result.append({
            "name": c.name,
            "status": c.status,
            "user": c.labels.get("ctf.user", "unknown"),
            "challenge": c.labels.get("ctf.challenge", "unknown"),
            "short_id": c.short_id,
        })
    return result
