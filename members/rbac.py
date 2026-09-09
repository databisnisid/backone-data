FEATURE_FIELDS = (
    "quota_string",
    "upload_baa",
    "invoice_number",
    "invoice_file",
    "po_file_user",
    "po_file_vendor",
    "bap_file",
    "ip_address",
    "sdwan_package",
    "project_number",
    "baa_status_category",
    "notes",
)

# Fields a role may WRITE on a manual site. Synced sites: nobody writes (V5).
# CORE_EDIT fields (rename/address/network/timeline) only for ops roles.
CORE_EDIT_FIELDS = (
    "name",
    "member_code",
    "member_id",
    "address",
    "location",
    "online_at",
    "offline_at",
    "service_line",
    "network",
    "links",
)

WRITE_BY_ROLE = {
    "Superuser": set(CORE_EDIT_FIELDS + FEATURE_FIELDS),
    "Support": set(CORE_EDIT_FIELDS + FEATURE_FIELDS),
    "Sales": {"baa_status_category", "upload_baa", "notes", "member_links"},
    "Purchasing": {"po_file_vendor"},
    "Finance": {"invoice_number", "invoice_file", "notes"},
    "External": set(),
    "External Network": set(),
}

# Fields a role may READ on top of the always-readable core grid fields.
READ_EXTRA_BY_ROLE = {
    "Sales": {"baa_status_category", "upload_baa", "notes", "member_links"},
    "Purchasing": {"po_file_vendor"},
    "Finance": {"invoice_number", "invoice_file", "po_file_user", "po_file_vendor", "notes"},
    "External": {"notes"},
    "External Network": {"notes"},
}

CORE_FIELDS = (
    "id",
    "name",
    "member_code",
    "member_id",
    "address",
    "location",
    "online_at",
    "offline_at",
    "network",
    "network_name",
    "network_group",
    "links",
    "member_links",
    "service_line",
    "is_online",
    "is_manual",
)


def roles_for(user):
    if user.is_superuser:
        yield "Superuser"
    for group in user.groups.all():
        yield group.name


def writable_fields(user):
    fields = set()
    for role in roles_for(user):
        fields |= WRITE_BY_ROLE.get(role, set())
    return fields


def readable_fields(user):
    fields = set(CORE_FIELDS)
    for role in roles_for(user):
        fields |= READ_EXTRA_BY_ROLE.get(role, set())
    return fields
