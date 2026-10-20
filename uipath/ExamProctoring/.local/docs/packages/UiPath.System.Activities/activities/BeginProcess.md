# Run Parallel Process

`UiPath.Core.Activities.BeginProcess`

Starts a UiPath process in the background on the same robot, without waiting for it to complete. The robot looks up the process in the given Orchestrator folder (or, when the calling job was started while the robot was disconnected, among its local packages) and runs it locally, in the session chosen by `TargetSession`. Not supported in unattended jobs. The calling workflow continues immediately after the process is launched. Only input arguments are passed to the target process; output arguments are not supported.

**Package:** `UiPath.System.Activities`
**Category:** Workflow > Invoke

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ProcessName` | Process name | `InArgument` | `string` | Yes | — | The name of the Orchestrator process (when `UsePackage` is `False`) or the package name (when `UsePackage` is `True`). Supports auto-complete from available processes in the configured folder. |
| `FolderPath` | Orchestrator folder path | `InArgument` | `string` | No | — | The Orchestrator folder containing the process or package. Leave unset to use the folder of the calling job; required to be unset when the calling job started while the robot was disconnected (see Notes). |
| `EntryPointPath` | Entry point | `InArgument` | `string` | No | — | The entry point `.xaml` path within the package. Only applicable when `UsePackage` is `True`. Cannot be used when `UsePackage` is `False`. |
| `Arguments` | Arguments | `Dictionary<string, InArgument>` | — | No | `{}` | A dictionary of input arguments to pass to the launched process. Use the **Refresh arguments** menu action to auto-populate from the selected process's schema. Only `In` direction arguments are supported. Use the **Use an expression** menu action to switch to expression mode. |
| `ArgumentsVariable` | Arguments variable | `InArgument` | `Dictionary<string, object>` | No | — | An expression-based alternative to `Arguments`. When set, this takes precedence over the `Arguments` dictionary at runtime. Use the **Use arguments** menu action to switch back to the literal dictionary. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `UsePackage` | Use package | `bool` | `True` | When `True`, the process is identified by its package name and optional entry point. When `False`, the process is identified by its Orchestrator process name. |
| `TargetSession` | Target session | `InvokeProcessTargetSession` | `Current` | The session in which the child process is started. |

## Valid Configurations

| `UsePackage` | `ProcessName` | `EntryPointPath` |
|---|---|---|
| `False` (by process name) | Orchestrator process name | Not allowed (validation error if set) |
| `True` (by package name) | Package name | Optional `.xaml` entry point path |

## XAML Example

```xml
<!-- Start a process by Orchestrator process name (fire and forget) -->
<ui:BeginProcess
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Run Parallel Process"
    UsePackage="False">
  <ui:BeginProcess.ProcessName>
    <InArgument x:TypeArguments="x:String">
      <VisualBasicValue x:TypeArguments="x:String" ExpressionText="&quot;InvoiceProcessor&quot;" />
    </InArgument>
  </ui:BeginProcess.ProcessName>
  <ui:BeginProcess.FolderPath>
    <InArgument x:TypeArguments="x:String">
      <VisualBasicValue x:TypeArguments="x:String" ExpressionText="&quot;Finance/Shared&quot;" />
    </InArgument>
  </ui:BeginProcess.FolderPath>
</ui:BeginProcess>
```

```xml
<!-- Start a process by package name with a specific entry point -->
<ui:BeginProcess
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Run Parallel Process"
    UsePackage="True">
  <ui:BeginProcess.ProcessName>
    <InArgument x:TypeArguments="x:String">
      <VisualBasicValue x:TypeArguments="x:String" ExpressionText="&quot;MyPackage&quot;" />
    </InArgument>
  </ui:BeginProcess.ProcessName>
  <ui:BeginProcess.EntryPointPath>
    <InArgument x:TypeArguments="x:String">
      <VisualBasicValue x:TypeArguments="x:String" ExpressionText="&quot;Main.xaml&quot;" />
    </InArgument>
  </ui:BeginProcess.EntryPointPath>
</ui:BeginProcess>
```

## Notes

- **Fire and forget** — unlike **Invoke Process**, or **Run Job** in any `ExecutionMode` other than `None` (Do not wait), `BeginProcess` does not wait for the launched process to finish. The calling workflow immediately continues after the child process is started.
- **Attended only**: when the calling workflow runs as an unattended job, the robot rejects the call and the activity fails with "Cannot start a parallel process from an unattended job." To start a process without waiting from an unattended job, use **Run Job** with `ExecutionMode` set to `None` (Do not wait), which creates a separate Orchestrator job.
- Only `In` direction arguments are supported in `Arguments`. Output arguments from the child process are not accessible.
- `Arguments` and `ArgumentsVariable` are mutually exclusive in the designer. Use the menu action on either property to toggle between the literal argument dictionary and a single expression variable. At runtime, `ArgumentsVariable` takes precedence over `Arguments` when both are set.
- When the robot is connected to Orchestrator, the target process must be published and available in the specified folder.
- When the calling job was started while the robot was disconnected from Orchestrator, the activity still works as long as the robot is still disconnected when it runs: the robot looks the package up by package ID in its offline processes feed, so `ProcessName` must be the package ID whichever `UsePackage` is set to, and starts the latest version found, prereleases included. Leave `FolderPath` unset in this case, since local packages have no folder and any folder value makes the lookup fail. A job that started while connected keeps using the process list it last received from Orchestrator only for as long as the Orchestrator setting `AttendedRobot.RunDisconnectedHours` allows (0 by default, so the list is dropped almost immediately).
- `EntryPointPath` is only valid when `UsePackage` is `True`. Setting it when `UsePackage` is `False` causes a validation error.
- The **Refresh arguments** menu action on the `Arguments` property auto-populates the argument dictionary from Orchestrator when a valid `ProcessName` (and optionally `EntryPointPath`) is set to a literal string.
