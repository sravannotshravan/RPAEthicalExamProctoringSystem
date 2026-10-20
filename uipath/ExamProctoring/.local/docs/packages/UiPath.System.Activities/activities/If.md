# If

`System.Activities.Statements.If`

Evaluates a Boolean condition and executes one of two branches depending on the result.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Condition` | Condition | `InArgument` | `bool` | Yes | — | The Boolean expression to evaluate. Evaluated once, before either branch runs. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Then` | Then | `Activity` | — | The activity to execute when `Condition` is `True`. Property element only — write `<If.Then>`; cannot be set as an XML attribute. Holds exactly one activity, so wrap several in a `Sequence`. |
| `Else` | Else | `Activity` | — | The activity to execute when `Condition` is `False`. Property element only — write `<If.Else>`. Optional: when omitted, a `False` condition does nothing. Holds exactly one activity. |

## XAML Example

```xml
<If Condition="[invoiceTotal &gt; 1000]"
    DisplayName="Check approval threshold"
    xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
    xmlns:ui="http://schemas.uipath.com/workflow/activities">
  <If.Then>
    <Sequence DisplayName="Needs approval">
      <Assign x:TypeArguments="x:Boolean" To="[requiresApproval]" Value="True" />
      <ui:LogMessage Level="Info" Message="Routing for approval." />
    </Sequence>
  </If.Then>
  <If.Else>
    <ui:LogMessage Level="Info" Message="Auto-approved." />
  </If.Else>
</If>
```

## Coded Workflows

`If` has no coded-workflow API and needs none. In a coded workflow, use the C# `if` / `else` statement. The
single-activity restriction on `Then` and `Else` does not apply — a C# block holds as many statements as you
like, so no `Sequence` wrapper is needed.

```csharp
if (invoiceTotal > 1000)
{
    requiresApproval = true;
    Log("Routing for approval.");
}
else
{
    Log("Auto-approved.");
}
```

## Notes

- This is a Workflow Foundation runtime activity from `System.Activities`, not a UiPath re-implementation. In XAML it is written **unprefixed** in the default namespace `http://schemas.microsoft.com/netfx/2009/xaml/activities` — never as `<ui:If>`.
- `Then` and `Else` each hold a **single** activity. Two or more activities in a branch must be wrapped in a [Sequence](Sequence.md); they cannot be direct children of `<If.Then>`.
- For more than two branches use [Else If](ElseIf.md) (`UiPath.Core.Activities.IfElseIfV2`) rather than nesting `If` activities, or [Switch](Switch.md) when branching on the value of a single expression.
- `<` and `>` must be escaped inside a XAML attribute: write `Condition="[total &gt; 1000]"`.
- `Condition` is evaluated once, so an expression with a side effect does not re-run per branch.
