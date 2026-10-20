# Switch

`System.Activities.Statements.Switch<T>`

Evaluates an expression and executes the single case whose key equals the result, or a default activity when no case matches.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Expression` | Expression | `InArgument` | `T` | Yes | — | The expression whose value selects the case. `T` is the type argument of the activity and determines the type of every case key. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Cases` | — | `IDictionary<T, Activity>` | — | The case table, keyed by value. Content property — write each case as a **bare child element carrying `x:Key`** directly inside `<Switch>`; there is no `<Switch.Cases>` wrapper element. Read-only collection, so it cannot be set as an XML attribute. |
| `Default` | Default | `Activity` | — | The activity to run when no case key matches. Property element only — write `<Switch.Default>`. Optional: when omitted, an unmatched value does nothing. Holds exactly one activity. |

## Valid Configurations

- `T` is set through `x:TypeArguments` on the `<Switch>` element and is normally `x:String` or `x:Int32`. Every case key must be of that type.
- Case keys must be **unique** and must be literal values — a case key cannot be an expression.
- Matching is by equality on the key, and at most one case runs. There is no fall-through between cases.
- Each case holds exactly one activity, so wrap several in a `Sequence`.
- When `Expression` matches no key and no `Default` is set, the activity completes without running anything.

## XAML Example

```xml
<Switch x:TypeArguments="x:String"
        Expression="[invoiceStatus]"
        DisplayName="Route by status"
        xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        xmlns:ui="http://schemas.uipath.com/workflow/activities">
  <Switch.Default>
    <ui:LogMessage Level="Error" Message="[&quot;Unknown status: &quot; + invoiceStatus]" />
  </Switch.Default>
  <Sequence x:Key="Approved" DisplayName="Approved">
    <ui:LogMessage Level="Info" Message="Posting the invoice." />
  </Sequence>
  <Sequence x:Key="Rejected" DisplayName="Rejected">
    <ui:LogMessage Level="Warn" Message="Returning to the submitter." />
  </Sequence>
</Switch>
```

## Coded Workflows

`Switch` has no coded-workflow API and needs none. In a coded workflow, use the C# `switch` statement or a
switch expression. The activity's equality-only restriction does not apply: C# supports relational and
pattern matching, so range and type tests that need `Else If` in XAML work directly here.

```csharp
switch (invoiceStatus)
{
    case "Approved": Log("Posting the invoice."); break;
    case "Rejected": Log("Returning to the submitter."); break;
    default: Log($"Unknown status: {invoiceStatus}"); break;
}
```

## Notes

- This is a Workflow Foundation runtime activity from `System.Activities`, not a UiPath re-implementation. In XAML it is written **unprefixed** in the default namespace `http://schemas.microsoft.com/netfx/2009/xaml/activities` — never as `<ui:Switch>`.
- The `x:Key` attribute on each child is what places it in `Cases`. A child without an `x:Key` is not a valid case.
- Switch compares values for equality only. For range checks, pattern matching, or compound conditions use [Else If](ElseIf.md) (`UiPath.Core.Activities.IfElseIfV2`) or nested [If](If.md) activities instead.
- For a `String` type argument, key matching is case-sensitive. Normalise the expression (for example with `[invoiceStatus.Trim().ToUpper()]`) if the incoming value's casing is not guaranteed.
- In XAML, generic type arguments use **parentheses**, not angle brackets: `x:TypeArguments="scg:List(x:String)"`.
