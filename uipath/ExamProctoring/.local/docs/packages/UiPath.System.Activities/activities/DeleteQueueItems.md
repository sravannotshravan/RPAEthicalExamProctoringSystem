# Delete Queue Items

`UiPath.Core.Activities.DeleteQueueItems`

Deletes items with the New state from a specified queue.

**Package:** `UiPath.System.Activities`
**Category:** Queues

## Properties

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `QueueItems` | Queue items | `InArgument<IEnumerable<QueueItem>>` | — | The collection of queue items to delete. Only items with status **New** can be deleted. |

## XAML Example

```xml
<ui:DeleteQueueItems
    QueueItems="[itemsToDelete]"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities" />
```

## Notes

- Requires an active Orchestrator connection. The robot must be connected to Orchestrator at runtime.
- Only queue items with status **New** can be deleted. Attempting to delete items in other states (In Progress, Successful, Failed, etc.) will result in an error.
- Use **Get Queue Items** to retrieve the collection of items to pass to this activity.
- The Orchestrator folder comes from each `QueueItem` in `QueueItems`; all items must share the same folder, or the activity throws before deleting any of them. A `FolderPath` left over from older XAML no longer selects the folder, but its expression is still evaluated before the activity runs — remove it.
