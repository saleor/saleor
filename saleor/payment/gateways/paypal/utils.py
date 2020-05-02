from paypalcheckoutsdk.core import LiveEnvironment, PayPalHttpClient, SandboxEnvironment


def get_paypal_client(**connection_params):
    """Set up and return PayPal Python SDK environment with PayPal access credentials.

    This sample uses SandboxEnvironment. In production, use LiveEnvironment.
    """
    client_id = connection_params.get("client_id")
    private_key = connection_params.get("private_key")
    sandbox_mode = connection_params.get("sandbox_mode")
    if sandbox_mode:
        environment = SandboxEnvironment(client_id=client_id, client_secret=private_key)
    else:
        environment = LiveEnvironment(client_id=client_id, client_secret=private_key)

    """Returns PayPal HTTP client instance with environment that has access
    credentials context. Use this instance to invoke PayPal APIs, provided the
    credentials have access. """
    return PayPalHttpClient(environment)
