# For Each

`UiPath.Core.Activities.ForEach<T>`

Performs an activity or a series of activities on each element of an enumeration.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Values` | In | `InArgument` | `System.Collections.IEnumerable` (non-generic) | Yes | — | The collection to iterate over. The element type `T` is the activity's type argument (`<ui:ForEach x:TypeArguments="...">`), not part of the `Values` type: bind it as `<InArgument x:TypeArguments="sc:IEnumerable">` with `xmlns:sc="clr-namespace:System.Collections;assembly=System.Private.CoreLib"`. |
| `Condition` | Condition | `Activity` | `bool` | No | — | The loop continues while this is `True` (default `True`). Set directly inside `<ui:ForEach.Condition>` — `Condition` is an `Activity<bool>`, so no `<InArgument>` wrapper. |
| `MaxIterations` | Max iterations | `InArgument` | `int` | No | — | Maximum number of iterations. A value of `0` means unlimited. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `TypeOfValues` | Argument type | `Type` | — | The element type `T` of the collection. Shown as a type-picker widget when supported by the designer. Changing this value morphs the activity to the selected generic type. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `CurrentIndex` | Index | `OutArgument` | `int` | The zero-based index of the current iteration. |

## XAML Example

```xml
<ui:ForEach x:TypeArguments="x:String"
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    xmlns:sc="clr-namespace:System.Collections;assembly=System.Private.CoreLib"
    DisplayName="For Each">
  <ui:ForEach.Values>
    <InArgument x:TypeArguments="sc:IEnumerable">
      <VisualBasicValue x:TypeArguments="sc:IEnumerable" ExpressionText="myList" />
    </InArgument>
  </ui:ForEach.Values>
  <ActivityAction x:TypeArguments="x:String">
    <ActivityAction.Argument>
      <DelegateInArgument x:TypeArguments="x:String" Name="item" />
    </ActivityAction.Argument>
    <Sequence DisplayName="Body">
      <!-- child activities reference the iterator variable "item" -->
    </Sequence>
  </ActivityAction>
</ui:ForEach>
```

## Notes

- **For Each** is a container/scope activity. Child activities are placed inside the `ActivityAction` body and can reference the iterator variable (e.g. `item`).
- The activity is generic (`ForEach<T>`): `T` is set on the activity (`x:TypeArguments`, or the `TypeOfValues` type picker) and types the iterator variable, while `Values` stays a non-generic `IEnumerable`. A generic type such as `IEnumerable(x:String)` on `Values` fails to load.
- The iterator variable name is auto-suggested based on the element type (e.g. `stringItem` for `String`) and can be renamed. If the suggested name was not changed manually, it is automatically updated when the type changes.
- `TypeOfValues` is only visible when the designer supports the `TypePicker` widget; in other environments the type is set implicitly.
- Use a `Break` activity inside the body to exit the loop early; use `Continue` to skip to the next element.
