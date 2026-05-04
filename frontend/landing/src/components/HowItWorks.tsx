"use client";

import ScrollReveal from "./ScrollReveal";
import { useLanguage } from "@/i18n/LanguageContext";

const stepIcons = [
  <svg key="play" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z" />
  </svg>,
  <svg key="edit" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" />
  </svg>,
  <svg key="sparkle" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 0 0-2.456 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
  </svg>,
  <svg key="grad" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M4.26 10.147a60.438 60.438 0 0 0-.491 6.347A48.62 48.62 0 0 1 12 20.904a48.62 48.62 0 0 1 8.232-4.41 60.46 60.46 0 0 0-.491-6.347m-15.482 0a50.636 50.636 0 0 0-2.658-.813A59.906 59.906 0 0 1 12 3.493a59.903 59.903 0 0 1 10.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.717 50.717 0 0 1 12 13.489a50.702 50.702 0 0 1 7.74-3.342M6.75 15a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm0 0v-3.675A55.378 55.378 0 0 1 12 8.443m-7.007 11.55A5.981 5.981 0 0 0 6.75 15.75v-1.5" />
  </svg>,
];

const numbers = ["01", "02", "03", "04"];

export default function HowItWorks() {
  const { t } = useLanguage();

  const steps = [
    { title: t.howItWorks.step1Title, description: t.howItWorks.step1Desc },
    { title: t.howItWorks.step2Title, description: t.howItWorks.step2Desc },
    { title: t.howItWorks.step3Title, description: t.howItWorks.step3Desc },
    { title: t.howItWorks.step4Title, description: t.howItWorks.step4Desc },
  ];

  return (
    <section id="how-it-works" className="relative py-28 overflow-hidden">
      <div className="relative z-10 max-w-5xl mx-auto px-6">
        <ScrollReveal>
          <div className="text-center mb-16">
            <p className="text-sm uppercase tracking-[0.2em] text-brand-400 font-medium mb-3">
              {t.howItWorks.label}
            </p>
            <h2 className="text-3xl sm:text-4xl font-bold text-fg">
              {t.howItWorks.title}{" "}
              <span className="gradient-text">{t.howItWorks.titleGradient}</span>
            </h2>
          </div>
        </ScrollReveal>

        <div className="relative">
          <div className="absolute left-[27px] top-8 bottom-8 w-px bg-gradient-to-b from-brand-500/40 via-purple-500/40 to-transparent hidden md:block" />

          <div className="space-y-8">
            {steps.map((step, i) => (
              <ScrollReveal key={i} delay={i * 0.12}>
                <div className="flex gap-6 md:gap-8 items-start group">
                  <div className="flex-shrink-0 relative">
                    <div className="w-14 h-14 rounded-2xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400 group-hover:bg-brand-500/20 group-hover:border-brand-500/40 transition-all duration-300 group-hover:shadow-[0_0_20px_rgba(236,72,153,0.2)]">
                      {stepIcons[i]}
                    </div>
                  </div>
                  <div className="flex-1 pb-2">
                    <div className="flex items-baseline gap-3 mb-2">
                      <span className="text-xs font-mono text-brand-500/60 tracking-wider">
                        {numbers[i]}
                      </span>
                      <h3 className="text-lg font-semibold text-fg">
                        {step.title}
                      </h3>
                    </div>
                    <p className="text-fg/60 text-[15px] leading-relaxed max-w-lg">
                      {step.description}
                    </p>
                  </div>
                </div>
              </ScrollReveal>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
