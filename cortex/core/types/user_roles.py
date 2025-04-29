from enum import Enum


class TelescopeUserRoles(Enum):
    PROJECT_OWNER = "project_owner"
    WORKSPACE_OWNER = "workspace_owner"
    PROJECT_EDITOR = "project_editor"
    WORKSPACE_EDITOR = "workspace_editor"
    WORKSPACE_VIEWER = "workspace_member"
    PROJECT_VIEWER = "project_viewer"

