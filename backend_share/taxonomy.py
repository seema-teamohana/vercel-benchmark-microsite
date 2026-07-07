"""
Canonical taxonomy mappings for the salary prediction system.

This module contains the role / level / location / quarter mappings developed
in the EDA notebook (Sections 6-10). It's imported by:
- The training script (to canonicalise training data)
- The backend orchestrator (to canonicalise user queries)

Keeping the logic here ensures train-time and query-time produce identical
canonical features for the same input.
"""
import re
import pandas as pd

# ============================================================
# Section 6 — Canonical role taxonomy
# ============================================================

TAXONOMY = {
    'Engineering': [
        'Software Engineering', 'Machine Learning Engineering', 'Data Engineering',
        'Infrastructure / DevOps / SRE', 'Security Engineering',
        'QA / Quality Engineering', 'Engineering Management',
        'Solutions / Forward-Deployed Engineering',
    ],
    'Product': [
        'Product Management', 'Product Design', 'Technical Program Management',
        'Product Operations',
    ],
    'Data Science / Research': [
        'Data Science / Analytics', 'Research',
    ],
    'Sales': [
        'Account Executive', 'Sales Development', 'Account Management',
        'Sales Engineering', 'Sales Operations', 'Sales Leadership',
    ],
    'Marketing': [
        'Growth / Demand Marketing', 'Product Marketing',
        'Brand / Creative / Content Marketing', 'Marketing \u2014 General',
    ],
    'Customer': [
        'Customer Success', 'Customer Support', 'Technical Support',
    ],
    'Operations': [
        'Business Operations', 'Strategic Programs', 'Engagement Management',
        'Operations Specialist',
    ],
    'Finance & Accounting': [
        'Finance', 'Accounting', 'Procurement',
    ],
    'People & Talent': [
        'Talent Acquisition / Recruiting', 'HR / People',
    ],
    'Legal': [
        'Legal / Compliance',
    ],
    'Manufacturing': [
        'Assembly / Production', 'Wiring / Electrical',
        'Construction / Installation', 'Materials / Warehouse',
        'Field Service', 'Field / Hardware Engineering',
    ],
    'Admin': [
        'Executive Assistant', 'Administrative',
    ],
}

FUNCTION_FOR_LEAF = {leaf: func for func, leaves in TAXONOMY.items() for leaf in leaves}


# ============================================================
# Section 7 — Role mapping rules
# ============================================================
# (Abbreviated — full rules from notebook builder script)

def cre(pattern):
    return re.compile(pattern, re.IGNORECASE)


