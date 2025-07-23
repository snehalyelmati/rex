import asyncio
from textwrap import dedent
from typing import Annotated, Dict, List, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool, tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from src.utilities.constants import (
    PLANNER_LLM,
    PLANNER_SYSTEM_PROMPT,
    SIMPLE_ACTION_LLM,
    SIMPLE_ACTION_PROMPT,
)

# TODO:
# Step 1: Define the AgentState
# Step 2: Build the Agent Graph
#           - Graph Builder
#           - Add Nodes and Edges to build the required graphs
#           - Compile the graph
# Step 3: Implement business logic in each node.
#           - Planner Node
#           - ReAct agent


class Plan(BaseModel):
    """Plan to follow in future"""

    steps: List[str] = Field(
        description="Sequence of steps to follow to perform the task at hand, should be in sorted order"
    )

    def __getitem__(self, idx: int):
        return self.steps[idx]


class AgentState(TypedDict):
    task: str
    messages: Annotated[Sequence[BaseMessage], add_messages]
    plan: Plan
    tools: List[BaseTool]
    # tools_by_name: Dict[str, BaseTool]


# Node Definitions
async def planner_node(state: AgentState):
    """
    This node will trigger the agentic workflow. It will analyze the task at hand and prepares the plan of execution.

    Returns: The plan of action.
    """
    # Append new system message
    state["messages"].extend(
        [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=state["task"]),
        ]
    )

    # Initialize new plan
    planner = ChatOpenAI(model=PLANNER_LLM, temperature=0).with_structured_output(Plan)
    plan = await planner.ainvoke(state["messages"])

    state["plan"] = plan

    return state


async def simple_react_agent(state: AgentState):
    """
    This node will perform the current first step of the plan.

    Returns: AgentState with the result in messages.
    """
    plan = state["plan"]
    plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))
    task = plan[0]
    task_formatted = SIMPLE_ACTION_PROMPT.format(plan_str=plan_str, task=task)

    print(f'Tools right now: {state["tools"]}.\n')

    llm = ChatOpenAI(model=SIMPLE_ACTION_LLM, temperature=0)
    agent_executor = create_react_agent(
        model=llm, tools=state["tools"], prompt=task_formatted
    )

    agent_response = await agent_executor.ainvoke(
        {"messages": [("user", task_formatted)]}
    )

    state = {
        "messages": [agent_response],
    }

    return state


def replanner_node(state: AgentState):
    return state


def finalize_node(state: AgentState):
    return state


# Utility Functions
def should_continue():
    """This function decides whether to proceed with forward to work on the task or end processing."""
    pass


async def build_agent():
    builder = StateGraph(AgentState)

    builder.add_node("planner", planner_node)
    builder.add_node("simple_agent", simple_react_agent)
    builder.add_node("replanner", replanner_node)
    builder.add_node("finalize", finalize_node)

    builder.add_edge(START, "planner")
    builder.add_edge("planner", "simple_agent")
    builder.add_edge("simple_agent", "replanner")
    builder.add_conditional_edges(
        source="replanner",
        path=should_continue,
        path_map={
            "END": "finalize",
            "CONTINUE": "simple_agent",
        },
    )
    builder.add_edge("replanner", "finalize")
    builder.add_edge("finalize", END)

    return builder.compile()


# DEBUG CODE: Use `python -m src.agent.upgraded_planner_agent` to run.
if __name__ == "__main__":
    print("Starting debug...")
    state = AgentState(
        messages=[],
        task="To add 5+10 and then multiply the result by itself.",
        plan=Plan(steps=[]),
        tools=[],
    )

    state = asyncio.run(planner_node(state))
    print(state)
    print()

    result = asyncio.run(simple_react_agent(state))

    print(result)
    print("Done!")
