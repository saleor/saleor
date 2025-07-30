# Webhooks API

Configure event-driven integrations and webhook notifications.

## Available Operations

This category includes 9 operations:

### Queries

#### `webhook`

Look up a webhook by ID. Requires one of the following permissions: MANAGE_APPS, OWNER.

**Returns:** `Webhook`

#### `webhookEvents`

List of all available webhook events.
  
  Requires one of the following permissions: MANAGE_APPS.

**Returns:** `[WebhookEvent!]`

#### `webhookSamplePayload`

Retrieve a sample payload for a given webhook event based on real data. It can be useful for some integrations where sample payload is required.

**Returns:** `JSONString`

### Mutations

#### `eventDeliveryRetry`

Retries event delivery. 
  
  Requires one of the following permissions: MANAGE_APPS.

**Returns:** `EventDeliveryRetry`

#### `webhookCreate`

Creates a new webhook subscription. 
  
  Requires one of the following permissions: MANAGE_APPS, AUTHENTICATED_APP.

**Returns:** `WebhookCreate`

#### `webhookDelete`

Delete a webhook. Before the deletion, the webhook is deactivated to pause any deliveries that are already scheduled. The deletion might fail if delivery is in progress. In such a case, the webhook is not deleted but remains deactivated. 
  
  Requires one of the following permissions: MANAGE_APPS, AUTHENTICATED_APP.

**Returns:** `WebhookDelete`

#### `webhookDryRun`

Performs a dry run of a webhook event. Supports a single event (the first, if multiple provided in the `query`). Requires permission relevant to processed event. 
  
  Requires one of the following permissions: AUTHENTICATED_STAFF_USER.

**Returns:** `WebhookDryRun`

#### `webhookTrigger`

Trigger a webhook event. Supports a single event (the first, if multiple provided in the `webhook.subscription_query`). Requires permission relevant to processed event. Successfully delivered webhook returns `delivery` with status='PENDING' and empty payload. 
  
  Requires one of the following permissions: AUTHENTICATED_STAFF_USER.

**Returns:** `WebhookTrigger`

#### `webhookUpdate`

Updates a webhook subscription. 
  
  Requires one of the following permissions: MANAGE_APPS, AUTHENTICATED_APP.

**Returns:** `WebhookUpdate`

## Usage Examples

*Coming soon - specific examples for this category.*

## Related Types

*Coming soon - related GraphQL types and inputs.*