MAPPING_RULES = {
    "Software Engineering": {
        "exact_role_strings": [
            "Software Engineering", "Software Engineer", "Software Engineer (IC)",
            "Software Engineering (EN.SODE)", "R&D-Software Engineering",
            "Software Development", "Backend Engineering", "Frontend Engineering",
            "Full Stack Engineering", "Mobile Engineering", "iOS Engineering",
            "Android Engineering", "Web Engineering",
        ],
        "role_regex": [
            cre(r"^ENG-\d+$"),
            cre(r"^software\s*engineer"),
            cre(r"\b(backend|frontend|full.?stack|mobile|ios|android)\s*(engineer|engineering|developer)"),
            cre(r"^developer$"),
        ],
        "title_keywords": [
            "software engineer", "software developer", "backend engineer",
            "frontend engineer", "fullstack engineer", "full stack engineer",
            "mobile engineer", "ios engineer", "android engineer",
            "web engineer", "platform engineer",
            # Developer variants (added 2026-07 for new-customer coverage)
            # Note: bare "developer" excluded to avoid false-matching "Developer Relations"
            "senior developer", "staff developer", "junior developer",
            "principal developer", "sr developer", "sr. developer",
            "software developer", "backend developer", "frontend developer",
            "web developer", "mobile developer", "model developer",
        ],
    },
    "Machine Learning Engineering": {
        "exact_role_strings": ["Machine Learning", "Machine Learning Engineering", "ML Engineering",
                                "AI Engineering", "Applied AI Engineering", "MLDG"],
        "role_regex": [cre(r"\bml\s*engineer"), cre(r"\bmachine\s*learning\b"), cre(r"\bapplied\s*ai\b")],
        "title_keywords": ["machine learning engineer", "ml engineer", "ai engineer",
                          "applied ai", "applied scientist"],
    },
    "Data Engineering": {
        "exact_role_strings": ["Data Engineering", "Data Engineer"],
        "role_regex": [cre(r"\bdata\s*engineer")],
        "title_keywords": ["data engineer", "analytics engineer"],
    },
    "Infrastructure / DevOps / SRE": {
        "exact_role_strings": [
            "Infrastructure", "Infrastructure Engineering", "DevOps",
            "Site Reliability Engineering", "SRE", "Platform Engineering",
            "Cloud Engineering", "Network Engineering",
            "Infrastructure Design Engineering", "Data Center Operations",
            "IT", "IT Engineering", "IT (IC)", "Information Technology",
            "Systems & Enablement (IC)",
        ],
        "role_regex": [
            cre(r"\b(devops|sre|site\s*reliability|infrastructure|platform|cloud|network)\s*engineer"),
            cre(r"^data\s*center"),
            cre(r"^IT\b"),
            cre(r"\bIT\s*\(IC\)$"),
            cre(r"systems?\s*&\s*enablement"),
        ],
        "title_keywords": [
            "devops engineer", "sre", "site reliability engineer",
            "infrastructure engineer", "cloud engineer", "network engineer",
            "production engineer", "data center", "it analyst",
            "it specialist", "it administrator", "systems administrator",
        ],
    },
    "Security Engineering": {
        "exact_role_strings": ["Security Engineering", "Security Engineer", "Cybersecurity",
                                "Security Operations", "Security Analyst"],
        "role_regex": [cre(r"\b(security|cyber)\s*(engineer|engineering|operations|analyst)"),
                       cre(r"^security\s*(operations|analyst)")],
        "title_keywords": ["security engineer", "cybersecurity", "security analyst", "security operations"],
    },
    "QA / Quality Engineering": {
        "exact_role_strings": ["QA", "Quality Engineering", "Quality Assurance",
                                "Test Engineering", "QA Engineering"],
        "role_regex": [cre(r"\b(qa|quality|test)\s*(engineer|engineering|specialist|analyst)")],
        "title_keywords": ["qa engineer", "quality engineer", "test engineer", "sdet",
                          "qa specialist", "qa analyst"],
    },
    "Engineering Management": {
        "exact_role_strings": ["Engineering (M)"],
        "role_regex": [cre(r"engineering\s*manag"), cre(r"manag.*engineer")],
        "title_keywords": [
            "engineering manager", "manager, engineering", "director, engineering",
            "director of engineering", "head of engineering", "vp engineering",
            "vp, engineering", "engineering director",
            "sr. manager, engineering", "sr manager, engineering",
            "senior manager, engineering",
            "manager, ml", "manager, machine learning",
            "manager, data engineering", "manager, security engineering",
            "manager, software engineering",
        ],
    },
    "Solutions / Forward-Deployed Engineering": {
        "exact_role_strings": ["Solutions Engineering", "Solutions Engineer",
                                "Forward Deployed Engineering", "Forward Deployed Engineer",
                                "Solutions Architect", "Implementations",
                                "Solutions Consultant", "Customer Engineer"],
        "role_regex": [cre(r"\bsolutions?\s*(engineer|architect|consultant)"),
                       cre(r"\bforward\s*deployed"), cre(r"^implementation"),
                       cre(r"^customer\s*engineer")],
        "title_keywords": [
            "solutions engineer", "solutions architect", "forward deployed engineer",
            "implementation engineer", "deployment engineer",
            "implementation manager", "implementation specialist",
            "solutions consultant", "customer engineer",
        ],
    },
    "Product Management": {
        "exact_role_strings": ["Product Management", "Product Manager", "Product Manager (IC)",
                                "R&D-Product Management & Design"],
        "role_regex": [cre(r"^product\s*manag"), cre(r"product\s*management")],
        "title_keywords": ["product manager", "product management", "principal product"],
    },
    "Product Design": {
        "exact_role_strings": ["Product Design", "Design", "UX Design", "UI/UX Design"],
        "role_regex": [cre(r"\b(product\s*design|ux\s*design|ui.?ux)")],
        "title_keywords": ["product designer", "ux designer", "ui designer",
                          "design lead", "senior designer",
                          "director, product design", "director of product design",
                          "head of design", "visual designer", "new grad designer"],
    },
    "Technical Program Management": {
        "exact_role_strings": ["Technical Program Management", "TPM", "Program Management"],
        "role_regex": [cre(r"\b(technical\s*program|tpm)\b")],
        "title_keywords": ["technical program manager", "tpm", "program manager, engineering"],
    },
    "Product Operations": {
        "exact_role_strings": ["Product Operations", "Product Ops"],
        "role_regex": [cre(r"product\s*op")],
        "title_keywords": ["product operations", "product ops"],
    },
    "Data Science / Analytics": {
        "exact_role_strings": ["Data Science", "Data Scientist", "Analytics", "Data Analyst",
                                "Business Analytics", "Business Intelligence"],
        "role_regex": [cre(r"\bdata\s*(scien|analyst|analytic)"),
                       cre(r"\b(analytics|business\s*intelligence)\b")],
        "title_keywords": ["data scientist", "data analyst", "analytics", "business intelligence",
                          "bi analyst", "business analyst"],
    },
    "Research": {
        "exact_role_strings": ["Research", "Research Scientist", "Research Engineer",
                                "R&D", "Research and Development", "SEAL"],
        "role_regex": [cre(r"\bresearch(er)?\b")],
        "title_keywords": ["research scientist", "research engineer", "researcher",
                          "principal scientist", "staff scientist"],
    },
    "Account Executive": {
        "exact_role_strings": ["Account Executive", "Account Executive (SA.FSDN.AE)",
                                "AE", "Enterprise Account Executive", "Channel Sales (IC)",
                                "AE Enterprise", "AE Mid-Enterprise, Strategic (M)"],
        "role_regex": [cre(r"account\s*executive"), cre(r"\(SA\.[A-Z\.]+\.AE\)"),
                       cre(r"^channel\s*sales"), cre(r"^AE\s"), cre(r"^AE,")],
        "title_keywords": ["account executive", "enterprise ae", "strategic account executive",
                          "commercial account executive", "ae, enterprise", "ae enterprise",
                          "channel manager", "regional channel manager"],
    },
    "Sales Development": {
        "exact_role_strings": ["Sales Development", "Sales Development Representative",
                                "SDR", "BDR", "Business Development Representative",
                                "BDR (IC)", "Business Dev", "Sales Enablement (IC)",
                                "GTM Enablement (SA.OPSE)", "GTM Enablement",
                                "Sales Enablement", "Field Enablement",
                                "Partnerships", "BD Operations"],
        "role_regex": [cre(r"\b(sdr|bdr|sales\s*development|business\s*development\s*rep)"),
                       cre(r"^business\s*dev"), cre(r"(sales|gtm|field)\s*enablement"),
                       cre(r"^partnerships?$"), cre(r"^bd\s*operations")],
        "title_keywords": ["sales development representative", "sdr", "bdr",
                          "business development representative", "sales enablement",
                          "gtm enablement", "field enablement", "partner manager", "partnerships"],
    },
    "Account Management": {
        "exact_role_strings": ["Account Management", "Account Manager",
                                "Customer Account Management", "Agent Success Manager",
                                "Manager, Account Management (SA.FSDS)"],
        "role_regex": [cre(r"^account\s*manager"), cre(r"agent\s*success"),
                       cre(r"\(SA\.FSDS\)")],
        "title_keywords": ["account manager", "technical account manager",
                          "strategic account manager", "growth account manager",
                          "agent success manager", "partner success",
                          "audit partner manager"],
    },
    "Sales Engineering": {
        "exact_role_strings": ["Sales Engineering", "Sales Engineer", "Pre-Sales"],
        "role_regex": [cre(r"\bsales\s*engineer"), cre(r"\bpre.?sales")],
        "title_keywords": ["sales engineer", "pre-sales engineer", "presales engineer"],
    },
    "Sales Leadership": {
        "exact_role_strings": ["Sales", "Sales (M)", "Sales Management",
                                "Sales-Sales General (Sales Plan)",
                                "Channel Management (SA.APAP.CM)"],
        "role_regex": [cre(r"sales.*(manager|director|head|leader|vp)"),
                       cre(r"(manager|director|head|vp).*sales"),
                       cre(r"^sales\s*management$"), cre(r"^sales.sales\s*general"),
                       cre(r"channel\s*management")],
        "title_keywords": ["sales manager", "manager, sales", "director, sales",
                          "director of sales", "head of sales", "vp of sales",
                          "vp, sales", "regional director", "enterprise sales director",
                          "manager, sales development", "director, sales development",
                          "senior manager, sales development", "sr. manager, sales development",
                          "sr manager, sales development",
                          "manager, account management", "director, account management",
                          "sr. manager, account management", "senior manager, account management",
                          "sr. manager, sales", "senior manager, sales", "sr manager, sales",
                          "rvp, sales", "rvp sales", "regional vp", "regional vice president"],
    },
    "Growth / Demand Marketing": {
        "exact_role_strings": ["Growth Marketing", "Demand Generation", "Demand & Growth (MK.PIDG)",
                                "Marketing-Digital Marketing", "Growth Marketer"],
        "role_regex": [cre(r"\b(growth|demand\s*gen|performance|acquisition|digital)\s*marketing"),
                       cre(r"\(MK\.PIDG\)"), cre(r"^growth\s*marketer")],
        "title_keywords": ["growth marketing", "demand generation", "demand gen",
                          "performance marketing", "acquisition marketing",
                          "paid marketing", "digital marketing manager", "growth marketer",
                          "event marketer"],
    },
    "Product Marketing": {
        "exact_role_strings": ["Product Marketing", "Product Marketing Manager", "PMM"],
        "role_regex": [cre(r"\bproduct\s*marketing"), cre(r"\bpmm\b")],
        "title_keywords": ["product marketing", "pmm"],
    },
    "Brand / Creative / Content Marketing": {
        "exact_role_strings": ["Brand Marketing", "Content Marketing", "Brand", "Content",
                                "Creative", "Editorial", "Brand Design"],
        "role_regex": [cre(r"\b(brand|content|creative|editorial)\s*marketing"),
                       cre(r"^brand\s*design")],
        "title_keywords": ["brand marketing", "content marketing", "creative director",
                          "editorial", "copywriter", "content strategist", "brand designer"],
    },
    "Marketing \u2014 General": {
        "exact_role_strings": ["Marketing", "Field Marketing", "Marketing Operations",
                                "Marketing Communications", "Communications", "General Marketing",
                                "Policy", "Public Affairs", "Public Relations",
                                "Marketing (MK.PIMC)", "Marketing (MK.PMMC)",
                                "Marketing (IC)", "Marketing General, Manager",
                                "Events", "Developer Relations", "Developer Relations (IC)"],
        "role_regex": [cre(r"^marketing"), cre(r"^general\s*marketing$"),
                       cre(r"\b(field|events|community)\s*marketing"),
                       cre(r"\bcommunications\b"), cre(r"^public\s*(affairs|relations)$"),
                       cre(r"\(MK\.(PIMC|PMMC)\)"), cre(r"^events?$"),
                       cre(r"developer\s*relations")],
        "title_keywords": ["marketing manager", "marketing analyst", "marketing specialist",
                          "field marketing", "events marketing", "marketing coordinator",
                          "vp marketing", "vp, marketing", "chief marketing officer",
                          "marketing director", "head of marketing", "communications",
                          "technical writer", "public affairs", "public relations",
                          "developer relations", "devrel", "events manager"],
    },
    "Customer Success": {
        "exact_role_strings": ["Customer Success", "Customer Success Manager", "CSM",
                                "Customer Success Engineering",
                                "Renewals (IC)", "Growth & Renewals (IC)"],
        "role_regex": [cre(r"customer\s*success"), cre(r"renewals"),
                       cre(r"growth\s*&\s*renewals")],
        "title_keywords": ["customer success manager", "customer success", "csm",
                          "client success", "manager, customer success",
                          "director, customer success", "head of customer success",
                          "renewal specialist", "renewals manager",
                          "growth & renewals account manager"],
    },
    "Customer Support": {
        "exact_role_strings": ["Customer Support", "Customer Service", "Customer Experience"],
        "role_regex": [cre(r"customer\s*(support|service|experience)")],
        "title_keywords": ["customer support", "customer service", "customer experience",
                          "support specialist", "support representative"],
    },
    "Technical Support": {
        "exact_role_strings": ["Technical Support", "Tech Support", "Support Engineering",
                                "Support Engineer", "Service Desk", "Support (IC)", "Support (M)"],
        "role_regex": [cre(r"(technical|tech)\s*support"), cre(r"support\s*engineer"),
                       cre(r"^service\s*desk"), cre(r"^support\s*\((ic|m)\)$")],
        "title_keywords": ["technical support", "support engineer", "tech support",
                          "service desk", "help desk"],
    },
    "Sales Operations": {
        "exact_role_strings": ["Sales Operations", "Sales Ops", "Revenue Operations", "RevOps",
                                "Deal Desk (SA.OPDD)", "Deal Desk"],
        "role_regex": [cre(r"\b(sales|revenue)\s*op"), cre(r"deal\s*desk")],
        "title_keywords": ["sales operations", "sales ops", "revenue operations", "revops",
                          "deal desk"],
    },
    "Business Operations": {
        "exact_role_strings": ["Business Operations", "Biz Ops", "Operations", "BizOps",
                                "Business Systems (TE.ESEA.BS)",
                                "Operations Project Management", "MFG Project Management",
                                "Capacity Planning",
                                "Billing and Collections (FI.OPBO)", "Billing and Collections"],
        "role_regex": [cre(r"^business\s*operations"), cre(r"^biz\s*ops"),
                       cre(r"business\s*systems"), cre(r"project\s*management"),
                       cre(r"capacity\s*planning"), cre(r"billing\s*(and|&)\s*collections")],
        "title_keywords": ["business operations", "biz ops", "operations manager",
                          "chief of staff", "strategy and operations", "business systems",
                          "project manager"],
    },
    "Strategic Programs": {
        "exact_role_strings": ["Strategic Projects", "Strategic Programs", "Strategy",
                                "Strategic PM"],
        "role_regex": [cre(r"strategic\s*(project|program|pm)"), cre(r"^strategy$")],
        "title_keywords": ["strategic projects", "strategic programs", "strategy lead",
                          "strategist", "strategic initiative", "strategic pm"],
    },
    "Engagement Management": {
        "exact_role_strings": ["Engagement Management", "Engagement Manager"],
        "role_regex": [cre(r"engagement\s*manag")],
        "title_keywords": ["engagement manager", "engagement lead"],
    },
    "Operations Specialist": {
        "exact_role_strings": ["Operations Specialist", "Operations Coordinator", "Operations Analyst",
                                "Workplace", "Facilities & Equipment Maintenance", "EH&S", "Power Ops"],
        "role_regex": [cre(r"operations\s*(specialist|coordinator|analyst|associate)"),
                       cre(r"^workplace"), cre(r"facilities"), cre(r"^EH&S$")],
        "title_keywords": ["operations specialist", "operations coordinator",
                          "operations analyst", "operations associate",
                          "workplace manager", "workplace coordinator", "workplace experience",
                          "workplace site coordinator", "workplace operations",
                          "facilities manager", "manager, facilities", "facilities coordinator",
                          "office manager", "office admin", "office coordinator"],
    },
    "Finance": {
        "exact_role_strings": ["Finance", "FP&A", "Financial Planning", "Strategic Finance",
                                "G&A-Finance", "Treasury", "Capital Markets",
                                "Corporate Development", "Corporate Development (SP.SPSP)"],
        "role_regex": [cre(r"^G&A-\d+$"), cre(r"\b(finance|fp&a|financial|treasury)\b"),
                       cre(r"^capital\s*markets"), cre(r"corporate\s*development")],
        "title_keywords": ["finance manager", "financial analyst", "fp&a", "strategic finance",
                          "finance director", "vp finance", "cfo", "chief financial",
                          "treasury", "capital markets", "corporate development",
                          "deal strategy analyst"],
    },
    "Accounting": {
        "exact_role_strings": ["Accounting", "Accountant", "Controller",
                                "Payroll", "Payroll (FI.OPPR)", "Payroll (IC)"],
        "role_regex": [cre(r"\b(accounting|accountant|controller|payroll)\b"),
                       cre(r"\(FI\.OPPR\)")],
        "title_keywords": ["accountant", "controller", "accounting manager",
                          "payroll specialist", "payroll manager"],
    },
    "Procurement": {
        "exact_role_strings": ["Procurement", "Sourcing", "Supply Chain", "Vendor Management"],
        "role_regex": [cre(r"\b(procurement|sourcing|buyer|supply\s*chain|vendor)\b")],
        "title_keywords": ["procurement", "sourcing manager", "buyer", "supply chain", "vendor manager"],
    },
    "Talent Acquisition / Recruiting": {
        "exact_role_strings": ["Talent Acquisition", "Recruiting", "Recruiter",
                                "Talent Acquisition (HR.TMTA)"],
        "role_regex": [cre(r"\b(talent\s*acquisition|recruit|sourc)"),
                       cre(r"\(HR\.TMTA\)")],
        "title_keywords": ["recruiter", "talent acquisition", "sourcer",
                          "technical recruiter", "recruiting coordinator", "talent partner"],
    },
    "HR / People": {
        "exact_role_strings": ["HR", "Human Resources", "People", "People Operations",
                                "People Ops", "HRBP", "Compensation", "Total Rewards",
                                "Benefits", "Compensation & Benefits",
                                "Compensation (HR.COCO)"],
        "role_regex": [cre(r"^(hr|human\s*resources|people)\b"),
                       cre(r"^compensation"), cre(r"total\s*rewards"),
                       cre(r"\(HR\.COCO\)")],
        "title_keywords": ["people operations", "human resources", "hr business partner",
                          "hrbp", "people partner", "chief people officer",
                          "compensation analyst", "compensation manager", "total rewards",
                          "benefits manager"],
    },
    "Legal / Compliance": {
        "exact_role_strings": ["Legal", "Compliance", "Legal & Compliance", "Counsel", "Lawyer"],
        "role_regex": [cre(r"\b(legal|compliance|counsel|paralegal|lawyer)\b")],
        "title_keywords": ["legal counsel", "general counsel", "compliance officer",
                          "paralegal", "attorney", "grc", "subject matter expert", "lawyer"],
    },
    "Assembly / Production": {
        "exact_role_strings": ["Assembly", "Assembly Tech", "Assembly Technician",
                                "Production", "Production Tech", "Manufacturing",
                                "Manufacturing Engineering", "CNC Operations", "CNC"],
        "role_regex": [cre(r"\bassembly\b"), cre(r"\bproduction\s*tech"),
                       cre(r"\bmanufacturing\b"), cre(r"^cnc")],
        "title_keywords": ["assembly technician", "assembler", "production technician",
                          "manufacturing technician", "cnc operator", "machinist"],
    },
    "Wiring / Electrical": {
        "exact_role_strings": ["Wire Tech", "Wiring", "Electrical", "Electrician",
                                "Instrumentation & Control Engineering"],
        "role_regex": [cre(r"\b(wire|wiring|electrical|electrician)\b"),
                       cre(r"instrumentation")],
        "title_keywords": ["wire technician", "electrician", "electrical technician",
                          "instrumentation"],
    },
    "Construction / Installation": {
        "exact_role_strings": ["Construction", "Installation", "Painter", "Welder"],
        "role_regex": [cre(r"\b(construction|installer|installation|painter|welder|carpent)\b")],
        "title_keywords": ["construction", "installer", "painter", "welder", "carpenter"],
    },
    "Materials / Warehouse": {
        "exact_role_strings": ["Materials", "Material Handler", "Warehouse",
                                "Inventory Control", "Logistics"],
        "role_regex": [cre(r"\b(material|warehouse|inventory|logistics|forklift)\b")],
        "title_keywords": ["material handler", "warehouse", "inventory", "logistics specialist"],
    },
    "Field Service": {
        "exact_role_strings": ["Field Service", "Field Technician", "Field Engineer"],
        "role_regex": [cre(r"\bfield\s*(service|tech|engineer)")],
        "title_keywords": ["field service technician", "field engineer", "field technician"],
    },
    "Field / Hardware Engineering": {
        "exact_role_strings": ["Hardware Engineering", "Hardware Engineer", "Electrical Engineering",
                                "Mechanical Engineering", "Systems Engineering",
                                "Sustaining Engineer", "Sustaining Engineer (IC)",
                                "Equipment Operations"],
        "role_regex": [cre(r"\b(hardware|mechanical|electrical)\s*engineer"),
                       cre(r"^systems?\s*engineer"), cre(r"sustaining\s*engineer"),
                       cre(r"^equipment\s*operations")],
        "title_keywords": ["hardware engineer", "mechanical engineer", "electrical engineer",
                          "systems engineer", "sustaining engineer"],
    },
    "Executive Assistant": {
        "exact_role_strings": ["Executive Assistant", "EA", "Executive Administrative Assistant"],
        "role_regex": [cre(r"executive\s*(assistant|admin)")],
        "title_keywords": ["executive assistant", "ea to", "chief of staff"],
    },
    "Administrative": {
        "exact_role_strings": ["Administrative", "Admin", "Administrative Assistant",
                                "Ops Assistant (IC)",
                                "General Management & Administration-Professional Services",
                                "General Management & Administration-Admin Support",
                                "General Management & Administration-PMO"],
        "role_regex": [cre(r"\b(administrative)\b"),
                       cre(r"^general\s*management.*administration"),
                       cre(r"^ops\s*assistant")],
        "title_keywords": ["administrative assistant", "receptionist",
                          "operations assistant", "office coordinator"],
    },
}


