# Clear Collection

`System.Activities.Statements.ClearCollection<T>`

Clears a specified collection of all items.

> **Do not use this activity in new workflows.** `Clear Collection` is one of the "old" collection activities, hidden from the Studio activity panel (`browsable: false` in the System package's portable metadata) since UiPath.System.Activities 22.10.3 because it is superseded by the newer collection activities. It exists only so that existing XAML keeps rendering and running. There is no direct one-for-one replacement that empties a collection **in place**: [Remove From Collection](RemoveFromCollection.md) with Action Type `All` (`RemoveAllElements`) clears the existing instance only when its `Result` already refers to that same collection object — the choice is made by object identity, not by which variable is used; left unbound it builds a fresh empty list that is then discarded, so the original collection is not modified at all. Where other references to that instance must observe the change, use a coded workflow and call `Clear()`; where they need not, assign a new empty collection with [Assign](Assign.md).

**Package:** `UiPath.System.Activities`
**Category:** Programming

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Collection` | Collection | `InArgument` | `ICollection<T>` | Yes | — | The collection to be cleared of contents. Must be a variable or argument holding an existing collection — the activity mutates it in place. Content property, so it may also be written as `<ClearCollection.Collection>`. |

## Valid Configurations

- `T` is the collection's item type and is set through `x:TypeArguments` on the element. It must match the item type of the value bound to `Collection`.
- `Collection` is an `InArgument`, but the activity **mutates the collection it points at** rather than returning a new one. There is no output property: after execution the same collection instance is empty.
- A `null` `Collection` throws `InvalidOperationException` at runtime. Guard it if the collection may not have been initialised.
- A fixed-size collection — notably an array — throws `NotSupportedException`, because `ICollection<T>.Clear` is not supported on it. Use a `List<T>` or another mutable collection.

## XAML Example

```xml
<ClearCollection x:TypeArguments="x:String"
                 Collection="[invoiceNumbers]"
                 DisplayName="Clear the invoice numbers"
                 xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
                 xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" />
```

## Coded Workflows

`ClearCollection` has no coded-workflow API — `"codedWorkflowSupport": false` in the package metadata — and
needs none. Call `Clear()` on the collection directly.

```csharp
invoiceNumbers.Clear();
```

## Notes

- This is a Workflow Foundation runtime activity from `System.Activities`, not a UiPath re-implementation. In XAML it is written **unprefixed** in the default namespace `http://schemas.microsoft.com/netfx/2009/xaml/activities` — never as `<ui:ClearCollection>`.
- In XAML, generic type arguments use **parentheses**, not angle brackets: `x:TypeArguments="scg:List(x:String)"`.
- The newer collection activities that supersede this one are different implementations with different class names: [Exists In Collection](ExistsInCollection.md), [Remove From Collection](RemoveFromCollection.md) (empties the collection only with Action Type `All` *and* its `Result` already referring to that same collection object), [Append Items to Collection](AppendItemToCollection.md), [Filter Collection](FilterCollection.md) and [Merge Collections](MergeCollections.md) are all `UiPath.Activities.System.Collections.*` types. They need their own CLR-namespace prefix — `xmlns:usc="clr-namespace:UiPath.Activities.System.Collections;assembly=UiPath.System.Activities"`, written `<usc:RemoveFromCollection>` — and are **not** reachable through the `ui:` schema prefix, which maps to `UiPath.Core.Activities`. Prefer them over this activity.
- The same 22.10.3 change hid the other "old" collection activities — Add To Collection, Exists In Collection and Remove From Collection in their `System.Activities.Statements.*` form. Upgrading the package does not break a workflow that already uses them. Hiding them in 22.10.3 did briefly make their properties uneditable in existing workflows, but that was fixed in 22.10.4, so on any supported version an upgraded workflow keeps both running them and editing them.
- To empty a `DataTable` rather than a collection, use [Clear Data Table](ClearDataTable.md).
- Reassigning the variable to a new empty collection with [Assign](Assign.md) is not equivalent: Clear Collection empties the existing instance, so other references to that same collection observe the change.
