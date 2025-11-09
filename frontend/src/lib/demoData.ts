import type { AnalyzeResponse, LinkedInJobSearchItem, LinkedInJobSearchResponse, GeneratePlanResponse } from '../types';

/**
 * Demo data for offline mode and fallback scenarios
 * Matches existing UI schemas exactly
 * Includes multiple CS roles: AI Engineer, Data Analyst, Data Engineer, Software Engineer
 */

// AI Engineer Demo
export const demoAnalysisAI: AnalyzeResponse = {
  domains: [
    { name: "AI Engineer", score: 0.9 },
    { name: "ML Engineer", score: 0.85 },
    { name: "Data Scientist", score: 0.75 },
  ],
  skills: {
    core: ["Python", "PyTorch", "TensorFlow", "Machine Learning", "Deep Learning"],
    adjacent: ["SQL", "Pandas", "NumPy", "Scikit-learn"],
    advanced: ["MLOps", "LLMs", "Transformers", "Vector Databases"],
  },
  strengths: [
    "Python programming skills",
    "Deep learning framework experience",
    "Machine learning expertise",
    "Data analysis capabilities",
  ],
  areas_for_growth: [
    "MLOps and model deployment",
    "Large Language Models (LLMs) and transformers",
    "Advanced ML techniques and model optimization",
  ],
  recommended_roles: [
    "AI Engineer",
    "ML Engineer",
    "Data Scientist",
    "ML Researcher",
  ],
  keywords_detected: ["python", "pytorch", "tensorflow", "machine learning", "ai", "ml"],
  debug: {
    hash: "demo1234",
    provider: "demo",
  },
  score: 85,
};

// Data Analyst Demo
export const demoAnalysisDataAnalyst: AnalyzeResponse = {
  domains: [
    { name: "Data Analyst", score: 0.92 },
    { name: "Business Analyst", score: 0.78 },
    { name: "BI Analyst", score: 0.72 },
  ],
  skills: {
    core: ["SQL", "Excel", "Python", "Statistics", "Data Visualization"],
    adjacent: ["Power BI", "Tableau", "Pandas", "NumPy"],
    advanced: ["ETL", "Data Warehousing", "A/B Testing", "Predictive Analytics"],
  },
  strengths: [
    "Strong SQL querying skills",
    "Excel proficiency with pivot tables and VLOOKUP",
    "Data visualization expertise",
    "Statistical analysis capabilities",
  ],
  areas_for_growth: [
    "Advanced SQL techniques (window functions, CTEs)",
    "Data warehouse platforms (Snowflake, BigQuery)",
    "Python data libraries (pandas, numpy)",
  ],
  recommended_roles: [
    "Data Analyst",
    "Business Analyst",
    "BI Analyst",
    "Analytics Engineer",
  ],
  keywords_detected: ["sql", "excel", "python", "data analysis", "statistics", "tableau"],
  debug: {
    hash: "demo5678",
    provider: "demo",
  },
  score: 88,
};

// Data Engineer Demo
export const demoAnalysisDataEngineer: AnalyzeResponse = {
  domains: [
    { name: "Data Engineer", score: 0.91 },
    { name: "ETL Engineer", score: 0.82 },
    { name: "Big Data Engineer", score: 0.75 },
  ],
  skills: {
    core: ["Python", "SQL", "ETL", "Data Pipelines", "Apache Airflow"],
    adjacent: ["Spark", "Kafka", "Hadoop", "AWS"],
    advanced: ["Data Lake", "Data Warehouse", "Real-time Processing", "Streaming"],
  },
  strengths: [
    "ETL pipeline development",
    "Data pipeline orchestration with Airflow",
    "Big data processing with Spark",
    "Cloud data infrastructure",
  ],
  areas_for_growth: [
    "Real-time streaming with Kafka",
    "Data lake architecture",
    "Advanced Spark optimization",
  ],
  recommended_roles: [
    "Data Engineer",
    "ETL Engineer",
    "Data Pipeline Engineer",
    "Big Data Engineer",
  ],
  keywords_detected: ["python", "sql", "etl", "airflow", "spark", "kafka", "data pipeline"],
  debug: {
    hash: "demo9012",
    provider: "demo",
  },
  score: 87,
};

