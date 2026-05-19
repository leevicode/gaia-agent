# BDI Design

This document explains the BDI-style reasoning used in the Game Deal-Finding MAS.

BDI means:

- **Beliefs** - what an agent currently knows or assumes
- **Goals** - what the agent wants to achieve
- **Plans** - possible actions the agent can choose
- **Plan selection** - the decision process for choosing one plan
- **Trace** - a record of the decision

The project uses SPADE for agent execution and messaging. It adds BDI concepts manually because the assignment allows either a BDI framework or manual BDI implementation.

## Assignment connection

The third project requires the system to clearly demonstrate:

- how beliefs are represented and updated
- how goals are selected or prioritized
- how plans are chosen and executed

This project demonstrates those requirements through:

```text
app/bdi.py
app/bdi_trace_store.py
bdi_trace.json
```

The runtime trace records the beliefs, goals, considered plans, selected plan, and reason for each important BDI decision.

## Why manual BDI

The original system already used SPADE agents and XMPP communication. Replacing it with another framework would risk breaking the working MAS.

Manual BDI was chosen because it:

- preserves SPADE and Prosody communication
- keeps the code understandable
- makes decisions deterministic
- gives clear report evidence
- avoids adding unnecessary LLM or framework complexity
- directly matches the assignment focus on beliefs, goals, and plans

## BDI core classes

The BDI core is in:

```text
app/bdi.py
```

### Goal

A goal contains:

```text
name
priority
description
```

Example:

```text
recommend_best_legitimate_deal
priority: 10
```

### Plan

A plan contains:

```text
name
trigger
priority
description
```

Example:

```text
select_legitimate_and_warn
trigger: legitimate_and_gray_market_available
priority: 10
```

### BDIState

`BDIState` holds:

```text
agent_name
beliefs
goals
plans
```

It also provides:

```text
set_belief
get_belief
add_goal
add_plan
select_highest_priority_plan
decide
```

### PlanDecision

`PlanDecision` records:

```text
agent_name
selected_plan
reason
beliefs
goals
considered_plans
```

It can be converted to a dictionary and saved into `bdi_trace.json`.

## BDI trace persistence

BDI traces are stored through:

```text
app/bdi_trace_store.py
```

The output file is:

```text
bdi_trace.json
```

Each trace entry represents one completed request. A software request now normally records:

```text
SoftwareCoordinatorAgent
AuthorizedResellerAgent
RecommendationAgent
```

A local console request normally records:

```text
LocalCoordinatorAgent
ValueRankerAgent
```

## Example trace shape

A simplified trace looks like this:

```json
{
  "request_id": "request-123",
  "scenario": "software_deal",
  "query": "Crimson Desert",
  "trace_count": 3,
  "traces": [
    {
      "agent_name": "SoftwareCoordinatorAgent",
      "selected_plan": "query_software_sources",
      "beliefs": {
        "match_status": "resolved",
        "title_is_resolved": true
      },
      "goals": [
        "resolve_software_title",
        "avoid_edition_mixups",
        "query_sources_only_after_resolution"
      ],
      "considered_plans": [
        "handle_ambiguity",
        "query_software_sources",
        "handle_not_found"
      ],
      "reason": "The requested game title resolved to one exact title, so source agents can be queried safely."
    }
  ]
}
```

## BDI agent: SoftwareCoordinatorAgent

### Purpose

Coordinates the software deal scenario.

### Main beliefs

| Belief | Meaning |
|---|---|
| `game_title` | user-provided title |
| `match_mode` | fuzzy or exact |
| `match_status` | resolved, ambiguous, or not_found |
| `resolved_game_title` | exact title after resolution |
| `suggestion_count` | number of ambiguity options |
| `title_is_resolved` | whether title has one exact result |
| `title_is_ambiguous` | whether input matches multiple titles |
| `title_not_found` | whether title matches no catalog entry |
| `exact_match_required_before_source_query` | source agents should not be queried until title is exact |
| `software_source_agents_available` | source agents are expected to be available |

### Goals

| Goal | Priority | Meaning |
|---|---:|---|
| `resolve_software_title` | 10 | Resolve title before searching |
| `avoid_edition_mixups` | 9 | Avoid mixing base game and editions |
| `query_sources_only_after_resolution` | 8 | Query sources only after exact resolution |

### Plans

