# Throw

`System.Activities.Statements.Throw`

Raises an exception, stopping the current branch of execution and propagating the error to the nearest matching handler.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Exception` | Exception | `InArgument` | `Exception` | Yes | — | The exception instance to raise, as is. Usually an expression that constructs one, such as `[New BusinessRuleException("Total is negative")]`. Content property, so it may also be written as `<Throw.Exception>`. |

## XAML Example

```xml
<Throw Exception="[New System.InvalidOperationException(&quot;Invoice total is negative.&quot;)]"
       DisplayName="Reject negative total"
       xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities" />
```

Constructing the exception through a property element, which is what Studio writes when the expression needs an explicit argument type:

```xml
<Throw DisplayName="Reject negative total"
       xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
       xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
       xmlns:s="clr-namespace:System;assembly=mscorlib">
  <Throw.Exception>
    <InArgument x:TypeArguments="s:Exception">[New System.InvalidOperationException(message)]</InArgument>
  </Throw.Exception>
</Throw>
```

## Coded Workflows

`Throw` has no coded-workflow API and needs none. In a coded workflow, use the C# `throw` statement.

```csharp
throw new InvalidOperationException("Invoice total is negative.");
```

## Notes

- This is a Workflow Foundation runtime activity from `System.Activities`, not a UiPath re-implementation. In XAML it is written **unprefixed** in the default namespace `http://schemas.microsoft.com/netfx/2009/xaml/activities` — never as `<ui:Throw>`.
- `Exception` must evaluate to an exception **instance**, not an exception type. `[New ArgumentException("x")]` is correct; `[GetType(ArgumentException)]` is not.
- A `null` `Exception` value is not ignored: the activity throws `InvalidOperationException` at runtime. Guard expressions that may return nothing.
- Inside a catch handler, prefer [Rethrow](Rethrow.md) over Throw when re-raising the exception being handled. Throw raises exactly the instance `Exception` evaluates to and creates nothing itself, so `Exception="[exception]"` re-raises the same object — but from a new throw site, which resets its stack trace. Use Throw there only when deliberately replacing the exception: construct the replacement yourself and pass the original as its inner exception so the cause is not lost.
- Use `BusinessRuleException` for expected, business-level failures and let technical exceptions propagate as themselves; UiPath retry and error-handling behaviour distinguishes the two.
- To end the whole workflow rather than raise a catchable error, use [Terminate Workflow](TerminateWorkflow.md).
