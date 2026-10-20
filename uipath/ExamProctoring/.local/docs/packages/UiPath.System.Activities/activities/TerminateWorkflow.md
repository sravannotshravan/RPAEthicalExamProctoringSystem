# Terminate Workflow

`System.Activities.Statements.TerminateWorkflow`

Ends the entire workflow immediately, reporting a reason or an exception. Unlike [Throw](Throw.md), the failure is not catchable — no enclosing [Try Catch](TryCatch.md) can intercept it.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Reason` | Reason | `InArgument` | `string` | No | — | A message describing why the workflow was terminated. When set it becomes the termination message, wrapping `Exception` as the inner exception if that is set too. |
| `Exception` | Exception | `InArgument` | `Exception` | No | — | An exception instance to terminate with, for callers that need a specific exception type. |

## Valid Configurations

`Reason` and `Exception` are optional individually but form a **one-of**: supplying neither is a validation error, so the workflow does not run at all.

| Set | Behaviour |
|-----|-----------|
| `Reason` only | Terminates with a `WorkflowTerminatedException` carrying `Reason` as its message. The usual choice. |
| `Exception` only | Terminates with the supplied exception, preserving its type and message. |
| Both | `Reason` becomes the termination message and the supplied `Exception` is kept as its **inner exception**. This is the most diagnostic option, not a redundant one. |
| Neither | Fails validation before execution. |

## XAML Example

```xml
<TerminateWorkflow Reason="Mandatory configuration file is missing."
                   DisplayName="Terminate: missing configuration"
                   xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities" />
```

Terminating with a specific exception instead of a message:

```xml
<TerminateWorkflow DisplayName="Terminate: unrecoverable state"
                   xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities"
                   xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml"
                   xmlns:s="clr-namespace:System;assembly=mscorlib">
  <TerminateWorkflow.Exception>
    <InArgument x:TypeArguments="s:Exception">[New System.InvalidOperationException(failureDetail)]</InArgument>
  </TerminateWorkflow.Exception>
</TerminateWorkflow>
```

## Coded Workflows

`TerminateWorkflow` has no coded-workflow API, and there is no exact equivalent. Letting an exception escape
the workflow method faults the job, which is the closest behaviour — but unlike the activity it stays
catchable on the way out, and `finally` blocks still run. There is no coded construct that ends a job
uncatchably.

## Notes

- This is a Workflow Foundation runtime activity from `System.Activities`, not a UiPath re-implementation. In XAML it is written **unprefixed** in the default namespace `http://schemas.microsoft.com/netfx/2009/xaml/activities` — never as `<ui:TerminateWorkflow>`.
- Termination is not catchable. A surrounding Try Catch does not run a handler, and `Finally` blocks do not execute — so do not rely on one for cleanup that must happen on this path.
- The job ends as **Faulted**. Use it for unrecoverable conditions, not for ordinary completion.
- To end the workflow successfully, or to return from the current file to its caller, use [Return](Return.md) instead.
- To raise a *catchable* error that an enclosing handler or a retry can act on, use [Throw](Throw.md).
- `Exception` must evaluate to an exception **instance**, not an exception type.
- The runtime default `DisplayName` is `TerminateWorkflow`; Studio writes the friendlier "Terminate Workflow".
