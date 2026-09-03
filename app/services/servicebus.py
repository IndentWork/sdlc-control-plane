"""
Service Bus sender — puts messages on the repo-index queue.

The namespace is derived from the tenant's tier and resource_code:
  shared    → sb-sdlc-shared-{env}
  dedicated → sb-sdlc-{resource_code}-{env}

Authentication uses DefaultAzureCredential (Managed Identity in Azure,
az CLI credentials locally). No connection string or key stored in code.
"""
import json
import os

from azure.identity.aio import DefaultAzureCredential
from azure.servicebus.aio import ServiceBusClient
from azure.servicebus import ServiceBusMessage


def _namespace_for(tier: str, resource_code: str) -> str:
    """Derive the Service Bus namespace FQDN from tenant tier and resource_code."""
    env = os.environ.get("ENV", "dev")
    if tier == "shared":
        name = f"sb-sdlc-shared-{env}"
    else:
        name = f"sb-sdlc-{resource_code}-{env}"
    return f"{name}.servicebus.windows.net"


async def send_message(tier: str, resource_code: str, payload: dict) -> None:
    """
    Send a single JSON message to the repo-index queue.
    Opens a connection, sends, then closes — no long-lived connection held.
    """
    namespace = _namespace_for(tier, resource_code)
    credential = DefaultAzureCredential()

    async with ServiceBusClient(namespace, credential) as client:
        async with client.get_queue_sender("repo-index") as sender:
            message = ServiceBusMessage(json.dumps(payload))
            await sender.send_messages(message)
