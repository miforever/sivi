"use client";

import Image from "next/image";
import ScrollReveal from "./ScrollReveal";
import { useLanguage } from "@/i18n/LanguageContext";

export default function About() {
  const { t } = useLanguage();

  return (
    <section id="about" className="relative py-28 overflow-hidden">
      <div className="relative z-10 max-w-4xl mx-auto px-6">
        <ScrollReveal>
          <div className="text-center mb-14">
            <p className="text-sm uppercase tracking-[0.2em] text-brand-400 font-medium mb-3">
              {t.about.label}
            </p>
            <h2 className="text-3xl sm:text-4xl font-bold text-fg">
              {t.about.title}{" "}
              <span className="gradient-text">{t.about.titleGradient}</span>{" "}
              {t.about.titlePost}
            </h2>
          </div>
        </ScrollReveal>

        <ScrollReveal delay={0.15}>
          <div className="glass-light rounded-2xl p-8 sm:p-10">
            <div className="max-w-2xl mx-auto text-center">
              <p className="text-fg/60 leading-relaxed mb-6 text-[15px]">
                {t.about.p1}
              </p>
              <p className="text-fg/60 leading-relaxed mb-8 text-[15px]">
                <span className="text-fg/90 font-medium">{t.about.p2Highlight}</span>{" "}
                {t.about.p2}
              </p>

              {/* Founder */}
              <div className="pt-8 border-t border-fg/10">
                <div className="flex flex-col items-center">
                  <div className="w-14 h-14 rounded-full overflow-hidden mb-3">
                    <Image
                      src="/inoyatullo-musayev.jpg"
                      alt="Inoyatullo Musayev"
                      width={56}
                      height={56}
                      className="w-full h-full object-cover"
                    />
                  </div>
                  <p className="text-fg font-semibold">Inoyatullo Musayev</p>
                  <p className="text-fg/50 text-sm">{t.about.founderRole}</p>
                  <p className="text-fg/40 text-xs mt-2 max-w-sm">
                    {t.about.founderBio}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
