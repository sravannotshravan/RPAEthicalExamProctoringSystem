# Try Catch

`System.Activities.Statements.TryCatch`

Executes a body of activities and handles any exception it throws with a matching catch handler, optionally running a block of activities afterwards whether or not an exception occurred.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Try` | Try | `Activity` | — | The activity to execute and monitor for exceptions. Property element only — write `<TryCatch.Try>`; cannot be set as an XML attribute. Holds exactly one activity, so wrap several in a `Sequence`. |
| `Catches` | Catches | `Collection<Catch>` | — | The ordered list of exception handlers. Property element only — write `<TryCatch.Catches>` containing one or more `<Catch x:TypeArguments="...">` children. Read-only collection, so it cannot be set as an XML attribute. |
| `Finally` | Finally | `Activity` | — | An activity that runs after `Try` completes or after a handler finishes, whether or not an exception was thrown. Property element only — write `<TryCatch.Finally>`. Holds exactly one activity. |
| `Variables` | Variables | `Collection<Variable>` | — | Variables scoped to this Try Catch and visible to `Try`, every handler, and `Finally`. Property element only — write `<TryCatch.Variables>`. |

## Valid Configurations

- `Try` is optional. With no `Try`, nothing can throw, so no handler runs, but `Finally` still runs when it is set; with neither, the activity completes immediately. A body to protect belongs in `Try`.
- At least one of `Catches` or `Finally` must be present: declaring neither is a validation error. Both may be set.
- Handler selection does **not** depend on the order of `Catches`. CoreWF returns the handler whose `ExceptionType` equals the thrown type exactly; failing that, it keeps the **most specific** assignable handler wherever it appears. A `Catch<System.Exception>` listed first therefore does not swallow a later `Catch<System.IO.FileNotFoundException>`.
- Each `ExceptionType` may appear only once: a duplicate is rejected when the `Catches` collection is built.
- If no handler matches, the exception propagates to the enclosing scope and **`Finally` does not run**. CoreWF schedules `Finally` only after `Try` or a matching catch handler *completes*; an unhandled fault never reaches that point.

## XAML Example

```xml
<TryCatch DisplayName="Read the invoice"
          xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
          xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
          xmlns:s="clr-namespace:System;assembly=mscorlib"
          xmlns:io="clr-namespace:System.IO;assembly=mscorlib"
          xmlns:ui="http://schemas.uipath.com/workflow/activities">
  <TryCatch.Try>
    <Sequence DisplayName="Try">
      <ui:ReadTextFile FileName="C:\data\invoice.txt" Content="[raw]" />
    </Sequence>
  </TryCatch.Try>
  <TryCatch.Catches>
    <Catch x:TypeArguments="io:FileNotFoundException">
      <ActivityAction x:TypeArguments="io:FileNotFoundException">
        <ActivityAction.Argument>
          <DelegateInArgument x:TypeArguments="io:FileNotFoundException" Name="exception" />
        </ActivityAction.Argument>
        <Sequence DisplayName="Handle missing file">
          <ui:LogMessage Level="Warn" Message="[&quot;Invoice not found: &quot; + exception.Message]" />
        </Sequence>
      </ActivityAction>
    </Catch>
    <Catch x:TypeArguments="s:Exception">
      <ActivityAction x:TypeArguments="s:Exception">
        <ActivityAction.Argument>
          <DelegateInArgument x:TypeArguments="s:Exception" Name="exception" />
        </ActivityAction.Argument>
        <Sequence DisplayName="Handle anything else">
          <ui:LogMessage Level="Error" Message="[exception.Message]" />
        </Sequence>
      </ActivityAction>
    </Catch>
  </TryCatch.Catches>
  <TryCatch.Finally>
    <Sequence DisplayName="Finally">
      <ui:LogMessage Level="Info" Message="Invoice read attempt finished." />
    </Sequence>
  </TryCatch.Finally>
</TryCatch>
```

## Coded Workflows

`TryCatch` has no coded-workflow API and needs none. In a coded workflow, use C# `try` / `catch` / `finally`.
The two differ on ordering, so do not carry habits across: C# clauses are evaluated top-down, so a general
clause placed first makes a later specific one unreachable and the compiler rejects it, whereas
`<TryCatch.Catches>` is order-independent and CoreWF picks the most specific assignable handler.

```csharp
using System.IO;                 // FileNotFoundException
using UiPath.Core.Activities;    // PathType - not auto-imported

try
{
    // Returns null for a missing path rather than throwing, so raise the specific exception here.
    var invoice = system.GetResourceForLocalPath(@"C:\data\invoice.txt", PathType.File)
        ?? throw new FileNotFoundException("Invoice not found.", @"C:\data\invoice.txt");
    var raw = system.ReadTextFile(invoice);
}
catch (FileNotFoundException ex)
{
    Log($"Invoice not found: {ex.Message}");
}
catch (Exception ex)
{
    Log(ex.Message);
}
finally
{
    Log("Invoice read attempt finished.");
}
```

## Notes

- This is a Workflow Foundation runtime activity from `System.Activities`, not a UiPath re-implementation. In XAML it is written **unprefixed** in the default namespace `http://schemas.microsoft.com/netfx/2009/xaml/activities` — never as `<ui:TryCatch>`.
- Each handler's body is an `ActivityAction`, and the `ActivityAction` → `ActivityAction.Argument` → `DelegateInArgument` wrapper is what names the caught exception so the handler can read it. It is not enforced — every level defaults to `null` — but a `Catch` without it still marks the exception handled, so omitting a level silently swallows instead of handling. See [Catch](Catch.md).
- Child activities cannot be direct children of an `ActivityAction`; its body must be a single activity, normally a [Sequence](Sequence.md).
- To re-raise the exception you are currently handling, use [Rethrow](Rethrow.md) inside the handler rather than [Throw](Throw.md): Throw would raise the same instance from a new throw site and reset its stack trace.
- `Finally` is **not** a guaranteed cleanup hook. It is skipped when no handler matches, and skipped when a handler itself throws, because both paths propagate the exception instead of completing. Cleanup that must happen on every path belongs outside the Try Catch. It *does* run after a handled exception, so logic there must not assume `Try` succeeded.
- For retrying a failing body instead of handling its error once, use [Retry Scope](RetryScope.md).