// Software Engineer Demo
export const demoAnalysisSoftwareEngineer: AnalyzeResponse = {
  domains: [
    { name: "Software Engineer", score: 0.93 },
    { name: "Backend Engineer", score: 0.85 },
    { name: "Full-Stack Engineer", score: 0.72 },
  ],
  skills: {
    core: ["Python", "Java", "JavaScript", "REST APIs", "Database Design"],
    adjacent: ["React", "Node.js", "Docker", "Git"],
    advanced: ["Microservices", "System Design", "Cloud Architecture", "CI/CD"],
  },
  strengths: [
    "Strong programming fundamentals",
    "API development and design",
    "Database design and optimization",
    "Version control and collaboration",
  ],
  areas_for_growth: [
    "System design and architecture",
    "Cloud platform expertise (AWS, Azure, GCP)",
    "Microservices architecture",
  ],
  recommended_roles: [
    "Software Engineer",
    "Backend Engineer",
    "Full-Stack Engineer",
    "API Developer",
  ],
  keywords_detected: ["python", "java", "javascript", "api", "database", "rest"],
  debug: {
    hash: "demo3456",
    provider: "demo",
  },
  score: 90,
};

// Default demo (AI Engineer for backward compatibility)
export const demoAnalysis: AnalyzeResponse = demoAnalysisAI;

// AI Engineer Jobs
export const demoJobsAI: LinkedInJobSearchItem[] = [
  {
    id: "demo-job-ai-1",
    title: "AI Engineer",
    company: "Tech Corp",
    location: "San Francisco, CA",
    url: "https://www.linkedin.com/jobs/view/demo1",
    listed_at: new Date().toISOString(),
    source: "demo",
    description_snippet: "We are looking for an AI Engineer with experience in PyTorch, TensorFlow, and MLOps...",
    matchScore: 88,
    reasons: [
      "Python experience matches requirements",
      "Deep learning framework knowledge",
      "ML expertise aligns with role",
    ],
    gaps: [
      "MLOps and model deployment",
      "LLM fine-tuning experience",
    ],
  },
  {
    id: "demo-job-ai-2",
    title: "ML Engineer",
    company: "AI Startup",
    location: "Remote",
    url: "https://www.linkedin.com/jobs/view/demo2",
    listed_at: new Date().toISOString(),
    source: "demo",
    description_snippet: "Join our ML team to build and deploy machine learning models at scale...",
    matchScore: 85,
    reasons: [
      "Strong ML background",
      "Python and PyTorch experience",
      "Data science skills",
    ],
    gaps: [
      "Production ML systems",
      "Model serving infrastructure",
    ],
  },
];

// Data Analyst Jobs
export const demoJobsDataAnalyst: LinkedInJobSearchItem[] = [
  {
    id: "demo-job-da-1",
    title: "Data Analyst",
    company: "Analytics Inc",
    location: "New York, NY",
    url: "https://www.linkedin.com/jobs/view/demo-da-1",
    listed_at: new Date().toISOString(),
    source: "demo",
    description_snippet: "We need a Data Analyst to analyze business metrics and create dashboards...",
    matchScore: 90,
    reasons: [
      "SQL expertise matches requirements",
      "Excel proficiency",
      "Data visualization skills",
    ],
    gaps: [
      "Advanced SQL (window functions)",
      "Power BI or Tableau certification",
    ],
  },
  {
    id: "demo-job-da-2",
    title: "Business Analyst",
    company: "Consulting Group",
    location: "Chicago, IL",
    url: "https://www.linkedin.com/jobs/view/demo-da-2",
    listed_at: new Date().toISOString(),
    source: "demo",
    description_snippet: "Join our team to analyze business processes and provide data-driven insights...",
    matchScore: 87,
    reasons: [
      "Data analysis capabilities",
      "Statistical analysis experience",
      "Business acumen",
    ],
    gaps: [
      "A/B testing experience",
      "Business intelligence tools",
    ],
  },
];

// Data Engineer Jobs
export const demoJobsDataEngineer: LinkedInJobSearchItem[] = [
  {
    id: "demo-job-de-1",
    title: "Data Engineer",
    company: "Data Platform Co",
    location: "Seattle, WA",
    url: "https://www.linkedin.com/jobs/view/demo-de-1",
    listed_at: new Date().toISOString(),
    source: "demo",
    description_snippet: "Build and maintain scalable data pipelines using Python, Airflow, and Spark...",
    matchScore: 89,
    reasons: [
      "ETL pipeline experience",
      "Python and SQL skills",
      "Data pipeline orchestration",
    ],
    gaps: [
      "Real-time streaming (Kafka)",
      "Data lake architecture",
    ],
  },
  {
    id: "demo-job-de-2",
    title: "ETL Engineer",
    company: "Enterprise Solutions",
    location: "Austin, TX",
    url: "https://www.linkedin.com/jobs/view/demo-de-2",
    listed_at: new Date().toISOString(),
    source: "demo",
    description_snippet: "Design and implement ETL processes for data warehouse integration...",
    matchScore: 86,
    reasons: [
      "ETL development experience",
      "Data warehouse knowledge",
      "SQL proficiency",
    ],
    gaps: [
      "Apache Airflow certification",
      "Cloud data platforms (Snowflake, BigQuery)",
    ],
  },
];