| Plan | Trigger | Meaning |
|---|---|---|
| `handle_ambiguity` | ambiguous | Ask the user to choose an exact title |
| `query_software_sources` | resolved | Query official, authorized, and gray-market agents |
| `handle_not_found` | not_found | Report no matching title |

### Example

Input:

```text
crimson
```

Selected plan:

```text
handle_ambiguity
```

Input after choosing:

```text
Crimson Desert
```

Selected plan:

```text
query_software_sources
```

## BDI agent: AuthorizedResellerAgent

### Purpose

Provides authorized reseller software deals. It uses CheapShark first by default and mock data as fallback.

### Main beliefs

| Belief | Meaning |
|---|---|
| `game_title` | exact resolved game title |
| `match_mode` | fuzzy or exact |
| `source_type` | authorized_reseller |
| `real_source_enabled` | whether CheapShark is enabled |
| `real_source_available` | whether CheapShark responded successfully |
| `real_source_returned_deals` | whether CheapShark returned usable deals |
| `mock_fallback_available` | whether mock fallback can be used |
| `mock_source_available` | whether mock source is available |
| `preserve_demo_stability` | demo should continue even if live source fails |
| `real_source_error` | error text if live source failed |

### Goals

| Goal | Priority | Meaning |
|---|---:|---|
| `find_authorized_reseller_deals` | 10 | Find authorized reseller deals |
| `preserve_demo_stability` | 9 | Fall back safely if live source fails |
| `prepare_for_real_source_integration` | 8 | Keep source integration extensible |

### Plans

| Plan | Trigger | Meaning |
|---|---|---|
| `query_real_source` | real source available and useful | Use CheapShark |
| `fallback_to_mock_source` | real source failed or returned no usable deals | Use mock data |
| `use_mock_source` | real source disabled | Use mock data |
| `return_no_results` | no real result and no fallback | Return no results |

### Non-trivial decision

This agent handles uncertainty from an external source. CheapShark can be unavailable, return no exact-title results, or return related products. The agent must preserve demo stability by falling back to mock data when necessary.

## BDI agent: RecommendationAgent

### Purpose

Selects the best legitimate software deal and warns about gray-market offers.

### Main beliefs

| Belief | Meaning |
|---|---|
| `game_title` | game being evaluated |
| `total_deal_count` | all deals received |
| `legitimate_deal_count` | non-gray-market deals |
| `recommendable_legitimate_deal_count` | legitimate deals with numeric EUR price |
| `foreign_currency_deal_count` | legitimate deals not yet EUR-comparable |
| `gray_market_deal_count` | gray-market deals |
| `legitimate_deal_available` | at least one recommendable legitimate deal exists |
| `foreign_currency_deal_available` | non-EUR deals exist |
| `gray_market_available` | gray-market deals exist |
| `gray_market_is_risky` | gray-market sources are risky |
| `do_not_compare_usd_as_eur` | USD must not be ranked as EUR unless converted |

### Goals

| Goal | Priority | Meaning |
|---|---:|---|
| `recommend_best_legitimate_deal` | 10 | Recommend best legitimate deal |
| `avoid_recommending_gray_market_as_main_choice` | 9 | Do not choose gray-market as main recommendation |
| `avoid_mixing_currencies_without_conversion` | 9 | Do not compare USD as EUR |
| `warn_about_gray_market` | 8 | Warn if gray-market offers exist |

### Plans

| Plan | Trigger | Meaning |
|---|---|---|
| `select_legitimate_and_warn` | legitimate and gray-market available | Recommend legitimate deal and warn |
| `select_legitimate_only` | only legitimate available | Recommend legitimate deal |
| `report_no_legitimate_deal` | no legitimate EUR-comparable deal | Report no main recommendation |

### Example

If CheapShark returns a converted EUR deal and gray-market offers exist:

```text
selected_plan: select_legitimate_and_warn
```

Gray-market is not chosen even if it is cheaper.

## BDI agent: LocalCoordinatorAgent

### Purpose

Coordinates local console search.

### Main beliefs

| Belief | Meaning |
|---|---|
| `product_name` | user-provided console product |
| `max_price` | user price limit |
| `radius_km` | user distance limit |
| `match_mode` | fuzzy or exact |
| `match_status` | resolved, ambiguous, or not_found |
| `resolved_product_name` | exact product edition |
| `product_is_resolved` | one exact product found |
| `product_is_ambiguous` | multiple editions match |
| `product_not_found` | no product matched |
| `price_constraint_present` | max price is provided |
| `radius_constraint_present` | radius is provided |

