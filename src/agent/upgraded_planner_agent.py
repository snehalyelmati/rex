import asyncio
from typing import Annotated, List, Sequence, TypedDict

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field

from src.utilities.constants import (
    FINALIZER_LLM,
    FINALIZER_PROMPT,
    PLANNER_LLM,
    PLANNER_SYSTEM_PROMPT,
    REPLANNER_LLM,
    REPLANNER_PROMPT,
    SIMPLE_ACTION_LLM,
    SIMPLE_ACTION_PROMPT,
    SUMMARIZER_LLM,
    SUMMARY_PROMPT,
)


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
    state["messages"].extend(
        [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=state["task"]),
        ]
    )

    llm = ChatOpenAI(model=PLANNER_LLM, temperature=0).with_structured_output(Plan)
    plan = await llm.ainvoke(state["messages"])
    state["plan"] = plan

    return state


async def simple_react_agent(state: AgentState):
    """
    This node will perform the current first step of the plan.

    Returns: AgentState with the result in messages.
    """
    plan = state["plan"]
    plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan.steps))
    task = plan[0]

    # Summarize past conversation history
    summarizer_llm = ChatOpenAI(model=SUMMARIZER_LLM, temperature=0)
    summary_prompt = SUMMARY_PROMPT.format(messages=state["messages"])
    summary = summarizer_llm.invoke(summary_prompt).content

    task_formatted = SIMPLE_ACTION_PROMPT.format(
        plan_str=plan_str, task=task, conv_history=summary
    )
    # print(f'Tools right now: {state["tools"]}.\n')

    # Agent LLM call
    llm = ChatOpenAI(model=SIMPLE_ACTION_LLM, temperature=0)
    agent_executor = create_react_agent(
        model=llm, tools=state["tools"], prompt=task_formatted
    )

    agent_response = await agent_executor.ainvoke(
        {"messages": [HumanMessage(content=task_formatted)]}
    )

    state["messages"].extend(
        [create_message_copy(m) for m in agent_response["messages"]]
    )

    return state


def create_message_copy(message):
    """Create a copy of a message maintaining only the required attributes for better context management."""
    if isinstance(message, ToolMessage):
        return ToolMessage(
            content=message.content,
            tool_call_id=message.tool_call_id,  # Important for tool calling
            id=getattr(message, "id", None),
        )
    elif isinstance(message, AIMessage):
        kwargs = {"content": message.content, "id": getattr(message, "id", None)}
        # Preserve tool_calls if they exist
        if hasattr(message, "tool_calls") and message.tool_calls:
            kwargs["tool_calls"] = message.tool_calls
        return AIMessage(**kwargs)
    else:
        # For HumanMessage, SystemMessage, etc.
        return type(message)(content=message.content, id=getattr(message, "id", None))


async def replanner_node(state: AgentState):
    """
    This node will check the current plan and modify it based on steps done and results returned in the previous steps.

    Returns: AgentState with updated plan.
    """
    state["messages"].append(
        HumanMessage(
            content=REPLANNER_PROMPT.format(
                task=state["task"],
                plan=state["plan"],
            )
        )
    )

    llm = ChatOpenAI(model=REPLANNER_LLM, temperature=0).with_structured_output(Plan)
    plan = await llm.ainvoke(state["messages"])
    state["plan"] = plan

    return state


async def finalize_node(state: AgentState):
    """
    This node will take into account of all the tasks done till now and prepare the final answer to return.

    Returns: AgentState with the final result in messages.
    """

    state["messages"].append(
        HumanMessage(
            content=FINALIZER_PROMPT.format(
                task=state["task"],
                plan=state["plan"],
            )
        )
    )

    llm = ChatOpenAI(model=FINALIZER_LLM, temperature=0)
    result = await llm.ainvoke(state["messages"])
    state["messages"].append(AIMessage(content=result.content))

    return state


# Utility Functions
def should_continue(state: AgentState):
    """This function decides whether to proceed with forward to work on the task or end processing."""

    if state["plan"].steps:
        return "CONTINUE"
    else:
        return "END"


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

    plan_state = asyncio.run(planner_node(state))

    action_state = asyncio.run(simple_react_agent(plan_state))
    print(f"Action_1 state: {action_state}\n")

    replanner_state = asyncio.run(replanner_node(action_state))
    print(f"Replanner_1 state: {replanner_state}\n")

    i = 2
    while replanner_state["plan"].steps:
        action_state = asyncio.run(simple_react_agent(plan_state))
        print(f"Action_{i} state: {action_state}\n")

        replanner_state = asyncio.run(replanner_node(action_state))
        print(f"Replanner_{i} state: {replanner_state}\n")

    final_state = asyncio.run(finalize_node(replanner_state))
    print(f"Final state: {final_state}\n")

    print("Done!")
