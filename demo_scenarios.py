"""
Nova Memory 2.0 — Demo Scenarios

Three end-to-end demonstrations that run with zero external dependencies
(only stdlib + numpy, which is already in requirements.txt):

  1. Healthcare AI Assistant
  2. Semiconductor Process Optimisation
  3. Education Personalisation

Each scenario exercises:
  - Multi-agent communication (CommunicationProtocol)
  - Real-time fine-tuning (FineTuningEngine — numpy mode)
  - Shared memory coordination (SharedMemory)

Run:
    python demo_scenarios.py
"""

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# Scenario 1 — Healthcare AI Assistant
# ---------------------------------------------------------------------------

def run_healthcare_demo() -> Dict[str, Any]:
    """
    Healthcare AI Assistant demo.

    Shows multi-agent coordination between a Healthcare Agent and a
    Data Analyser Agent, with real-time fine-tuning on patient interactions.
    """
    print("\n" + "=" * 70)
    print("DEMO SCENARIO 1: Healthcare AI Assistant")
    print("=" * 70)

    from core.multi_agent_communication import CommunicationProtocol, Agent
    from core.real_time_fine_tuning import FineTuningEngine

    # 1. Initialise agents
    print("\n1. Initialising multi-agent system...")
    protocol = CommunicationProtocol()

    protocol.register_agent(Agent(
        agent_id="healthcare_agent",
        name="Healthcare Agent",
        role="healthcare_agent",
        capabilities=["patient_history", "diagnosis", "treatment_planning"],
    ))
    protocol.register_agent(Agent(
        agent_id="data_analyzer_agent",
        name="Data Analyser Agent",
        role="data_analyzer",
        capabilities=["data_processing", "analysis", "reporting"],
    ))
    print("   [OK] Agents registered")

    # 2. Fine-tuning engine
    print("\n2. Initialising real-time fine-tuning engine...")
    fine_tuning = FineTuningEngine(model_size="small")
    print("   [OK] Fine-tuning engine initialised")

    # 3. Store patient memories
    print("\n3. Storing patient memories...")
    patient_memories = [
        "Patient John Doe, 45 years old",
        "Diagnosis: Diabetes Type 2",
        "Allergic to penicillin",
        "Takes insulin twice daily",
        "Blood sugar levels: 120-150 mg/dL (stable)",
        "Last HbA1c: 6.8% (good control)",
        "Patient prefers morning appointments",
    ]
    for mem in patient_memories:
        fine_tuning.store_memory(mem)
    print(f"   [OK] Stored {len(patient_memories)} memories")

    # 4. Simulate multi-agent interaction
    print("\n4. Simulating multi-agent interaction...")

    # Store patient record in shared memory
    protocol.shared_memory.store_memory(
        memory_id="patient_123",
        content="Patient John Doe, 45 years old, diabetes type 2, allergic to penicillin",
        metadata={"patient_id": "123", "last_updated": datetime.now(timezone.utc).isoformat()},
    )

    patient_data = protocol.shared_memory.retrieve_memory("patient_123")
    print(f"   Step 1 — Retrieved: {patient_data['content'][:60]}...")

    stats1 = fine_tuning.fine_tune_on_interaction({
        "user_message": "What is the patient's current treatment status?",
        "agent_response": (
            "Patient John Doe has diabetes type 2. He takes insulin twice daily "
            "and his blood sugar levels are stable at 120-150 mg/dL. Last HbA1c was 6.8%."
        ),
        "user_feedback": "positive",
    })
    print(f"   Step 2 — Fine-tuned  loss={stats1['loss']:.4f}  mode={stats1['mode']}")

    # New lab results
    new_lab = {
        "blood_sugar": "135 mg/dL",
        "hemoglobin_a1c": "7.1%",
        "comment": "Slightly elevated but within acceptable range",
    }
    protocol.shared_memory.store_memory(
        memory_id="lab_results_latest",
        content=f"Latest lab results: {json.dumps(new_lab)}",
        metadata={"type": "lab_results", "date": datetime.now(timezone.utc).isoformat()},
    )
    print("   Step 3 — Lab results stored")

    stats2 = fine_tuning.fine_tune_on_interaction({
        "user_message": "What are the latest lab results?",
        "agent_response": (
            "Latest results: blood sugar 135 mg/dL, HbA1c 7.1%. "
            "Slightly elevated but within acceptable range."
        ),
        "user_feedback": "positive",
    })
    print(f"   Step 4 — Fine-tuned  loss={stats2['loss']:.4f}")

    # Care plan
    care_plan = {
        "action": "update_treatment",
        "recommendation": (
            "Continue current insulin regimen. Monitor blood sugar twice daily. "
            "Consider adjusting insulin dosage if HbA1c exceeds 7.5%."
        ),
        "agent": "healthcare_agent",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    protocol.shared_memory.store_memory(
        memory_id="care_plan_latest",
        content=json.dumps(care_plan),
        metadata={"type": "care_plan", "priority": "high"},
    )
    print("   Step 5 — Care plan generated and stored")

    # 5. Metrics
    print("\n5. Performance metrics:")
    metrics = fine_tuning.get_performance_metrics()
    print(f"   Total iterations: {metrics['total_iterations']}")
    print(f"   Recent loss:      {metrics['recent_loss']:.4f}")
    print(f"   Memories stored:  {metrics['num_memories']}")

    print("\n[OK] Healthcare demo complete!")
    return {
        "scenario": "healthcare",
        "status": "completed",
        "agents_active": 2,
        "iterations": metrics["total_iterations"],
        "memories_stored": metrics["num_memories"],
    }


# ---------------------------------------------------------------------------
# Scenario 2 — Semiconductor Process Optimisation
# ---------------------------------------------------------------------------

def run_semiconductor_demo() -> Dict[str, Any]:
    """
    Semiconductor Optimisation demo.

    Shows sensor-data ingestion, real-time fine-tuning on process readings,
    and parameter optimisation recommendations.
    """
    print("\n" + "=" * 70)
    print("DEMO SCENARIO 2: Semiconductor Process Optimisation")
    print("=" * 70)

    from core.multi_agent_communication import CommunicationProtocol, Agent
    from core.real_time_fine_tuning import FineTuningEngine

    print("\n1. Initialising multi-agent system...")
    protocol = CommunicationProtocol()
    protocol.register_agent(Agent(
        agent_id="sensors_agent",
        name="Sensors Agent",
        role="sensors_agent",
        capabilities=["sensor_data", "monitoring", "alerts"],
    ))
    protocol.register_agent(Agent(
        agent_id="optimizer_agent",
        name="Optimiser Agent",
        role="optimizer_agent",
        capabilities=["process_optimization", "data_analysis", "decision_making"],
    ))
    print("   [OK] Agents registered")

    print("\n2. Initialising fine-tuning engine...")
    fine_tuning = FineTuningEngine(model_size="medium")
    print("   [OK] Fine-tuning engine initialised")

    print("\n3. Storing manufacturing parameters...")
    params = [
        "Semiconductor fabrication line A",
        "Temperature: 85°C",
        "Pressure: 1.2 atm",
        "Throughput: 95%",
        "Defect rate: 0.15%",
        "Power consumption: 450 kW",
        "Optimisation goal: maximise throughput while maintaining quality",
    ]
    for p in params:
        fine_tuning.store_memory(p)
    print(f"   [OK] Stored {len(params)} parameters")

    print("\n4. Simulating sensor readings...")
    sensor_readings = {
        "temperature": 87,
        "pressure": 1.18,
        "throughput": 94.5,
        "defect_rate": 0.18,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    protocol.shared_memory.store_memory(
        memory_id="sensor_reading_latest",
        content=json.dumps(sensor_readings),
        metadata={"type": "sensor_data", "location": "line_A"},
    )
    print("   [OK] Sensor reading stored")

    stats = fine_tuning.fine_tune_on_interaction({
        "user_message": "Analyse current sensor readings",
        "agent_response": (
            "Temperature 87°C, Pressure 1.18 atm, Throughput 94.5%, Defect rate 0.18%. "
            "Slight deviation from optimal — recommend parameter adjustment."
        ),
        "user_feedback": "positive",
    })
    print(f"   Fine-tuned  loss={stats['loss']:.4f}")

    print("\n5. Applying optimisation...")
    optimisation = {
        "action": "optimize_parameters",
        "current": sensor_readings,
        "recommended": {
            "temperature": 86,
            "pressure": 1.20,
            "throughput": 96,
            "defect_rate": 0.12,
        },
        "expected_improvement": "2% throughput increase, 0.06% defect reduction",
        "agent": "optimizer_agent",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    protocol.shared_memory.store_memory(
        memory_id="optimisation_latest",
        content=json.dumps(optimisation),
        metadata={"type": "optimisation", "priority": "high"},
    )
    print("   [OK] Optimisation applied")

    print("\n6. Performance metrics:")
    metrics = fine_tuning.get_performance_metrics()
    print(f"   Total iterations: {metrics['total_iterations']}")
    print(f"   Recent loss:      {metrics['recent_loss']:.4f}")
    print(f"   Memories stored:  {metrics['num_memories']}")

    print("\n[OK] Semiconductor demo complete!")
    return {
        "scenario": "semiconductor",
        "status": "completed",
        "agents_active": 2,
        "iterations": metrics["total_iterations"],
        "memories_stored": metrics["num_memories"],
    }


# ---------------------------------------------------------------------------
# Scenario 3 — Education Personalisation
# ---------------------------------------------------------------------------

def run_education_demo() -> Dict[str, Any]:
    """
    Education Personalisation demo.

    Shows student-profile tracking, personalised learning-plan generation,
    and fine-tuning on student progress feedback.
    """
    print("\n" + "=" * 70)
    print("DEMO SCENARIO 3: Education Personalisation")
    print("=" * 70)

    from core.multi_agent_communication import CommunicationProtocol, Agent
    from core.real_time_fine_tuning import FineTuningEngine

    print("\n1. Initialising multi-agent system...")
    protocol = CommunicationProtocol()
    protocol.register_agent(Agent(
        agent_id="teacher_agent",
        name="Teacher Agent",
        role="teacher_agent",
        capabilities=["curriculum_design", "student_tracking", "assessment"],
    ))
    protocol.register_agent(Agent(
        agent_id="tutor_agent",
        name="Tutor Agent",
        role="tutor_agent",
        capabilities=["personalized_learning", "concept_explanation", "practice"],
    ))
    print("   [OK] Agents registered")

    print("\n2. Initialising fine-tuning engine...")
    fine_tuning = FineTuningEngine(model_size="small")
    print("   [OK] Fine-tuning engine initialised")

    print("\n3. Storing student profiles...")
    profiles = [
        "Student: Sarah Johnson",
        "Grade: 10th Grade",
        "Subject: Mathematics",
        "Current level: Algebra II",
        "Strengths: Problem-solving, Geometry",
        "Weaknesses: Calculus, Statistics",
        "Learning style: Visual learner",
        "Progress: 75% through curriculum",
    ]
    for p in profiles:
        fine_tuning.store_memory(p)
    print(f"   [OK] Stored {len(profiles)} student profiles")

    print("\n4. Simulating student progress...")
    progress = {
        "student": "Sarah Johnson",
        "topic": "Calculus",
        "current_score": 72,
        "improvement": "+8 points this week",
        "next_topic": "Derivatives",
        "recommended_actions": [
            "Additional practice problems",
            "Video tutorials on derivatives",
            "One-on-one tutoring session",
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    protocol.shared_memory.store_memory(
        memory_id="student_progress_latest",
        content=json.dumps(progress),
        metadata={"type": "student_progress", "student": "Sarah Johnson"},
    )
    print("   [OK] Student progress stored")

    stats = fine_tuning.fine_tune_on_interaction({
        "user_message": "Update student progress and create personalised plan",
        "agent_response": (
            "Sarah Johnson's Calculus score improved by 8 points this week. "
            "Ready to move to Derivatives. Recommended: practice problems, "
            "video tutorials, and a one-on-one tutoring session."
        ),
        "user_feedback": "positive",
    })
    print(f"   Fine-tuned  loss={stats['loss']:.4f}")

    print("\n5. Creating personalised learning plan...")
    learning_plan = {
        "student": "Sarah Johnson",
        "current_level": "Algebra II",
        "next_level": "Calculus (Derivatives)",
        "personalised_plan": [
            {"day": "Monday",    "topic": "Derivatives intro",    "activity": "Video tutorial + practice"},
            {"day": "Wednesday", "topic": "Derivative rules",      "activity": "Practice problems"},
            {"day": "Friday",    "topic": "Application problems",  "activity": "Problem-solving session"},
        ],
        "assessment": "Weekly quiz on derivatives",
        "agent": "teacher_agent",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    protocol.shared_memory.store_memory(
        memory_id="learning_plan_latest",
        content=json.dumps(learning_plan),
        metadata={"type": "learning_plan", "priority": "high"},
    )
    print("   [OK] Personalised learning plan created")

    print("\n6. Performance metrics:")
    metrics = fine_tuning.get_performance_metrics()
    print(f"   Total iterations: {metrics['total_iterations']}")
    print(f"   Recent loss:      {metrics['recent_loss']:.4f}")
    print(f"   Memories stored:  {metrics['num_memories']}")

    print("\n[OK] Education demo complete!")
    return {
        "scenario": "education",
        "status": "completed",
        "agents_active": 2,
        "iterations": metrics["total_iterations"],
        "memories_stored": metrics["num_memories"],
    }


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("NOVA MEMORY 2.0 — DEMO SCENARIOS")
    print("=" * 70)

    results: List[Dict[str, Any]] = []

    results.append(run_healthcare_demo())
    time.sleep(1)

    results.append(run_semiconductor_demo())
    time.sleep(1)

    results.append(run_education_demo())

    print("\n" + "=" * 70)
    print("DEMO SUMMARY")
    print("=" * 70)
    for r in results:
        print(
            f"  {r['scenario'].capitalize():20s}  "
            f"status={r['status']}  "
            f"agents={r['agents_active']}  "
            f"memories={r['memories_stored']}  "
            f"iterations={r['iterations']}"
        )

    print("\n[OK] All demo scenarios completed successfully!")
