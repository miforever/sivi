import type { MetadataRoute } from "next";

const SITE_URL = "https://sivi.uz";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  return [
    {
      url: `${SITE_URL}/`,
      lastModified: now,
      changeFrequency: "weekly",
      priority: 1,
      alternates: {
        languages: {
          "en-US": `${SITE_URL}/`,
          "uz-UZ": `${SITE_URL}/`,
          "ru-RU": `${SITE_URL}/`,
          "x-default": `${SITE_URL}/`,
        },
      },
    },
  ];
}
