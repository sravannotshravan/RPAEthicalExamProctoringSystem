# Sequence

`System.Activities.Statements.Sequence`

Executes a set of child activities in order, one after another. Sequence is the default container for a workflow body, and the required wrapper wherever a container exposes a single activity slot but more than one activity is needed in it.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Activities` | — | `Collection<Activity>` | — | The ordered list of child activities. Content property — write children directly inside `<Sequence>`; there is no `<Sequence.Activities>` wrapper element. Read-only collection, so it cannot be set as an XML attribute. |
| `Variables` | Variables | `Collection<Variable>` | — | Variables scoped to this Sequence and visible to every descendant. Property element only — write `<Sequence.Variables>`; cannot be set as an XML attribute. |

## XAML Example

```xml
<Sequence DisplayName="Greet the user"
          xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
          xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
          xmlns:ui="http://schemas.uipath.com/workflow/activities">
  <Sequence.Variables>
    <Variable x:TypeArguments="x:String" Name="greeting" />
  </Sequence.Variables>
  <Assign x:TypeArguments="x:String" To="[greeting]" Value="[&quot;Hello, &quot; + userName]" />
  <ui:LogMessage Level="Info" Message="[greeting]" />
</Sequence>
```

## Coded Workflows

`Sequence` has no coded-workflow API and needs none. In a coded workflow, ordered execution is simply
consecutive C# statements, and a scoped block is `{ }`. What would be `Sequence.Variables` becomes ordinary
local variables, scoped by the block that declares them.

## Notes

- This is a Workflow Foundation runtime activity from `System.Activities`, not a UiPath re-implementation. In XAML it is written **unprefixed** in the default namespace `http://schemas.microsoft.com/netfx/2009/xaml/activities` — never as `<ui:Sequence>`.
- `Sequence` is mandatory wherever a container exposes a single activity slot but several activities are needed. `<If.Then>`, `<If.Else>`, `<TryCatch.Try>`, `<TryCatch.Finally>` and the body of an `ActivityAction` each hold exactly one activity — wrap the rest in a `Sequence`. See [If](If.md) and [Try Catch](TryCatch.md).
- Variables declared here go out of scope when the Sequence completes. Declare a variable on the outermost Sequence that still needs to read it.
- A `<Variable>` with no `Default` starts at the type's default, which is `Nothing`/`null` for every reference type. A collection declared that way is not an empty collection, so it validates clean at design time and throws `NullReferenceException` on the first use at runtime. Give collection variables a `Default` — `Default="[New List(Of String)]"` in a VB.NET project; in a C# project, where `[...]` would still be parsed as VB.NET, a `<Variable.Default>` element holding `<CSharpValue x:TypeArguments="scg:List(x:String)">new List&lt;string&gt;()</CSharpValue>` — or assign one before first use, as the example above does for `greeting`.
- The runtime default `DisplayName` is `Sequence`; Studio writes the name shown in the designer.
