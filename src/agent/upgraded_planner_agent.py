import asyncio
from typing import Annotated, List, Sequence, TypedDict

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph, add_messages
from pydantic import BaseModel, Field

from src.utilities.constants import PLANNER_LLM, PLANNER_SYSTEM_PROMPT

# TODO:
# Step 1: Define the AgentState
# Step 2: Build the Agent Graph
#           - Graph Builder
#           - Add Nodes and Edges to build the required graphs
#           - Compile the graph
# Step 3: Implement business logic in each node.
#           - Planner Node


class Plan(BaseModel):
    """Plan to follow in future"""

    steps: List[str] = Field(
        description="Sequence of steps to follow to perform the task at hand, should be in sorted order"
    )


class AgentState(TypedDict):
    task: str
    messages: Annotated[Sequence[BaseMessage], add_messages]
    plan: Plan


# Node Definitions
async def planner_node(state: AgentState):
    """
    This node will trigger the agentic workflow.

    Inputs: System message, Task
    Output: Initialize plan and persist in-memory.

    """
    # Append new system message
    state = {
        "messages": [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=state["task"]),
        ],
    }

    # Initialize new plan
    planner = ChatOpenAI(model=PLANNER_LLM, temperature=0).with_structured_output(Plan)
    plan = await planner.ainvoke(state["messages"])

    state["plan"] = plan

    return state


def simple_react_agent(state: AgentState):
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
    result = asyncio.run(
        planner_node(
            AgentState(
                messages=[], task="To add 5+10 and then multiply the result by itself."
            )
        )
    )
    print(result)
    print("Done!")
