# Write Line

`System.Activities.Statements.WriteLine`

Writes a line of text to the workflow's text writer. Under the robot that writer forwards each line to the job log at **Trace** level, so the output is filtered by the logging level rather than discarded.

**Package:** `UiPath.System.Activities`
**Category:** Programming

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Text` | Text | `InArgument` | `string` | No | — | The text to write. Content property, so it may also be written as `<WriteLine.Text>`. When not set, an empty line is written. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `TextWriter` | — | `InArgument<TextWriter>` | — | The writer that receives the text. Hidden in the designer (`isVisible: false`); settable in raw XAML for hosts that redirect output. When not set, the runtime falls back to the `TextWriter` the host registers as a workflow extension, and only to `Console.Out` if there is none. The robot registers one, which is why Write Line reaches the job log. |

## XAML Example

```xml
<WriteLine Text="[&quot;Processed invoice &quot; + invoiceNumber]"
           DisplayName="Write progress to console"
           xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities" />
```

## Coded Workflows

`WriteLine` has no method of its own on `ISystemService`, but it does have an inherited equivalent: use
`Log(...)`, declared on `CodedWorkflowBase`, which writes at `LogLevel.Info` unless you pass another level.
That is `UiPath.CodedWorkflows.LogLevel`; qualify it when `UiPath.Core.Activities` is also imported, since
that namespace has its own `LogLevel` and the bare name is then ambiguous (CS0104).
On Windows the robot also redirects `Console.Out` to the same sink, so `Console.WriteLine(...)` is not lost
either — it simply arrives at Trace level, like Write Line. Use `Log` whenever the level matters.

```csharp
Log($"Processed invoice {invoiceNumber}");                   // Info, the default
Log($"Invoice {invoiceNumber} is overdue", UiPath.CodedWorkflows.LogLevel.Warn);  // explicit level
Console.WriteLine("local debug only");      // Trace level, visible only at Verbose/Trace
```

## Notes

- This is a Workflow Foundation runtime activity from `System.Activities`, not a UiPath re-implementation. In XAML it is written **unprefixed** in the default namespace `http://schemas.microsoft.com/netfx/2009/xaml/activities` — never as `<ui:WriteLine>`.
- **Prefer [Log Message](LogMessage.md) when the level matters.** Write Line does reach the job log, but always at **Trace** level, so it is visible only when the robot is logging at Verbose or Trace and is easy to miss at the default level. Log Message lets you set the level, so use it for anything that must be seen later; Write Line suits local debugging in Studio's Output panel.
- `Text` is optional: a Write Line with no text emits a blank line rather than failing.
- Attached-text formatting is not supported — build the string in the expression, for example `[String.Format("Row {0} of {1}", i, total)]`.
- The runtime default `DisplayName` is `WriteLine`; Studio writes the friendlier "Write Line".
