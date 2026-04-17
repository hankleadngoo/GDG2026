"""
Synthetic candidate data generator for Agent 4 (Competitive Profiler).

Produces records that exactly match the Qdrant payload schema defined in
plans/plan_agent4.md.  No external API calls — all data is generated
deterministically from seeded random pools.

Output:  data/synthetic_data/synthetic_candidates.json
         data/synthetic_data/synthetic_candidates_by_role.json  (grouped view)

Run:
    python data/synthetic_data/generate.py
"""

import json
import random
import uuid
from collections import defaultdict
from pathlib import Path

# ── Reproducibility ──────────────────────────────────────────────────────────
SEED = 42
random.seed(SEED)

BATCH_ID = "GDGOC_Hackathon_2026"
OUTPUT_DIR = Path(__file__).parent

# ── Role definitions ─────────────────────────────────────────────────────────
# Each entry: (job_title, n_candidates, core_skill_pool, tool_pool)
ROLES = [
    {
        "job_title": "Software Engineer",
        "n": 120,
        "core_skills": [
            "Python", "Java", "C++", "JavaScript", "TypeScript",
            "Data Structures", "Algorithms", "Object-Oriented Programming",
            "REST APIs", "Microservices", "System Design", "SQL",
            "Unit Testing", "CI/CD",
        ],
        "tools": [
            "Git", "Docker", "Linux", "Kubernetes", "FastAPI", "Spring Boot",
            "React", "PostgreSQL", "Redis", "Kafka", "Jenkins", "GitHub Actions",
            "VS Code", "IntelliJ",
        ],
    },
    {
        "job_title": "Data Scientist",
        "n": 90,
        "core_skills": [
            "Python", "Machine Learning", "Deep Learning", "Statistics",
            "Data Analysis", "SQL", "Feature Engineering", "NLP",
            "Computer Vision", "Time Series Analysis", "A/B Testing",
            "Data Visualization", "Probability", "Linear Algebra",
        ],
        "tools": [
            "TensorFlow", "PyTorch", "scikit-learn", "Pandas", "NumPy",
            "Jupyter", "Matplotlib", "Seaborn", "Spark", "Airflow",
            "Git", "Docker", "Weights & Biases", "Hugging Face",
        ],
    },
    {
        "job_title": "Data Engineer",
        "n": 60,
        "core_skills": [
            "Python", "SQL", "ETL Pipelines", "Data Warehousing",
            "Distributed Systems", "Data Modeling", "Batch Processing",
            "Stream Processing", "Data Quality", "Cloud Storage",
        ],
        "tools": [
            "Apache Spark", "Apache Kafka", "Airflow", "dbt", "BigQuery",
            "Redshift", "Snowflake", "Hadoop", "Docker", "Git",
            "Terraform", "GCP", "AWS", "Azure Data Factory",
        ],
    },
    {
        "job_title": "ML Engineer",
        "n": 60,
        "core_skills": [
            "Python", "Machine Learning", "Deep Learning", "MLOps",
            "Model Deployment", "Feature Stores", "Model Monitoring",
            "Distributed Training", "REST APIs", "System Design",
        ],
        "tools": [
            "PyTorch", "TensorFlow", "Kubeflow", "MLflow", "Docker",
            "Kubernetes", "FastAPI", "Redis", "Git", "Triton",
            "Weights & Biases", "Ray", "Seldon", "BentoML",
        ],
    },
    {
        "job_title": "Backend Developer",
        "n": 80,
        "core_skills": [
            "Python", "Java", "Go", "Node.js", "REST APIs",
            "GraphQL", "Microservices", "Database Design", "SQL",
            "Authentication", "Caching", "Message Queues", "System Design",
        ],
        "tools": [
            "FastAPI", "Django", "Spring Boot", "Express.js", "PostgreSQL",
            "MySQL", "MongoDB", "Redis", "RabbitMQ", "Kafka",
            "Docker", "Kubernetes", "Git", "Nginx",
        ],
    },
    {
        "job_title": "Frontend Developer",
        "n": 60,
        "core_skills": [
            "JavaScript", "TypeScript", "HTML", "CSS", "React",
            "Vue.js", "Angular", "Responsive Design", "Accessibility",
            "State Management", "REST APIs", "Performance Optimization",
        ],
        "tools": [
            "React", "Next.js", "Vue", "Tailwind CSS", "Webpack",
            "Vite", "Jest", "Cypress", "Figma", "Git",
            "Storybook", "GraphQL", "Redux", "Zustand",
        ],
    },
    {
        "job_title": "DevOps Engineer",
        "n": 50,
        "core_skills": [
            "Linux", "CI/CD", "Infrastructure as Code", "Cloud Architecture",
            "Container Orchestration", "Monitoring", "Security", "Networking",
            "Scripting", "Site Reliability Engineering",
        ],
        "tools": [
            "Docker", "Kubernetes", "Terraform", "Ansible", "Jenkins",
            "GitHub Actions", "GitLab CI", "Prometheus", "Grafana",
            "AWS", "GCP", "Azure", "Helm", "Vault",
        ],
    },
    {
        "job_title": "Cybersecurity Analyst",
        "n": 40,
        "core_skills": [
            "Penetration Testing", "Vulnerability Assessment", "SIEM",
            "Incident Response", "Network Security", "Malware Analysis",
            "Threat Intelligence", "Cryptography", "Forensics", "Risk Assessment",
        ],
        "tools": [
            "Wireshark", "Metasploit", "Burp Suite", "Nmap", "Splunk",
            "Snort", "Kali Linux", "OWASP ZAP", "CrowdStrike",
            "Nessus", "OpenVAS", "Git", "Python", "PowerShell",
        ],
    },
    {
        "job_title": "Product Manager",
        "n": 40,
        "core_skills": [
            "Product Strategy", "Roadmap Planning", "User Research",
            "A/B Testing", "Agile", "Scrum", "Stakeholder Management",
            "Data Analysis", "Market Research", "UX Design",
        ],
        "tools": [
            "Jira", "Confluence", "Figma", "Mixpanel", "Google Analytics",
            "Amplitude", "Notion", "Miro", "Tableau", "SQL",
        ],
    },
    {
        "job_title": "QA Engineer",
        "n": 40,
        "core_skills": [
            "Test Planning", "Test Automation", "Manual Testing",
            "API Testing", "Performance Testing", "Bug Reporting",
            "Regression Testing", "Test Cases Design", "SDLC",
        ],
        "tools": [
            "Selenium", "Cypress", "Playwright", "Postman", "JMeter",
            "TestRail", "JIRA", "Git", "Pytest", "Appium",
        ],
    },
]

