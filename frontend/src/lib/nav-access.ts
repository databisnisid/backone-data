// C36/V51: users in External / External Network lose Quota, Networks, Pengaturan.
// Membership in either group wins over any other role group; is_superuser wins over
// this rule and is checked by the caller before consulting this.
const EXTERNAL_GROUPS = new Set(["External", "External Network"]);

export const EXTERNAL_HIDDEN_NAV_IDS = new Set(["quota", "networks", "organizations"]);

export function isExternalNavHidden(groups: readonly string[]): boolean {
  return groups.some((group) => EXTERNAL_GROUPS.has(group));
}
