"use client";

import { motion } from "framer-motion";
import ScrollReveal from "./ScrollReveal";
import { useLanguage } from "@/i18n/LanguageContext";

export default function CTA() {
  const { t } = useLanguage();

  return (
    <section className="relative py-28 overflow-hidden">
      <div className="relative z-10 max-w-3xl mx-auto px-6 text-center">
        <ScrollReveal>
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-fg mb-5 leading-tight">
            {t.cta.titleLine1}
            <br />
            {t.cta.titleLine2 && <>{t.cta.titleLine2}{" "}</>}
            <span className="gradient-text">{t.cta.titleGradient}</span>
          </h2>
          <p className="text-fg/60 text-lg mb-10 max-w-xl mx-auto">
            {t.cta.subtitle}
          </p>
        </ScrollReveal>

        <ScrollReveal delay={0.2}>
          <motion.a
            href="https://t.me/SiviAIBot"
            target="_blank"
            rel="noopener noreferrer"
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.98 }}
            className="inline-flex items-center gap-3 px-10 py-4 rounded-full text-lg font-semibold text-white bg-gradient-to-r from-brand-400 to-brand-500 hover:from-brand-500 hover:to-brand-600 transition-all duration-300 shadow-[0_0_40px_rgba(236,72,153,0.3)] hover:shadow-[0_0_60px_rgba(236,72,153,0.5)]"
          >
            <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z" />
            </svg>
            {t.cta.button}
          </motion.a>
        </ScrollReveal>
      </div>
    </section>
  );
}