// Software Engineer Jobs
export const demoJobsSoftwareEngineer: LinkedInJobSearchItem[] = [
  {
    id: "demo-job-se-1",
    title: "Software Engineer",
    company: "Tech Startup",
    location: "San Francisco, CA",
    url: "https://www.linkedin.com/jobs/view/demo-se-1",
    listed_at: new Date().toISOString(),
    source: "demo",
    description_snippet: "Build scalable backend systems using Python, Java, and modern frameworks...",
    matchScore: 92,
    reasons: [
      "Strong programming skills",
      "API development experience",
      "Database design knowledge",
    ],
    gaps: [
      "System design and architecture",
      "Cloud platform expertise",
    ],
  },
  {
    id: "demo-job-se-2",
    title: "Backend Engineer",
    company: "SaaS Platform",
    location: "Remote",
    url: "https://www.linkedin.com/jobs/view/demo-se-2",
    listed_at: new Date().toISOString(),
    source: "demo",
    description_snippet: "Develop RESTful APIs and microservices for our cloud-based platform...",
    matchScore: 88,
    reasons: [
      "REST API development",
      "Backend framework experience",
      "Database optimization",
    ],
    gaps: [
      "Microservices architecture",
      "Container orchestration (Kubernetes)",
    ],
  },
];

// Default demo jobs (AI Engineer for backward compatibility)
export const demoJobs: LinkedInJobSearchItem[] = demoJobsAI;

export const demoJobsResponse: LinkedInJobSearchResponse = {
  jobs: demoJobs,
  nextCursor: null,
  debug: {
    source: "demo",
    count: demoJobs.length,
    hash: "demo1234",
    message: "Demo mode - using static job data",
  },
};

export const demoPlan: GeneratePlanResponse = {
  role: "AI Engineer",
  objectives: [
    "Master MLOps and model deployment",
    "Learn LLM fine-tuning techniques",
    "Build production ML systems",
  ],
  plan_days: [
    {
      day: 1,
      title: "MLOps Fundamentals",
      actions: [
        "Complete 'MLOps Specialization' on Coursera (https://www.coursera.org/specializations/mlops)",
        "Set up MLflow tracking server locally",
        "Read 'MLOps: Continuous delivery and automation pipelines in ML'",
      ],
    },
    {
      day: 2,
      title: "Model Deployment",
      actions: [
        "Take 'Deploying Machine Learning Models' on Udemy (https://www.udemy.com/course/deploying-machine-learning-models/)",
        "Deploy a simple model with FastAPI",
        "Create Docker container for model serving",
      ],
    },
    {
      day: 3,
      title: "LLM Basics",
      actions: [
        "Complete 'Introduction to Large Language Models' on Coursera",
        "Experiment with Hugging Face transformers library",
        "Fine-tune a small language model on custom dataset",
      ],
    },
    {
      day: 4,
      title: "Advanced LLM Techniques",
      actions: [
        "Learn about RAG (Retrieval-Augmented Generation)",
        "Build a RAG system with vector database",
        "Implement prompt engineering best practices",
      ],
    },
    {
      day: 5,
      title: "Production ML Systems",
      actions: [
        "Study 'Designing Machine Learning Systems' book",
        "Build end-to-end ML pipeline with Airflow",
        "Implement monitoring and alerting for ML models",
      ],
    },
    {
      day: 6,
      title: "Model Optimization",
      actions: [
        "Learn model quantization and pruning",
        "Optimize model inference speed",
        "Implement A/B testing for ML models",
      ],
    },
    {
      day: 7,
      title: "Portfolio Building",
      actions: [
        "Create GitHub repo with ML pipeline project",
        "Write blog post about MLOps best practices",
        "Prepare case study for interviews",
      ],
    },
  ],
  deliverables: [
    "ML pipeline with MLflow",
    "Deployed model with FastAPI",
    "Fine-tuned LLM with Hugging Face",
    "RAG implementation with vector database",
  ],
  apply_checkpoints: [
    {
      when: "Day 3",
      criteria: [
        "MLflow pipeline complete",
        "Model deployed successfully",
      ],
    },
    {
      when: "Day 7",
      criteria: [
        "Portfolio project complete",
        "All deliverables ready",
      ],
    },
  ],
};

