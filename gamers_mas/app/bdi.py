from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Goal:
    name: str
    priority: int = 1
    description: str = ""


@dataclass(frozen=True)
class Plan:
    name: str
    trigger: str
    priority: int = 1
    description: str = ""


@dataclass(frozen=True)
class PlanDecision:
    agent_name: str
    selected_plan: str
    reason: str
    beliefs: dict[str, Any]
    goals: list[str]
    considered_plans: list[str]

    def to_dict(self) -> dict:
        return {
            "agent_name": self.agent_name,
            "selected_plan": self.selected_plan,
            "reason": self.reason,
            "beliefs": self.beliefs,
            "goals": self.goals,
            "considered_plans": self.considered_plans,
        }


@dataclass
class BDIState:
    agent_name: str
    beliefs: dict[str, Any] = field(default_factory=dict)
    goals: list[Goal] = field(default_factory=list)
    plans: list[Plan] = field(default_factory=list)

    def set_belief(self, name: str, value: Any) -> None:
        self.beliefs[name] = value

    def get_belief(self, name: str, default: Any = None) -> Any:
        return self.beliefs.get(name, default)

    def add_goal(self, goal: Goal) -> None:
        self.goals.append(goal)

    def add_plan(self, plan: Plan) -> None:
        self.plans.append(plan)

    def sorted_goals(self) -> list[Goal]:
        return sorted(
            self.goals,
            key=lambda goal: (-goal.priority, goal.name),
        )

    def sorted_plans(self) -> list[Plan]:
        return sorted(
            self.plans,
            key=lambda plan: (-plan.priority, plan.name),
        )

    def plan_names(self) -> list[str]:
        return [plan.name for plan in self.sorted_plans()]

    def goal_names(self) -> list[str]:
        return [goal.name for goal in self.sorted_goals()]

    def decide(self, selected_plan_name: str, reason: str) -> PlanDecision:
        available_plan_names = {plan.name for plan in self.plans}

        if selected_plan_name not in available_plan_names:
            raise ValueError(
                f"Unknown plan '{selected_plan_name}' for agent '{self.agent_name}'."
            )

        return PlanDecision(
            agent_name=self.agent_name,
            selected_plan=selected_plan_name,
            reason=reason,
            beliefs=dict(self.beliefs),
            goals=self.goal_names(),
            considered_plans=self.plan_names(),
        )

    def select_highest_priority_plan(self, trigger: str, reason: str) -> PlanDecision:
        matching_plans = [
            plan for plan in self.sorted_plans()
            if plan.trigger == trigger
        ]

        if not matching_plans:
            raise ValueError(
                f"No plan found for trigger '{trigger}' in agent '{self.agent_name}'."
            )

        selected_plan = matching_plans[0]

        return self.decide(
            selected_plan_name=selected_plan.name,
            reason=reason,
        )