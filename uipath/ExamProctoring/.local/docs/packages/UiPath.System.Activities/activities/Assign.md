# Assign

`System.Activities.Statements.Assign`

`System.Activities.Statements.Assign<T>`

Evaluates an expression and stores the result in a variable or argument. Assign is the primary way to set a value in a XAML workflow.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `To` | To variable | `OutArgument` | `T` | Yes | — | The target that receives the value. Must be writable — a variable, or an `Out`/`InOut` argument. A literal or a read-only expression is rejected at validation time. |
| `Value` | Set value | `InArgument` | `T` | Yes | — | The expression to evaluate. Its type must be assignable to the type of `To`. |

## Valid Configurations

`Assign` has a non-generic and a generic form. Both are valid XAML and both appear in real workflows.

| Form | Shape | When to use |
|------|-------|-------------|
| Generic — `Assign<T>` | `x:TypeArguments` on the element; `To` and `Value` as attributes | The compact form, and what Studio writes for a simple assignment. |
| Non-generic — `Assign` | No `x:TypeArguments`; `To` and `Value` as `<Assign.To>` / `<Assign.Value>` property elements wrapping typed `OutArgument` / `InArgument` children | When the argument type has to be stated on the inner element, such as a constructed generic type. |

## XAML Example

```xml
<Assign x:TypeArguments="x:String"
        DisplayName="Build the greeting"
        To="[greeting]"
        Value="[&quot;Hello, &quot; + userName]"
        xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" />
```

The non-generic form, assigning to a constructed generic target:

```xml
<Assign DisplayName="Start the table list"
        xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
        xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
        xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib"
        xmlns:sd="clr-namespace:System.Data;assembly=System.Data">
  <Assign.To>
    <OutArgument x:TypeArguments="scg:List(sd:DataTable)">[tables]</OutArgument>
  </Assign.To>
  <Assign.Value>
    <InArgument x:TypeArguments="scg:List(sd:DataTable)">[New List(Of DataTable)]</InArgument>
  </Assign.Value>
</Assign>
```

Two things about that initialiser. The `[...]` shorthand is always VB.NET, so the form above is for a VB.NET project only. A C# project writes both sides as elements instead: `<CSharpReference x:TypeArguments="scg:List(sd:DataTable)">tables</CSharpReference>` inside the `OutArgument`, and `<CSharpValue x:TypeArguments="scg:List(sd:DataTable)">new List&lt;DataTable&gt;()</CSharpValue>` inside the `InArgument`. And the `xmlns:sd` prefix resolves `sd:DataTable` for **XAML only**; it is not an import for the expression compiler. The project must also import `System.Data` (Project Settings → Imports), or the expression fails with "Type 'DataTable' is not defined".

## Coded Workflows

`Assign` has no coded-workflow API and needs none. In a coded workflow, use plain C# assignment; the target
must be a variable, field, property or `out`/`ref` parameter, just as `To` must be writable in XAML.

```csharp
var greeting = $"Hello, {userName}";
```

## Notes

- This is a Workflow Foundation runtime activity from `System.Activities`, not a UiPath re-implementation. In XAML it is written **unprefixed** in the default namespace `http://schemas.microsoft.com/netfx/2009/xaml/activities` — never as `<ui:Assign>`.
- In XAML, generic type arguments use **parentheses**, not angle brackets: `x:TypeArguments="scg:List(x:String)"`, never `List<String>`.
- `To` is an `OutArgument` but is listed as an input because it is a value the author supplies. The activity exposes no separate output property.
- To set several variables in one step, use [Multiple Assign](MultipleAssign.md) (`UiPath.Core.Activities.MultipleAssign`) rather than chaining Assign activities.
- Assigning to an argument of the current workflow requires that argument's direction to be `Out` or `InOut`; assigning to an `In` argument fails validation.
