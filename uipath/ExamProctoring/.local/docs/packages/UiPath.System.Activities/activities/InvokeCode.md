# Invoke Code

`UiPath.Core.Activities.InvokeCode`

Synchronously invokes VB.NET or C# code, optionally passing it a list of input arguments. This activity can also return out arguments to the caller workflow.

**Package:** `UiPath.System.Activities`
**Category:** Programming

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| ContinueOnError | Continue on error | InArgument | `bool` | No | — | When `True`, execution continues to the next activity even if this activity throws an error. |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| Code | Code | `string` | — | The VB.NET or C# source code to execute. Required. Accepts only literal code: `Code` is a plain `string`, not an `InArgument`, so it cannot be bound to a variable or expression. |
| Language | Language | `NetLanguage` | `NetLanguage.VBNet` | The programming language of the code snippet (`VBNet` or `CSharp`). |
| Arguments | Arguments | `Dictionary<string, Argument>` | — | Named input/output argument bindings that make workflow variables available inside the code and allow returning values back to the workflow. |

### Output

_No dedicated output arguments. Return values are passed back through the `Arguments` dictionary using `OutArgument` or `InOutArgument` entries._

## Enum Reference

### NetLanguage

| Value | Description |
|-------|-------------|
| `VBNet` | Visual Basic .NET (default) |
| `CSharp` | C# |

## XAML Example

```xml
<ui:InvokeCode Language="VBNet"
               Code="Dim doubled As Integer = input * 2&#xA;result = doubled"
               xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities">
  <ui:InvokeCode.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument"
                    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib">
      <InArgument x:TypeArguments="x:Int32" x:Key="input">[inputValue]</InArgument>
      <OutArgument x:TypeArguments="x:Int32" x:Key="result">[resultValue]</OutArgument>
    </scg:Dictionary>
  </ui:InvokeCode.Arguments>
</ui:InvokeCode>
```

## Notes

- The XAML example sets `Code` as an attribute and uses `&#xA;` for line breaks. This is the preferred form for generated snippets and portable tooling output. In a child element (`<ui:InvokeCode.Code>` with bare text, CDATA or `<x:String>`), XAML collapses every run of whitespace (line breaks, indentation, tabs, repeated spaces) into a single space, so code that depends on it changes meaning: everything after a C# `//` comment becomes part of the comment, and when the code before it still compiles, validation passes and those statements never run; multi-line VB code fails with `BC30205: End of statement expected`; string literals containing tabs or repeated spaces change value. Keep multi-line code in the attribute form, or in a child `<x:String xml:space="preserve">`: the `xml:space="preserve"` attribute is what keeps the whitespace.
- The `Arguments` dictionary must be authored inline as `<scg:Dictionary x:TypeArguments="x:String, Argument">`. An external `<x:Reference>` to a sibling dictionary node is not portable across consumers and should be avoided.
- Argument bindings in the `Arguments` dictionary use the variable name as the key; direction (`In`, `Out`, `InOut`) determines data flow.
- The code snippet is compiled and executed at runtime in the same process as the robot; it has access to all .NET BCL types.
- Use `InArgument` entries to pass data into the code and `OutArgument` entries to receive results back.
- `Language` defaults to `VBNet` whatever the project's expression language. In a C# project set `Language="CSharp"`, as the Studio designer does; otherwise the C# code is compiled as VB.NET and fails with VB compiler errors (`BC30800`, `BC30037`, …).