# ── Education pools ──────────────────────────────────────────────────────────
EDUCATION_LEVELS = ["High School", "Associate", "Undergraduate", "Master", "PhD"]
EDUCATION_WEIGHTS = [0.03, 0.05, 0.58, 0.29, 0.05]

MAJORS_BY_ROLE = {
    "Software Engineer":      ["Computer Science", "Software Engineering", "Information Technology", "Computer Engineering"],
    "Data Scientist":         ["Data Science", "Statistics", "Mathematics", "Computer Science", "Applied Mathematics"],
    "Data Engineer":          ["Computer Science", "Information Systems", "Data Engineering", "Software Engineering"],
    "ML Engineer":            ["Computer Science", "Data Science", "Electrical Engineering", "Applied Mathematics"],
    "Backend Developer":      ["Computer Science", "Software Engineering", "Information Technology"],
    "Frontend Developer":     ["Computer Science", "Software Engineering", "Web Development", "Information Technology"],
    "DevOps Engineer":        ["Computer Science", "Information Technology", "Network Engineering", "Systems Administration"],
    "Cybersecurity Analyst":  ["Cybersecurity", "Information Security", "Computer Science", "Network Engineering"],
    "Product Manager":        ["Business Administration", "Computer Science", "Information Systems", "Marketing"],
    "QA Engineer":            ["Computer Science", "Software Engineering", "Information Technology", "Quality Assurance"],
}

# ── Experience distribution (years) by seniority ────────────────────────────
SENIORITY_MIX = [
    ("Intern / Fresher",  0.20, (0.0,  0.9)),
    ("Junior",           0.30, (1.0,  2.9)),
    ("Mid-level",        0.30, (3.0,  5.9)),
    ("Senior",           0.15, (6.0, 10.0)),
    ("Lead / Principal", 0.05, (10.0, 18.0)),
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def pick_seniority() -> tuple[str, float]:
    """Return (seniority_label, years_of_experience)."""
    labels   = [s[0] for s in SENIORITY_MIX]
    weights  = [s[1] for s in SENIORITY_MIX]
    chosen   = random.choices(labels, weights=weights, k=1)[0]
    lo, hi   = next(s[2] for s in SENIORITY_MIX if s[0] == chosen)
    years    = round(random.uniform(lo, hi), 1)
    return chosen, years


def pick_skills(role: dict, years: float) -> dict:
    """
    Pick a realistic skill set based on years of experience.
    More experience → more skills.
    """
    n_core  = min(len(role["core_skills"]),  max(2, int(3 + years * 0.8) + random.randint(-1, 2)))
    n_tools = min(len(role["tools"]),        max(2, int(2 + years * 0.6) + random.randint(-1, 2)))

    core  = random.sample(role["core_skills"], n_core)
    tools = random.sample(role["tools"],       n_tools)
    return {"core": sorted(core), "tools": sorted(tools)}


def pick_education(job_title: str) -> dict:
    level = random.choices(EDUCATION_LEVELS, weights=EDUCATION_WEIGHTS, k=1)[0]
    major = random.choice(MAJORS_BY_ROLE.get(job_title, ["Computer Science"]))
    return {"level": level, "major": major}


def generate_candidate(role: dict) -> dict:
    """Generate one candidate record matching the Qdrant payload schema."""
    _, years = pick_seniority()
    return {
        "candidate_id":        str(uuid.uuid4()),
        "job_title":           role["job_title"],
        "batch_id":            BATCH_ID,
        "years_of_experience": years,
        "skills":              pick_skills(role, years),
        "education":           pick_education(role["job_title"]),
    }


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    all_candidates: list[dict] = []

    for role in ROLES:
        for _ in range(role["n"]):
            all_candidates.append(generate_candidate(role))

    random.shuffle(all_candidates)

    # ── Flat file ─────────────────────────────────────────────────────────────
    flat_path = OUTPUT_DIR / "synthetic_candidates.json"
    flat_path.write_text(
        json.dumps(all_candidates, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # ── Grouped by role ───────────────────────────────────────────────────────
    by_role: dict[str, list] = defaultdict(list)
    for c in all_candidates:
        by_role[c["job_title"]].append(c)

    grouped_path = OUTPUT_DIR / "synthetic_candidates_by_role.json"
    grouped_path.write_text(
        json.dumps(dict(by_role), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"[OK] Generated {len(all_candidates)} synthetic candidates")
    print(f"    Saved to: {flat_path}")
    print(f"    Grouped:  {grouped_path}")
    print()
    print("Role breakdown:")
    for title, cands in sorted(by_role.items()):
        avg_exp = sum(c["years_of_experience"] for c in cands) / len(cands)
        print(f"  {title:<28}  {len(cands):>4} candidates  avg_exp={avg_exp:.1f}yr")


if __name__ == "__main__":
    main()
