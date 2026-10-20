# Run Job

`UiPath.Activities.System.Jobs.RunJob`

Initiates any type of job (Agent, Agentic process, RPA workflows, API workflow, Testing process, etc.) via Orchestrator to be picked up by any available robots. It allows for flexible configuration of the execution mode (Do not wait, Wait for job completion or Suspend execution until job completion). It returns output arguments unless started in the Do not wait mode.

**Package:** `UiPath.System.Activities`
**Category:** Run

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `ProcessName` | Process name | InArgument | `string` | Yes | — | The name of the Orchestrator process to start. Supports auto-complete from available processes in the configured folder. |
| `RuntimeType` | Runtime type | InArgument | `JobRuntimeType` | No | `Default` | The runtime license the job runs on: `Unattended` (Production), `NonProduction`, `TestAutomation` (Testing), `AutomationCloud` (Cloud - VM), `AutomationCloudTestAutomation` (Cloud - VM Testing), `Serverless` (Cloud - Serverless) or `ServerlessTestAutomation` (Cloud - Serverless Testing). `Default` lets Orchestrator choose. See **Runtime type at run time** below. |
| `Machine` | Machine | InArgument | `string` | No | — | The name of the machine on which the job will execute. It must be assigned to the folder of the process being started. If not specified, any available machine is used. See **Machine and Account at run time** below. |
| `Account` | Account | InArgument | `string` | No | — | The name of the unattended robot that executes the job, as Orchestrator lists it in that folder (for example `jane.doe@contoso.com-unattended`), not the user's login. If not specified, the default account associated with the machine is used. See **Machine and Account at run time** below. |
| `EntryPointPath` | Entry point path | InArgument | `string` | No | — | Override the default entry-point workflow of the target process (e.g. `Main.xaml` or a coded entry point). Leave empty to use the process's configured entry point. |
| `Priority` | Priority | InArgument | `JobPriorityV2` | No | `Inherited` | The priority the job is started with. `Inherited` (default) uses the priority configured on the target process. Granular values map to Orchestrator's `SpecificPriorityValue`; on Orchestrators without granular priority support the value is down-converted to Low/Normal/High. In raw XAML use the enum name, e.g. `Priority="High"`. |
| `TimeoutMS` | Timeout (milliseconds) | InArgument | `int` | No | `600000` (10 min) | Maximum time in milliseconds to wait for the job to complete. Only applicable when `ExecutionMode` is `Busy` (Wait for job completion). Read-only for other modes. |
| `ContinueOnError` | Continue on error | InArgument | `bool` | No | `false` | When `True`, execution continues even if this activity encounters an error. Read-only when `ExecutionMode` is `None`. |
| `Input` | Input | InArgument (untyped) | dynamic | No | null | Single-object input mode. The variable bound here is serialized to JSON and passed as the process's input. Type is determined by Studio when the target process's schema is imported; see **Authoring `Input` / `Output` in raw XAML** below. |
| `Arguments` | Arguments | `Dictionary<string, Argument>` | dynamic | No | empty | Dictionary mode — per-argument bindings keyed by the target process's argument names. Mixed `InArgument` / `OutArgument` entries are allowed; `OutArgument` entries capture top-level output properties. This is the **only Input/Output binding that is straightforward to author in raw XAML.** |

