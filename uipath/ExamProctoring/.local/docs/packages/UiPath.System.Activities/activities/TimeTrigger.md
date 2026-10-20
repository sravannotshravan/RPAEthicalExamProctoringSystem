# Time Trigger

`UiPath.Core.Activities.TimeTrigger`

Schedule a recurrent time to start a job.

**Package:** `UiPath.System.Activities`
**Category:** Triggers

## Properties

### Configuration

> In the designer these labels are **contextual**: the same field is reused across frequencies, so `DailyRepeat`, `HourlyRepeat`, `MonthlyRepeat`, and `MinuteByMinuteRepeat` all display **Trigger every**, and the `*StartingTime` fields display **At what time**. Which rows appear depends on the selected `Frequency` — see [Valid Configurations](#valid-configurations).

| Name | Display Name | Type | Default | Description |
|------|-------------|------|---------|-------------|
| `Frequency` | Frequency | `TimeFrequency` | — | The scheduling frequency mode. Determines which other scheduling properties are shown. |
| `TimeZone` | Timezone | `string` | — | The time zone used to interpret scheduling times. Supports IANA and Windows time zone identifiers. |
| `CronExpression` | Quartz Cron expression | `string` | `"0 0 12 ? * MON-FRI *"` | A Quartz-style cron expression. Visible only when `Frequency` is `CronExpression`. |
| `DailyRepeat` | Trigger every | `int?` | — | Repeat interval in days. Visible only when `Frequency` is `Daily`. |
| `DailyStartingTime` | At what time | `DateTime?` | — | The time of day to start when using the Daily frequency. Visible only when `Frequency` is `Daily`. |
| `HourlyRepeat` | Trigger every | `int?` | — | Repeat interval in hours. Visible only when `Frequency` is `Hourly`. |
| `HourlyStartingMinutes` | Starting at minute | `int?` | — | Minutes past the hour at which to start when using the Hourly frequency. Visible only when `Frequency` is `Hourly`. |
| `MinuteByMinuteRepeat` | Trigger every | `int?` | — | Repeat interval in minutes. Visible only when `Frequency` is `MinuteByMinute`. |
| `WeeklyDaysToRunOn` | On the following day(s) of the week | `List<DayOfWeek>` | — | Days of the week on which to trigger. Visible when `Frequency` is `Weekly`. |
| `WeeklyStartingTime` | At what time | `DateTime?` | — | The time of day to start when using the Weekly frequency. Visible only when `Frequency` is `Weekly`. |
| `MonthlyRepeat` | Trigger every | `int?` | — | Repeat interval in months. Visible only when `Frequency` is `Monthly`. |
| `MonthDaySelection` | On | `MonthDaySelectionType` | — | Controls whether to trigger on specific calendar days or on a weekday-of-month pattern. Visible only when `Frequency` is `Monthly`. |
| `MonthlyDaysToRunOn` | On the following day(s) of the week | `List<DayOfWeek>` | — | Days of the week to use with the monthly weekday pattern. |
| `DaysOfMonthToRunOn` | On the following day(s) of the month | `List<string>` | — | Specific calendar day numbers of the month to trigger on. |
| `MonthlyStartingTime` | At what time | `DateTime?` | — | The time of day to start when using the Monthly frequency. Visible only when `Frequency` is `Monthly`. |

### Output

| Name | Display Name | Kind | Type | Description |
|------|-------------|------|------|-------------|
| `Result` | Job data | OutArgument | `CurrentJobInfo` | Runtime information about the triggered job, including Process name, Workflow name, User Name, User Email, and Timestamp. |

## Valid Configurations

The properties shown in the designer depend on the selected `Frequency` value:

### Hourly

Set `Frequency` to `Hourly`. Configure:
- `HourlyRepeat` — run every N hours.
- `HourlyStartingMinutes` — minutes past the hour when the trigger fires.

### Daily

Set `Frequency` to `Daily`. Configure:
- `DailyRepeat` — run every N days.
- `DailyStartingTime` — time of day (hour and minute) at which to fire.

### Weekly

Set `Frequency` to `Weekly`. Configure:
- `WeeklyDaysToRunOn` — which days of the week to fire.
- `WeeklyStartingTime` — time of day at which to fire on those days.

### Monthly

Set `Frequency` to `Monthly`. Configure:
- `MonthlyRepeat` — run every N months.
- `MonthDaySelection` — choose between specific calendar days (`DaysOfMonthToRunOn`) or a weekday-of-month pattern (`MonthlyDaysToRunOn`).
- `MonthlyStartingTime` — time of day at which to fire.

### Minute By Minute

Set `Frequency` to `MinuteByMinute`. Configure:
- `MinuteByMinuteRepeat` — run every N minutes.

### Cron Expression

Set `Frequency` to `CronExpression`. Configure:
- `CronExpression` — a Quartz-style seven-field cron string (seconds, minutes, hours, day-of-month, month, day-of-week, year).
- `TriggerEveryPlaceHolder` is displayed as a read-only hint when `Frequency` is `Weekly` or `CronExpression`.

### Enum Reference

**`TimeFrequency`**

| Value | Description |
|-------|-------------|
| `Hourly` | Trigger every N hours |
| `Daily` | Trigger every N days at a specified time |
| `Weekly` | Trigger on specified days of the week |
| `Monthly` | Trigger on specified days of the month |
| `MinuteByMinute` | Trigger every N minutes |
| `CronExpression` | Cron Expression |

**`MonthDaySelectionType`**

| Value | Description |
|-------|-------------|
| `DayOfMonth` | Trigger on specific numbered days of the month |
| `DayOfWeek` | Trigger on a named weekday occurrence within the month |

## XAML Example

```xml
<!-- Daily at 09:00, every weekday -->
<ui:TimeTrigger
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Time Trigger"
    Frequency="Daily"
    DailyRepeat="1"
    DailyStartingTime="[New DateTime(2000,1,1,9,0,0)]"
    TimeZone="UTC"
    Result="[jobInfo]" />
```

```xml
<!-- Cron expression: every weekday at noon -->
<ui:TimeTrigger
    xmlns:ui="clr-namespace:UiPath.Core.Activities;assembly=UiPath.System.Activities"
    DisplayName="Time Trigger"
    Frequency="CronExpression"
    CronExpression="0 0 12 ? * MON-FRI *"
    TimeZone="UTC"
    Result="[jobInfo]" />
```

## Notes

- **Time Trigger** is a scope/container activity. Place the automation logic to execute on each scheduled firing inside its body.
- The `Result` output provides a `CurrentJobInfo` object accessible within the trigger body for runtime context.
- `TimeZone` accepts standard IANA time zone identifiers (e.g., `America/New_York`) or Windows time zone names (e.g., `Eastern Standard Time`).
- Cron expressions follow the Quartz scheduler format with seven fields. The default `"0 0 12 ? * MON-FRI *"` fires at 12:00 noon every weekday.
