# Invoke Method

`System.Activities.Statements.InvokeMethod`

Calls a public method on a .NET type or object by name, passing arguments and optionally capturing the return value.

> **Do not author this activity.** `InvokeMethod` is hidden from the Studio activity panel (`browsable: false` in the System package's portable metadata) and maps to `WorkflowPlaceholderViewModel`, so a cross-platform project renders it as an unresolved placeholder rather than a usable activity. Do not emit it in new workflows. To call .NET code, use [Invoke Code](InvokeCode.md) or a coded workflow. This page exists so that an agent reading or migrating existing legacy Windows XAML can understand the element it finds.

**Package:** `UiPath.System.Activities`
**Category:** Programming

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `MethodName` | Method Name | `Property` | `string` | Yes | — | The name of the method to call. A plain string property, not an argument, so it cannot be a runtime expression — the method name must be known at design time. Leaving it unset is a validation error. |
| `TargetType` | Target Type | `Property` | `Type` | No | — | The type whose **static** method is called. Written as `{x:Type ...}`. Mutually exclusive with `TargetObject`. |
| `TargetObject` | Target Object | `InArgument` | `Object` | No | — | The instance whose method is called. Mutually exclusive with `TargetType`. |
| `RunAsynchronously` | Run Asynchronously | `Property` | `bool` | No | `False` | When `True`, the method is invoked on a background thread and the activity does not block the workflow thread while it runs. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Parameters` | Parameters | `Collection<Argument>` | — | The method arguments, in declaration order. Content property — write each as a bare `<InArgument x:TypeArguments="...">` (or `OutArgument` / `InOutArgument` for `out`/`ref` parameters) child directly inside `<InvokeMethod>`; there is no `<InvokeMethod.Parameters>` wrapper element. Read-only collection, so it cannot be set as an XML attribute. |
| `GenericTypeArguments` | — | `Collection<Type>` | — | Type arguments for a generic method. Property element only — write `<InvokeMethod.GenericTypeArguments>` containing `<x:Type .../>` children. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | `OutArgument` | `Object` | The method's return value. Leave unbound for a `void` method. |

## Valid Configurations

Exactly one of `TargetType` and `TargetObject` must be set — the pair selects between a static and an instance call. Setting both, or neither, fails validation.

| Call kind | Set | Leave empty |
|-----------|-----|-------------|
| Static method | `TargetType` | `TargetObject` |
| Instance method | `TargetObject` | `TargetType` |

Further constraints:

- `Parameters` must match the target method's signature in **count, order and type**. There is no name-based binding, and a mismatch is a **validation error**, not a runtime one: `MethodResolver` builds the parameter types from `Parameters` and reports `PublicMethodWithMatchingParameterDoesNotExist` when no overload matches, or `ReturnTypeIncompatible` when `Result`'s type does not fit.
- An `out` or `ref` parameter must be given as an `OutArgument` or `InOutArgument` respectively; an `InArgument` in that position fails.
- `Result` must be left unbound for a `void` method.
- `GenericTypeArguments` is required when, and only when, the target method is generic.

## XAML Example

```xml
<InvokeMethod MethodName="Add"
              DisplayName="Add the table to the list"
              xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
              xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
              xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib"
              xmlns:sd="clr-namespace:System.Data;assembly=System.Data">
  <InvokeMethod.TargetObject>
    <InArgument x:TypeArguments="scg:List(sd:DataTable)">[tables]</InArgument>
  </InvokeMethod.TargetObject>
  <InArgument x:TypeArguments="sd:DataTable">[currentTable]</InArgument>
</InvokeMethod>
```

A static call capturing a return value:

```xml
<InvokeMethod MethodName="IsNullOrWhiteSpace"
              TargetType="{x:Type x:String}"
              DisplayName="Check for blank input"
              xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
              xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">
  <InvokeMethod.Result>
    <OutArgument x:TypeArguments="x:Boolean">[isBlank]</OutArgument>
  </InvokeMethod.Result>
  <InArgument x:TypeArguments="x:String">[userInput]</InArgument>
</InvokeMethod>
```

## Coded Workflows

`InvokeMethod` has no coded-workflow API — `"codedWorkflowSupport": false` in the package metadata — and
needs none. In a coded workflow, call the method directly: the compiler checks the name, argument types and
return type at build time, where the activity checks them at workflow validation and only against the
*declared* argument types. **This is the recommended replacement when migrating an `InvokeMethod` out of
legacy XAML.**

```csharp
tables.Add(currentTable);
var isBlank = string.IsNullOrWhiteSpace(userInput);
```

## Notes

- This is a Workflow Foundation runtime activity from `System.Activities`, not a UiPath re-implementation. In XAML it is written **unprefixed** in the default namespace `http://schemas.microsoft.com/netfx/2009/xaml/activities` — never as `<ui:InvokeMethod>`.
- The method is resolved by reflection, but **at design time**, not only when the workflow runs: `CacheMetadata` builds a `MethodResolver`, which reports a validation error when no public method matches the name and parameter types. A renamed or removed method therefore surfaces in the designer.
- Resolution uses the **declared** type of `TargetObject`, not the runtime value, so typing it `x:Object` fails validation with "`Object` does not have a public instance method named ...". Declare the real type — `scg:List(sd:DataTable)` above, not `x:Object`.
- `Result` and `TargetObject` are **non-generic** `OutArgument`/`InArgument` on this activity, so neither can be written in attribute form: `Result="[isBlank]"` cannot infer a type and throws `XamlObjectWriterException` on load. Use the property-element form with an explicit `x:TypeArguments`, as both examples above do.
- `MethodName` is a plain CLR string property rather than an `InArgument`, so it cannot be computed from a variable.
- `RunAsynchronously` does not make a synchronous method cancellable. The workflow cannot interrupt the call once it starts.
- Do not confuse this with the UiPath invoke activities, which are all `ui:`-prefixed and supported for new work: [Invoke Code](InvokeCode.md), [Invoke Com Method](InvokeComMethod.md), [Invoke PowerShell](InvokePowerShell.md), [Invoke VBScript](InvokeVBScript.md), [Invoke Workflow File](InvokeWorkflow.md) and [Invoke Process](InvokeProcess.md).
