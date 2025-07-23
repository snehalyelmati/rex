from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, StateGraph, add_messages


# Step 1: Define the AgentState
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


# Node Definitions
def planner_node(state: AgentState):
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


# Step 2: Build the Agent Graph
async def build_agent():

    # Step 2.1: Graph Builder
    builder = StateGraph(AgentState)

    # Step 2.1.1: Add Nodes and Edges to build the required graphs
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

    # Step 2.1.2: Compile the graph
    return builder.compile()
