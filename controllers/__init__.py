# 1. Imports depuis le contrôleur de gestion du personnel
from .staff_controller import (
    get_all_staff_combined,
    update_staff_member,
    delete_staff_member,
    add_accountant,
    get_all_accountants,
    update_accountant,
    delete_accountant
)

# 2. Imports depuis le contrôleur des clients
from .client_controller import (
    get_all_clients_combined,
    get_all_clients,
    get_client_by_id,
    add_client,
    update_client,
    delete_client,
    update_client_combined
)

# 3. Imports depuis le contrôleur des documents
from .document_controller import (
    add_document,
    get_client_documents,
    get_client_documents_combined,
    delete_document,
    delete_document_combined,
    get_web_document_content
)

# 4. Imports depuis le contrôleur des échéances (deadlines) et alertes
from .deadline_controller import (
    get_overdue_count,
    get_all_overdue_deadlines,
    add_deadline,
    get_client_deadlines,
    get_client_deadlines_combined,
    update_deadline_status,
    update_deadline_status_combined,
    delete_deadline_combined
)

# 5. Imports pour les statistiques et le tableau de bord
from .dashboard_controller import (
    get_charts_data,
    get_admin_dashboard_stats
)