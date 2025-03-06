class DocsMeta:
    API_GLOBAL_DESCRIPTION = """
    Use this API to interact with Telescope's APIs 🚀

    Supported Entities are mentioned below:
    1. Workspaces - Top level organizational units
    2. Environments - Development stages within workspaces (e.g., Development, Staging, Production)
    3. Consumers - End users within specific environments
    4. Consumer Groups - Collections of consumers that share common attributes
    5. Data Sources - External data systems that integrate with environments
    """

    TAGS_META = [
        {
            "name": "Workspaces",
            "description": """
            Operations to manage workspaces.
            
            A workspace is the top-level organizational unit that contains multiple environments.
            Each workspace must have a unique name.
            """,
        },
        {
            "name": "Environments",
            "description": """
            Operations to manage environments within workspaces.
            
            Environments represent different stages of development (e.g., Development, Staging, Production).
            Each environment must have a unique name within its workspace.
            """,
        },
        {
            "name": "Consumers",
            "description": """
            Operations to manage consumers within environments.
            
            Consumers represent end users of the system and are associated with specific environments.
            Each consumer must have a unique email within their environment.
            """,
        },
        {
            "name": "Consumer Groups",
            "description": """
            Operations to manage consumer groups and their members.
            
            Consumer groups allow clustering of consumers that share common attributes or behaviors.
            Each group belongs to a specific environment and has a many-to-many relationship with consumers.
            Groups must have a unique name within their environment.
            """,
        },
        {
            "name": "Data Sources",
            "description": """
            Operations to manage data sources connected to environments.
            
            Data sources represent external data systems like databases, data warehouses, and document stores.
            Each data source is associated with a specific environment and must have configuration details.
            Data sources must have a unique name within their environment.
            """,
        },
        {
            "name": "Health",
            "description": "Endpoints to check server readiness and system health",
        },
    ]
