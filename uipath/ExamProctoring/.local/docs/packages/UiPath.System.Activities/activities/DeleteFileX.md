# Delete File

`UiPath.Core.Activities.DeleteFileX`

Deletes the specified file.

**Package:** `UiPath.System.Activities`
**Category:** System > File

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Path` | File (local path) | `InArgument` | `string` | Yes* | - | Full path of the file to delete. Overload group: `Path`. |
| `FileResource` | File | `InArgument` | `IResource` | Yes* | - | Resource reference to the file to delete, used when `Path` is empty. A folder resource is rejected while the folder exists. Overload group: `FileResource`. |

## XAML Example

```xml
<ui:DeleteFileX
    DisplayName="Delete File"
    Path="C:\temp\old-report.txt" />
```

`xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"`

## Notes

- This activity is Windows-only.
- If there is no file at the path and its folder exists, nothing happens and no error is raised. If the folder does not exist, the activity fails.
- A path that points to a folder fails with `The provided path points to a folder, not a file.`; neither a path nor a resource fails with `File path is missing. Provide either a file path or a file resource.`
