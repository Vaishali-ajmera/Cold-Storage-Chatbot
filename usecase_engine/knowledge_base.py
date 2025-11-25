QUESTION_BANK = {
    "version": "v1.2_streamlined",
    "section_order": ["general_context", "usecase_sections"],
    "general_context": {
        "title": "Your Cold Storage Advisory Profile",
        "description": "To give you the most accurate and helpful advice, please answer these quick questions about your farm, location, and storage needs.",
        "questions": [
            {
                "id": "user_pincode",
                "text": "Please enter your site PIN code.",
                "input_type": "text",
                "required": True,
                "help_text": "Used for ambient temp, tariffs, and region-specific schemes.",
            },
            {
                "id": "primary_produce_list",
                "text": "What is the primary crop/commodity you focus on?",
                "input_type": "multi_select",
                "required": True,
                "options": [
                    "Potato",
                    "Onion",
                    "Apple",
                    "Banana",
                    "Mango",
                    "Garlic",
                    "Chilli",
                    "Mixed Vegetables",
                    "Flowers",
                    "Other",
                ],
                "help_text": "Select the main crops to determine ideal T/RH and equipment type.",
            },
            {
                "id": "business_model",
                "text": "Who will primarily use the facility?",
                "input_type": "select",
                "required": True,
                "options": [
                    "Own farm only",
                    "Rental/Commercial",
                    "FPO/Coop",
                    "Trader/Supply chain",
                    "Mixed",
                ],
                "help_text": "Determines utilization strategy and certification needs.",
            },
            {
                "id": "want_subsidy_loan",
                "text": "Are you interested in subsidy or loan assistance?",
                "input_type": "select",
                "required": True,
                "options": ["Yes", "Maybe", "No"],
                "help_text": "If Yes, we will collect detailed finance data later.",
            },
            {
                "id": "major_problem_to_solve",
                "text": "What is your single biggest challenge right now?",
                "input_type": "select",
                "required": True,
                "options": [
                    "High energy cost",
                    "Spoilage/Losses",
                    "Need to build new storage",
                    "Need financing",
                    "Transport issues",
                    "Frequent breakdowns",
                ],
                "help_text": "Helps the chatbot focus its initial advice.",
            },
        ],
    },
    "usecase_sections": {
        # ---------------------------------------------------------------------
        # 1) Build New Cold Storage (STREAMLINED)
        # ---------------------------------------------------------------------
        "build_new_cold_storage": {
            "title": "Build a New Cold Storage",
            "description": "Essential inputs for initial sizing, cost estimation, and location feasibility.",
            "sections": [
                {
                    "id": "sizing_and_finance",
                    "title": "Sizing & Budget",
                    "order": 1,
                    "questions": [
                        {
                            "id": "peak_quantity_mt",
                            "text": "Peak quantity to store (MT)",
                            "input_type": "number",
                            "required": True,
                            "validation": {"min": 0.1, "max": 10000},
                        },
                        {
                            "id": "storage_duration_days",
                            "text": "Average storage duration per batch (days)",
                            "input_type": "select",
                            "required": True,
                            "options": ["<30", "30–90", "90–180", "180+"],
                        },
                        {
                            "id": "max_total_budget",
                            "text": "Maximum total project budget (INR)",
                            "input_type": "number",
                            "required": True,
                            "help_text": "Used for initial cost feasibility assessment.",
                        },
                        {
                            "id": "land_size_sqft",
                            "text": "Available land area (sq.ft)",
                            "input_type": "number",
                            "required": True,
                            "help_text": "Minimum required for the capacity. Check feasibility.",
                        },
                    ],
                },
                {
                    "id": "utility_and_design",
                    "title": "Power & Design Needs",
                    "order": 2,
                    "questions": [
                        {
                            "id": "electricity_type",
                            "text": "Electricity connection type",
                            "input_type": "select",
                            "required": True,
                            "options": [
                                "3-phase stable",
                                "3-phase with outages",
                                "Single-phase",
                                "No connection",
                            ],
                        },
                        {
                            "id": "avg_power_cut_hours",
                            "text": "Average grid outage (hrs/day)",
                            "input_type": "number",
                            "required": True,
                            "validation": {"min": 0, "max": 24},
                        },
                        {
                            "id": "building_type",
                            "text": "Preferred building type",
                            "input_type": "select",
                            "required": True,
                            "options": [
                                "PUF panels",
                                "Pre-engineered steel (PEB)",
                                "Concrete (RCC)",
                                "Not sure",
                            ],
                        },
                        {
                            "id": "num_chambers",
                            "text": "Number of temperature chambers",
                            "input_type": "select",
                            "required": True,
                            "options": ["1", "2", "3", "4", "Not sure"],
                        },
                    ],
                },
            ],
        },
        # ---------------------------------------------------------------------
        # 2) Upgrade Existing Cold Storage (STREAMLINED)
        # ---------------------------------------------------------------------
        "upgrade_existing_cold_storage": {
            "title": "Upgrade Existing Cold Storage",
            "description": "Diagnostic questions for retrofits, energy savings, and equipment upgrades.",
            "sections": [
                {
                    "id": "current_status_diagnosis",
                    "title": "Facility Status & Issue",
                    "order": 1,
                    "questions": [
                        {
                            "id": "existing_capacity_mt",
                            "text": "Current storage capacity (MT)",
                            "input_type": "number",
                            "required": True,
                        },
                        {
                            "id": "current_refrigerant_type",
                            "text": "Current refrigerant used (approx)",
                            "input_type": "select",
                            "required": True,
                            "options": [
                                "R22 legacy",
                                "R404A/HFC",
                                "Ammonia",
                                "CO2",
                                "Unknown",
                            ],
                        },
                        {
                            "id": "symptoms",
                            "text": "What are the main issues? (select all)",
                            "input_type": "multi_select",
                            "required": True,
                            "options": [
                                "High energy bills",
                                "Uneven temperatures",
                                "Frequent breakdowns",
                                "High spoilage",
                                "Ice formation",
                                "Low occupancy",
                            ],
                        },
                        {
                            "id": "current_power_consumption_kwh",
                            "text": "Average power consumption (kWh/day) if known",
                            "input_type": "number",
                            "required": False,
                        },
                    ],
                },
                {
                    "id": "upgrade_goals_budget",
                    "title": "Goals & Constraints",
                    "order": 2,
                    "questions": [
                        {
                            "id": "primary_upgrade_goal",
                            "text": "Primary goal for upgrade",
                            "input_type": "select",
                            "required": True,
                            "options": [
                                "Reduce energy costs",
                                "Increase capacity",
                                "Reduce downtime",
                                "Improve product quality",
                            ],
                        },
                        {
                            "id": "budget_for_upgrade",
                            "text": "Planned budget for upgrades (INR)",
                            "input_type": "number",
                            "required": False,
                        },
                        {
                            "id": "accept_operational_downtime",
                            "text": "Can you tolerate downtime for retrofit?",
                            "input_type": "select",
                            "required": True,
                            "options": [
                                "Yes — up to 7 days",
                                "Yes — up to 30 days",
                                "No — minimal downtime",
                            ],
                        },
                    ],
                },
            ],
        },
        # ---------------------------------------------------------------------
        # 3) Optimize Temperature & Humidity (STREAMLINED)
        # ---------------------------------------------------------------------
        "optimize_temperature_humidity": {
            "title": "Optimize Temperature & Humidity",
            "description": "Questions to set correct setpoints, discover operational flaws, and provide SOPs.",
            "sections": [
                {
                    "id": "commodity_and_issues",
                    "title": "Observed Conditions & Flaws",
                    "order": 1,
                    "questions": [
                        {
                            "id": "observed_issues_conditions",
                            "text": "Observed spoilage/quality issues (select all)",
                            "input_type": "multi_select",
                            "required": True,
                            "options": [
                                "Sprouting",
                                "Chilling injury",
                                "Mold/fungal growth",
                                "Shriveling",
                                "Weight loss",
                                "No idea",
                            ],
                        },
                        {
                            "id": "current_setpoint_temp_c",
                            "text": "Current temperature setpoint (°C) if known",
                            "input_type": "number",
                            "required": False,
                            "validation": {"min": -40, "max": 50},
                        },
                        {
                            "id": "current_rh_pct",
                            "text": "Current relative humidity (%) if known",
                            "input_type": "number",
                            "required": False,
                            "validation": {"min": 0, "max": 100},
                        },
                    ],
                },
                {
                    "id": "handling_and_practices",
                    "title": "Handling & Packaging",
                    "order": 2,
                    "questions": [
                        {
                            "id": "packaging_type",
                            "text": "Packaging / stacking used",
                            "input_type": "select",
                            "required": True,
                            "options": ["Loose", "Crates", "Cartons", "Racks"],
                        },
                        {
                            "id": "pre_cooling_available",
                            "text": "Do you use pre-cooling?",
                            "input_type": "select",
                            "required": True,
                            "options": ["Yes", "No"],
                        },
                        {
                            "id": "willing_to_change_packaging",
                            "text": "Open to changing packaging/stacking?",
                            "input_type": "select",
                            "required": True,
                            "options": ["Yes", "Maybe", "No"],
                        },
                    ],
                },
            ],
        },
        # ---------------------------------------------------------------------
        # 4) Reduce Transport Losses (STREAMLINED)
        # ---------------------------------------------------------------------
        "reduce_transport_losses": {
            "title": "Reduce Transport Losses",
            "description": "Questions for assessing cold chain breaks and recommending logistics fixes.",
            "sections": [
                {
                    "id": "transit_profile",
                    "title": "Transit Profile",
                    "order": 1,
                    "questions": [
                        {
                            "id": "transit_distance_km",
                            "text": "Typical transit distance (km)",
                            "input_type": "number",
                            "required": True,
                        },
                        {
                            "id": "transit_time_hours",
                            "text": "Typical transit time (hours)",
                            "input_type": "number",
                            "required": True,
                        },
                        {
                            "id": "typical_loss_percent",
                            "text": "Approx spoilage/loss % during transit (if known)",
                            "input_type": "number",
                            "required": False,
                        },
                    ],
                },
                {
                    "id": "vehicle_and_cooling",
                    "title": "Vehicle & Cooling",
                    "order": 2,
                    "questions": [
                        {
                            "id": "vehicle_types",
                            "text": "Primary transport vehicle type",
                            "input_type": "select",
                            "required": True,
                            "options": [
                                "Open truck",
                                "Insulated truck",
                                "Reefer",
                                "Small pickup/van",
                            ],
                        },
                        {
                            "id": "is_precooled_before_loading",
                            "text": "Is produce precooled before loading?",
                            "input_type": "select",
                            "required": True,
                            "options": ["Yes", "Partially", "No"],
                        },
                        {
                            "id": "where_cold_chain_breaks",
                            "text": "Where cold chain typically breaks? (select all)",
                            "input_type": "multi_select",
                            "required": True,
                            "options": [
                                "Pickup",
                                "In transit",
                                "At market",
                                "During loading",
                                "None",
                            ],
                        },
                    ],
                },
            ],
        },
        # ---------------------------------------------------------------------
        # 5) Get Subsidy or Loan (STREAMLINED)
        # ---------------------------------------------------------------------
        "get_subsidy_or_loan": {
            "title": "Subsidy & Loan Assistance",
            "description": "Essential eligibility and document collection for scheme matching.",
            "sections": [
                {
                    "id": "applicant_profile",
                    "title": "Eligibility Criteria",
                    "order": 1,
                    "questions": [
                        {
                            "id": "applicant_type",
                            "text": "Applicant entity type",
                            "input_type": "select",
                            "required": True,
                            "options": [
                                "Individual farmer",
                                "FPO/Coop",
                                "Company/Trader",
                            ],
                        },
                        {
                            "id": "applicant_category",
                            "text": "Farmer category (affects subsidy rate)",
                            "input_type": "select",
                            "required": True,
                            "options": [
                                "Marginal/Small (<2ha)",
                                "Large (>2ha)",
                                "SC/ST",
                                "FPO/Coop",
                            ],
                        },
                        {
                            "id": "land_ownership_proof",
                            "text": "Land ownership/lease proof available?",
                            "input_type": "select",
                            "required": True,
                            "options": [
                                "Yes — owned",
                                "Yes — leased",
                                "No — to be acquired",
                            ],
                        },
                    ],
                },
                {
                    "id": "finance_needs",
                    "title": "Project & Finance",
                    "order": 2,
                    "questions": [
                        {
                            "id": "project_type_finance",
                            "text": "Project for which finance is needed",
                            "input_type": "select",
                            "required": True,
                            "options": [
                                "New cold storage",
                                "Expansion/Upgrade",
                                "Solar installation",
                                "Working capital",
                            ],
                        },
                        {
                            "id": "max_total_budget",
                            "text": "Total project cost (INR)",
                            "input_type": "number",
                            "required": True,
                        },
                        {
                            "id": "documents_available",
                            "text": "Key documents available?",
                            "input_type": "multi_select",
                            "required": True,
                            "options": [
                                "Land deed/lease",
                                "DPR/Quotation",
                                "Bank statement/CIBIL check",
                                "Business registration",
                                "None",
                            ],
                        },
                    ],
                },
            ],
        },
        # ---------------------------------------------------------------------
        # 6) Solar / Hybrid Energy Options (STREAMLINED)
        # ---------------------------------------------------------------------
        "solar_energy_for_cold_storage": {
            "title": "Solar & Hybrid Energy",
            "description": "Collects energy profile to size PV/battery or hybrid solution and calculate ROI.",
            "sections": [
                {
                    "id": "energy_profile",
                    "title": "Energy Consumption Profile",
                    "order": 1,
                    "questions": [
                        {
                            "id": "avg_daily_energy_kwh",
                            "text": "Average daily consumption (kWh/day)",
                            "input_type": "number",
                            "required": True,
                        },
                        {
                            "id": "monthly_grid_bill_inr",
                            "text": "Average monthly electricity bill (INR) if known",
                            "input_type": "number",
                            "required": False,
                        },
                        {
                            "id": "peak_load_kw",
                            "text": "Peak electrical load (kW) if known",
                            "input_type": "number",
                            "required": False,
                        },
                    ],
                },
                {
                    "id": "site_and_preferences",
                    "title": "Site & Preferences",
                    "order": 2,
                    "questions": [
                        {
                            "id": "roof_area_sqm",
                            "text": "Available roof/ground area for PV (sq.m)",
                            "input_type": "number",
                            "required": False,
                        },
                        {
                            "id": "interest_in_battery_backup",
                            "text": "Interested in battery backup",
                            "input_type": "select",
                            "required": True,
                            "options": ["Yes", "Maybe", "No"],
                        },
                        {
                            "id": "diesel_backup_for_hybrid",
                            "text": "Do you want DG as part of hybrid?",
                            "input_type": "select",
                            "required": True,
                            "options": ["Yes", "No", "Maybe"],
                        },
                    ],
                },
            ],
        },
    },
}