### Configuration

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `ExecutionMode` | Execution mode | `JobExecutionMode` | `JobExecutionMode.Busy` | Determines how the initiated job is processed. See Valid Configurations below. |
| `FailWhenFaulted` | Continue when job fails | `bool` | `true` (i.e., fail when faulted) | When `True`, a faulted job causes this activity to throw an error. When `False`, a faulted job is ignored and execution continues. Designer label shows the inverse semantics ("Continue when job fails" — checked = `FailWhenFaulted=False`). Read-only when `ExecutionMode` is `None`. |
| `FolderPath` | Folder path | `string` | — | The Orchestrator folder containing the process. Leave empty to use the folder of the current process. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Job` | Job data | OutArgument | `OrchestratorJob` (`UiPath.Core.Activities`) | An object containing information about the initiated job (e.g., Job ID, status, output arguments). Not populated when `ExecutionMode` is `None`. |
| `Output` | Output | OutArgument (untyped) | dynamic | Single-object output mode. The variable bound here is populated by deserializing the process's `OutputArguments` JSON. Type is determined by Studio when the target process's schema is imported; see **Authoring `Input` / `Output` in raw XAML** below. Not populated when `ExecutionMode` is `None`. |

## Valid Configurations

The behavior and available properties depend on the `ExecutionMode` value:

| `ExecutionMode` | Behavior | `TimeoutMS` | `ContinueOnError` | `FailWhenFaulted` | Output |
|---|---|---|---|---|---|
| `None` (Do not wait) | Starts the job and returns immediately without waiting. | Read-only | Read-only | Read-only | `Job` is populated with basic job info; no output arguments. |
| `Busy` (Wait for job completion) | Starts the job and blocks the current robot until the job completes or times out. | Editable | Editable | Editable | `Job` is fully populated including output arguments. |
| `Suspend` (Suspend until job completion) | Starts the job and suspends the current workflow (persistence required). Resumes when the job completes. | Read-only | Editable | Editable | `Job` is fully populated including output arguments on resume. |

### Enum Reference

**`JobExecutionMode`**

| Value | Description |
|-------|-------------|
| `None` | Do not wait — fire and forget. |
| `Busy` | Wait for job completion by blocking the robot thread. |
| `Suspend` | Suspend the workflow until the job completes (requires persistence infrastructure). |

**`JobPriorityV2`** (namespace `UiPath.Activities.System.Jobs`)

| Value | Numeric value |
|-------|---------------|
| `Inherited` | 0 (use the target process's configured priority) |
| `Lowest` | 5 |
| `VeryLow` | 15 |
| `Low` | 25 |
| `MediumLow` | 35 |
| `Medium` | 45 |
| `MediumHigh` | 55 |
| `High` | 65 |
| `VeryHigh` | 75 |
| `Highest` | 85 |
| `Critical` | 95 |

**`JobRuntimeType`** (namespace `UiPath.Activities.System.Jobs`)

| Value | Orchestrator label |
|-------|--------------------|
| `Default` | Default (Orchestrator chooses) |
| `Unattended` | Production (Unattended) |
| `NonProduction` | NonProduction |
| `TestAutomation` | Testing |
| `AutomationCloud` | Cloud - VM |
| `AutomationCloudTestAutomation` | Cloud - VM Testing |
| `Serverless` | Cloud - Serverless |
| `ServerlessTestAutomation` | Cloud - Serverless Testing |

## XAML Example

```xml
<!-- Wait for job completion -->
<ui:RunJob
    xmlns:ui="clr-namespace:UiPath.Activities.System.Jobs;assembly=UiPath.System.Activities"
    DisplayName="Run Job"
    ProcessName="InvoiceProcessor"
    ExecutionMode="Busy"
    TimeoutMS="[600000]"
    FailWhenFaulted="True"
    Job="[jobData]" />
```

```xml
<!-- Fire and forget -->
<ui:RunJob
    xmlns:ui="clr-namespace:UiPath.Activities.System.Jobs;assembly=UiPath.System.Activities"
    DisplayName="Run Job"
    ProcessName="BackgroundReporter"
    ExecutionMode="None" />
```

Pin the job to a machine and account in another folder. Literal values are plain attribute text, with no quotes and no brackets; use `[expression]` only for a variable or expression:

```xml
<ui:RunJob
    xmlns:ui="clr-namespace:UiPath.Activities.System.Jobs;assembly=UiPath.System.Activities"
    DisplayName="Run Job"
    FolderPath="Finance/Invoices"
    ProcessName="InvoiceProcessor"
    Machine="Finance-Unattended-01"
    Account="svc-invoices-unattended"
    ExecutionMode="None" />
```

Run the job on a specific runtime license. In raw XAML use the enum name:

```xml
<ui:RunJob
    xmlns:ui="clr-namespace:UiPath.Activities.System.Jobs;assembly=UiPath.System.Activities"
    DisplayName="Run Job"
    ProcessName="InvoiceProcessor"
    RuntimeType="NonProduction"
    ExecutionMode="None" />
```

Dictionary-mode arguments — pass typed inputs and capture typed outputs by argument name:

```xml
<ui:RunJob
    xmlns:ui="clr-namespace:UiPath.Activities.System.Jobs;assembly=UiPath.System.Activities"
    xmlns:scg="clr-namespace:System.Collections.Generic;assembly=mscorlib"
    DisplayName="Run Job"
    ProcessName="InvoiceProcessor"
    ExecutionMode="Busy"
    Job="[jobData]">
  <ui:RunJob.Arguments>
    <scg:Dictionary x:TypeArguments="x:String, Argument">
      <InArgument x:TypeArguments="x:String" x:Key="in_InvoiceId">[invoiceId]</InArgument>
      <InArgument x:TypeArguments="x:Double" x:Key="in_Amount">[amount]</InArgument>
      <OutArgument x:TypeArguments="x:String" x:Key="out_Status">[processStatus]</OutArgument>
      <OutArgument x:TypeArguments="x:Boolean" x:Key="out_Approved">[wasApproved]</OutArgument>
    </scg:Dictionary>
  </ui:RunJob.Arguments>
