import packageJson from "../../package.json";

const currentYear = new Date().getFullYear();

export const APP_CONFIG = {
  name: "BackOne Data",
  version: packageJson.version,
  copyright: `© ${currentYear}, PT. BackOne.`,
  meta: {
    title: "BackOne Data - Dashboard Manajemen Situs",
    description:
      "Dashboard internal BackOne untuk pemantauan situs jaringan, kuota bandwidth, grouping network, dan organisasi.",
  },
};
