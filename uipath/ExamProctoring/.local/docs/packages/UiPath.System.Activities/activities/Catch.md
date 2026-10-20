# Catch

`System.Activities.Statements.Catch<TException>`

A single exception handler belonging to a [Try Catch](TryCatch.md). The type argument selects which exceptions the handler accepts, and its body receives the caught exception.

> **Not selectable on its own.** `Catch<TException>` is hidden from the Studio activity panel (`browsable: false` in Studio's core-activity metadata; this package's own metadata declares no entry for the type) because it is never added directly — the **Try Catch** designer creates one per catch block. Author it only as a child of `<TryCatch.Catches>`; never emit a bare `<Catch>` as a workflow activity. It is documented here so that an agent reading or editing existing XAML understands the element.

**Package:** `UiPath.System.Activities`
**Category:** Workflow
**Required Scope:** `System.Activities.Statements.TryCatch`

## Properties

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ExceptionType` | — | `Type` | — | The exception type this handler accepts. **Read-only** — it is derived from the element's `x:TypeArguments` and cannot be set as a property or an XML attribute. |
| `Action` | — | `ActivityAction<TException>` | — | The handler body. Content property — write the `<ActivityAction x:TypeArguments="...">` directly inside `<Catch>`; there is no `<Catch.Action>` wrapper element. |

## Valid Configurations

The `x:TypeArguments` on `<Catch>` and on its inner `<ActivityAction>` must be **the same type**, and that type must derive from `System.Exception`. A mismatch fails workflow validation.

The handler body is a three-level shape. None of the three is strictly required — `Catch<T>.Action`, `ActivityAction<T>.Argument` and `ActivityDelegate.Handler` all default to `null` — but leaving one out changes behaviour rather than failing validation:

| Level | Element | Leaving it out |
|-------|---------|----------------|
| 1 | `<ActivityAction x:TypeArguments="TException">` | The `Catch` still matches and still marks the exception **handled**, so it is silently swallowed and no handler logic runs. Do this only when that is the intent. |
| 2 | `<ActivityAction.Argument>` with a `<DelegateInArgument x:TypeArguments="TException" Name="..." />` | The handler runs, but nothing names the caught exception, so it cannot be logged or inspected. |
| 3 | A single activity, normally a `Sequence` | The handler is empty, which swallows the exception as in level 1. `Handler` is the content property and takes **one** activity: several activities cannot be direct children of the `ActivityAction`. |

The full three-level form used in the examples below is the right default — it is the only one in which the handler can read the exception.

## XAML Example

```xml
<TryCatch DisplayName="Update the record"
          xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
          xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
          xmlns:s="clr-namespace:System;assembly=mscorlib"
          xmlns:ui="http://schemas.uipath.com/workflow/activities">
  <TryCatch.Try>
    <Sequence DisplayName="Try">
      <ui:LogMessage Level="Info" Message="Updating the record" />
    </Sequence>
  </TryCatch.Try>
  <TryCatch.Catches>
    <Catch x:TypeArguments="s:InvalidOperationException">
      <ActivityAction x:TypeArguments="s:InvalidOperationException">
        <ActivityAction.Argument>
          <DelegateInArgument x:TypeArguments="s:InvalidOperationException" Name="exception" />
        </ActivityAction.Argument>
        <Sequence DisplayName="Handle invalid state">
          <ui:LogMessage Level="Error" Message="[exception.Message]" />
          <Rethrow />
        </Sequence>
      </ActivityAction>
    </Catch>
  </TryCatch.Catches>
</TryCatch>
```

## Coded Workflows

`Catch<TException>` has no coded-workflow API and needs none. A handler is a C# `catch (TException ex)`
clause, and the exception variable it declares replaces the `DelegateInArgument` the XAML form needs. There
is no wrapper element to get right.

```csharp
catch (InvalidOperationException ex)
{
    Log(ex.Message);
    throw;
}
```

## Notes

- This is a Workflow Foundation runtime activity from `System.Activities`, not a UiPath re-implementation. In XAML it is written **unprefixed** in the default namespace `http://schemas.microsoft.com/netfx/2009/xaml/activities` — never as `<ui:Catch>`.
- It has no activity-panel category of its own, because it is not offered in the panel. It is listed under Workflow alongside its parent for convenience.
- The `DelegateInArgument` `Name` is the variable the body uses to read the exception; `exception` is the conventional name Studio writes.
- Handler selection ignores document order: an exact `ExceptionType` match wins outright, and otherwise the most specific assignable handler runs even when it is listed after a broader one. Each `ExceptionType` may appear only once in a `<TryCatch.Catches>`.
- The `Name` of a `DelegateInArgument` is scoped to this handler only — it is not visible to the `Try` or `Finally` blocks.
- In the designer this element renders as the exception-type row of a Try Catch's Catches section rather than as a standalone activity card.
