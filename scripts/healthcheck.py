import os
import urllib.request


def main() -> None:
    allowed_hosts = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost")
    host = allowed_hosts.split(",", maxsplit=1)[0].strip() or "localhost"
    request = urllib.request.Request(
        "http://localhost:8000/health",
        headers={"Host": host},
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        if response.status != 200:
            raise RuntimeError(f"health check returned HTTP {response.status}")


if __name__ == "__main__":
    main()
