"use client";

import ScrollReveal from "./ScrollReveal";
import { useLanguage } from "@/i18n/LanguageContext";

export default function Video() {
  const { t } = useLanguage();

  return (
    <section className="relative py-20 overflow-hidden">
      <div className="max-w-4xl mx-auto px-6">
        <ScrollReveal>
          <div className="text-center mb-10">
            <p className="text-sm uppercase tracking-[0.2em] text-brand-400 font-medium mb-3">
              {t.video.label}
            </p>
            <h2 className="text-3xl sm:text-4xl font-bold text-white">
              {t.video.title}{" "}
              <span className="gradient-text">{t.video.titleGradient}</span>
            </h2>
          </div>
        </ScrollReveal>

        <ScrollReveal delay={0.2}>
          <div className="relative aspect-video rounded-2xl overflow-hidden glass border border-white/10">
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-surface-medium/80 to-surface-dark/80">
              <div className="w-20 h-20 rounded-full bg-brand-500/20 border border-brand-500/30 flex items-center justify-center mb-5 animate-glow">
                <svg className="w-8 h-8 text-brand-400 ml-1" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
              </div>
              <p className="text-white/40 text-sm tracking-wider uppercase">
                {t.video.placeholder}
              </p>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