</ui:RunJob>
```

## Coded Workflow Example

In coded workflows, `RunJob` is exposed as `system.RunJob(...)` / `system.RunJobAsync(...)`. The priority is set through `RunJobOptionalParameters.Priority`:

```csharp
using UiPath.Activities.System.Jobs;   // JobPriorityV2 — NOT auto-imported (only the .Jobs.Coded namespace is)

[Workflow]
public void Execute()
{
    var opts = new RunJobOptionalParameters
    {
        Priority = JobPriorityV2.High,
        FailWhenJobFails = true
    };

    var (jobData, outputJson) = system.RunJob(
        processName: "InvoiceProcessor",
        orchestratorFolderPath: "Finance/Invoices",
        inputArguments: new { InvoiceId = invoiceId },
        runJobOptionalParameters: opts
    );

    Log($"Job {jobData.Id} completed with priority {opts.Priority}. Output: {outputJson}");
}
```

Leaving `Priority` unset (or setting it to `JobPriorityV2.Inherited`, the default) starts the job with the priority configured on the target process. See the package's coded API documentation (`docs/coded/coded-api.md`) for the full `RunJob` signature and the other `RunJobOptionalParameters` members.

The entry point, runtime type, machine and account are set the same way, through `RunJobOptionalParameters.EntryPointPath`, `RuntimeType` (`JobRuntimeType`, from `UiPath.Activities.System.Jobs`), `Machine` and `Account`. Leave the string options `null`, and `RuntimeType` on `JobRuntimeType.Default`, to keep their defaults:

```csharp
var (jobData, outputJson) = system.RunJob(
    processName: "InvoiceProcessor",
    orchestratorFolderPath: "Finance/Invoices",
    inputArguments: new { InvoiceId = invoiceId },
    doNotWait: true,
    runJobOptionalParameters: new RunJobOptionalParameters
    {
        Machine = "Finance-Unattended-01",
        Account = "svc-invoices-unattended"
    }
);
```

## Authoring `Input` / `Output` in raw XAML

`RunJob` exposes three mutually-exclusive ways to pass arguments to and from the triggered process. They look the same in Studio (selectable via the designer's mode menu) but serialize very differently:

| Mode | Property/properties used | Authorable in raw XAML? | Notes |
|------|--------------------------|-------------------------|-------|
| **Dictionary** | `Arguments` (`Dictionary<string, Argument>`) | **Yes** — see the example above. | Per-argument `InArgument`/`OutArgument` entries keyed by the target process's argument names. Each entry carries its own `x:TypeArguments`. |
| **Data Mapper** | `Input` + `Output` (both untyped `Argument`) | Only with effort — requires knowing the target process's argument schema and binding a matching typed variable. Studio normally fills this in when you point at a process. | The `Input` and `Output` properties are marked `[Browsable(false)]` on the activity. They can still be serialized; their effective type is taken from the bound variable. Without Studio's schema import, you must know the target process's argument shape and declare a typed variable of the same shape. |
| **Object** | `Input` *or* `Output` (single object, untyped) | Same as Data Mapper, with the constraint that the variable type matches the schema-implied object class for the process. | Same caveat — no auto-discovery without Studio. |

**Recommendation for coding agents authoring without Studio:** use the **Dictionary** mode (`Arguments`). It's the only mode whose XAML form is fully self-describing — type info travels inline with each argument, and no external schema is required.

## Runtime type at run time

`RuntimeType` is sent to Orchestrator as part of the request that starts the job. Leaving it on `Default` sends nothing, so Orchestrator picks the runtime from what the folder offers, exactly as before the property existed.

- If the folder has no machine with slots of the chosen runtime type, Orchestrator refuses to start the job and the activity fails with Orchestrator's error, for example `Testing runtime license selected. There are no Testing runtimes configured on the templates in this folder.`
- Orchestrator rejects a Cloud - Serverless runtime type with a 400 error for processes that are not cross-platform, and where Serverless is not enabled for the tenant.
- For agent, API, Maestro (agentic process, case management, business rules, flow), MCP server and function processes, Orchestrator decides the runtime type itself and ignores the one sent. Studio therefore hides the property when `ProcessName` is a literal naming one of those process types. A value already stored in the workflow is not removed when the workflow loads; it is cleared when the process or folder is changed afterwards.
- When Run Job runs inside a job whose process has execution settings configured in Orchestrator (Package Requirements), the runtime type configured there replaces the one set on the activity.
- It combines with `Machine` and `Account`; the machine must have slots of the chosen runtime type.

## Machine and Account at run time

Orchestrator starts a job on a specific machine and account by their ids, so before starting the job the activity looks both names up. It does this in the folder of the process being started, which is the folder the process was found in (`FolderPath`, or the current folder when that is empty):

1. The account is resolved first, among the unattended robots of that folder.
2. The machine is then resolved among the machines assigned to that folder, narrowed to those the account may run on under the folder's account-machine mappings (Orchestrator's tenant-level mappings apply where the folder defines none).

Permissions: the executing robot needs only folder-level rights on that folder, with no tenant-wide `Machines.View` or `Robots.View`. `Processes.View` and `Jobs.Create`, which starting the job requires anyway, are enough for both lookups.

Failures, all raised before any job is created:

| Situation | Error |
|-----------|-------|
| The machine is not assigned to the process's folder, or the account may not run on it | `The specified Machine '<name>' was not found in the folder of the process being started. Verify that the value is correct, the machine is assigned to that folder, and, when an account is also set, that the account is allowed to run on that machine.` |
| The account is not an unattended robot in that folder | `The specified Account '<name>' was not found in the folder of the process being started. Verify that the value is correct and that the account is an unattended robot assigned to that folder.` |
| The robot lacks access to the account lookup | `…Ensure the executing account holds any one of these permissions on that folder: Jobs.Create, SubFolders.View, Units.View, Users.View` |
| The robot lacks access to the machine lookup | `…on that folder: Jobs.Create, Machines.View` |

Because the account is resolved first, its error is the one reported when both lookups would fail.

If the process lookup finds no release, no folder is known, so both lookups fall back to tenant-wide reads, which need tenant-level `Robots.View` (account) or `Machines.View` (machine):

- Without those permissions, the activity fails with an access-denied error that names the process first (`The process '<name>' was not found in the folder, so the Machine '<name>' was looked up across the tenant, …`), then the missing tenant permission.
- With them, a Machine or Account name that matches nothing tenant-wide fails with the not-found error in its tenant-wide wording (`…the resource is assigned in the current folder, …`).
- Otherwise the job is started by process name, which Orchestrator rejects if the process does not exist.

## Notes

- Requires an active Orchestrator connection. The process must be published and available in the specified (or current) Orchestrator folder.
- **Suspend mode** requires a persistence-enabled environment. The calling workflow is suspended and resumed by the Orchestrator persistence infrastructure once the triggered job finishes. This allows the calling robot to be freed while waiting.
- Input and output arguments for the triggered process are configured via the dynamic **Arguments** / **Input** / **Output** properties in the designer. The designer auto-imports the argument schema from the selected process when `ProcessName` is set to a literal string. See **Authoring `Input` / `Output` in raw XAML** above for the three modes and their raw-XAML feasibility.
- The XAML-serialized property is `FailWhenFaulted` (default `True`). The Studio designer displays it under the inverted label **"Continue when job fails"** — checking that designer box sets `FailWhenFaulted = False`. Always use `FailWhenFaulted` as the attribute name in raw XAML.
- The `Job` output is of type `UiPath.Core.Activities.OrchestratorJob` — when binding from XAML, declare its namespace with `xmlns:uca="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"` and use `Variable x:TypeArguments="uca:OrchestratorJob"` for the receiving variable.
- `Machine` and `Account` support auto-complete from Orchestrator-connected data sources. Leave empty to allow Orchestrator to assign automatically.
- Both lists are scoped to `FolderPath`: `Machine` offers only the machines assigned to that folder, and `Account` only the unattended accounts available there. The permissions behind them are evaluated against the folder, not the tenant, so a folder-level role is sufficient and no tenant-wide `Machines.View` is required. Changing `FolderPath` re-queries both lists. Neither ever falls back to a tenant-wide list: leaving `FolderPath` empty scopes both to the folder Studio is currently working in, or to the personal workspace when there is none, the same folder the process list uses, and a folder that does not exist gives an empty list.
- `Machine` and `Account` narrow each other according to the folder's account-machine mappings: selecting an account limits the machines on offer to those it may execute on, and selecting a machine limits the accounts. Where a folder defines no mapping of its own, Orchestrator's tenant-level mapping applies. If either property is set to a variable or expression rather than a typed-in value, it cannot be read at design time, so it does not narrow the other list — the full folder list is offered instead. Execution is unaffected.
- In a solution, `Machine` and `Account` offer a list only while `ProcessName` is a variable or expression, because only then is `FolderPath` editable, and only for a typed-in `FolderPath`; with it empty the lists stay empty. When `ProcessName` is a solution process, the folder is decided at deployment, so both become expression editors: enter the names as string expressions, for example `"Machine-A-1"`, as they exist in the deployment folder. They are resolved there at run time, and a name that does not exist, or an account the folder does not map to the machine, fails the activity with a not-found error.
- `FolderPath` supports Orchestrator modern folder paths (e.g., `Finance/Invoices`).
