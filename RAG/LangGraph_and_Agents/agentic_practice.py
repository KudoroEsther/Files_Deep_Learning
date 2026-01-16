# Practice Exercise Solutions - Simplified

from typing import TypedDict, Literal, Annotated
from pydantic import BaseModel, Field
import operator

# ============================================================================
# EXERCISE 1: Reflection with Quality Metrics
# ============================================================================

class QualityScore(BaseModel):
    clarity: int = Field(ge=1, le=5)
    completeness: int = Field(ge=1, le=5)
    accuracy: int = Field(ge=1, le=5)

class MetricState(TypedDict):
    task: str
    draft: str
    iterations: int

def metric_generate(state: MetricState) -> dict:
    if state["iterations"] == 0:
        prompt = f"Create a response for: {state['task']}"
    else:
        prompt = f"Improve this draft to be clearer and more complete:\n{state['draft']}"
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"draft": response.content}

def metric_critic(state: MetricState) -> dict:
    llm_with_structure = llm.with_structured_output(QualityScore)
    
    prompt = f"""Score this response (1-5 each):
Task: {state['task']}
Response: {state['draft']}

Rate clarity, completeness, and accuracy."""
    
    score = llm_with_structure.invoke([HumanMessage(content=prompt)])
    print(f"Iteration {state['iterations']+1} - Clarity:{score.clarity} Completeness:{score.completeness} Accuracy:{score.accuracy}")
    
    return {"iterations": state["iterations"] + 1}

def should_continue_metric(state: MetricState) -> Literal["generate", "__end__"]:
    if state["iterations"] == 0:
        return "generate"
    if state["iterations"] >= 2:
        return "__end__"
    # Add actual scoring logic here if needed
    return "__end__"

# Build graph
metric_builder = StateGraph(MetricState)
metric_builder.add_node("generate", metric_generate)
metric_builder.add_node("critic", metric_critic)

metric_builder.add_edge(START, "generate")
metric_builder.add_edge("generate", "critic")
metric_builder.add_conditional_edges("critic", should_continue_metric)

metric_agent = metric_builder.compile()


# ============================================================================
# EXERCISE 2: Plan-Execute + Reflection
# ============================================================================

class HybridState(TypedDict):
    input: str
    plan: list[str]
    step: int
    results: Annotated[list[str], operator.add]
    draft: str
    iterations: int

def plan(state: HybridState) -> dict:
    prompt = f"Create a 3-step plan for: {state['input']}"
    response = llm.invoke([HumanMessage(content=prompt)])
    
    steps = [line.strip() for line in response.content.split('\n') 
             if line.strip() and any(c.isdigit() for c in line[:3])]
    
    print(f"📋 Plan: {steps}")
    return {"plan": steps, "step": 0, "results": [], "iterations": 0}

def execute(state: HybridState) -> dict:
    current = state["plan"][state["step"]]
    print(f"⚙️ Step {state['step']+1}: {current}")
    
    response = llm.invoke([HumanMessage(content=f"Execute: {current}")])
    
    return {
        "results": [response.content],
        "step": state["step"] + 1
    }

def reflect(state: HybridState) -> dict:
    if state["iterations"] == 0:
        prompt = f"Summarize these results:\n{state['results']}"
    else:
        prompt = f"Improve this summary to be more beginner-friendly:\n{state['draft']}"
    
    response = llm.invoke([HumanMessage(content=prompt)])
    print(f"✍️ Draft iteration {state['iterations']+1}")
    
    return {"draft": response.content, "iterations": state["iterations"] + 1}

def route_execute(state: HybridState) -> Literal["execute", "reflect"]:
    return "execute" if state["step"] < len(state["plan"]) else "reflect"

def route_reflect(state: HybridState) -> Literal["reflect", "__end__"]:
    return "__end__" if state["iterations"] >= 2 else "reflect"

# Build graph
hybrid_builder = StateGraph(HybridState)
hybrid_builder.add_node("plan", plan)
hybrid_builder.add_node("execute", execute)
hybrid_builder.add_node("reflect", reflect)

hybrid_builder.add_edge(START, "plan")
hybrid_builder.add_edge("plan", "execute")
hybrid_builder.add_conditional_edges("execute", route_execute)
hybrid_builder.add_conditional_edges("reflect", route_reflect)

hybrid_agent = hybrid_builder.compile()


# ============================================================================
# TEST
# ============================================================================

print("EXERCISE 1: Metric Reflection")
result1 = metric_agent.invoke({"task": "Explain quantum computing", "draft": "", "iterations": 0})
print(f"\n✅ Final: {result1['draft']}\n")

print("\nEXERCISE 2: Hybrid Agent")
result2 = hybrid_agent.invoke({"input": "Research Python benefits and summarize for beginners"})
print(f"\n✅ Final: {result2['draft']}\n")
