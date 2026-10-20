# Evaluate Business Rule

`UiPath.Core.Activities.EvaluateBusinessRule`

Evaluates a DMN (Decision Model and Notation) business rule file and returns the result.

**Package:** `UiPath.System.Activities`
**Category:** Workflow

## Properties

### Input

| Name | Display Name | Kind | Type | Required | Default | Description |
|------|-------------|------|------|----------|---------|-------------|
| `BusinessRule` | Business rule | `InArgument` | `string` | Yes | — | The path or identifier of the DMN business rule file to evaluate. Supports expression auto-complete. |
| `Arguments` | Inputs | `Property` | `Dictionary<string, Argument>` | No | `new Dictionary<string, Argument>()` | The named input and output arguments passed to and from the business rule. Populated from the rule file definition. |
| `ArgumentsVariable` | Inputs variable | `Property` | `InArgument<Dictionary<string, object>>` | No | — | An alternative way to supply input arguments as a single dictionary variable instead of individual named arguments. |

## XAML Example

```xml
<ui:EvaluateBusinessRule
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Evaluate Business Rule">
  <ui:EvaluateBusinessRule.BusinessRule>
    <InArgument x:TypeArguments="x:String">
      <VisualBasicValue x:TypeArguments="x:String" ExpressionText="&quot;Rules\LoanApproval.dmn&quot;" />
    </InArgument>
  </ui:EvaluateBusinessRule.BusinessRule>
  <ui:EvaluateBusinessRule.Arguments>
    <!-- argument entries are populated automatically from the .dmn file -->
  </ui:EvaluateBusinessRule.Arguments>
</ui:EvaluateBusinessRule>
```

## Notes

- This activity is marked **experimental** in the designer (indicated by the `ExperimentalLabel` property rendered as an info label).
- `Arguments` and `ArgumentsVariable` provide two different ways to supply input data to the rule:
  - `Arguments` is a structured dictionary of typed `Argument` objects (input and output) that is populated automatically when a valid `BusinessRule` file is selected. In a project it is derived from the rule downloaded from Orchestrator: for a rule package (`.uirule`) from the `entry-points.json` manifest inside it, falling back to the model in the package only for older packages that carry no manifest, and for a DMN file published on its own from the model itself. The manifest comes first because it is the only place a published rule's argument schemas exist, and because a published package can hold a DMN version the in-process parser does not read. In a Solution it is derived from the input and output JSON Schemas in the business rule's resource spec (the flat `inputArgumentsSchemaV2`/`outputArgumentsSchemaV2` pair, or the default decision among `entryPoints`), the same source Run Job uses for a process. When the spec carries no contract, the designer shows an info message and the arguments can be entered manually.
  - `ArgumentsVariable` accepts a pre-built `Dictionary<string, object>` variable for dynamic or programmatic argument supply.
- Output values from the DMN decision are written back into the output-direction entries of the `Arguments` dictionary. Values are converted to the declared argument type when the engine returns a different one (for example a JSON integer into an `Int32` argument).
- The `InfoBox` property is a designer-only text block used to surface contextual help; it has no runtime effect.
- Decision outputs that look like ISO-8601 timestamps are returned as `DateTime` values rather than strings. Typed `DateTime` arguments are unaffected; a `String`-typed argument or an untyped `ArgumentsVariable` entry receives a `DateTime` where earlier versions gave the original string.

## Evaluation engine

All decisions in the DMN model are evaluated and their outputs merged. When two decisions produce the same output name, the first value is kept and a warning is logged.

The engine follows the rule's storage format, which the designer resolves when the rule is selected and stores in `RuleFormat`:

| `RuleFormat` | tenant enabled | tenant not enabled |
|---|---|---|
| `Dmn` | in-process DMN engine | in-process DMN engine |
| `UiRule` | Business Rules engine service | fails: a package cannot be read in process |
| unset | in-process DMN engine | in-process DMN engine |

"Tenant enabled" means the platform reports the Business Rules service as provisioned (`IAccessProvider.GetResourceUrl("businessrules")`, behind `ExecutorFeatureKeys.AccessProviderV3`) and the `BusinessRuleRpaActivityEnabled` flag of the `business-rules` feature-flag application is on. The flag is read through the platform feature-flags client provider and cached for five minutes per tenant; when a refresh fails the last known value is kept for one minute. When a `UiRule` rule finds the tenant not enabled, the activity throws with error code `System.BusinessRules.Sys.ServiceRequired`, because the rule cannot be evaluated any other way.

`RuleFormat` is unset for a workflow authored before the property existed, for a rule named by an expression rather than chosen in the picker, and for a rule that is not published at all. Those run in process on every tenant, so a published workflow does not change engine because the tenant it runs in has the service. Only `UiRule` asks service discovery and the feature flag; every other format makes no extra call.

The call is made through the `UiPath.BusinessRules.Client` SDK, authenticated with the robot's token requested at scope `Orchestrator` — the same scope the activity has always sent, because the engine accepted an Orchestrator-scoped token when the request still went through the Orchestrator client. `businessrules` is the service's name in the platform service registry, not a token scope. The SDK chooses the endpoint from the request it is given:

- **Deployed.** The rule was found in Orchestrator, so its folder key and published version are sent and it is evaluated at `/v1/business-rules/evaluate`. This covers both a named `FolderPath` and an empty one: an empty `FolderPath` means the rule lives in the job's own folder, and the lookup is already scoped there.
- **Debug.** `FolderPath` is empty **and** Orchestrator lists no rule of that name in the job's folder, so the rule is not published anywhere and the only copy is the one in the job's Studio project. The job's key is sent instead of a folder key, and the service resolves the project from that job's lineage, at `/v1/business-rules/debug/evaluate`. The rule's version is not sent on this path — a version names a deployed rule, which is not what is being evaluated.

A `FolderPath` that names a folder is always a deployed run, even when the rule is not found there or its folder key cannot be resolved: it fails as the deployed run it is, rather than evaluating whatever the job's Studio project happens to hold under the same name.

A rule that is published to the job's folder **and** also edited in the Studio project evaluates the **published** copy. Publish the edit to evaluate it.

The SDK retries transient failures, so `TimeoutMS` bounds each attempt rather than the whole call; the activity's own cancellation still bounds the operation as a whole. It does not retry on the debug path, because that path re-reads and re-compiles the Studio project on every call.

The engine used is logged once at Verbose level, as `Business rule engine: Local` or `Business rule engine: BusinessRulesService`.

The in-process path also guards against the artifact not matching the stored format: a rule that turns out to be a package throws with error code `System.BusinessRules.Sys.UnexpectedRuleFormat`, naming the rule, rather than failing as an XML parsing error.

A failed remote evaluation throws with error code `System.BusinessRules.Sys.EngineEvaluationFailed` and the engine's error detail; it does not fall back to the in-process engine. An output value that cannot be converted to the declared argument type throws with error code `System.BusinessRules.Sys.OutputConversionFailed`, naming the argument.
