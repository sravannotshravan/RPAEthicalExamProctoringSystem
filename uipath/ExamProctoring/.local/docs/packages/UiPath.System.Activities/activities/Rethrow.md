# Rethrow

`System.Activities.Statements.Rethrow`

Re-raises the exception currently being handled, preserving its original stack trace. Valid only inside a catch handler.

**Package:** `UiPath.System.Activities`
**Category:** Workflow
**Required Scope:** `System.Activities.Statements.Catch<TException>`

## Properties

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|

_This activity has no configurable properties._

## XAML Example

```xml
<TryCatch DisplayName="Read the invoice"
          xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
          xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
          xmlns:s="clr-namespace:System;assembly=mscorlib"
          xmlns:ui="http://schemas.uipath.com/workflow/activities">
  <TryCatch.Try>
    <Sequence DisplayName="Try">
      <ui:ReadTextFile FileName="C:\data\invoice.txt" Content="[raw]" />
    </Sequence>
  </TryCatch.Try>
  <TryCatch.Catches>
    <Catch x:TypeArguments="s:Exception">
      <ActivityAction x:TypeArguments="s:Exception">
        <ActivityAction.Argument>
          <DelegateInArgument x:TypeArguments="s:Exception" Name="exception" />
        </ActivityAction.Argument>
        <Sequence DisplayName="Log and re-raise">
          <ui:LogMessage Level="Error" Message="[exception.Message]" />
          <Rethrow DisplayName="Rethrow" />
        </Sequence>
      </ActivityAction>
    </Catch>
  </TryCatch.Catches>
</TryCatch>
```

## Coded Workflows

`Rethrow` has no coded-workflow API and needs none. Inside a `catch` block, a bare `throw;` re-raises the
current exception with its original stack trace intact. `throw ex;` resets the stack trace — it is the
coded-workflow form of the Throw-instead-of-Rethrow mistake described above.

```csharp
catch (Exception ex)
{
    Log(ex.Message);
    throw;            // preserves the stack trace; `throw ex;` would reset it
}
```

## Notes

- This is a Workflow Foundation runtime activity from `System.Activities`, not a UiPath re-implementation. In XAML it is written **unprefixed** in the default namespace `http://schemas.microsoft.com/netfx/2009/xaml/activities` — never as `<ui:Rethrow>`.
- Rethrow takes no exception argument: it always re-raises the exception of the enclosing handler. There is nothing to configure.
- It must sit inside the body of a [Catch](Catch.md) handler. Placing it anywhere else — in a `Try` block, a `Finally` block, or the workflow body — fails validation.
- Prefer Rethrow over [Throw](Throw.md) when re-raising the exception you are handling. Throw given the caught exception raises the same instance from a new throw site, which resets its stack trace and makes the root cause harder to find in robot logs; Rethrow keeps the original trace. Throw is for raising a different exception, which you construct yourself.
- Use it to log or clean up locally while still letting the error reach the caller. If the exception should be swallowed instead, omit Rethrow entirely.
