import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import Script from "next/script";
import "./globals.css";

const inter = Inter({
  subsets: ["latin", "cyrillic"],
  variable: "--font-inter",
});

const SITE_URL = "https://sivi.uz";
const SITE_NAME = "Sivi";
const DESCRIPTION =
  "Sivi is your AI career agent on Telegram — build better CVs, find matching jobs in Uzbekistan, and prepare for interviews, all in chat.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: "Sivi — AI Career Agent for CVs, Jobs & Interviews",
    template: "%s | Sivi",
  },
  description: DESCRIPTION,
  applicationName: SITE_NAME,
  authors: [{ name: "Sivi", url: SITE_URL }],
  creator: "Sivi",
  publisher: "Sivi",
  keywords: [
    "AI career agent",
    "resume builder",
    "CV builder",
    "AI resume",
    "job search Uzbekistan",
    "Telegram job bot",
    "interview preparation",
    "vakansiya",
    "ish qidirish",
    "rezyume",
    "поиск работы",
    "AI карьера",
    "резюме",
    "Sivi",
  ],
  category: "technology",
  alternates: {
    canonical: "/",
    languages: {
      "en-US": "/",
      "uz-UZ": "/",
      "ru-RU": "/",
      "x-default": "/",
    },
  },
  openGraph: {
    title: "Sivi — AI Career Agent for CVs, Jobs & Interviews",
    description: DESCRIPTION,
    url: SITE_URL,
    siteName: SITE_NAME,
    type: "website",
    locale: "en_US",
    alternateLocale: ["uz_UZ", "ru_RU"],
    images: [
      {
        url: "/logo-bg.png",
        width: 2400,
        height: 2400,
        alt: "Sivi — AI Career Agent",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Sivi — AI Career Agent for CVs, Jobs & Interviews",
    description: DESCRIPTION,
    images: ["/logo-bg.png"],
  },
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/logo.png", type: "image/png" },
    ],
    apple: "/logo.png",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0a0a0a" },
  ],
  width: "device-width",
  initialScale: 1,
};

const structuredData = {
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": `${SITE_URL}#organization`,
      name: SITE_NAME,
      url: SITE_URL,
      logo: `${SITE_URL}/logo.png`,
      sameAs: ["https://t.me/sivi_uz_bot"],
    },
    {
      "@type": "WebSite",
      "@id": `${SITE_URL}#website`,
      url: SITE_URL,
      name: SITE_NAME,
      description: DESCRIPTION,
      publisher: { "@id": `${SITE_URL}#organization` },
      inLanguage: ["en", "uz", "ru"],
    },
    {
      "@type": "SoftwareApplication",
      name: SITE_NAME,
      operatingSystem: "Telegram",
      applicationCategory: "BusinessApplication",
      description: DESCRIPTION,
      url: SITE_URL,
      offers: {
        "@type": "Offer",
        price: "0",
        priceCurrency: "USD",
      },
    },
  ],
};

const themeInitScript = `(function(){try{var t=localStorage.getItem('sivi-theme');if(t==='dark'){document.documentElement.classList.add('dark');}}catch(e){}})();`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="uz" className={`${inter.variable} h-full antialiased`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
      </head>
      <body className="min-h-full flex flex-col font-sans">
        {children}
        <Script
          id="ld-json"
          type="application/ld+json"
          strategy="beforeInteractive"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(structuredData) }}
        />
      </body>
    </html>
  );
}
