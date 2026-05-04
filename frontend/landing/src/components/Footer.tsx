"use client";

import Image from "next/image";
import { useLanguage } from "@/i18n/LanguageContext";

export default function Footer() {
  const { t } = useLanguage();

  return (
    <footer className="relative border-t border-fg/10">
      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="flex flex-col md:flex-row items-center justify-between gap-8">
          {/* Logo & tagline */}
          <div className="flex items-center gap-3">
            <Image src="/logo.png" alt="Sivi" width={28} height={28} />
            <span className="text-fg font-semibold">Sivi</span>
            <span className="text-fg/30 mx-2">|</span>
            <span className="text-fg/50 text-sm">{t.footer.tagline}</span>
          </div>

          {/* Links */}
          <div className="flex items-center gap-6 text-sm text-fg/50">
            <a href="#features" className="hover:text-fg/80 transition-colors">
              {t.footer.features}
            </a>
            <a href="#about" className="hover:text-fg/80 transition-colors">
              {t.footer.about}
            </a>
            <a
              href="https://t.me/SiviAIBot"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-fg/80 transition-colors"
            >
              {t.footer.telegram}
            </a>
          </div>

          {/* Contact */}
          <div className="text-sm text-fg/40">
            <a
              href="mailto:inmusfa@gmail.com"
              className="hover:text-fg/70 transition-colors"
            >
              inmusfa@gmail.com
            </a>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-fg/10 text-center text-xs text-fg/30">
          &copy; {new Date().getFullYear()} Sivi. {t.footer.rights}
        </div>
      </div>
    </footer>
  );
}
