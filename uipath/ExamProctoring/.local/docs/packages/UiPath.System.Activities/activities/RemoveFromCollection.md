# Remove from Collection

`UiPath.Activities.System.Collections.RemoveFromCollection<T>`

Remove the specified element from a collection.

**Package:** `UiPath.System.Activities`
**Category:** Collection

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Collection` | Collection | `InArgument` | `ICollection<T>` | Yes | — | The collection from which to remove elements. |
| `Item` | Item | `InArgument` | `T` | No | — | The element value to remove. Visible when **Action Type** is `Item`. Mutually exclusive with `Index` and `RemoveAllElements`. |
| `Index` | Index | `InArgument` | `int` | No | — | The zero-based index of the element to remove. Visible when **Action Type** is `Index`. Mutually exclusive with `Item` and `RemoveAllElements`. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `RemoveAllElements` | Remove all elements | `bool` | `false` | When `true`, clears the entire collection. Controlled by the **Action Type** selector in the designer. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Result | `OutArgument` | `List<T>` | The collection after removal. The activity decides by **object identity**, not by which variable is used, so a second variable that already aliases the same collection counts as the same collection. For the `Item` and `Index` actions: when `Result` is unbound, or already refers to that same collection object, the original is mutated in-place; when it refers to a different collection object a copy is returned. **`All` does not follow that rule** — it empties the original instance only when `Result` already refers to that same collection object; otherwise it returns a new empty `List<T>` and leaves the original untouched, so an unbound `Result` means nothing is removed at all. |

## Valid Configurations

The designer presents an **Action Type** selector that controls which properties are visible:

| Action Type | Visible input properties | Behaviour |
|-------------|--------------------------|-----------|
| `Item` (default) | `Collection`, `Item` | Removes the first occurrence of the specified value. |
| `Index` | `Collection`, `Index` | Removes the element at the specified zero-based index. |
| `All` | `Collection` | Clears all elements from the collection. |

Setting `RemoveAllElements = true` together with `Item` or `Index` is a validation error. Setting both `Item` and `Index` simultaneously is also a validation error.

## XAML Example

```xml
<usc:RemoveFromCollection x:TypeArguments="x:String"
    DisplayName="Remove from Collection"
    Collection="[myList]"
    Item="hello"
    Result="[updatedList]"
    xmlns:usc="clr-namespace:UiPath.Activities.System.Collections;assembly=UiPath.System.Activities"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" />
```

## Notes

The type parameter `T` is inferred from the connected variable or argument.

For `Index` removal, if the collection does not implement `IList`, the element at the given position is looked up with `ElementAt` and then removed by value. Only the first matching element is removed when using `Item` mode.
