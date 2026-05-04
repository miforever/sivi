"use client";

import ScrollReveal from "./ScrollReveal";
import { useLanguage } from "@/i18n/LanguageContext";

const icons = [
  <svg key="resume" className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
  </svg>,
  <svg key="search" className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
  </svg>,
  <svg key="chat" className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 0 1-.825-.242m9.345-8.334a2.126 2.126 0 0 0-.476-.095 48.64 48.64 0 0 0-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0 0 11.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155" />
  </svg>,
];

const styles = [
  { gradient: "from-brand-400/20 to-purple-500/20", iconBg: "bg-brand-500/15 text-brand-400" },
  { gradient: "from-purple-500/20 to-brand-400/20", iconBg: "bg-purple-500/15 text-purple-400" },
  { gradient: "from-brand-400/20 to-brand-600/20", iconBg: "bg-brand-400/15 text-brand-300" },
];

export default function Features() {
  const { t } = useLanguage();

  const features = [
    { title: t.features.resumeTitle, description: t.features.resumeDesc },
    { title: t.features.jobTitle, description: t.features.jobDesc },
    { title: t.features.interviewTitle, description: t.features.interviewDesc },
  ];

  return (
    <section id="features" className="relative py-28 overflow-hidden">
      <div className="relative z-10 max-w-6xl mx-auto px-6">
        <ScrollReveal>
          <div className="text-center mb-16">
            <p className="text-sm uppercase tracking-[0.2em] text-brand-400 font-medium mb-3">
              {t.features.label}
            </p>
            <h2 className="text-3xl sm:text-4xl font-bold text-fg">
              {t.features.title}{" "}
              <span className="gradient-text">{t.features.titleGradient}</span>
            </h2>
          </div>
        </ScrollReveal>

        <div className="grid md:grid-cols-3 gap-6">
          {features.map((feature, i) => (
            <ScrollReveal key={i} delay={i * 0.15}>
              <div className="group relative h-full p-8 rounded-2xl glass-light hover:bg-fg/[0.04] transition-all duration-500 hover:-translate-y-1">
                <div className={`absolute inset-0 rounded-2xl bg-gradient-to-br ${styles[i].gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500 -z-10 blur-xl`} />
                <div className={`w-14 h-14 rounded-xl ${styles[i].iconBg} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                  {icons[i]}
                </div>
                <h3 className="text-xl font-semibold text-fg mb-3">
                  {feature.title}
                </h3>
                <p className="text-fg/60 leading-relaxed text-[15px]">
                  {feature.description}
                </p>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
