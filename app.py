import streamlit as st

from Agent import graph
from memory import (
    init_memory_db,
    save_project,
    list_projects,
)


# --------------------------------------------------
# 1. PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Project Helper AI",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 Project Helper AI")

st.write(
    "Turn your project idea into a structured plan "
    "with the help of AI agents."
)

st.divider()


# --------------------------------------------------
# 2. INITIALIZE DATABASE
# --------------------------------------------------

try:
    init_memory_db()
except Exception as e:
    st.error("Database connection failed.")
    st.exception(e)
    st.stop()


# --------------------------------------------------
# 3. PROJECT IDEA INPUT
# --------------------------------------------------

st.subheader("💡 Generate a Project Plan")

with st.form("project_idea_form"):
    idea = st.text_area(
        "Describe your project idea",
        placeholder=(
            "Example: Build an AI interview preparation "
            "assistant using Python and LLMs. "
            "It should generate questions, evaluate answers, "
            "and track student progress."
        ),
        height=150,
    )

    generate_button = st.form_submit_button(
        "🚀 Generate Project Plan",
        type="primary",
        use_container_width=True,
    )


# --------------------------------------------------
# 4. RUN THE LANGGRAPH WORKFLOW
# --------------------------------------------------

if generate_button:
    if not idea.strip():
        st.warning("Please enter your project idea first.")

    else:
        try:
            with st.spinner(
                "🤖 AI agents are analyzing your project idea..."
            ):
                result = graph.invoke(
                    {"idea": idea.strip()}
                )

            if not isinstance(result, dict):
                raise TypeError(
                    "The LangGraph workflow must return a dictionary."
                )

            st.session_state["project_result"] = result
            st.session_state["project_idea"] = idea.strip()

            st.success("✅ Project plan generated successfully!")

        except Exception as e:
            st.error("Project generation failed.")
            st.exception(e)


# --------------------------------------------------
# 5. DISPLAY GENERATED RESULTS
# --------------------------------------------------

result = st.session_state.get("project_result")

if result:
    st.divider()
    st.subheader("📋 Generated Project Results")

    display_fields = {
        "requirements": "📝 Requirements",
        "research": "🔍 Research",
        "architecture": "🏗️ Architecture",
        "task_plan": "📌 Task Plan",
        "workflow_diagram": "🔄 Workflow Diagram",
        "plan": "📦 Project Blueprint",
        "quality_review": "✅ Quality Review",
        "implementation_guide": "💻 Implementation Guide",
        "error": "⚠️ Workflow Error",
    }

    displayed_anything = False

    for key, label in display_fields.items():
        value = result.get(key)

        if value is not None and value != "" and value != []:
            displayed_anything = True

            with st.expander(
                label,
                expanded=(key == "plan"),
            ):
                if isinstance(value, (dict, list)):
                    st.json(value)
                else:
                    st.write(value)

    if not displayed_anything:
        st.info(
            "The workflow returned a result, but no recognized "
            "output fields were populated."
        )
        st.json(result)


    # --------------------------------------------------
    # 6. SAVE GENERATED PROJECT TO POSTGRESQL
    # --------------------------------------------------

    st.subheader("💾 Save Your Project")

    if st.button(
        "💾 Save Project to Database",
        type="secondary",
        use_container_width=True,
    ):
        try:
            plan = result.get("plan") or {}

            if isinstance(plan, dict):
                project_name = plan.get(
                    "project_name",
                    "Untitled Project",
                )
                blueprint = plan
            else:
                project_name = "Untitled Project"
                blueprint = {"plan": str(plan)}

            project_id = save_project(
                project_name=project_name,
                idea=st.session_state.get(
                    "project_idea",
                    "",
                ),
                blueprint=blueprint,
            )

            st.success(
                f"Project saved successfully! ID: {project_id}"
            )

        except Exception as e:
            st.error("Could not save the project.")
            st.exception(e)


# --------------------------------------------------
# 7. DISPLAY SAVED PROJECTS
# --------------------------------------------------

st.divider()
st.subheader("🗂️ Saved Projects")

try:
    projects = list_projects()

    if projects:
        st.caption(f"Total saved projects: {len(projects)}")

        for project in projects:
            project_id = project.get("id", "N/A")
            project_name = project.get(
                "project_name",
                "Untitled Project",
            )

            with st.expander(
                f"📁 #{project_id} — {project_name}"
            ):
                st.write(
                    "**Project idea:**",
                    project.get("idea", "Not available"),
                )

                st.write(
                    "**Status:**",
                    project.get("status", "Unknown"),
                )

                st.write(
                    "**Current milestone:**",
                    project.get("current_milestone")
                    or "Not started",
                )

                if project.get("updated_at"):
                    st.caption(
                        f"Last updated: {project['updated_at']}"
                    )

    else:
        st.info(
            "No projects saved yet. Generate a project plan "
            "and save it to see it here."
        )

except Exception as e:
    st.error("Could not load saved projects.")
    st.exception(e)


# --------------------------------------------------
# 8. FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "🤖 Project Helper AI | Powered by LangGraph, "
    "LLMs, Streamlit, and PostgreSQL"
)
idea = st.text_area(
    "Enter your project idea",
    placeholder="Example: Build an AI interview preparation assistant...",
    height=150
)

if st.button("🚀 Generate Project Plan"):
    if not idea.strip():
        st.warning("Please enter your project idea first.")
    else:
        with st.spinner("AI agents are building your project plan..."):
            try:
                result = graph.invoke({"idea": idea.strip()})
                st.success("Project plan generated!")

                st.subheader("📋 Requirements")
                st.write(result.get("requirements", ""))

                st.subheader("🏗️ Architecture")
                st.write(result.get("architecture", ""))

                st.subheader("📝 Implementation Roadmap")
                st.write(result.get("task_plan", ""))

                st.subheader("🔄 Workflow Diagram")
                st.code(
                    result.get("workflow_diagram", ""),
                    language="mermaid"
                )

                st.subheader("💡 Implementation Guide")
                st.write(result.get("implementation_guide", ""))

            except Exception as e:
                st.error(f"Project workflow failed: {e}")

