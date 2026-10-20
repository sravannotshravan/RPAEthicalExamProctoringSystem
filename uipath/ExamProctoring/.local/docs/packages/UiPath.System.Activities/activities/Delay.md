# Delay

`System.Activities.Statements.Delay`

Pauses execution of the current branch for a specified amount of time.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `Duration` | Duration | `InArgument` | `TimeSpan` | Yes | — | How long to wait, as a `TimeSpan`. Content property, so it may also be written as `<Delay.Duration>`. |

## Valid Configurations

`Duration` accepts either a literal `TimeSpan` string or an expression:

| Form | Example | Notes |
|------|---------|-------|
| Literal | `Duration="00:00:05"` | `hh:mm:ss`, optionally `d.hh:mm:ss.fff`. Parsed by the `TimeSpan` type converter. |
| Expression | `Duration="[TimeSpan.FromSeconds(retryDelay)]"` | Any expression evaluating to a `TimeSpan`. Use this when the wait is computed. |

A `Duration` of `00:00:00` completes immediately rather than erroring.

## XAML Example

```xml
<Delay Duration="00:00:05"
       DisplayName="Wait 5 seconds"
       xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities" />
```

A computed wait, as used in a polling loop:

```xml
<Delay Duration="[TimeSpan.FromSeconds(pollIntervalSeconds)]"
       DisplayName="Wait before next poll"
       xmlns="http://schemas.microsoft.com/netfx/2009/xaml/activities" />
```

## Coded Workflows

`Delay` is one of only two core activities with a direct coded-workflow equivalent (the other is Write Line,
whose equivalent is `Log`). `CodedWorkflowBase` exposes
inherited `Delay(...)` and `DelayAsync(...)` helpers, each taking either a `TimeSpan` or milliseconds, so use
those rather than calling `Thread.Sleep` or `Task.Delay` yourself. They need no `using` directive and no
service accessor — they are members of the class your workflow already derives from.

```csharp
Delay(TimeSpan.FromSeconds(5));       // synchronous
Delay(5000);                          // milliseconds

await DelayAsync(TimeSpan.FromSeconds(5));   // asynchronous
await DelayAsync(5000);
```

Prefer `DelayAsync` in an async workflow: `Delay` blocks the calling thread, since it is `Thread.Sleep`
underneath, while `DelayAsync` wraps `Task.Delay`.

## Notes

- This is a Workflow Foundation runtime activity from `System.Activities`, not a UiPath re-implementation. In XAML it is written **unprefixed** in the default namespace `http://schemas.microsoft.com/netfx/2009/xaml/activities` — never as `<ui:Delay>`.
- **A number on its own means days, not seconds.** `Duration="5"` parses as five *days* (`TimeSpan` reads a bare integer as days), so the workflow silently waits far longer than intended. For five seconds write `"00:00:05"` or `[TimeSpan.FromSeconds(5)]`.
- A negative `Duration` throws `ArgumentOutOfRangeException` at runtime; only zero is treated as "no wait".
- Delay blocks only the branch it sits in. In a `Parallel` or `ParallelForEach`, other branches continue.
- A long Delay makes the job occupy a robot for its whole duration. For waits measured in minutes or longer, prefer scheduling or a trigger over a Delay.
- To wait for a condition rather than a fixed period, poll inside a loop with a short Delay, or use the activity that waits for the event directly — for example [Wait Queue Item](WaitQueueItem.md).
