import os
from typing import TypedDict, Any

from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, END, START

from model import projectplan



load_dotenv()



llm = ChatOllama(
    model=os.getenv("OLLAMA_MODEL", "gemma4:31b-cloud").strip(),
    temperature=0,
)

planner_llm = llm.with_structured_output(projectplan)




class AgentState(TypedDict, total=False):
    idea: str
    requirements: str
    plan: dict[str, Any]
    error: str
    research: str
    clarification_questions: str
    architecture: str
    task_plan: str
    workflow_diagram: str
    quality_review: str
    implementation_guide: str




def ask_llm(role: str, task: str) -> str:
    response = llm.invoke(
        f"""
You are the {role} for an AI Project Architect.

Follow these rules:
- Be practical and technically accurate.
- Clearly label assumptions.
- Do not invent user requirements.
- Prefer a simple MVP before advanced features.

TASK:
{task}
"""
    )
    return str(response.content)





def Analyzer_Agent(state: AgentState):
    idea = state.get("idea", "").strip()

    if not idea:
        return {"error": "Please enter a project idea."}

    analysis_prompt = f"""
You are a Senior AI Project Requirements Analyst, Software
Architect, Product Manager, and Technical Mentor.

Analyze this project idea:
{idea}

Include:
1. Project overview and expected product.
2. Problem statement.
3. Target users.
4. User stories and use cases.
5. Functional requirements, separating MVP from later features.
6. Relevant non-functional requirements.
7. AI/automation requirements, tools, storage, evaluation, and risks.

Clearly distinguish known information from assumptions.
Do not invent numerical performance targets.
Keep the analysis useful and reasonably concise.
"""

    response = llm.invoke(analysis_prompt)

    return {"requirements": str(response.content)}



def clarification_Agent(state: AgentState):
    result = ask_llm(
        "Requirements Clarification Specialist",
        f"""
Project idea:
{state.get('idea', '')}

Initial analysis:
{state.get('requirements', '')[:2500]}

Identify important unanswered questions that could change
the architecture, cost, security, or project scope.
For each question, explain why it matters and suggest a
clearly labeled default assumption where appropriate.
Do not pretend the user has answered these questions.
Keep the response concise.
"""
    )
    return {"clarification_questions": result}




def Research_idea(state: AgentState):
    if not os.getenv("TAVILY_API_KEY"):
        return {
            "research": (
                "Web research skipped because TAVILY_API_KEY is missing. "
                "The remaining agents may use general model knowledge."
            )
        }

    try:
        search_tool = TavilySearch(max_results=5, topic="general")
        results = search_tool.invoke({
            "query": (
                "Official documentation and recommended technologies for "
                + state.get("idea", "")
            )
        })
        return {"research": str(results)[:4000]}
    except Exception as exc:
        return {"research": f"Research unavailable: {exc}"}




def Architecture_Agent(state: AgentState):
    result = ask_llm(
        "Software Architect",
        f"""
Project:
{state.get('idea', '')}

Requirements:
{state.get('requirements', '')[:2000]}

Research:
{state.get('research', '')[:1500]}

Design the system architecture. Explain:
1. Frontend and backend, if needed.
2. Main components and responsibilities.
3. Data flow between components.
4. Database and storage choices.
5. External APIs and integrations.
6. Security and error handling.
7. Why each technology is suitable.

Separate researched information from recommendations.
Avoid unnecessary technologies. Keep the answer concise.
"""
    )
    return {"architecture": result}




def plan_task(state: AgentState):
    result = ask_llm(
        "Technical Project Planner",
        f"""
Project:
{state.get('idea', '')}

Architecture:
{state.get('architecture', '')[:2000]}

Create an ordered implementation roadmap with 5 to 8 tasks.
For each milestone include its goal, tasks, required files,
dependencies, deliverable, acceptance criteria, and tests.
Start with the smallest working MVP.
Keep the answer concise.
"""
    )
    return {"task_plan": result}




def design_workflow(state: AgentState):
    result = ask_llm(
        "Workflow Designer",
        f"""
Project:
{state.get('idea', '')}

Architecture:
{state.get('architecture', '')[:1500]}

Task plan:
{state.get('task_plan', '')[:1500]}

Create a valid Mermaid flowchart beginning with `flowchart TD`.
Show user input, processing steps, storage and external tools
when relevant, plus success and failure paths.
Use simple node IDs and quoted labels.
Return diagram code only.
"""
    )

    result = result.replace("```mermaid", "").replace("```", "").strip()
    return {"workflow_diagram": result}