### Goals

| Goal | Priority | Meaning |
|---|---:|---|
| `resolve_console_product` | 10 | Resolve console edition |
| `avoid_console_edition_mixups` | 9 | Avoid mixing Disc and Digital editions |
| `respect_user_price_and_radius_constraints` | 8 | Use max price and radius |
| `query_sources_only_after_resolution` | 7 | Query only after exact product is known |

### Plans

| Plan | Trigger | Meaning |
|---|---|---|
| `handle_ambiguity` | ambiguous | Ask user to choose an edition |
| `query_console_sources` | resolved | Query official and marketplace agents |
| `handle_not_found` | not_found | Report no matching product |

## BDI agent: ValueRankerAgent

### Purpose

Ranks local console deals.

### Main beliefs

| Belief | Meaning |
|---|---|
| `product_name` | console product being ranked |
| `total_deal_count` | number of deals received |
| `deals_available` | whether ranking is possible |
| `used_or_refurbished_deal_count` | count of condition-risky offers |
| `lower_trust_deal_count` | count of offers below trust threshold |
| `ranking_uses_price_shipping_trust_and_distance` | ranking uses multiple factors |

### Goals

| Goal | Priority | Meaning |
|---|---:|---|
| `rank_local_console_deals_by_value` | 10 | Rank offers by value |
| `avoid_blindly_selecting_cheapest_offer` | 9 | Consider trust and distance too |
| `support_warning_generation` | 8 | Preserve information for warnings |

### Plans

| Plan | Trigger | Meaning |
|---|---|---|
| `rank_available_deals` | deals_available | Sort deals |
| `report_no_deals` | no_deals_available | Report no results |

## Why these decisions are non-trivial

The software scenario includes:

- ambiguous user input
- uncertain external live source
- fallback planning
- related-product filtering
- currency conversion
- gray-market risk conflict
- multi-step cooperation

The local scenario includes:

- ambiguous edition names
- price and radius constraints
- ranking with multiple factors
- trust and condition warnings

This satisfies the assignment requirement for non-trivial decision making.

## How beliefs are updated

Beliefs are created from:

- user input
- catalog matching result
- source response result
- live source success or failure
- number of deals returned
- currency conversion result
- presence of gray-market offers
- local ranking input

The project does not implement a continuous perception loop like a full AgentSpeak interpreter. Instead, it builds a fresh `BDIState` at each decision point. That is sufficient for this assignment because the decision trace clearly shows which beliefs were used for each plan selection.

## How goals are prioritized

Goals are stored as `Goal` objects with integer priority.

Higher priority goals sort first.

Example:

```text
recommend_best_legitimate_deal: 10
avoid_recommending_gray_market_as_main_choice: 9
warn_about_gray_market: 8
```

This gives the report a clear way to show which goals matter most.

## How plans are selected

Plans are stored as `Plan` objects with triggers and priorities.

For example, the software coordinator has:

```text
handle_ambiguity -> ambiguous
query_software_sources -> resolved
handle_not_found -> not_found
```

When the `match_status` belief is `ambiguous`, the selected plan is `handle_ambiguity`.

## How plans are executed

After the selected plan is recorded, the agent performs the related action.

Examples:

| Selected plan | Execution |
|---|---|
| `handle_ambiguity` | send ambiguity choices to OutputAgent |
| `query_software_sources` | send requests to source agents |
| `query_real_source` | query CheapShark |
| `fallback_to_mock_source` | query mock authorized reseller source |
| `select_legitimate_and_warn` | select legitimate deal and attach gray-market warning |
| `rank_available_deals` | sort local console offers |

## Evidence to include in the report

Use screenshots showing:

1. Software ambiguity:
   - input `crimson`
   - selected plan `handle_ambiguity`
   - choices printed

2. Software exact run:
   - selected plan `query_software_sources`
   - `AuthorizedResellerAgent` selected `query_real_source`
   - converted CheapShark deal
   - gray-market warning

3. Local ambiguity:
   - input `Playstation`
   - selected plan `handle_ambiguity`
   - Disc/Digital choices

4. Local ranking:
   - selected plan `query_console_sources`
   - `ValueRankerAgent` selected `rank_available_deals`
   - top ranked deals and warnings

5. `bdi_trace.json`:
   - software trace with 3 agents
   - local trace with 2 agents


