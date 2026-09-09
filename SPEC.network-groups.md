# SPEC — Network Group Edit (Frontend)

> Status: **implemented & deployed**. Network group CRUD backend + FE shipped.
> Kept out of SPEC.md (separate feature), build loop closed.
>

## §G — Goal

One line (caveman):
- Admin edits Network Group in frontend — create/rename/assign-unassign networks/delete group; a group's member-sites are auto-derived from its assigned networks (sites whose `network.network_group` = group).

## §C — Constraints

- Reuse legacy models: `NetworksGroup` + `Networks.network_group` FK. No new site→group M2M.
- "Choose which networks belong to group" = set each network's `network_group` FK (networks in a group move under it).
- "Which member(site) belong to group" = inherited via network. A site joins a group because its `network.network_group` == group. No per-site direct assignment.
- New structure = just create new `NetworksGroup` rows (legacy groups still readable; legacy structure not rebuilt).
- Backend: `NetworksGroupViewSet` (currently ReadOnlyModelViewSet) becomes writable — create/update/delete groups + assign networks (set the FK). Assign path must PATCH networks' `network_group`.
- Permission: admin-only write (superuser). Reads stay per existing RBAC (IsAuthenticated).
- FE: Networks page gets group management — list groups, "Tambah Group", per-group edit (name + multi-select networks + read-only derived member-sites), delete with confirmation.
- Delete semantics: group delete → its networks' `network_group` SET_NULL (become Ungroup). No cascade to sites.
- `Members.network_group` property (derived via network) unchanged — site group shown from network.
- Role gate: superuser-only writes (custom `IsSuperUser`, mirrors `members/apis.py:18`). FE gates group-edit controls on `isSuperuser`. Reads stay `IsAuthenticated`.

## §I — Interfaces

- `networks/apis.py` — `NetworksGroupViewSet` writable (List/Create/Retrieve/Update/Destroy, `get_permissions` → `IsSuperUser` on write); `NetworksViewSet` gains `UpdateModelMixin` + superuser-write PATCH for `network_group` assignment. `NetworksGroupSerializer` adds read-only `sites` (derived `Members.network__network_group` count).
- `networks/urls.py` — router registration unchanged; ensure writable routes exposed.
- FE: `frontend/src/app/(main)/networks/_components/networks-view.tsx` — group CRUD UI (`isSuperuser` prop gates controls); `networks/page.tsx` fetches `/api/auth/me/` and passes the flag.

## §V — Invariants (proposed)

- V31 — group CRUD persists to backend; create/rename/assign/delete reflected live in `/networks` and in site `network_group`.
- V32 — group delete orphans its networks (SET_NULL → Ungroup), never deletes sites.
- V33 — write ops on group endpoint admin-only; non-admin reads unchanged.

## §T — Tasks

| ID | Status | Task | Cites |
|---|---|---|---|
| T1 | x | Backend: make `NetworksGroupViewSet` writable (create/update/destroy) + network assignment (set `network_group`) | V33 |
| T2 | x | Backend: admin-only write permission on group endpoint | V33 |
| T3 | x | FE: Networks page — group list + "Tambah Group" + per-group edit (name, network multi-select, derived member-sites read-only) + delete confirm | V31,V32 |
| T4 | x | Verify: group create/rename/assign/delete round-trips; orphan networks Ungroup; site `network_group` reflects assignment | V31,V32 |

## §B — Bugs

| ID | Date | Cause | Fix |
|---|---|---|---|
