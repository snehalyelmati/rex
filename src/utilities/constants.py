from textwrap import dedent

# PLANNER_LLM = "gpt-4.1"
PLANNER_LLM = "gpt-4.1"
SIMPLE_ACTION_LLM = "gpt-4.1"
SUMMARIZER_LLM = "gpt-4o"
REPLANNER_LLM = "gpt-4.1"
FINALIZER_LLM = "gpt-4.1"

PLANNER_SYSTEM_PROMPT = dedent(
    """Planner Stage:
- For the given objective, come up with a simple step by step plan based on the tools available to you.
- This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps.
- Be very explicit and detailed with the steps of the plan. Add all the necessary information in the step.
- The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.
"""
)

SIMPLE_ACTION_PROMPT = dedent(
    """For the following plan:
    {plan_str}

You are tasked with executing step [1], {task}.

Summarized past conversation history:
{conv_history}
"""
)

SUMMARY_PROMPT = dedent(
    """This is the past conversation, summarize it to retain key information and details.
    {messages}
"""
)

REPLANNER_PROMPT = dedent(
    """Replanner Stage:
Update the plan considering previous steps and conversation history and return only the plan. If no more steps are needed and you can return to the user, then respond with that. 

Otherwise, fill out the plan. 
- For the given objective, come up with a simple step by step plan based on the tools available to you.
- This plan should involve individual tasks, that if executed correctly will yield the correct answer. Do not add any superfluous steps.
- Be very explicit and detailed with the steps of the plan. Add all the necessary information in the step.
- The result of the final step should be the final answer. Make sure that each step has all the information needed - do not skip steps.
- If information is already available in the conversation history, do not call additional tools for the same purpose. Do not do any redundant tool calls.

Your objective is this:
{task}

Your original plan was this:
{plan}

Only add steps to the plan that still NEED to be done. Do not return previously done steps as part of the plan.
"""
)

FINALIZER_PROMPT = dedent(
    """Now, for the task, based on the conversation history, finalize the output to return to the user.

Your objective is this:
{task}

Return only the answer, do not add anything that is not necessary.
"""
)

_PAST_HISTORY = """
Past conversation history:
{messages}
"""