# ============================================================
# Role mapping function
# ============================================================

SENIORITY_PATTERNS = [
    re.compile(r"\b(sr\.?|senior|staff|principal|junior|jr\.?|lead)\b", re.IGNORECASE),
    re.compile(r"\b(I{1,3}|IV|V)\b"),
    re.compile(r"\b\d+\b"),
]


def clean_title(title):
    if pd.isna(title) or title is None:
        return ""
    cleaned = str(title)
    for pat in SENIORITY_PATTERNS:
        cleaned = pat.sub(" ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


_exact_lookup = {}
for leaf, rules in MAPPING_RULES.items():
    for s in rules.get("exact_role_strings", []):
        _exact_lookup[s.strip().lower()] = leaf


def map_role_for_row(row):
    """Map a row (with 'Job role' and 'Job title') to a canonical role."""
    role = row.get("Job role")
    title = row.get("Job title")

    # Title-priority: management roles
    if title is not None and not pd.isna(title):
        cleaned = clean_title(title).lower()
        for leaf_priority in ["Engineering Management", "Sales Leadership"]:
            rules = MAPPING_RULES.get(leaf_priority, {})
            for kw in rules.get("title_keywords", []):
                if kw.lower() in cleaned:
                    return (leaf_priority, "title_priority")

    # Exact role match
    if role is not None and not pd.isna(role):
        leaf = _exact_lookup.get(str(role).strip().lower())
        if leaf:
            return (leaf, "exact_role")

    # Role regex
    if role is not None and not pd.isna(role):
        for leaf, rules in MAPPING_RULES.items():
            for pat in rules.get("role_regex", []):
                if pat.search(str(role)):
                    return (leaf, "role_regex")

    # Title keyword fallback
    if title is not None and not pd.isna(title):
        cleaned = clean_title(title).lower()
        if cleaned:
            for leaf, rules in MAPPING_RULES.items():
                for kw in rules.get("title_keywords", []):
                    if kw.lower() in cleaned:
                        return (leaf, "title")

    # Title regex fallback — apply role_regex patterns against the cleaned title.
    # Useful when the Job role field is empty but the Job title matches a role pattern
    # (e.g. bare "Developer" as a title should match the '^developer$' role regex).
    if title is not None and not pd.isna(title):
        cleaned = clean_title(title).lower()
        if cleaned:
            for leaf, rules in MAPPING_RULES.items():
                for pat in rules.get("role_regex", []):
                    if pat.search(cleaned):
                        return (leaf, "title_regex")

    return ("Other", "unmapped")


# ============================================================
# Level canonicalisation
# ============================================================

def normalise_level(lvl):
    if lvl is None or pd.isna(lvl):
        return None
    return re.sub(r"\s+", " ", str(lvl).strip())


MANAGER_OTHER = {
    'MGR Manager', 'MGR Sales Leader', 'MGR Quota Sales Director',
    'MGR Associate Manager', 'MGR Sr. Manager',
    'IC Manager', 'IC Associate Manager', 'IC Sr. Manager', 'Sr Dir',
}
EXECUTIVE_OTHER = {'VP', 'Exec', 'IC Director', 'E4', 'E5', 'E6'}
SENIOR_IC_OTHER = {'IC Sales Setter', 'S Specialist', 'S6'}
UNKNOWN_BUCKET = {'Contractor', 'ICQ2', 'MGRQ1', 'L8', 'G12', 'M9', 'M10', 'M11'}


def bucket_level(lvl):
    if lvl is None or pd.isna(lvl):
        return 'Unknown'
    if lvl in MANAGER_OTHER:
        return 'Manager (other)'
    if lvl in EXECUTIVE_OTHER:
        return 'Executive (other)'
    if lvl in SENIOR_IC_OTHER:
        return 'Senior IC (other)'
    if lvl in UNKNOWN_BUCKET:
        return 'Unknown'
    # For standard levels (IC4, M5, P3, L4, etc.) — pass through as-is.
    return lvl


def infer_level_from_title(title):
    """Infer canonical level from job title when unambiguous.

    Returns a canonical level string ('IC1', 'IC4', 'M3', 'Executive', etc)
    or None if the title has no clear level marker.

    Two-pass logic:
      Pass 1: management / executive markers (checked first, so 'Senior Manager'
              becomes M4 rather than IC4).
      Pass 2: IC seniority markers, only if not managerial.

    Explicitly returns None for ambiguous titles like bare 'Software Engineer'
    or 'Customer Support Representative' — we'd rather leave a row unmapped
    than mislabel its level.
    """
    if title is None or pd.isna(title):
        return None
    t = str(title).lower().strip()

    # ------------------------------------------------------------------
    # PASS 1: management / executive markers
    # ------------------------------------------------------------------
    # Executive: chief officers, VPs
    if re.search(r'\b(ceo|cto|cfo|cpo|coo|cmo|chief\s+\w+\s+officer)\b', t):
        return 'Executive'
    if re.search(r'\b(svp|senior vice president|executive vice president|evp)\b', t):
        return 'Executive'
    if re.search(r'\bvice president\b|\bvp\b|\bvp,', t):
        return 'Executive'

    # Director: senior director, head of, director of
    if re.search(r'\bsenior director\b|\bsr\.?\s+director\b|\bhead of\b', t):
        return 'Director'
    if re.search(r'\bdirector\b', t):
        # 'Assistant/Associate Director' is manager-level, not director
        if re.search(r'\bassistant director\b|\bassoc(iate)?\s+director\b', t):
            return 'M4'
        return 'Director'

    # Manager (but exclude IC-role "Manager" titles like Product Manager)
    if re.search(r'\bsenior manager\b|\bsr\.?\s+manager\b', t):
        return 'M4'
    if re.search(r'\bmanager\b', t):
        # These are IC roles despite 'Manager' in title. Let the normal role
        # mapping determine level via other signals.
        if re.search(
            r'\b(product|program|project|technical program|marketing|account|'
            r'customer success|engagement)\s+manager\b',
            t,
        ):
            return None
        return 'M3'

    # ------------------------------------------------------------------
    # PASS 2: IC seniority markers
    # ------------------------------------------------------------------
    if re.search(r'\bintern\b', t):
        return 'IC1'
    if re.search(r'^(jr|junior)\b|\bjunior\s+(engineer|developer|analyst|designer|scientist)\b', t):
        return 'IC1'
    if re.search(r'^associate\b|\bassociate\s+(engineer|developer|analyst|designer|scientist)\b', t):
        return 'IC2'
    if re.search(r'^(sr|senior|sr\.)\b|\bsenior\s+(engineer|developer|analyst|designer|scientist|associate)\b', t):
        return 'IC4'
    if re.search(r'^staff\b|\bstaff\s+(engineer|developer|analyst|designer|scientist)\b', t):
        return 'IC5'
    if re.search(r'^principal\b|\bprincipal\s+(engineer|developer|analyst|designer|scientist)\b', t):
        return 'IC6'

    return None
    return lvl


MANAGER_ROLES = {'Engineering Management', 'Sales Leadership'}
SUPPORT_ROLES = {'Customer Support', 'Technical Support'}
MANUFACTURING_ROLES = {
    'Assembly / Production', 'Wiring / Electrical',
    'Construction / Installation', 'Materials / Warehouse',
    'Field Service', 'Field / Hardware Engineering',
}


def derive_track(row):
    code = row.get('level_canonical')
    role = row.get('canonical_role')

    def track_from_role():
        if role in MANAGER_ROLES:
            return 'Manager'
        if role in SUPPORT_ROLES or role in MANUFACTURING_ROLES:
            return 'Support'
        if role and role != 'Other':
            return 'IC'
        return 'Unknown'

    if code == 'Manager (other)':       return 'Manager'
    if code == 'Executive (other)':     return 'Executive'
    if code == 'Senior IC (other)':     return 'IC'
    if code == 'Unknown':               return track_from_role()

    if isinstance(code, str):
        if code.startswith('IC'):       return 'IC'
        if code.startswith('M') and not code.startswith('Manager'): return 'Manager'
        if code.startswith('E'):        return 'Executive'
        if code.startswith('S'):        return 'Support'
        if code.startswith('P'):        return 'IC'

    if isinstance(code, str) and (code.startswith('L') or code.startswith('G')):
        return track_from_role()

    return 'Unknown'


# ============================================================
# Location mapping
# ============================================================

LOCATION_RULES = [
    # US METROS
    (r'san francisco|sf office|sf bay|sunnyvale|mountain view|palo alto|bellevue.*wa', 'US', 'SF Bay Area'),
    (r'new york|nyc|^ny$', 'US', 'NYC Metro'),
    (r'washington.*dc|^washington$|ionq dc|dc \(college park\)', 'US', 'DC Metro'),
    (r'seattle|ionq seattle', 'US', 'Seattle Metro'),
    (r'boston|ionq boston|massachusetts|cambridge.*ma', 'US', 'Boston Metro'),
    (r'denver|arvada|brighton.*co|^colorado$', 'US', 'Denver Metro'),
    (r'austin', 'US', 'Austin'),
    (r'los angeles|^la$|santa monica|culver city', 'US', 'LA Metro'),
    (r'chicago|^illinois$(?!.*remote)', 'US', 'Chicago Metro'),
    (r'atlanta|^georgia$(?!.*remote)', 'US', 'Atlanta Metro'),
    (r'dallas|^dallas, tx', 'US', 'Dallas Metro'),
    (r'houston', 'US', 'Houston Metro'),
    (r'tulsa', 'US', 'Tulsa'),
    (r'raleigh|durham|chapel hill', 'US', 'Raleigh-Durham'),
    (r'abilene.*tx', 'US', 'Abilene TX'),
    (r'amarillo.*tx', 'US', 'Amarillo TX'),
    (r'st\.? louis|saint louis', 'US', 'St. Louis'),
    (r'sojo', 'US', 'Other US Metro'),
    (r'usa remote\s*-\s*california|remote\s*-\s*california', 'US', 'SF Bay Area'),
    (r'usa remote\s*-\s*new york|remote\s*-\s*ny\b', 'US', 'NYC Metro'),
    (r'usa remote\s*-\s*texas|remote\s*-\s*tx\b', 'US', 'Dallas Metro'),
    (r'usa remote\s*-\s*illinois', 'US', 'Chicago Metro'),
    (r'usa remote\s*-\s*florida', 'US', 'Other US Metro'),
    (r'usa remote\s*-\s*georgia', 'US', 'Atlanta Metro'),
    (r'usa remote\s*-\s*colorado', 'US', 'Denver Metro'),
    (r'usa remote\s*-\s*arizona', 'US', 'Other US Metro'),
    (r'usa remote\s*-\s*north carolina', 'US', 'Raleigh-Durham'),
    (r'usa remote\s*-\s*washington', 'US', 'Seattle Metro'),
    (r'usa remote\s*-\s*massachusetts', 'US', 'Boston Metro'),
    (r'usa.*zone 1', 'US', 'Other US Metro'),
    (r'usa.*zone 2', 'US', 'Other US Metro'),
    (r'us \(remote\)|remote u\.?s\.?|usa remote(?!\s*-)', 'US', None),
    (r'^texas$|^california$|^new york$|^colorado$|^washington$|^virginia$|^florida$|^hawaii$|^ohio$|^nevada$|^tennessee$|^arizona$|^pennsylvania$|^michigan$|^utah$|^missouri$|^north carolina$|^new jersey$|^indiana$|^minnesota$|^oregon$|^new mexico$|^nebraska$|^kansas$|^kentucky$|^alabama$|^maryland$|^connecticut$|^wisconsin$|^iowa$|^wyoming$|^idaho$|^maine$|^delaware$|^vermont$|^rhode island$|^south carolina$|^louisiana$|^arkansas$|^mississippi$', 'US', None),
    (r'ponchatoula.*la|springfield.*oh|sparks.*nv|spokane|tucson|salt lake|kansas city|nashville|cheyenne.*wy|, wy\b', 'US', 'Other US Metro'),
    (r'^united states$|^us$|^usa$|^north america$', 'US', None),
    (r', us\b|, usa\b|united states', 'US', 'Other US Metro'),

    # Vercel-style hierarchical formats: "Region - Country" or "Region - Sub - Country"
    # The country is typically the last segment.
    (r'north america\s*-\s*usa', 'US', None),
    (r'north america\s*-\s*canada', 'Canada', None),
    (r'north america\s*-\s*mexico', 'Mexico', None),
    (r'europe\s*-\s*western\s*-\s*united kingdom', 'UK', None),
    (r'europe\s*-\s*western\s*-\s*germany', 'Germany', None),
    (r'europe\s*-\s*western\s*-\s*france', 'France', None),
    (r'europe\s*-\s*western\s*-\s*netherlands', 'Netherlands', None),
    (r'europe\s*-\s*western\s*-\s*spain', 'Spain', None),
    (r'europe\s*-\s*western\s*-\s*italy', 'Italy', None),
    (r'europe\s*-\s*western\s*-\s*ireland', 'Ireland', None),
    (r'europe\s*-\s*nordic\s*-\s*sweden', 'Sweden', None),
    (r'europe\s*-\s*nordic\s*-\s*norway', 'Norway', None),
    (r'europe\s*-\s*nordic\s*-\s*denmark', 'Denmark', None),
    (r'europe\s*-\s*nordic\s*-\s*finland', 'Finland', None),
    (r'europe\s*-\s*eastern\s*-\s*poland', 'Poland', None),
    (r'asia pacific\s*-\s*australia', 'Australia', None),
    (r'asia pacific\s*-\s*india', 'India', None),
    (r'asia pacific\s*-\s*singapore', 'Singapore', None),
    (r'asia pacific\s*-\s*japan', 'Japan', None),
    (r'south america\s*-\s*argentina', 'Argentina', None),
    (r'south america\s*-\s*brazil', 'Brazil', None),
    # Last-resort patterns: if "North America" appears alone (Docker-style), prefer US
    (r'^north america$', 'US', None),
    (r'^europe$', 'Other / Unknown', None),

    # ------------------------------------------------------------------
    # New-customer location formats (2026-07 additions)
    # These are variants used by customers in the second batch of data.
    # Placed here (before generic country patterns) so they take priority.
    # ------------------------------------------------------------------

    # US "Remote" variants — all resolve to US
    (r'^remote\s*-\s*us$|^remote\s*-us$|^remote-us$|^us\s*-\s*remote$|^us\s*remote$', 'US', None),
    (r'^remote\s*\(\s*united states\s*\)$|^remote\s*\(\s*us\s*\)$', 'US', None),
    (r'^united states \(general\)$|^united states \(premium\)$|^us\s*-\s*national', 'US', None),
    (r'^us\s*-\s*geo\s*\d', 'US', None),  # US - Geo 1, US - Geo 2 etc
    (r'^us\s*-\s*oak$', 'US', 'SF Bay Area'),   # Oakland is SF Bay
    (r'^us\s*-\s*dc$', 'US', 'DC Metro'),
    (r'^us\s*-\s*nyc$', 'US', 'NYC Metro'),

    # Named US cities (bare)
    (r'^minneapolis$', 'US', 'Minneapolis'),
    (r'^madison$', 'US', 'Madison'),
    (r'^redwood city$', 'US', 'SF Bay Area'),
    (r'^sunnyvale,?\s*ca?$', 'US', 'SF Bay Area'),
    (r'^new york city$', 'US', 'NYC Metro'),
    (r'^remote \(united states\)$', 'US', None),

    # Canada variants
    (r'^ottawa$', 'Canada', 'Ottawa'),
    (r'^maple$', 'Canada', 'Toronto'),  # Radiant's Maple, Ontario office
    (r'^remote\s*\(\s*canada\s*\)$', 'Canada', None),
    (r'^canada$', 'Canada', None),  # bare "Canada"

    # UK variants
    (r'^uk\s*-\s*national', 'UK', None),
    (r'^remote\s*\(\s*united kingdom\s*\)$|^remote\s*\(\s*uk\s*\)$', 'UK', None),
    (r'^united kingdom \(general\)$', 'UK', None),

    # Mexico variants
    (r'^remote\s*-\s*mexico$|^remote\s*\(\s*mexico\s*\)$', 'Mexico', None),
    (r'^remote\s*-\s*contractor$', 'Mexico', None),  # baubap-specific — their contractors are Mexico-based

    # India variants
    (r'^remote\s*\(\s*india\s*\)$|^offshore\s*-\s*india$', 'India', None),
    (r'^in\s*-\s*geo\s*\d', 'India', None),  # IN - Geo 1 (Bengaluru, Mumbai)
    (r'^bengaluru$|^bangalore$', 'India', 'Bangalore'),
    (r'^mumbai$', 'India', 'Mumbai'),

    # Europe (country-level) — variants
    (r'^hungary$|^budapest$', 'Hungary', None),
    (r'^portugal$|^lisbon$|^porto$', 'Portugal', None),
    (r'^warsaw$', 'Poland', 'Warsaw'),
    (r'^south korea$|^seoul$', 'South Korea', None),

    # Regional catch-alls that DON'T identify country — resolve to Unknown
    # (These were common in the new data and caused false-positive on country patterns)
    (r'^americas$|^apac$|^emea$|^latam$', 'Other / Unknown', None),
    (r'^remote\s*-\s*latam$|^remote\s*-\s*apac$|^offshore\s*-\s*latam$', 'Other / Unknown', None),

    # UK
    (r'london', 'UK', 'London'),
    (r'manchester', 'UK', 'Manchester'),
    (r'edinburgh', 'UK', 'Edinburgh'),
    (r'gbr remote|uk remote|remote.*gb', 'UK', None),
    (r'united kingdom|^uk$|england|wales|scotland|ionq uk', 'UK', None),

    # Ireland
    (r'dublin', 'Ireland', 'Dublin'),
    (r'^ireland$', 'Ireland', None),

    # Canada
    (r'toronto', 'Canada', 'Toronto'),
    (r'vancouver|british columbia', 'Canada', 'Vancouver'),
    (r'montreal|quebec', 'Canada', 'Montreal'),
    (r'ontario', 'Canada', 'Toronto'),
    (r'alberta|calgary', 'Canada', 'Calgary'),
    (r'nova scotia|halifax', 'Canada', 'Other Canada Metro'),
    (r'saskatchewan|regina|saskatoon', 'Canada', 'Other Canada Metro'),
    (r'manitoba|winnipeg', 'Canada', 'Other Canada Metro'),
    (r'remote\s*-\s*canada|^canada\b|ionq quantum canada', 'Canada', None),

    # Mexico
    (r'mexico city', 'Mexico', 'Mexico City'),
    (r'^mexico$', 'Mexico', None),

    # Australia
    (r'sydney|new south wales', 'Australia', 'Sydney'),
    (r'melbourne|victoria', 'Australia', 'Melbourne'),
    (r'northern territory|darwin', 'Australia', 'Other Australia Metro'),
    (r'queensland|brisbane', 'Australia', 'Brisbane'),
    (r'perth|western australia', 'Australia', 'Perth'),
    (r'^australia\b', 'Australia', None),

    # Europe (other)
    (r'amsterdam', 'Netherlands', 'Amsterdam'),
    (r'^netherlands$', 'Netherlands', None),
    (r'paris', 'France', 'Paris'),
    (r'^france$', 'France', None),
    (r'berlin', 'Germany', 'Berlin'),
    (r'munich', 'Germany', 'Munich'),
    (r'hamburg', 'Germany', 'Hamburg'),
    (r'^germany', 'Germany', None),
    (r'madrid|^spain', 'Spain', 'Madrid'),
    (r'barcelona', 'Spain', 'Barcelona'),
    (r'milan|rome|^italy$', 'Italy', None),
    (r'lisbon|^portugal', 'Portugal', 'Lisbon'),
    (r'zurich|basel|geneva|switzerland', 'Switzerland', 'Zurich'),
    (r'ionq quantum switzerland', 'Switzerland', 'Zurich'),
    (r'stockholm|^sweden$|ionq.*sweden', 'Sweden', None),
    (r'budapest|^hungary', 'Hungary', 'Budapest'),
    (r'warsaw|^poland', 'Poland', None),
    (r'bucharest|^romania', 'Romania', None),
    (r'sofia|^bulgaria', 'Bulgaria', None),
    (r'reykjavik|reykjanesbaer|^iceland', 'Iceland', None),
    (r'^europe$', 'Other / Unknown', None),

    # Middle East
    (r'doha|^qatar$', 'Qatar', 'Doha'),
    (r'tel aviv', 'Israel', 'Tel Aviv'),
    (r'^israel$|isr |, il\b', 'Israel', None),
    (r'united arab emirates|^uae$|dubai', 'UAE', 'Dubai'),
    (r'riyadh|jeddah|^saudi arabia', 'Saudi Arabia', None),

    # Asia
    (r'tokyo|^japan$', 'Japan', 'Tokyo'),
    (r'bengaluru|bangalore', 'India', 'Bangalore'),
    (r'mumbai', 'India', 'Mumbai'),
    (r'delhi|gurgaon|gurugram', 'India', 'Delhi NCR'),
    (r'hyderabad', 'India', 'Hyderabad'),
    (r'^india$', 'India', None),
    (r'singapore', 'Singapore', 'Singapore'),

    # LatAm
    (r'argentina|buenos aires', 'Argentina', 'Buenos Aires'),
    (r'brazil|sao paulo|são paulo', 'Brazil', None),
    (r'^uruguay$|montevideo', 'Uruguay', None),
    (r'^colombia$|bogota|bogotá', 'Colombia', None),
    (r'^peru$|lima', 'Peru', None),
    (r'^chile$|santiago', 'Chile', None),

    # Oceania (other)
    (r'new zealand|auckland|wellington', 'New Zealand', None),

    # Europe (other small)
    (r'^belgium$|brussels', 'Belgium', None),
    (r'norway|oslo|tordal', 'Norway', None),
    (r'finland|helsinki', 'Finland', None),
    (r'denmark|copenhagen', 'Denmark', None),

    # Remote (region unspecified) — kept for legacy handling but NEW code should
    # use map_location_with_customer_context() which resolves "Remote" to the
    # customer's HQ country when possible.
    (r'^remote$', 'Other / Unknown', None),
]

COMPILED_LOCATION_RULES = [(re.compile(p, re.IGNORECASE), c, m) for p, c, m in LOCATION_RULES]


# ============================================================
# Customer HQ lookup — used for resolving bare "Remote" strings
# and for the "HQ" location value some customers use.
#
# Best-guess mapping based on public knowledge of these companies.
# Defaults to US for unlisted customers (matches ~85% of TeamOhana's
# actual customer base).
# ============================================================
CUSTOMER_HQ_COUNTRY = {
    # Non-US HQs (confirmed)
    'jane_app':          'Canada',
    'solink':            'Canada',
    'hyperexponential':  'UK',
    'baubap':            'Mexico',

    # US HQs (confirmed)
    'attain':            'US',
    'cedar_cares':       'US',
    'evenup':            'US',
    'everlaw':           'US',
    'fetch':             'US',
    'gravie':            'US',
    'ironclad':          'US',
    'juniper_square':    'US',
    'komodo':            'US',
    'lastpass':          'US',
    'malbek':            'US',
    'ontra':             'US',
    'rad_ai':            'US',
    'radiant':           'US',
    'security_score_card': 'US',
    'sonatus':           'US',
    'sprout_social':     'US',
    'tilt':              'US',
    'zip':               'US',

    # Original master-sheet customers (from prior anonymised training data)
    'DOC': 'US', 'docker': 'US',
    # If we later confirm HQ for VANT, SCAL, CRUS, etc. add here.
}
DEFAULT_HQ_COUNTRY = 'US'  # fallback for unlisted customers


def is_remote_string(loc):
    if loc is None or pd.isna(loc):
        return False
    return bool(re.search(r'\bremote\b', str(loc), re.IGNORECASE))


def map_location(loc):
    """Map a raw location string to (country, metro, is_remote)."""
    if loc is None or pd.isna(loc):
        return ('Other / Unknown', None, False)
    s = str(loc).strip()
    if ';' in s:
        s = s.split(';')[0].strip()
    is_remote = is_remote_string(s)
    for pat, country, metro in COMPILED_LOCATION_RULES:
        if pat.search(s):
            return (country, metro, is_remote)
    return ('Other / Unknown', None, is_remote)


def map_location_with_customer_context(loc, customer_id=None):
    """Same as map_location, but resolves ambiguous strings ('Remote', 'HQ')
    to the customer's HQ country when we know it.

    This is what the training pipeline uses. The public /predict endpoint
    doesn't have a customer_id, so it uses map_location() directly — which
    is fine because public users pick a country explicitly from the dropdown.

    Args:
        loc: raw location string.
        customer_id: string identifier for the customer; used to look up HQ.
                     If None or unknown, ambiguous strings become Other / Unknown.
    """
    if loc is None or pd.isna(loc):
        return ('Other / Unknown', None, False)

    s = str(loc).strip()
    if ';' in s:
        s = s.split(';')[0].strip()

    # Check for the two ambiguous patterns that require customer context
    is_bare_remote = re.match(r'^remote$', s, re.IGNORECASE) is not None
    is_hq          = re.match(r'^hq$',     s, re.IGNORECASE) is not None

    if is_bare_remote or is_hq:
        if customer_id:
            hq_country = CUSTOMER_HQ_COUNTRY.get(customer_id.lower(), DEFAULT_HQ_COUNTRY)
        else:
            hq_country = DEFAULT_HQ_COUNTRY
        # 'Remote' means WFH from HQ country. 'HQ' means at HQ (in-office).
        return (hq_country, None, is_bare_remote)

    # Otherwise fall through to standard mapping
    return map_location(s)


# ============================================================
# Hire quarter
# ============================================================

REFERENCE_DATE = pd.Timestamp('2021-01-01')


def to_quarter_numeric(d):
    """Months since 2021-01-01, snapped to quarter boundary. Q1 2021 = 0."""
    if d is None or pd.isna(d):
        return None
    d = pd.Timestamp(d)
    months = (d.year - REFERENCE_DATE.year) * 12 + (d.month - REFERENCE_DATE.month)
    return (months // 3) * 3


def quarter_label(q_numeric):
    """Reverse: numeric back to '2025Q3'."""
    if q_numeric is None or pd.isna(q_numeric):
        return None
    months_offset = int(q_numeric)
    year = REFERENCE_DATE.year + months_offset // 12
    qtr = (months_offset % 12) // 3 + 1
    return f"{year}Q{qtr}"
