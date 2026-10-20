# File Change Trigger

`UiPath.Core.Activities.FileChangeTriggerV3`

Triggers when a file system change matching the configured path, filter, and change type is detected.

**Package:** `UiPath.System.Activities`
**Category:** Triggers

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Path` | Path | `InArgument` | `string` | Yes | - | File or folder path to monitor. Environment variables are expanded at runtime. |
| `FileNameFilter` | File name filter | `InArgument` | `string` | No | Empty | File name filter passed to the file watcher. If `Path` is a file and this is empty, the file name is inferred from `Path`. |

### Event

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `NotifyFilters` | Notify filters | `InArgument` | `NotifyFilters` | Yes | `FileName` | File system attributes that raise events. |
| `ChangeType` | Change type | `InArgument` | `WatcherChangeTypes` | Yes | `Changed` | Type of file system change to monitor. |

### Options

| Name | Display Name | Kind | Type | Default | Description |
|------|-------------|------|------|---------|-------------|
| `IncludeSubdirectories` | Include subdirectories | `InArgument` | `bool` | `false` | When `true`, monitors subfolders recursively. |

### Output

| Name | Type | Description |
|------|------|-------------|
| `FileChangeInfo` | `FileChangeInfo` | Trigger argument containing `ChangeType`, `FullPath`, `Name`, `OldFullPath`, and `OldName`. |

## XAML Example

```xml
<ui:FileChangeTriggerV3
    DisplayName="File Change Trigger"
    Path="C:\input"
    FileNameFilter="*.csv"
    NotifyFilters="FileName"
    ChangeType="Created"
    IncludeSubdirectories="False" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This activity is Windows-only.
- `NotifyFilters` and `ChangeType` cannot be zero; validation fails for empty flag values.
- Use this activity inside a trigger scope or a trigger-enabled workflow surface.
- Changes that happen while the trigger is starting are queued and delivered once it is listening, so the first change after the trigger starts is not lost.
- If delivering an event fails, the trigger keeps firing for later changes. Only the first such failure is traced in full.
- Stopping the trigger, for example when its scope completes or is cancelled, waits at most about 4 seconds for the file watchers to shut down. If the watched location is an unresponsive network share, shutdown finishes in the background and a warning is traced.
