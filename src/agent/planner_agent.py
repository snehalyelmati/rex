import operator
from typing import Annotated, Dict, List, Sequence, Tuple, Union

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import create_react_agent
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class AgentState(TypedDict):
    input: str
    plan: List[str]
    past_steps: Annotated[List[Tuple], operator.add]
    response: str
    messages: Annotated[Sequence[BaseMessage], add_messages]


class Plan(BaseModel):
    """Plan to follow in future"""

    steps: List[str] = Field(
        description="different steps to follow, should be in sorted order"
    )


class Response(BaseModel):
    """Response to user."""

    response: str


class Act(BaseModel):
    """Action to perform."""

    action: Union[Response, Plan] = Field(
        description="Action to perform. If you want to respond to user, use Response. "
        "If you need to further use tools to get the answer, use Plan."
    )


planner_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """For the given objective, come up with a simple step by step plan. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.""",
        ),
        ("placeholder", "{messages}"),
    ]
)
planner = planner_prompt | ChatOpenAI(
    model="gpt-4.1-2025-04-14", temperature=0
).with_structured_output(Plan)

replanner_prompt = ChatPromptTemplate.from_template(
    """For the given objective, come up with a simple step by step plan. \
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps. \
The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.

Your objective was this:
{input}

Your original plan was this:
{plan}

You have currently done the follow steps:
{past_steps}

Past conversation history:
{messages}

Update your plan accordingly. If no more steps are needed and you can return to the user, then respond with that. Otherwise, fill out the plan. Only add steps to the plan that still NEED to be done. Do not return previously done steps as part of the plan."""
)

replanner = replanner_prompt | ChatOpenAI(
    # model="gpt-4o", temperature=0
    model="gpt-4.1-2025-04-14",
    temperature=0,
).with_structured_output(Act)


async def plan_step(state: AgentState):
    plan = await planner.ainvoke(
        {"messages": state["messages"] + [("user", "Task: " + state["input"])]}
    )
    return {
        "plan": plan.steps,
    }


async def execute_step(state: AgentState):
    plan = state["plan"]
    plan_str = "\n".join(f"{i+1}. {step}" for i, step in enumerate(plan))
    task = plan[0]
    task_formatted = f"""For the following plan:
{plan_str}\n\nYou are tasked with executing step {1}, {task}."""
    agent_response = await agent_executor.ainvoke(
        {"messages": [("user", task_formatted)]}
    )

    return {
        "past_steps": [(task, agent_response["messages"][-1].content)],
        # "messages": agent_response,
    }


async def replan_step(state: AgentState):
    output = await replanner.ainvoke(state)

    if isinstance(output.action, Response):
        return {
            "response": output.action.response,
            "messages": AIMessage(output.action.response),
        }
    else:
        return {"plan": output.action.steps}


def should_end(state: AgentState):
    if "response" in state and state["response"]:
        return END
    else:
        return "agent"


async def build_agent(tools_available):
    llm = ChatOpenAI(model="gpt-4o")
    prompt = "You are a helpful assistant."

    global agent_executor
    agent_executor = create_react_agent(llm, tools_available, prompt=prompt)

    builder = StateGraph(AgentState)

    builder.add_node("planner", plan_step)
    builder.add_node("agent", execute_step)
    builder.add_node("replan", replan_step)

    builder.add_edge(START, "planner")
    builder.add_edge("planner", "agent")
    builder.add_edge("agent", "replan")
    builder.add_conditional_edges(
        "replan",
        should_end,
        ["agent", END],
    )

    return builder.compile()