def generate_blueprint(state: AgentState):
    prompt = f"""
Create a practical project blueprint using the supplied
ProjectPlan schema.

PROJECT IDEA:
{state.get('idea', '')}

REQUIREMENTS:
{state.get('requirements', '')[:1200]}

CLARIFICATION QUESTIONS:
{state.get('clarification_questions', '')[:700]}

RESEARCH:
{state.get('research', '')[:1000]}

ARCHITECTURE:
{state.get('architecture', '')[:1200]}

IMPLEMENTATION PLAN:
{state.get('task_plan', '')[:1000]}

IMPORTANT SCHEMA RULES:
1. project_name must be a string.
2. problem_statement must be a string.
3. target must be a LIST of target-user descriptions.
4. features, technology, and risk must be lists.
5. component must be a list of objects.
6. Each component must contain:
   - name: string
   - purpose: string
   - input: list of strings
   - output: list of strings
   - dependencies: list of strings
7. milestone must be a list of objects.
8. Each milestone must contain:
   - name: string
   - goal: string
   - description: string
   - tasks: list of strings
   - dependencies: list of strings
   - deliverable: string
   - acceptance_criteria: list of strings
   - tests: list of strings

For example:
- target: ["QA engineers", "Software development teams"]
- input: ["Natural language testing requirement", "DOM snapshot"]
- output: ["Generated Playwright test script"]
- goal: "Build the first working automated browser test."

Follow the actual ProjectPlan schema exactly. Do not omit
required fields. Use concise, realistic MVP details.
Do not claim tests have been executed.
"""



def review_project(state: AgentState):
    result = ask_llm(
        "Senior Software Quality Reviewer",
        f"""
Review this proposed project design.

Idea:
{state.get('idea', '')}

Blueprint:
{str(state.get('plan', {}))[:1800]}

Architecture:
{state.get('architecture', '')[:1000]}

Tasks:
{state.get('task_plan', '')[:1000]}

Check missing requirements, inconsistent components,
incorrect dependencies, security/privacy risks, unrealistic
milestones, missing tests, and unnecessary complexity.
Classify findings as Critical, Important, or Optional.
Suggest concrete fixes. Do not claim code was executed or tested.
Keep the review concise.
"""
    )
    return {"quality_review": result}




def guide_implement_agent(state: AgentState):
    result = ask_llm(
        "Python Implementation Mentor",
        f"""
Give a concise, practical implementation guide for this project.

Project idea:
{state.get('idea', '')}

Blueprint:
{str(state.get('plan', {}))[:1500]}

Architecture:
{state.get('architecture', '')[:1000]}

Task plan:
{state.get('task_plan', '')[:1000]}

Include:
1. Suggested folder structure.
2. First files to create.
3. Recommended implementation order.
4. First milestone and how to test it.
5. Common errors to watch for.

Do not generate the entire application code.
"""
    )
    return {"implementation_guide": result}


# --------------------------------------------------
# 13. Build and compile the LangGraph workflow
# --------------------------------------------------

workflow = StateGraph(AgentState)

workflow.add_node("Analyzer_Agent", Analyzer_Agent)
workflow.add_node("clarification_Agent", clarification_Agent)
workflow.add_node("Research_idea", Research_idea)
workflow.add_node("Architecture_Agent", Architecture_Agent)
workflow.add_node("plan_task", plan_task)
workflow.add_node("design_workflow", design_workflow)
workflow.add_node("generate_blueprint", generate_blueprint)
workflow.add_node("review_project", review_project)
workflow.add_node("guide_implement_agent", guide_implement_agent)

workflow.add_edge(START, "Analyzer_Agent")
workflow.add_edge("Analyzer_Agent", "clarification_Agent")
workflow.add_edge("clarification_Agent", "Research_idea")
workflow.add_edge("Research_idea", "Architecture_Agent")
workflow.add_edge("Architecture_Agent", "plan_task")
workflow.add_edge("plan_task", "design_workflow")
workflow.add_edge("design_workflow", "generate_blueprint")
workflow.add_edge("generate_blueprint", "review_project")
workflow.add_edge("review_project", "guide_implement_agent")
workflow.add_edge("guide_implement_agent", END)

graph = workflow.compile()



if __name__ == "__main__":
    idea = input("Enter your project idea: ").strip()

    if not idea:
        raise SystemExit("Please enter a valid project idea.")

    try:
        result = graph.invoke({"idea": idea})

        print("\n========== PROJECT BLUEPRINT ==========")
        print(result.get("plan", {}))

        print("\n========== ARCHITECTURE ==========")
        print(result.get("architecture", ""))

        print("\n========== IMPLEMENTATION ROADMAP ==========")
        print(result.get("task_plan", ""))

        print("\n========== WORKFLOW DIAGRAM ==========")
        print(result.get("workflow_diagram", ""))

        print("\n========== QUALITY REVIEW ==========")
        print(result.get("quality_review", ""))

        print("\n========== IMPLEMENTATION GUIDE ==========")
        print(result.get("implementation_guide", ""))

        print("\n========== CLARIFICATION QUESTIONS ==========")
        print(result.get("clarification_questions", ""))

    except Exception as exc:
        print(f"Project workflow failed: {exc}")
