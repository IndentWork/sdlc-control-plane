"""
Service Bus sender — publishes messages to the sdlc-events topic.

The namespace is derived from the tenant's tier and resource_code:
  shared    → sb-sdlc-shared-{env}
  dedicated → sb-sdlc-{resource_code}-{env}

The action field is set as an application property so Service Bus can route
the message to the correct subscription based on SQL filter rules.

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
    Publish a message to the sdlc-events topic.
    The action field (from payload) is set as an application property so
    Service Bus subscriptions can filter on it.
    Opens a connection, publishes, then closes — no long-lived connection held.
    """
    namespace = _namespace_for(tier, resource_code)
    credential = DefaultAzureCredential()

    async with ServiceBusClient(namespace, credential) as client:
        async with client.get_topic_sender("sdlc-events") as sender:
            message = ServiceBusMessage(
                json.dumps(payload),
                application_properties={"action": payload.get("action")}
            )
            await sender.send_messages(message)
