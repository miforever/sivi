"use client";

import { motion } from "framer-motion";
import Image from "next/image";
import { useLanguage } from "@/i18n/LanguageContext";

export default function Hero() {
  const { t } = useLanguage();

  const stats = [
    { value: t.hero.statFreeValue, label: t.hero.statFreeLabel },
    { value: t.hero.statLangValue, label: t.hero.statLangLabel },
    { value: t.hero.statAiValue, label: t.hero.statAiLabel },
  ];

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-surface-medium via-surface-dark to-surface-darker" />

      <div className="relative z-10 max-w-5xl mx-auto px-6 text-center pt-24 pb-20">
        {/* Logo */}
        <motion.div
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="mb-8"
        >
          <Image
            src="/logo.png"
            alt="Sivi"
            width={100}
            height={100}
            className="mx-auto animate-float drop-shadow-[0_0_40px_rgba(236,72,153,0.3)]"
            priority
          />
        </motion.div>

        {/* Headline */}
        <motion.h1
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-[1.1] mb-6 text-fg"
        >
          {t.hero.titlePre}{" "}
          <span className="gradient-text">{t.hero.titleGradient}</span>
          <br />
          {t.hero.titlePost}
        </motion.h1>

        {/* Subtitle */}
        <motion.p
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.7, delay: 0.4 }}
          className="text-lg sm:text-xl text-fg/60 max-w-2xl mx-auto mb-10 leading-relaxed"
        >
          {t.hero.subtitle}{" "}
          <span className="text-fg/90">{t.hero.subtitleHighlight}</span>
          <br className="hidden sm:block" />
          {t.hero.subtitleEnd}
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.7, delay: 0.6 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <a
            href="https://t.me/SiviAIBot"
            target="_blank"
            rel="noopener noreferrer"
            className="group relative px-8 py-3.5 rounded-full text-base font-semibold text-white bg-gradient-to-r from-brand-400 to-brand-500 hover:from-brand-500 hover:to-brand-600 transition-all duration-300 hover:shadow-[0_0_32px_rgba(236,72,153,0.5)] hover:scale-[1.02]"
          >
            <span className="flex items-center gap-2.5">
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z" />
              </svg>
              {t.hero.cta}
            </span>
          </a>
          <a
            href="#features"
            className="px-8 py-3.5 rounded-full text-base font-medium text-fg/80 border border-fg/15 hover:border-fg/30 hover:text-fg hover:bg-fg/5 transition-all duration-300"
          >
            {t.hero.learnMore}
          </a>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.7, delay: 0.9 }}
          className="mt-20 flex justify-center gap-0 max-w-xl mx-auto"
        >
          {stats.map((stat, i) => (
            <div key={stat.label} className={`text-center flex-1 min-w-0 px-4 sm:px-8 ${i > 0 ? "border-l border-fg/10" : ""}`}>
              <div className="text-lg sm:text-2xl font-bold gradient-text leading-tight">
                {stat.value}
              </div>
              <div className="text-[10px] sm:text-xs text-fg/40 mt-1 uppercase tracking-wide leading-tight">
                {stat.label}
              </div>
            </div>
          ))}
        </motion.div>
      </div>

      {/* Bottom fade — blends hero into page background */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-[var(--bg-canvas)] to-transparent" />
    </section>
  );
}
