from textwrap import dedent

PLANNER_LLM = "gpt-4.1"
SIMPLE_ACTION_LLM = "gpt-4o"
REPLANNER_LLM = "gpt-4.1"
FINALIZER_LLM = "gpt-4o"

PLANNER_SYSTEM_PROMPT = dedent(
    """For the given objective, come up with a simple step by step plan.
This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps.
The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.
"""
)

SIMPLE_ACTION_PROMPT = dedent(
    """For the following plan:
    {plan_str}

You are tasked with executing step [1], {task}.
"""
)

REPLANNER_PROMPT = dedent(
    """Now, update the plan accordingly and return only the plan. If no more steps are needed and you can return to the user, then respond with that. Otherwise, fill out the plan. Only add steps to the plan that still NEED to be done. Do not return previously done steps as part of the plan.

Your objective is this:
{task}

Your original plan was this:
{plan}

Past conversation history:
{messages}
"""
)

FINALIZER_PROMPT = dedent(
    """Now, for the task, based on the conversation history, finalize the output to return to the user.

Your objective is this:
{task}

Past conversation history:
{messages}

Return only the answer, do not add anything that is not necessary.
"""
)
